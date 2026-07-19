import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

from camel_tools.data import CATALOGUE
from camel_tools.disambig.bert import BERTUnfactoredDisambiguator
from camel_tools.disambig.score_function import FEATURE_SET_MAP
from camel_tools.utils.dediac import dediac_ar

ROOT = Path(__file__).resolve().parents[1]
TOP = 5
BATCH_SIZE = 32


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rerun the frozen CAMeL BERT context cases"
    )
    parser.add_argument("cases", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as input_file:
        while chunk := input_file.read(8 * 1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def load_cases(path: Path) -> list[dict]:
    cases = []
    seen_ids = set()
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        case_id = case.get("id") if isinstance(case, dict) else None
        text = case.get("text") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"{path}:{line_number}: missing non-empty string id")
        if not isinstance(text, str) or not text:
            raise ValueError(f"{path}:{line_number}: missing non-empty string text")
        if case_id in seen_ids:
            raise ValueError(f"{path}:{line_number}: duplicate id {case_id!r}")
        seen_ids.add(case_id)
        cases.append({"id": case_id, "text": text})
    if not cases:
        raise ValueError(f"{path}: no cases found")
    return cases


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def dataset_files(dataset_name: str, model_name: str) -> list[dict]:
    root = Path(CATALOGUE.get_dataset(dataset_name, model_name).path)
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def scoring_values(values: dict, feature_names: list[str]) -> dict[str, str]:
    missing = [name for name in feature_names if name not in values]
    if missing:
        raise RuntimeError(f"BERT prediction is missing scoring features: {missing}")
    return {name: values[name] for name in feature_names}


def summarize_analysis(scored_analysis, prediction: dict, features: list[str]) -> dict:
    analysis = scored_analysis.analysis
    candidate_features = {name: analysis.get(name, "") for name in features}
    return {
        "score": float(scored_analysis.score),
        "feature_match_count": sum(
            candidate_features[name] == prediction[name] for name in features
        ),
        "scoring_features": candidate_features,
        "analysis": {
            name: analysis.get(name)
            for name in ("lex", "source", "stemgloss", "pos", "root", "pattern")
        },
    }


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    reserved = {
        args.cases.resolve(),
        (ROOT / "results" / "camel-tools-1.5.7-ranked.json").resolve(),
        (ROOT / "results" / "camel-tools-1.6.0-ranked.json").resolve(),
    }
    if output in reserved:
        raise SystemExit("--output must not overwrite the cases or historical reports")

    cases = load_cases(args.cases)
    model_root = Path(CATALOGUE.get_dataset("DisambigBertUnfactored", "msa").path)
    model_config = json.loads((model_root / "default_config.json").read_text())
    feature_set = model_config["feature"]
    if feature_set not in FEATURE_SET_MAP:
        raise ValueError(f"unknown CAMeL scoring feature set: {feature_set!r}")
    feature_names = list(FEATURE_SET_MAP[feature_set])

    disambiguator = BERTUnfactoredDisambiguator.pretrained(
        model_name="msa",
        top=TOP,
        use_gpu=False,
        batch_size=BATCH_SIZE,
        pretrained_cache=False,
        cache_size=0,
        ranking_cache_size=0,
    )

    results = []
    for case in cases:
        tokens = case["text"].split()
        bert_tokens = [dediac_ar(token) or token for token in tokens]
        predictions = disambiguator.tag_sentence(bert_tokens, use_analyzer=False)
        words = disambiguator.disambiguate(tokens)
        if not (len(tokens) == len(predictions) == len(words)):
            raise RuntimeError(f"{case['id']}: token and output counts differ")

        token_results = []
        for word, bert_token, prediction in zip(
            words, bert_tokens, predictions, strict=True
        ):
            prediction = scoring_values(prediction, feature_names)
            token_results.append(
                {
                    "surface": word.word,
                    "bert_input": bert_token,
                    "predicted_features": prediction,
                    "analyses": [
                        summarize_analysis(analysis, prediction, feature_names)
                        for analysis in word.analyses
                    ],
                }
            )

        results.append(
            case
            | {
                "input_tokens": tokens,
                "bert_input_tokens": bert_tokens,
                "tokens": token_results,
            }
        )

    report = {
        "schema_version": 2,
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform() or "unknown",
            "camel_tools": importlib.metadata.version("camel-tools"),
            "torch": importlib.metadata.version("torch"),
            "transformers": importlib.metadata.version("transformers"),
            "device": "cpu",
            "model_name": "msa",
            "top": TOP,
            "batch_size": BATCH_SIZE,
            "pretrained_cache": False,
            "analyzer_cache_size": 0,
            "ranking_cache_size": 0,
            "scoring_features": feature_names,
            "prediction_capture": (
                "separate tag_sentence(use_analyzer=False) pass over "
                "dediacritized tokens"
            ),
        },
        "cases": {"path": display_path(args.cases), "sha256": sha256(args.cases)},
        "model_config": model_config,
        "model_files": dataset_files("DisambigBertUnfactored", "msa"),
        "morphology_files": dataset_files("MorphologyDB", model_config["db_name"]),
        "results": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
