# Frozen comparison artifacts

These files can be used to review and rescore the comparison. They do not
contain everything needed to rerun data collection.

- `search-queries.jsonl` and `representative-queries.jsonl`: query inputs.
- `context-passages.jsonl`: passage inputs.
- `*-analyses.json`: named analyzer outputs and recorded request metadata.
- `*-ballot.csv`: analyzer-neutral ballots.
- `*-grades.csv`: final judgments with ballot fields preserved.
- `*-analyzer-map.json`: maps ballot labels back to analyzers.

They reproduce the reported counts and the paired CAMeL MLE/BERT lexical-delta
report. They cannot call the remote services or rebuild the ballots. Exact
service versions and reviewer details were not recorded.

See the method and limitations in the [main README](../README.md).
