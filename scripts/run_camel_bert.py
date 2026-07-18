import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from camel_tools.data import CATALOGUE
from camel_tools.disambig.bert import BERTUnfactoredDisambiguator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe CAMeL BERT against frozen sentence cases"
    )
    parser.add_argument("cases", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--pretrained-cache", action="store_true")
    return parser.parse_args()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as input_file:
        while chunk := input_file.read(8 * 1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def dataset_files(dataset_name: str, model_name: str) -> list[dict[str, Any]]:
    root = Path(CATALOGUE.get_dataset(dataset_name, model_name).path)
    return [
        {"path": str(path), "size": path.stat().st_size, "sha256": digest(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def analysis_result(scored_analysis: Any) -> dict[str, Any]:
    analysis = scored_analysis.analysis
    return {
        "score": scored_analysis.score,
        "analysis": {
            key: analysis.get(key)
            for key in ("lex", "source", "stemgloss", "pos", "root", "pattern")
        },
    }


def word_result(word: Any) -> dict[str, Any]:
    return {
        "surface": word.word,
        "analyses": [analysis_result(analysis) for analysis in word.analyses],
    }


def main() -> int:
    args = parse_args()
    cases = [
        json.loads(line) for line in args.cases.read_text().splitlines() if line.strip()
    ]
    started = perf_counter()
    disambiguator = BERTUnfactoredDisambiguator.pretrained(
        top=args.top,
        use_gpu=False,
        pretrained_cache=args.pretrained_cache,
    )
    load_seconds = perf_counter() - started
    results = []
    for case in cases:
        started = perf_counter()
        words = disambiguator.disambiguate(case["text"].split())
        results.append(
            case
            | {
                "elapsed_seconds": round(perf_counter() - started, 6),
                "tokens": [word_result(word) for word in words],
            }
        )
    model_config = json.loads(
        (
            Path(CATALOGUE.get_dataset("DisambigBertUnfactored", "msa").path)
            / "default_config.json"
        ).read_text()
    )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": {
            "python": platform.python_version(),
            "camel_tools": importlib.metadata.version("camel-tools"),
            "torch": importlib.metadata.version("torch"),
            "transformers": importlib.metadata.version("transformers"),
            "top": args.top,
            "pretrained_cache": args.pretrained_cache,
            "load_seconds": round(load_seconds, 6),
        },
        "cases": {"path": str(args.cases), "sha256": digest(args.cases)},
        "model_config": model_config,
        "model_files": dataset_files("DisambigBertUnfactored", "msa"),
        "morphology_files": dataset_files("MorphologyDB", model_config["db_name"]),
        "results": results,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
