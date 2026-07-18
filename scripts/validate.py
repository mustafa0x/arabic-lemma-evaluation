import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SELECTORS = ("camel-mle", "camel-bert", "alma")
EXPECTED = {
    "query": {
        "rows": 91,
        "adjudicated": 90,
        "lemma": {"camel-mle": 72, "camel-bert": 74, "alma": 71},
        "search_term": {"camel-mle": 79, "camel-bert": 83, "alma": 79},
    },
    "context": {
        "rows": 473,
        "adjudicated": 473,
        "lemma": {"camel-mle": 369, "camel-bert": 376, "alma": 379},
        "search_term": {"camel-mle": 401, "camel-bert": 410, "alma": 412},
    },
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as input_file:
        while chunk := input_file.read(8 * 1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def ranked_signature(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in result.items() if key != "elapsed_seconds"}
        for result in report["results"]
    ]


def verify_ranked_reports() -> None:
    cases_path = ROOT / "cases" / "camel-bert-context.jsonl"
    reports = [
        load_json(ROOT / "results" / "camel-tools-1.5.7-ranked.json"),
        load_json(ROOT / "results" / "camel-tools-1.6.0-ranked.json"),
    ]
    case_rows = [
        json.loads(line) for line in cases_path.read_text().splitlines() if line.strip()
    ]
    expected_cases = [{"id": row["id"], "text": row["text"]} for row in case_rows]

    for report in reports:
        assert report["cases"]["sha256"] == digest(cases_path)
        actual_cases = [
            {"id": row["id"], "text": row["text"]} for row in report["results"]
        ]
        assert actual_cases == expected_cases
        assert report["runtime"]["top"] == 5
        assert report["runtime"]["pretrained_cache"] is False

    assert ranked_signature(reports[0]) == ranked_signature(reports[1])

    selected = {}
    for result in reports[1]["results"]:
        selected[result["id"]] = [
            token["analyses"][0]["analysis"]["lex"] for token in result["tokens"]
        ]
    assert selected["isolated_audhu"] == ["عاذ"]
    assert selected["diacritized_qul_audhu"] == ["قال", "اعوذ"]
    assert selected["diacritized_qul_audhu_birabbi"] == ["قال", "عاذ", "رَبّ"]


def judged_candidate(row: dict[str, str]) -> dict[str, Any] | None:
    if row["judgment"] in ("UNCERTAIN", "ALL_WRONG"):
        return None
    candidates = json.loads(row["candidates_json"])
    return next(
        candidate for candidate in candidates if candidate["label"] == row["judgment"]
    )


def score_comparison(scope: str) -> dict[str, Any]:
    report = load_json(ROOT / "comparison" / f"{scope}-analyses.json")
    with (ROOT / "comparison" / f"{scope}-grades.csv").open(newline="") as input_file:
        grades = list(csv.DictReader(input_file))

    queries = {query["id"]: query for query in report["queries"]}
    scores = {
        "rows": len(grades),
        "adjudicated": 0,
        "lemma": {selector: 0 for selector in SELECTORS},
        "search_term": {selector: 0 for selector in SELECTORS},
    }

    for row in grades:
        if row["judgment"] == "UNCERTAIN":
            continue
        scores["adjudicated"] += 1
        chosen = judged_candidate(row)
        wanted_search_term = row["canonical_search_term"] or (
            chosen["production_search_term"] if chosen else ""
        )
        token_index = int(row["token_index"])
        for selector in SELECTORS:
            token = queries[row["query_id"]]["analyses"][selector]["tokens"][
                token_index
            ]
            if chosen and (
                token["lexical_identity"],
                token["selection_status"],
            ) == (
                chosen["lexical_identity"],
                chosen["selection_status"],
            ):
                scores["lemma"][selector] += 1
            if token["production_search_term"] == wanted_search_term:
                scores["search_term"][selector] += 1

    return scores


def verify_comparison_inputs() -> None:
    query_report = load_json(ROOT / "comparison" / "query-analyses.json")
    context_report = load_json(ROOT / "comparison" / "context-analyses.json")
    renamed_inputs = {
        "queries.jsonl": ROOT / "comparison" / "search-queries.jsonl",
        "representative.jsonl": ROOT / "comparison" / "representative-queries.jsonl",
    }
    for original_name, expected_hash in query_report["query_files"].items():
        assert digest(renamed_inputs[original_name]) == expected_hash
    assert digest(ROOT / "comparison" / "context-passages.jsonl") == next(
        iter(context_report["query_files"].values())
    )
    assert (
        digest(ROOT / "comparison" / "query-ballot.csv")
        == query_report["grading"]["csv"]["sha256"]
    )
    assert (
        digest(ROOT / "comparison" / "context-ballot.csv")
        == context_report["grading"]["csv"]["sha256"]
    )
    assert (
        digest(ROOT / "comparison" / "query-analyzer-map.json")
        == query_report["grading"]["private_key"]["sha256"]
    )
    assert (
        digest(ROOT / "comparison" / "context-analyzer-map.json")
        == context_report["grading"]["private_key"]["sha256"]
    )


def main() -> int:
    verify_ranked_reports()
    verify_comparison_inputs()
    for scope in ("query", "context"):
        actual = score_comparison(scope)
        assert actual == EXPECTED[scope], (scope, actual, EXPECTED[scope])
        print(f"{scope}: {actual['adjudicated']} adjudicated tokens")
        print(f"  lemma: {actual['lemma']}")
        print(f"  search term: {actual['search_term']}")
    print("ranked reports and comparison artifacts are internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
