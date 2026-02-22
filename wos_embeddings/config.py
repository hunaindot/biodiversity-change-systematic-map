"""Configuration for WoS embeddings generation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None

ENV_PREFIX = "EMBED_"


def _int_env(name: str, default: int, env: os._Environ | dict[str, str]) -> int:
    """Parse integer from environment variable."""
    raw = env.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _bool_env(name: str, default: bool, env: os._Environ | dict[str, str]) -> bool:
    """Parse boolean from environment variable."""
    raw = env.get(name)
    if raw is None:
        return default
    return raw.lower() in ("true", "1", "yes", "on")


def _path_env(name: str, default: str, env: os._Environ | dict[str, str]) -> Path:
    """Parse path from environment variable."""
    raw = env.get(name)
    return Path(raw) if raw else Path(default)


def _str_env(name: str, default: str, env: os._Environ | dict[str, str]) -> str:
    """Parse string from environment variable."""
    return env.get(name, default)


def maybe_load_dotenv(dotenv_path: str | Path | None = None) -> None:
    """Load a .env file if python-dotenv is available. No-op otherwise."""
    if load_dotenv is None:
        return
    load_dotenv(dotenv_path=dotenv_path, override=False)


@dataclass
class EmbedConfig:
    """Configuration for WoS document embedding generation.

    Attributes:
        partitions_base: Base directory containing partition folders (1-234)
        output_base: Base directory for embedding outputs
        model_name: HuggingFace model identifier for embeddings
        embedding_dimension: Expected dimension of output embeddings
        text_prefix: Prefix for text before embedding (required for nomic-embed)
        batch_size: Number of texts to embed in a single batch
        trust_remote_code: Whether to trust remote code for model loading
        resume: Whether to skip already-processed records
        overwrite: Whether to reprocess everything (ignores resume)
        skip_empty_abstracts: Whether to skip records with empty abstracts
        num_workers: Number of workers for data loading (not for embedding)
        save_format: Format for saving embeddings (npz, hdf5, or pickle)
        metadata_format: Format for saving metadata (parquet or csv)
    """

    # Paths
    partitions_base: Path = Path("data/partitions")
    output_base: Path = Path("data/embeddings")

    # Model settings
    model_name: str = "nomic-ai/nomic-embed-text-v1.5"
    embedding_dimension: int = 768
    text_prefix: str = "clustering:"
    trust_remote_code: bool = True

    # Processing settings
    batch_size: int = 8
    resume: bool = True
    overwrite: bool = False
    skip_empty_abstracts: bool = False
    num_workers: int = 4

    # Output format
    save_format: str = "npz"  # npz, hdf5, or pickle
    metadata_format: str = "parquet"  # parquet or csv

    @classmethod
    def from_env(
        cls,
        env: os._Environ | dict[str, str] | None = None,
        dotenv_path: str | Path | None = None,
    ) -> "EmbedConfig":
        """Create config from environment variables.

        Environment variables (all optional, with EMBED_ prefix):
            - EMBED_PARTITIONS_BASE: Path to partitions directory
            - EMBED_OUTPUT_BASE: Path to output directory
            - EMBED_MODEL: Model name/identifier
            - EMBED_BATCH_SIZE: Batch size for embedding
            - EMBED_RESUME: Whether to resume (true/false)
            - EMBED_OVERWRITE: Whether to overwrite (true/false)
            - EMBED_SKIP_EMPTY: Whether to skip empty abstracts (true/false)
            - EMBED_NUM_WORKERS: Number of data loading workers
            - EMBED_SAVE_FORMAT: Format for embeddings (npz/hdf5/pickle)
            - EMBED_METADATA_FORMAT: Format for metadata (parquet/csv)

        Args:
            env: Environment dict (defaults to os.environ)
            dotenv_path: Path to .env file to load

        Returns:
            EmbedConfig with values from environment or defaults
        """
        env = env or os.environ
        maybe_load_dotenv(dotenv_path)
        prefix = ENV_PREFIX

        return cls(
            partitions_base=_path_env(f"{prefix}PARTITIONS_BASE", str(cls.partitions_base), env),
            output_base=_path_env(f"{prefix}OUTPUT_BASE", str(cls.output_base), env),
            model_name=_str_env(f"{prefix}MODEL", cls.model_name, env),
            batch_size=_int_env(f"{prefix}BATCH_SIZE", cls.batch_size, env),
            resume=_bool_env(f"{prefix}RESUME", cls.resume, env),
            overwrite=_bool_env(f"{prefix}OVERWRITE", cls.overwrite, env),
            skip_empty_abstracts=_bool_env(f"{prefix}SKIP_EMPTY", cls.skip_empty_abstracts, env),
            num_workers=_int_env(f"{prefix}NUM_WORKERS", cls.num_workers, env),
            save_format=_str_env(f"{prefix}SAVE_FORMAT", cls.save_format, env),
            metadata_format=_str_env(f"{prefix}METADATA_FORMAT", cls.metadata_format, env),
        )
