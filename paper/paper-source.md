---
title: "Post-Quantum Cryptography in Practice: Benchmarking, Protocol Integration, and Migration Strategy for Real Systems"
author: "Michael Kurilko"
date: "April 2026"
bibliography: references.bib
csl: ieee.csl
abstract: |
  Accurate identity resolution under noisy, incomplete, and diverse personal data is crucial to large-scale user databases and knowledge graphs. Such a requirement is illustrated by Tributary—an effort to build a person-centric, world-wide knowledge resource (“Wikipedia of all people”)—where storing a single canonical record per person underpins data integrity and downstream analytics. Herein, we compare three paradigms of probabilistic record linkage—Fellegi–Sunter, Gradient Boosted Trees (GBT), and a Transformer model—on a synthetic pipeline injecting realistic corruptions (typos, field swaps, missingness, as well as semantic variation). The three implementations are developed from scratch and enabled with a lightweight dashboard aiding in threshold tuning, error examination, as well as monitoring.
  
  Across five datasets (500 pairs each), GBT achieved the best precision–recall balance (97.1% precision, 94.3% recall at 0.95 threshold). The Transformer excelled under extreme textual variation but suffered precision loss, while Fellegi–Sunter performed well on clean data but failed under corruption. Inspired by these complementary behaviors, we propose a simple stacking procedure: logistic regression meta-learner over the three models' scores. The combined score demonstrates better class separability and stably located operating points, supporting Tributary's goals directly and applicable across domains including healthcare, finance, and customer data integration.
link-citations: true
filters:
  - pandoc-crossref
---

# Introduction

# References
