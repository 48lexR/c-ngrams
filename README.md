# C N-gram models: LING 401 Final Project, Fall 2026

* Primary question: can we use n-gram models to generate code?
* Metrics: negative-log loss, potentially compiler errors

## Things to test

* Window size (i.e. `n`)
* characters vs. tokens
* Smoothing algorithms

## Project Design

* `data/training` contains all the C code used to create the n-gram model
* `data/testing` contains all the C code used to test the n-gram model
* `src/` contains the primary python code
* `src/data.db` is a database that contains the n-grams as well as their probabilities

