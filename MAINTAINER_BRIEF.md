# CAMeL maintainer brief

## Question

Is it expected for the MSA unfactored BERT disambiguator to rank a generated
`backoff` proper-name analysis of fully vocalized `أَعُوذُ` above the available
lexical verb analysis in the two-token input `قُلْ أَعُوذُ`?

The same token selects the lexical lemma `عاذ` in isolation and when one more
context token is present.

## Smallest evidence

These values come from the committed CAMeL Tools 1.6.0 report. The 1.5.7 report
has the same ranked outputs.

| Input | Rank | Lemma | Source | POS | Score |
| --- | ---: | --- | --- | --- | ---: |
| `أَعُوذُ` | 1 | `عاذ` | `lex` | `verb` | 1.0 |
|  | 2 | `عَوَّذ` | `lex` | `verb` | 1.0 |
| `قُلْ أَعُوذُ` | 1 | `اعوذ` | `backoff` | `noun_prop` | 1.0 |
|  | 2 | `عاذ` | `lex` | `verb` | 0.6363636364 |
| `قُلْ أَعُوذُ بِرَبِّ` | 1 | `عاذ` | `lex` | `verb` | 1.0 |
|  | 2 | `عَوَّذ` | `lex` | `verb` | 1.0 |

The model configuration uses `ADD_PROP` backoff. CAMeL dediacritizes the
sentence before BERT prediction and then analyzes the original token. The
historical reports do not preserve the predicted feature bundle, so they do
not by themselves distinguish a prediction error from scorer, tie-breaker, or
backoff behavior.

A new run of [`scripts/run_camel_bert.py`](scripts/run_camel_bert.py) records a
separately captured feature prediction and each candidate's values for the
configured scoring features. That capture uses the public
`tag_sentence(..., use_analyzer=False)` path; it is diagnostic evidence, not an
instrumented copy of the disambiguator's private prediction object.

## Evidence files

- [`cases/camel-bert-context.jsonl`](cases/camel-bert-context.jsonl): exact
  inputs.
- [`results/camel-tools-1.6.0-ranked.json`](results/camel-tools-1.6.0-ranked.json):
  historical 1.6.0 ranked output.
- [`results/camel-tools-1.5.7-ranked.json`](results/camel-tools-1.5.7-ranked.json):
  matching historical 1.5.7 output.
- [`scripts/run_camel_bert.py`](scripts/run_camel_bert.py): diagnostic rerunner.

## Reproduce

```bash
python -m pip install -r requirements.txt
camel_data -i defaults
python scripts/run_camel_bert.py cases/camel-bert-context.jsonl \
  --output results/new-ranked-run.json
python scripts/validate.py --ranked-report results/new-ranked-run.json
```

The committed 1.6.0 report records Transformers 4.43.4, below CAMeL Tools
1.6.0's declared minimum. Treat it as historical evidence rather than a
supported 1.6.0 environment.

## Requested guidance

1. Is the `ADD_PROP` selection expected for this input?
2. Which layer is most useful to inspect: feature prediction, analyzer backoff,
   scoring, or tie-breaking?
3. Would these inputs be useful as an upstream diagnostic or regression test?

The broader system comparison is supporting context only, not a benchmark.
