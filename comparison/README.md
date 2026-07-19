# Frozen comparison artifacts

This directory is an audit bundle, not a complete experiment pipeline.

- `search-queries.jsonl` and `representative-queries.jsonl`: query inputs.
- `context-passages.jsonl`: passage inputs.
- `*-analyses.json`: named analyzer outputs and recorded request metadata.
- `*-ballot.csv`: analyzer-neutral ballots.
- `*-grades.csv`: final judgments with ballot fields preserved.
- `*-analyzer-map.json`: maps ballot labels back to analyzers.

The committed files are sufficient to reproduce the reported counts and the
paired CAMeL MLE/BERT lexical-delta report. They are not sufficient to call the
remote services or regenerate the ballots from raw responses. Exact service
revisions and reviewer-process metadata were not preserved.

See [`../METHOD.md`](../METHOD.md) for measure definitions and limits.
