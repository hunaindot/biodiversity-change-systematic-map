from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .candidates import extract_taxon_candidates
from .config import FilterConfig, IndexConfig
from .indexing import build_index
from .search import TaxonSearcher


def _index_config_from_args(args: argparse.Namespace) -> IndexConfig:
    cfg = IndexConfig.from_env()
    if args.csv_path:
        cfg.csv_path = Path(args.csv_path)
    if args.index_dir:
        cfg.index_dir = Path(args.index_dir)
    if args.edge_min is not None:
        cfg.edge_min = args.edge_min
    if args.edge_max is not None:
        cfg.edge_max = args.edge_max
    if args.num_threads is not None:
        cfg.num_threads = args.num_threads
    if args.heap_size_bytes is not None:
        cfg.heap_size_bytes = args.heap_size_bytes
    if args.chunksize is not None:
        cfg.chunksize = args.chunksize
    return cfg


def cmd_build(args: argparse.Namespace) -> None:
    cfg = _index_config_from_args(args)
    filters = FilterConfig()
    index = build_index(cfg, filters, reset=not args.no_reset)
    print(f"Index built at {cfg.index_dir.resolve()}")
    print(f"Schema fields: {list(index.schema().fields())}")


def cmd_search(args: argparse.Namespace) -> None:
    cfg = IndexConfig.from_env()
    if args.index_dir:
        cfg.index_dir = Path(args.index_dir)
    searcher = TaxonSearcher(cfg.index_dir)
    results = searcher.search(args.query, limit=args.limit)
    for res in results:
        print(
            f"{res.score:.2f} | taxon_id={res.taxon_id} | rank={res.taxon_rank} | "
            f"status={res.taxonomic_status} | sci={res.scientific_name} | canon={res.canonical_name}"
        )


def cmd_candidates(args: argparse.Namespace) -> None:
    if args.text:
        text = args.text
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    cands = extract_taxon_candidates(text, max_terms=args.max_terms)
    for cand in cands:
        print(cand)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tantivy taxonomy retrieval helpers.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build-index", help="Build the Tantivy index from the curated CSV.")
    p_build.add_argument("--csv-path", type=str, help="Override CSV path (default: env or config default).")
    p_build.add_argument("--index-dir", type=str, help="Override index directory.")
    p_build.add_argument("--edge-min", type=int, help="Minimum edge n-gram length.")
    p_build.add_argument("--edge-max", type=int, help="Maximum edge n-gram length.")
    p_build.add_argument("--num-threads", type=int, help="Writer thread count.")
    p_build.add_argument("--heap-size-bytes", type=int, help="Writer heap size in bytes.")
    p_build.add_argument("--chunksize", type=int, help="pandas read_csv chunk size.")
    p_build.add_argument("--no-reset", action="store_true", help="Do not delete an existing index directory first.")
    p_build.set_defaults(func=cmd_build)

    p_search = sub.add_parser("search", help="Run a quick search against the built index.")
    p_search.add_argument("query", type=str, help="Query string (Tantivy query syntax).")
    p_search.add_argument("--index-dir", type=str, help="Override index directory.")
    p_search.add_argument("--limit", type=int, default=10, help="Maximum results to return.")
    p_search.set_defaults(func=cmd_search)

    p_cand = sub.add_parser("candidates", help="Extract likely taxon mentions from text.")
    p_cand.add_argument("--text", type=str, help="Raw text to scan (if omitted, reads stdin).")
    p_cand.add_argument("--file", type=str, help="Path to a file containing text.")
    p_cand.add_argument("--max-terms", type=int, default=80, help="Maximum candidates to return.")
    p_cand.set_defaults(func=cmd_candidates)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
