# Method and limits

This repository contains two bodies of evidence with different reproducibility
boundaries:

1. seven focused CAMeL BERT cases that can be rerun locally;
2. a larger frozen comparison that can be inspected and rescored, but not
   regenerated end to end from the committed files.

## Focused CAMeL BERT cases

`cases/camel-bert-context.jsonl` preserves the exact text used for the focused
observations. The historical runner tokenized each case with `text.split()` and
saved up to five analyses in returned rank order. Each candidate includes its
normalized score, lemma, source, gloss, part of speech, root, and pattern.

### Historical runs

| Report | Python | PyTorch | Transformers | CAMeL Tools |
| --- | --- | --- | --- | --- |
| `camel-tools-1.5.7-ranked.json` | 3.12.13 | 2.11.0 | 4.43.4 | 1.5.7 |
| `camel-tools-1.6.0-ranked.json` | 3.12.13 | 2.11.0 | 4.43.4 | 1.6.0 |

The reports contain the same model configuration, recorded model and
morphology-file hashes, and ranked outputs. Both record
`pretrained_cache=False`. Other cache sizes and a complete transitive package
freeze were not preserved, so the repository cannot show that CAMeL Tools code
was the only environmental difference.

CAMeL Tools 1.6.0 declares Transformers 4.44.0 or newer, while the historical
1.6.0 report records 4.43.4. The report remains useful as frozen evidence, but
it is not a supported 1.6.0 environment.

Tagged source references:

- <https://github.com/CAMeL-Lab/camel_tools/blob/v1.5.7/setup.py>
- <https://github.com/CAMeL-Lab/camel_tools/blob/v1.6.0/setup.py>
- <https://github.com/CAMeL-Lab/camel_tools/blob/v1.6.0/camel_tools/disambig/bert/unfactored.py>

### Current runner

`scripts/run_camel_bert.py` adds diagnostic fields while retaining the
historical ranked-output shape. It records:

- exact input tokens and the dediacritized tokens supplied to BERT;
- a feature prediction for the model's configured scoring features;
- each candidate's values for those features and its exact match count;
- explicit batch, device, and cache settings;
- package versions and dataset-relative model-data hashes.

The feature prediction is captured in a separate public
`tag_sentence(..., use_analyzer=False)` pass. It is not an instrumented copy of
the private prediction used inside `disambiguate`. The final CAMeL score may
also reflect its tag-frequency tie-breaker and backoff penalty, so
`feature_match_count` is not a reconstruction of the complete score.

The current runner uses CPU inference, batch size 32,
`pretrained_cache=False`, analyzer cache size zero, and ranking cache size zero.
Those settings make a diagnostic rerun explicit; they are not a claim about
the cause of the historical result.

`requirements.txt` contains top-level pins that satisfy CAMeL Tools 1.6.0's
declared version constraints. It is not a full lockfile. Save `pip freeze`
beside a new result when exact package identity matters. CAMeL model data can
change independently, so the report hashes the files it used.

## Frozen comparison

The query sample contains 44 queries and 91 token positions. One position is
`UNCERTAIN`, leaving 90 decided positions. The passage sample contains 24
passages and 473 decided token positions. The inputs were selected for a
practical Arabic search workflow and include difficult forms; they are not
random samples of Arabic.

Each named report preserves selected outputs from CAMeL MLE, CAMeL unfactored
BERT, and SinaLab Alma. CAMELMORPH candidates are retained as inventory
information, not as a fourth selected-output system.

For each sample, the repository contains a blank ballot, a completed grade
file, and a separate map from analyzer-neutral labels to analyzers. A judgment
selects a candidate, marks all candidates wrong, or records uncertainty. The
completed grade files retain the ballot fields, and the analyzer maps remain
available for manual inspection.

The artifacts preserve final judgments but not reviewer count or
qualifications, independent annotations, an adjudication stage, agreement
statistics, or a versioned annotation guide. They should therefore be
described as frozen judgments, not as a documented multi-annotator study.

### Measures

- **Lexical identity:** agreement on decided rows with a lexical gold outcome.
  The denominator includes `ALL_WRONG` rows that supply a canonical lemma; all
  preserved systems receive zero credit on those rows.
- **Search output:** agreement on the stored `production_search_term`. This
  includes an empty output when the chosen outcome is `no_trusted_lemma` and
  uses the canonical search term on `ALL_WRONG` rows. It is a project-specific
  search measure, not linguistic lemma accuracy.

The paired delta report includes selected lexical-gold rows where CAMeL MLE and
CAMeL BERT differ in lexical correctness. `ALL_WRONG`, `UNCERTAIN`, and gold
`no_trusted_lemma` rows are excluded.

### Reproducibility boundary

The comparison inputs, named outputs, ballots, final grades, and analyzer maps
are committed. The code that called remote services, normalized responses, and
built ballots is not. Exact deployed service revisions were also unavailable.
The comparison should therefore be described as a frozen audit bundle rather
than an end-to-end reproducible experiment.

## General limits

The samples are too small and search-oriented to rank Arabic lemmatizers in
general, establish a state-of-the-art result, or identify the best system for
Classical Arabic. Latency fields in the frozen reports are observations, not
controlled performance measurements.

The top-level MIT license covers authored code and documentation in this
repository. It does not by itself relicense third-party Arabic texts, CAMeL
model data, or remote-service outputs.
