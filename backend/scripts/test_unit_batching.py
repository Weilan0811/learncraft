from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def configure_imports() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test unit batching strategy.")
    parser.add_argument("--concurrency", type=int, default=3, help="Batch size / future unit concurrency.")
    parser.add_argument("--unit-count", type=int, default=7, help="Number of sample units.")
    parser.add_argument("--output-dir", default=None, help="Directory for the result JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    configure_imports()

    from app.workflows.parallel_units import build_unit_batches

    unit_ids = [f"unit-{index:02d}" for index in range(1, args.unit_count + 1)]
    batches = build_unit_batches(unit_ids, concurrency=args.concurrency)
    flattened = [unit_id for batch in batches for unit_id in batch]
    max_batch_size = max((len(batch) for batch in batches), default=0)
    result = {
        "case": "unit_batching",
        "concurrency": args.concurrency,
        "unit_count": args.unit_count,
        "batches": batches,
        "max_batch_size": max_batch_size,
        "preserves_order": flattened == unit_ids,
        "passed": flattened == unit_ids and max_batch_size <= max(1, args.concurrency),
    }
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / "concurrency_test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "unit_batching.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**result, "output_path": str(output_path)}, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
