"""Repository contract: results consume prepared data, never raw coding joins."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "notebooks" / "results"
FORBIDDEN_CODE = (
    "build_merged_corpus(",
    "get_merged_corpus_config",
    "from data_helpers.prep.corpus import",
    "from data_helpers.prep import corpus",
    "data/coding-",
    "data/screening/",
    "data/gbif/",
)


def test_results_notebooks_do_not_load_raw_corpus_or_taxa_sources() -> None:
    violations: list[str] = []
    notebooks = sorted(RESULTS_DIR.glob("*.ipynb"))
    assert notebooks, "No results notebooks found."

    for path in notebooks:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        code = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        )
        for forbidden in FORBIDDEN_CODE:
            if forbidden in code:
                violations.append(f"{path.name}: {forbidden}")

    assert not violations, (
        "Results notebooks must load prepared data-processing artifacts. "
        f"Raw-source references found: {violations}"
    )
