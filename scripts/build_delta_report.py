import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "camel-mle-vs-bert-lexical-deltas.csv"
FIELDS = (
    "scope",
    "transition",
    "query_id",
    "query",
    "token_index",
    "surface",
    "gold_lemmas",
    "gold_identity",
    "mle_lemma",
    "mle_identity",
    "mle_source",
    "mle_pos",
    "bert_lemma",
    "bert_identity",
    "bert_source",
    "bert_pos",
    "notes",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the paired CAMeL MLE/BERT lexical-delta report"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed report differs from freshly rendered output",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{path}: malformed CSV row")
    return rows


def selected_candidate(row: dict[str, str]) -> dict | None:
    if row["judgment"] in ("ALL_WRONG", "UNCERTAIN"):
        return None
    candidates = json.loads(row["candidates_json"])
    matches = [
        candidate for candidate in candidates if candidate["label"] == row["judgment"]
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{row['comparison_id']}: judgment does not name one candidate"
        )
    return matches[0] if matches[0]["selection_status"] == "selected" else None


def is_correct(token: dict, candidate: dict) -> bool:
    return (
        token["selection_status"] == "selected"
        and token["lexical_identity"] == candidate["lexical_identity"]
    )


def system_fields(prefix: str, token: dict) -> dict[str, str]:
    analysis = token.get("raw_analysis") or {}
    return {
        f"{prefix}_lemma": token["raw_lemma"],
        f"{prefix}_identity": token["lexical_identity"],
        f"{prefix}_source": analysis.get("source", ""),
        f"{prefix}_pos": analysis.get("pos", ""),
    }


def build_rows() -> list[dict[str, str]]:
    rows = []
    for scope in ("query", "context"):
        report = load_json(ROOT / "comparison" / f"{scope}-analyses.json")
        queries = {query["id"]: query for query in report["queries"]}
        grades = load_csv(ROOT / "comparison" / f"{scope}-grades.csv")

        for grade in grades:
            gold = selected_candidate(grade)
            if gold is None:
                continue
            query = queries[grade["query_id"]]
            token_index = int(grade["token_index"])
            mle = query["analyses"]["camel-mle"]["tokens"][token_index]
            bert = query["analyses"]["camel-bert"]["tokens"][token_index]
            mle_correct = is_correct(mle, gold)
            bert_correct = is_correct(bert, gold)
            if mle_correct == bert_correct:
                continue

            row = {
                "scope": scope,
                "transition": "bert_fix" if bert_correct else "bert_regression",
                "query_id": grade["query_id"],
                "query": grade["query"],
                "token_index": grade["token_index"],
                "surface": grade["surface"],
                "gold_lemmas": " | ".join(gold["raw_lemmas"]),
                "gold_identity": gold["lexical_identity"],
                "notes": grade["notes"],
            }
            row.update(system_fields("mle", mle))
            row.update(system_fields("bert", bert))
            rows.append(row)
    return rows


def render(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main() -> int:
    args = parse_args()
    rows = build_rows()
    rendered = render(rows)

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != rendered:
            raise SystemExit(f"derived report is stale: run {Path(__file__).name}")
        print(f"derived report is current: {OUTPUT} ({len(rows)} rows)")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as output_file:
        output_file.write(rendered)
    print(f"wrote {len(rows)} rows to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
