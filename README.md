# Arabic lemma examples and comparisons

This repository contains the material offered in a SIGARAB discussion about
Arabic lemmatization for search:

- frozen examples where CAMeL BERT changes its answer with context;
- the complete top-five analyses for those examples;
- a small comparison of CAMeL MLE, CAMeL BERT, and Alma on search queries and
  passages from Classical Arabic and MSA texts; and
- the judgments used to check those outputs.

The aim is to make the examples inspectable and reproducible, not to present a
new Arabic lemmatization benchmark or claim a state-of-the-art result.

## The clearest example

For the same fully vocalized word, CAMeL BERT selected different analyses as
the surrounding text changed:

| Text | Selected lemma for `أَعُوذُ` | What happened |
| --- | --- | --- |
| `أَعُوذُ` | `عاذ` | lexical analysis |
| `قُلْ أَعُوذُ` | `اعوذ` | generated proper-name fallback; `عاذ` is rank 2 |
| `قُلْ أَعُوذُ بِرَبِّ` | `عاذ` | lexical analysis again |

The full ranked outputs are in
[`results/camel-tools-1.5.7-ranked.json`](results/camel-tools-1.5.7-ranked.json)
and
[`results/camel-tools-1.6.0-ranked.json`](results/camel-tools-1.6.0-ranked.json).
The rankings were identical across the two CAMeL Tools versions in these
frozen cases. Both runs disabled the pretrained ranking cache and recorded the
model and morphology-file hashes.

CAMeL BERT also makes genuine repairs. For example, in `قتل أبيه الكافر`, MLE
treated `أبيه` as the proper name “Abbé,” while BERT and Alma returned `أب`
(father). The point is not that BERT is poor; it is that its contextual choices
are not consistently better for this search use case.

## Small comparison

We checked two bounded samples. “Lemma” below means the selected lexical lemma.
“Search term” allows the narrow spelling normalization used by our search
system, so it does not count harmless orthographic differences as failures.

| Sample | Measure | CAMeL MLE | CAMeL BERT | Alma |
| --- | --- | ---: | ---: | ---: |
| 90 adjudicated query tokens | lemma | 72 | **74** | 71 |
| 90 adjudicated query tokens | search term | 79 | **83** | 79 |
| 473 passage tokens | lemma | 369 | 376 | **379** |
| 473 passage tokens | search term | 401 | 410 | **412** |

These numbers are descriptive, not a leaderboard. The query sample was built
around practical search questions and known difficult forms. The passage
sample adds nearby text but is still small. The broad comparison called remote
services whose exact revisions were not available, so the reports record them
as unverified. The focused CAMeL BERT reproduction is stronger: it was rerun in
controlled environments and records its model identities.

## Where things are

- [`cases/`](cases) contains the seven frozen CAMeL BERT examples.
- [`results/`](results) contains every returned top-five analysis for CAMeL
  Tools 1.5.7 and 1.6.0.
- [`comparison/`](comparison) contains the query and passage inputs, full named
  analyzer outputs, blank ballots, completed grading CSVs, and the analyzer
  maps that were kept aside until grading was complete.
- [`METHOD.md`](METHOD.md) explains selection, grading, and limitations.
- [`scripts/run_camel_bert.py`](scripts/run_camel_bert.py) reruns the focused
  CAMeL example set.
- [`scripts/validate.py`](scripts/validate.py) checks file relationships,
  reproduces the table above, and confirms that the two ranked runs agree.

Run the local checks with:

```bash
python scripts/validate.py
```

To rerun CAMeL BERT after installing CAMeL Tools and its MSA unfactored model:

```bash
python scripts/run_camel_bert.py cases/camel-bert-context.jsonl \
  --output results/new-ranked-run.json
```

The generated report includes runtime versions, elapsed time, input hashes,
and hashes for the model and morphology data it actually used.
