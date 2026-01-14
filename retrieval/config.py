from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None

ENV_PREFIX = "RETRIEVAL_"


def _default_threads() -> int:
    cpu = os.cpu_count() or 8
    # Match the notebook logic: cap at 6 and leave a couple cores free.
    return min(6, max(2, cpu - 2))


def _int_env(name: str, default: int, env: os._Environ | dict[str, str]) -> int:
    raw = env.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _path_env(name: str, default: str, env: os._Environ | dict[str, str]) -> Path:
    raw = env.get(name)
    return Path(raw) if raw else Path(default)


def maybe_load_dotenv(dotenv_path: str | Path | None = None) -> None:
    """Load a .env file if python-dotenv is available. No-op otherwise."""
    if load_dotenv is None:
        return
    load_dotenv(dotenv_path=dotenv_path, override=False)


# DEFAULT_STATUSES: list[str] = [
#     "accepted",
#     "synonym",
#     "homotypic synonym",
#     "heterotypic synonym",
#     "proparte synonym",
# ]

DEFAULT_STATUSES: list[str] = []

# DEFAULT_RANKS: list[str] = ["kingdom", "phylum", "class", "order", "genus", "species"]

DEFAULT_RANKS: list[str] = []

DEFAULT_COLUMNS: list[str] = [
    "taxonID",
    "scientificName",
    "scientificNameAuthorship",
    "canonicalName",
    "genericName",
    "specificEpithet",
    "infraspecificEpithet",
    "taxonRank",
    "taxonomicStatus",
    "nomenclaturalStatus",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "vernaculars_named",
    "curated_description",
    "species_id",
    "livingPeriod_curated",
    "lifeForm_curated",
    "habitat_curated",
    "marine_curated",
    "freshwater_curated",
    "terrestrial_curated",
    "extinct_curated",
    "hybrid_curated",
    "ageInDays_curated",
    "sizeInMillimeter_curated",
    "massInGram_curated",
]


@dataclass
class IndexConfig:
    csv_path: Path = Path("data/gbif/curated/gbif_curated.csv")
    index_dir: Path = Path("data/retrieval/tantivy_gbif_taxa_index")
    edge_min: int = 3
    edge_max: int = 10
    num_threads: int = _default_threads()
    heap_size_bytes: int = 1_500_000_000
    chunksize: int = 50_000

    @classmethod
    def from_env(
        cls,
        env: os._Environ | dict[str, str] | None = None,
        dotenv_path: str | Path | None = None,
    ) -> "IndexConfig":
        env = env or os.environ
        maybe_load_dotenv(dotenv_path)
        prefix = ENV_PREFIX
        return cls(
            csv_path=_path_env(f"{prefix}CSV_PATH", str(cls.csv_path), env),
            index_dir=_path_env(f"{prefix}INDEX_DIR", str(cls.index_dir), env),
            edge_min=_int_env(f"{prefix}EDGE_MIN", cls.edge_min, env),
            edge_max=_int_env(f"{prefix}EDGE_MAX", cls.edge_max, env),
            num_threads=_int_env(f"{prefix}NUM_THREADS", cls.num_threads, env),
            heap_size_bytes=_int_env(f"{prefix}HEAP_SIZE_BYTES", cls.heap_size_bytes, env),
            chunksize=_int_env(f"{prefix}CHUNKSIZE", cls.chunksize, env),
        )


@dataclass
class FilterConfig:
    allowed_statuses: Sequence[str] = field(default_factory=lambda: list(DEFAULT_STATUSES))
    allowed_ranks: Sequence[str] = field(default_factory=lambda: list(DEFAULT_RANKS))
    selected_columns: Sequence[str] = field(default_factory=lambda: list(DEFAULT_COLUMNS))

    def status_filter(self, status: str) -> bool:
        return not self.allowed_statuses or status in self.allowed_statuses

    def rank_filter(self, rank: str) -> bool:
        return not self.allowed_ranks or rank in self.allowed_ranks

    def select_columns(self, columns: Iterable[str]) -> list[str]:
        cols = list(columns)
        if not self.selected_columns:
            return cols
        return [c for c in self.selected_columns if c in cols]
