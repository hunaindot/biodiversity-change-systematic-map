# WoS Embeddings

Generate embeddings for Web of Science (WoS) research articles using `nomic-ai/nomic-embed-text-v1.5`.

This package processes ~2.34 million research articles across 234 partitions, embedding the combination of article titles and abstracts. It supports incremental processing with resume capability, making it robust for long-running batch jobs.

## Features

- **High-quality embeddings**: Uses nomic-embed-text-v1.5 (768-dimensional embeddings)
- **Incremental processing**: Resume from interruptions without reprocessing
- **Progress tracking**: JSON-based progress tracking for each partition
- **Efficient storage**: NPZ compressed format for embeddings, Parquet for metadata
- **Batch processing**: Memory-efficient batching for large datasets
- **CLI & Python API**: Use from command line or import as a library

## Installation

### Dependencies

```bash
pip install sentence-transformers torch numpy pandas pyarrow tqdm
```

Or if you have a `requirements.txt`:
```
sentence-transformers>=2.0.0
torch>=2.0.0
numpy>=1.24.0
pandas>=2.0.0
pyarrow>=10.0.0
tqdm>=4.65.0
```

## Quick Start

### Python API

```python
from wos_embeddings import process_partition, EmbedConfig

# Process a single partition
config = EmbedConfig()
summary = process_partition("1", config)

# Process multiple partitions
from wos_embeddings import process_partitions
results = process_partitions(["1", "2", "3"], config)

# Process all partitions
from wos_embeddings import process_all_partitions
results = process_all_partitions(config, start=1, end=234)
```

### Command Line

```bash
# Process a single partition
python -m wos_embeddings process --partition 1

# Process a range of partitions
python -m wos_embeddings process --start 1 --end 10

# Process all partitions
python -m wos_embeddings process-all

# Verify outputs
python -m wos_embeddings verify 1

# Show statistics
python -m wos_embeddings stats 1
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
EMBED_PARTITIONS_BASE=data/partitions
EMBED_OUTPUT_BASE=data/embeddings
EMBED_MODEL=nomic-ai/nomic-embed-text-v1.5
EMBED_BATCH_SIZE=64
EMBED_RESUME=true
EMBED_SKIP_EMPTY=false
```

### Python Configuration

```python
from wos_embeddings import EmbedConfig

config = EmbedConfig(
    partitions_base="data/partitions",
    output_base="data/embeddings",
    model_name="nomic-ai/nomic-embed-text-v1.5",
    text_prefix="clustering:",  # Task prefix for embeddings
    batch_size=64,
    resume=True,  # Skip already-processed records
    overwrite=False,  # Set True to reprocess everything
    skip_empty_abstracts=False,  # Set True to skip records with no abstract
)
```

## Data Structure

### Input

Each partition folder (`data/partitions/1/`, `data/partitions/2/`, etc.) contains a single Excel file with columns:
- `Article Title` - Article title
- `Abstract` - Article abstract
- `UT (Unique WOS ID)` - Unique identifier

### Output

For each partition (`data/embeddings/1/`, `data/embeddings/2/`, etc.):

#### `embeddings.npz`
Compressed NumPy array containing:
- `embeddings`: (N, 768) float32 array of embeddings
- `record_ids`: (N,) array of UT IDs

#### `metadata.parquet`
Parquet file with columns:
- `ut`: UT (Unique WOS ID)
- `title`: Article title
- `abstract`: Article abstract
- `combined_text`: The actual text that was embedded
- `embedding_index`: Index into embeddings array
- `text_length`: Character count of combined text
- `processed_at`: Timestamp when processed

#### `meta.json`
Progress tracking with:
- `partition_name`: Partition identifier
- `total_records`: Total records in partition
- `processed_records`: Number of successfully processed records
- `failed_records`: Number of failed records
- `processing_status`: Current status (pending/in_progress/completed/failed)
- `processed_ut_ids`: List of processed UT IDs (for resume capability)
- `model_name`: Embedding model used
- `embedding_dimension`: Dimension of embeddings

## Loading Results

```python
from wos_embeddings import load_embeddings, load_metadata, EmbedConfig

config = EmbedConfig()

# Load embeddings for partition 1
embeddings_data = load_embeddings("1", config)
embeddings = embeddings_data['embeddings']  # (N, 768) numpy array
record_ids = embeddings_data['record_ids']  # List of UT IDs

# Load metadata
metadata = load_metadata("1", config)  # pandas DataFrame
```

