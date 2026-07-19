# Arabic lemma diagnostics for CAMeL Tools

This repository preserves two related pieces of evidence:

- seven context-sensitive CAMeL BERT examples with complete ranked outputs (up
  to five analyses per token);
- a frozen, search-oriented comparison of CAMeL MLE, CAMeL BERT, and SinaLab
  Alma.

It is intended for diagnosis and audit. It is not a general Arabic
lemmatization benchmark and does not support a state-of-the-art claim.

CAMeL maintainers can start with
[`MAINTAINER_BRIEF.md`](MAINTAINER_BRIEF.md).

## Main observation

For the same fully vocalized token, CAMeL BERT selected different analyses as
context changed:

| Input | Rank 1 for `أَعُوذُ` | Rank 2 |
| --- | --- | --- |
| `أَعُوذُ` | `عاذ`, lexical verb, score 1.0 | `عَوَّذ`, lexical verb, score 1.0 |
| `قُلْ أَعُوذُ` | `اعوذ`, backoff proper noun, score 1.0 | `عاذ`, lexical verb, score 0.6364 |
| `قُلْ أَعُوذُ بِرَبِّ` | `عاذ`, lexical verb, score 1.0 | `عَوَّذ`, lexical verb, score 1.0 |

The complete historical outputs are in
[`results/camel-tools-1.5.7-ranked.json`](results/camel-tools-1.5.7-ranked.json)
and
[`results/camel-tools-1.6.0-ranked.json`](results/camel-tools-1.6.0-ranked.json).
They contain the same rankings, model configuration, and recorded model-data
hashes.

The historical 1.6.0 report records Transformers 4.43.4, below CAMeL Tools
1.6.0's declared minimum of 4.44.0. It is therefore useful as frozen evidence,
not as a supported or fully locked 1.6.0 environment. See
[`METHOD.md`](METHOD.md#historical-runs).

CAMeL BERT also makes useful corrections. In `قولهم ليت شعري`, for example,
the frozen comparison records CAMeL MLE selecting adjectival `شِعْرِيّ`, while
CAMeL BERT and Alma select the expected lemma `شِعْر`. The focused examples are
a request to understand a particular backoff choice, not a claim that
contextual disambiguation is generally worse.

## Rerun the focused cases

Use Python 3.12 and install CAMeL's default data package:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
camel_data -i defaults
python -m pip check

python scripts/run_camel_bert.py cases/camel-bert-context.jsonl \
  --output results/new-ranked-run.json
python -m pip freeze > results/new-ranked-run.freeze.txt
python scripts/validate.py --ranked-report results/new-ranked-run.json
```

The requirements file contains top-level pins, not a complete transitive lock.
The runner records package versions, exact input tokens, the dediacritized BERT
input, a separately captured feature prediction, explicit cache settings, and
model-data hashes.

## Frozen comparison

The broader comparison is an audit bundle rather than an end-to-end
reproduction. Its inputs, named outputs, ballots, final judgments, and analyzer
maps are committed. The service-calling and ballot-generation source is not,
and exact remote service revisions were unavailable.

Two measures are reported:

| Sample | Measure | Rows | CAMeL MLE | CAMeL BERT | Alma |
| --- | --- | ---: | ---: | ---: | ---: |
| query tokens | lexical identity | 88 | 71 | 72 | 71 |
| query tokens | search output | 90 | 79 | 83 | 79 |
| passage tokens | lexical identity | 468 | 367 | 373 | 378 |
| passage tokens | search output | 473 | 401 | 410 | 412 |

- **Lexical identity** covers decided rows with a lexical gold outcome.
  `ALL_WRONG` rows remain in the denominator because they supply a canonical
  lemma; every preserved system receives zero credit on those rows.
- **Search output** compares the stored `production_search_term`, including an
  empty output where the judgment says no trusted lemma should be used. This is
  specific to the source search application, not linguistic lemma accuracy.

The earlier README's “lemma” row mixed lexical matches with exact matches to
`no_trusted_lemma` alternatives. It is not used as lemma accuracy here.

A paired CAMeL MLE/BERT report is in
[`reports/camel-mle-vs-bert-lexical-deltas.csv`](reports/camel-mle-vs-bert-lexical-deltas.csv).
On rows with a selected lexical gold candidate, it contains four BERT fixes and
three regressions in the query sample, and 16 fixes and 10 regressions in the
passage sample.

These counts are descriptive. The samples were assembled for a practical
search workflow and include deliberately difficult forms; no general system
ranking should be inferred.

## Check the committed artifacts

```bash
python scripts/validate.py
python scripts/build_delta_report.py --check
```

The validator checks the focused-case claims, recorded source hashes, and the
reported totals. It does not attempt to recreate the missing comparison
pipeline.

## Repository map

- [`MAINTAINER_BRIEF.md`](MAINTAINER_BRIEF.md): smallest actionable report.
- [`METHOD.md`](METHOD.md): environments, measures, and limits.
- [`cases/`](cases): seven focused inputs.
- [`results/`](results): historical ranked CAMeL BERT reports.
- [`comparison/`](comparison): frozen comparison artifacts.
- [`reports/`](reports): reports derived from committed data.
