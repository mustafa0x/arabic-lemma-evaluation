# Method and limits

## Focused CAMeL BERT cases

The seven inputs in `cases/camel-bert-context.jsonl` freeze a small set of
context-sensitive observations. They include the same word alone, in a
two-token phrase, in a three-token phrase, and in longer passages.

For each token, the runner saves the top five analyses in model order. Each
entry includes the score, lemma, source, gloss, part of speech, root, and
pattern. It also records the installed package versions and hashes the model,
configuration, morphology database, and input file.

The supplied reports were produced with:

- Python 3.12.13;
- PyTorch 2.11.0;
- Transformers 4.43.4;
- CAMeL Tools 1.5.7 and 1.6.0; and
- `pretrained_cache=False`.

The two versions used the same model and morphology data. Their ranked results
are identical after ignoring timings and other run metadata.

## Comparison samples

The query comparison has 44 queries and 91 token positions. One position was
left uncertain, leaving 90 adjudicated positions. The inputs combine a small
diagnostic set with representative search queries.

The context comparison has 24 passages and 473 adjudicated token positions.
The passages were frozen before the final comparison and include Classical
Arabic, heritage prose, and modern explanatory text.

Each report preserves the selected output from:

- CAMeL Tools MLE;
- CAMeL Tools unfactored BERT; and
- SinaLab Alma.

It also preserves CAMELMORPH candidates as inventory information. Candidate
availability is not the same as selecting the right lemma, so it is not scored
as another lemmatizer.

The blank ballot CSVs show the alternatives without analyzer names. A judgment
chooses the correct candidate, marks all candidates wrong, or records
uncertainty. The completed grading CSVs preserve those judgments. When all
candidates are wrong, they also give the intended lemma and search term. The
analyzer maps were kept aside while the outputs were graded and are included
here for auditability. The named analyzer outputs and the judgments are
sufficient for `scripts/validate.py` to reproduce the reported scores without
relying on those maps.

Two measures are kept separate:

- **Lemma:** whether the selected lexical lemma matches the adjudicated choice.
- **Search term:** whether the result becomes the intended search form after
  the project's narrow Arabic spelling normalization.

This distinction matters in a search evaluation, but the normalized score
should not be read as linguistic lemmatization accuracy.

## What this does not establish

The samples are too small and deliberately too search-oriented to rank Arabic
lemmatizers in general. They do not replace established treebank or
morphological-disambiguation evaluations. They also do not establish the best
system for Classical Arabic.

The larger comparison used remote services. Their URLs and parameters are in
the reports, but their deployed source revisions were unavailable and are
therefore marked `unverified`. Latency values in those files are observations,
not controlled performance benchmarks.