## Incremental Processing

The package automatically tracks which records have been processed. If processing is interrupted:

1. Progress is saved to `meta.json` after each batch
2. On restart, already-processed records are skipped
3. Processing continues from where it left off

To force reprocessing:
```python
config = EmbedConfig(overwrite=True)
process_partition("1", config)
```

## Text Preparation

For each record:
1. Combine `Article Title` and `Abstract`
2. Add the prefix `clustering:` (required by nomic-embed-text-v1.5)
3. Generate embedding using sentence-transformers

Example:
```
Input:
  Title: "Climate change impacts on biodiversity"
  Abstract: "This study examines..."

Combined text for embedding:
  "clustering: Climate change impacts on biodiversity This study examines..."
```

## Performance

- **Per partition**: ~1-2 minutes (10,000 records)
- **All 234 partitions**: ~4-8 hours (sequential processing)
- **Disk space**: ~4-5 GB total for all embeddings and metadata
- **Memory usage**: ~2-3 GB peak (model + single partition in memory)

## CLI Reference

### `process`
Process a single partition or range of partitions.

```bash
python -m wos_embeddings process --partition 1
python -m wos_embeddings process --start 1 --end 10
python -m wos_embeddings process --partition 1 --batch-size 128
python -m wos_embeddings process --partition 1 --no-resume
python -m wos_embeddings process --partition 1 --overwrite
```

### `process-all`
Process all partitions (1-234).

```bash
python -m wos_embeddings process-all
python -m wos_embeddings process-all --start 50 --end 100
python -m wos_embeddings process-all --batch-size 128
```

### `verify`
Verify that outputs are consistent.

```bash
python -m wos_embeddings verify 1
```

Checks:
- Embeddings file exists and is valid
- Metadata file exists and is valid
- Number of embeddings matches metadata rows
- Record IDs are consistent

### `stats`
Show processing statistics for a partition.

```bash
python -m wos_embeddings stats 1
```

Displays:
- Processing status
- Total/processed/failed/remaining records
- Progress percentage
- Last update timestamp

## API Reference

### `process_partition(partition_name, config, show_progress)`
Process a single partition.

**Args:**
- `partition_name` (str): Partition identifier (e.g., "1", "50")
- `config` (EmbedConfig): Configuration object
- `show_progress` (bool): Whether to show progress bar

**Returns:** Dictionary with processing summary

### `process_partitions(partition_names, config, show_progress)`
Process multiple partitions sequentially.

**Args:**
- `partition_names` (list or range): List of partition identifiers
- `config` (EmbedConfig): Configuration object
- `show_progress` (bool): Whether to show progress bar

**Returns:** Dictionary mapping partition names to summaries

### `process_all_partitions(config, start, end, show_progress)`
Process all partitions from start to end.

**Args:**
- `config` (EmbedConfig): Configuration object
- `start` (int): First partition number (default: 1)
- `end` (int): Last partition number (default: 234)
- `show_progress` (bool): Whether to show progress bar

**Returns:** Dictionary mapping partition names to summaries

### `load_embeddings(partition_name, config)`
Load embeddings from disk.

**Args:**
- `partition_name` (str): Partition identifier
- `config` (EmbedConfig): Configuration object

**Returns:** Dict with 'embeddings' (np.ndarray) and 'record_ids' (list)

### `load_metadata(partition_name, config)`
Load metadata from disk.

**Args:**
- `partition_name` (str): Partition identifier
- `config` (EmbedConfig): Configuration object

**Returns:** pandas DataFrame with metadata

## Error Handling

The package handles common errors gracefully:

- **Missing partition files**: Skipped with warning
- **Empty abstracts**: Uses title only (or skips if `skip_empty_abstracts=True`)
- **Processing failures**: Failed records tracked in `meta.json`
- **Interruptions**: Progress saved after each batch, can resume

## Troubleshooting

### Model download fails
The first run downloads the model (~500MB). If it fails:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
```

### Out of memory
Reduce batch size:
```python
config = EmbedConfig(batch_size=32)  # Default is 64
```

### Resume not working
Check `meta.json` in the partition output folder. Delete it to start fresh:
```bash
rm data/embeddings/1/meta.json
```

## License

Part of the biodiversity research project.
