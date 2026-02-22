"""WoS Document Embeddings Package

Generate embeddings for Web of Science research articles using nomic-embed-text-v1.5.
Supports incremental processing with resume capability for ~2.34M records across 234 partitions.
"""

from .config import EmbedConfig
from .processor import process_partition, process_partitions, process_all_partitions
from .storage import load_embeddings, load_metadata

__all__ = [
    "EmbedConfig",
    "process_partition",
    "process_partitions",
    "process_all_partitions",
    "load_embeddings",
    "load_metadata",
]

__version__ = "0.1.0"
