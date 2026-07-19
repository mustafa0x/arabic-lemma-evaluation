# CAMeL BERT lemma diagnostics

This repository documents an unexpected result from CAMeL Tools' BERT-based
Arabic analyzer. It includes the exact inputs, the top five analyses for each
token, and a small comparison with CAMeL MLE and SinaLab Alma.

## What we observed

CAMeL returns a different lemma for the same fully vocalized word when a small
amount of context is added:

| Input | First result for `أَعُوذُ` | Second result |
| --- | --- | --- |
| `أَعُوذُ` | `عاذ`, dictionary verb, score 1.0 | `عَوَّذ`, dictionary verb, score 1.0 |
| `قُلْ أَعُوذُ` | `اعوذ`, generated proper name, score 1.0 | `عاذ`, dictionary verb, score 0.6364 |
| `قُلْ أَعُوذُ بِرَبِّ` | `عاذ`, dictionary verb, score 1.0 | `عَوَّذ`, dictionary verb, score 1.0 |

This does not mean that BERT is generally worse. For example, in
`قولهم ليت شعري`, MLE returns adjectival `شِعْرِيّ`, while BERT and Alma return
the expected lemma `شِعْر`.

## Small comparison

We also compared the three analyzers on 44 search queries and 24 passages:

| Sample | Measure | Words | CAMeL MLE | CAMeL BERT | Alma |
| --- | --- | ---: | ---: | ---: | ---: |
| search queries | expected lemma | 88 | 71 | 72 | 71 |
| search queries | normalized search form | 90 | 79 | 83 | 79 |
| passages | expected lemma | 468 | 367 | 373 | 378 |
| passages | normalized search form | 473 | 401 | 410 | 412 |

The lemma comparison ignores diacritics. The search comparison also applies
the spelling normalization used by our search engine. This is a small sample
of difficult search cases, not a general Arabic lemmatization benchmark.

The inputs, outputs, and judgments are in [`comparison/`](comparison). The
direct CAMeL MLE/BERT differences are in
[`camel-mle-vs-bert-lexical-deltas.csv`](camel-mle-vs-bert-lexical-deltas.csv).

## Reproduce the result

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
camel_data -i defaults
python scripts/run_camel_bert.py camel-bert-context.jsonl \
  --output new-ranked-run.json
python scripts/validate.py --ranked-report new-ranked-run.json
```

The recorded output is in
[`camel-tools-1.6.0-ranked.json`](camel-tools-1.6.0-ranked.json).

## Question for the CAMeL team

In `قُلْ أَعُوذُ`, why does the generated proper-name result `اعوذ` rank above
the available verb `عاذ`, when `عاذ` ranks first both without context and with
one more word of context?

Is this expected? If not, where would you recommend looking for the cause, and
would these examples be useful as a regression test?

<details>
  <summary><h2>Method and limitations</h2></summary>

### Focused cases

[`camel-bert-context.jsonl`](camel-bert-context.jsonl) contains the
seven exact inputs. The runner saves the top five analyses for each token,
along with package versions and hashes of the model files.

The recorded CAMeL Tools 1.5.7 and 1.6.0 runs produced the same rankings. The
1.6.0 run used Transformers 4.43.4, although that CAMeL release requires 4.44.0
or newer. The current requirements use a supported Transformers version.

The runner also records a separate BERT feature prediction to help with
diagnosis. It comes from a second public API call, so it should not be treated
as the exact internal prediction that produced the ranked results.

### Comparison

The comparison contains 44 search queries and 24 passages selected for a
practical Arabic search project. It includes deliberately difficult cases and
is not a random sample of Arabic.

The files preserve the analyzer outputs and final judgments. They do not
preserve reviewer details, the code that called the remote services and built
the ballots, or the exact service versions. The reported scores can be checked
from the committed files, but the collection process cannot be rerun exactly.

“Expected lemma” compares lemmas after removing diacritics. “Normalized search
form” also applies the spelling rules used by the search engine. These results
should not be read as a general ranking of Arabic lemmatizers.

The repository's MIT license covers its original code and documentation, not
third-party texts, models, or service outputs.

</details>
