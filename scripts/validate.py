import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("camel-mle", "camel-bert", "alma")
EXPECTED = {
    "query": {
        "rows": 91,
        "decided": 90,
        "lexical_rows": 88,
        "lexical": {"camel-mle": 71, "camel-bert": 72, "alma": 71},
        "search": {"camel-mle": 79, "camel-bert": 83, "alma": 79},
        "deltas": {"bert_fix": 4, "bert_regression": 3},
    },
    "context": {
        "rows": 473,
        "decided": 473,
        "lexical_rows": 468,
        "lexical": {"camel-mle": 367, "camel-bert": 373, "alma": 378},
        "search": {"camel-mle": 401, "camel-bert": 410, "alma": 412},
        "deltas": {"bert_fix": 16, "bert_regression": 10},
    },
}
FOCUS = {
    ("isolated_audhu", 0): [
        ("عاذ", "lex", "verb", 1.0),
        ("عَوَّذ", "lex", "verb", 1.0),
    ],
    ("diacritized_qul_audhu", 1): [
        ("اعوذ", "backoff", "noun_prop", 1.0),
        ("عاذ", "lex", "verb", 0.6363636363643478),
    ],
    ("diacritized_qul_audhu_birabbi", 1): [
        ("عاذ", "lex", "verb", 1.0),
        ("عَوَّذ", "lex", "verb", 1.0),
    ],
}
SOURCE_FILES = {
    "query": {
        "queries.jsonl": "search-queries.jsonl",
        "representative.jsonl": "representative-queries.jsonl",
    },
    "context": {"lemma-context-sample-v2-20260718.jsonl": "context-passages.jsonl"},
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the committed lemma-evaluation artifacts"
    )
    parser.add_argument(
        "--ranked-report",
        action="append",
        default=[],
        type=Path,
        help="also compare a new focused report; may be repeated",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as input_file:
        while chunk := input_file.read(8 * 1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    check(isinstance(value, dict), f"{path}: expected a JSON object")
    return value


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as input_file:
        return list(csv.DictReader(input_file))


def ranking_signature(report: dict) -> list[dict]:
    return [
        {
            "id": result["id"],
            "text": result["text"],
            "tokens": [
                {
                    "surface": token["surface"],
                    "analyses": [
                        {"score": item["score"], "analysis": item["analysis"]}
                        for item in token["analyses"]
                    ],
                }
                for token in result["tokens"]
            ],
        }
        for result in report["results"]
    ]


def data_identity(records: list[dict]) -> list[tuple[int, str]]:
    return sorted((record["size"], record["sha256"]) for record in records)


def load_ranked_report(path: Path, cases: list[dict], cases_hash: str) -> dict:
    report = load_json(path)
    check(report["cases"]["sha256"] == cases_hash, f"{path}: cases hash differs")
    check(report["runtime"]["top"] == 5, f"{path}: expected top=5")
    check(
        report["runtime"]["pretrained_cache"] is False,
        f"{path}: pretrained cache must be disabled",
    )
    expected = [(case["id"], case["text"]) for case in cases]
    actual = [(result["id"], result["text"]) for result in report["results"]]
    check(actual == expected, f"{path}: cases or order differ")
    return report


def validate_focused_reports() -> tuple[list[dict], list[dict]]:
    cases_path = ROOT / "camel-bert-context.jsonl"
    cases = load_jsonl(cases_path)
    reports = [
        load_ranked_report(path, cases, sha256(cases_path))
        for path in (
            ROOT / "camel-tools-1.5.7-ranked.json",
            ROOT / "camel-tools-1.6.0-ranked.json",
        )
    ]

    check(
        reports[0]["model_config"] == reports[1]["model_config"],
        "historical model configurations differ",
    )
    check(reports[1]["model_config"]["backoff"] == "ADD_PROP", "backoff differs")
    for key in ("model_files", "morphology_files"):
        check(
            data_identity(reports[0][key]) == data_identity(reports[1][key]),
            f"historical {key} differ",
        )
    check(
        ranking_signature(reports[0]) == ranking_signature(reports[1]),
        "historical ranked outputs differ",
    )

    by_id = {result["id"]: result for result in reports[1]["results"]}
    for (case_id, token_index), expected in FOCUS.items():
        analyses = by_id[case_id]["tokens"][token_index]["analyses"][:2]
        for rank, (item, wanted) in enumerate(zip(analyses, expected, strict=True), 1):
            analysis = item["analysis"]
            actual = (analysis["lex"], analysis["source"], analysis["pos"])
            check(actual == wanted[:3], f"{case_id}: unexpected rank {rank}")
            check(
                math.isclose(item["score"], wanted[3], rel_tol=0, abs_tol=1e-12),
                f"{case_id}: unexpected score at rank {rank}",
            )
    return cases, reports


def compare_new_report(path: Path, cases: list[dict], historical: dict) -> None:
    cases_path = ROOT / "camel-bert-context.jsonl"
    report = load_ranked_report(path, cases, sha256(cases_path))
    rankings = (
        "match"
        if ranking_signature(report) == ranking_signature(historical)
        else "differ"
    )
    model_data = (
        "match"
        if report["model_config"] == historical["model_config"]
        and data_identity(report["model_files"])
        == data_identity(historical["model_files"])
        and data_identity(report["morphology_files"])
        == data_identity(historical["morphology_files"])
        else "differ"
    )
    print(f"{path}: valid; rankings {rankings}; model data {model_data}")


def verify_recorded_hashes(scope: str, report: dict) -> None:
    for recorded_name, local_name in SOURCE_FILES[scope].items():
        path = ROOT / "comparison" / local_name
        check(
            sha256(path) == report["query_files"][recorded_name],
            f"{scope}: source hash differs for {local_name}",
        )
    for key, suffix in (("csv", "ballot.csv"), ("private_key", "analyzer-map.json")):
        path = ROOT / "comparison" / f"{scope}-{suffix}"
        check(
            sha256(path) == report["grading"][key]["sha256"],
            f"{scope}: recorded hash differs for {path.name}",
        )


def chosen_candidate(row: dict[str, str]) -> dict | None:
    if row["judgment"] in ("ALL_WRONG", "UNCERTAIN"):
        return None
    candidates = json.loads(row["candidates_json"])
    matches = [item for item in candidates if item["label"] == row["judgment"]]
    check(len(matches) == 1, f"{row['comparison_id']}: invalid judgment")
    return matches[0]


def lexical_match(token: dict, candidate: dict) -> bool:
    return (
        token["selection_status"] == "selected"
        and token["lexical_identity"] == candidate["lexical_identity"]
    )


def score_scope(scope: str) -> dict:
    report = load_json(ROOT / "comparison" / f"{scope}-analyses.json")
    verify_recorded_hashes(scope, report)
    grades = load_csv(ROOT / "comparison" / f"{scope}-grades.csv")
    queries = {query["id"]: query for query in report["queries"]}
    metrics = {
        "rows": len(grades),
        "decided": 0,
        "lexical_rows": 0,
        "lexical": {system: 0 for system in SYSTEMS},
        "search": {system: 0 for system in SYSTEMS},
        "deltas": Counter(),
    }

    for grade in grades:
        if grade["judgment"] == "UNCERTAIN":
            continue
        metrics["decided"] += 1
        gold = chosen_candidate(grade)
        if grade["judgment"] == "ALL_WRONG":
            lexical_gold = True
            expected_search = grade["canonical_search_term"]
        else:
            lexical_gold = gold["selection_status"] == "selected"
            expected_search = gold["production_search_term"]
        if lexical_gold:
            metrics["lexical_rows"] += 1

        query = queries[grade["query_id"]]
        token_index = int(grade["token_index"])
        tokens = {
            system: query["analyses"][system]["tokens"][token_index]
            for system in SYSTEMS
        }
        correct = {
            system: gold is not None and lexical_match(token, gold)
            for system, token in tokens.items()
        }
        for system, token in tokens.items():
            if lexical_gold and correct[system]:
                metrics["lexical"][system] += 1
            if token["production_search_term"] == expected_search:
                metrics["search"][system] += 1

        if gold is not None and gold["selection_status"] == "selected":
            mle_correct = correct["camel-mle"]
            bert_correct = correct["camel-bert"]
            if mle_correct != bert_correct:
                key = "bert_fix" if bert_correct else "bert_regression"
                metrics["deltas"][key] += 1

    metrics["deltas"] = {
        "bert_fix": metrics["deltas"]["bert_fix"],
        "bert_regression": metrics["deltas"]["bert_regression"],
    }
    check(metrics == EXPECTED[scope], f"{scope}: reproduced totals differ: {metrics}")
    return metrics


def print_metrics(scope: str, metrics: dict) -> None:
    print(
        f"{scope}: lexical {metrics['lexical']} / {metrics['lexical_rows']}; "
        f"search {metrics['search']} / {metrics['decided']}; "
        f"BERT vs MLE {metrics['deltas']['bert_fix']} fixes, "
        f"{metrics['deltas']['bert_regression']} regressions"
    )


def main() -> int:
    args = parse_args()
    try:
        cases, reports = validate_focused_reports()
        for scope in ("query", "context"):
            print_metrics(scope, score_scope(scope))
        for path in args.ranked_report:
            compare_new_report(path, cases, reports[1])
        print("committed focused and comparison artifacts are consistent")
        return 0
    except (IndexError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
