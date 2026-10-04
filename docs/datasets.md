# Dataset Documentation & Methodology (Phase 1)

This document provides complete documentation of all datasets and corpora used in Phase 1 for classical text baseline evaluation and evidence retrieval.

---

## 1. Reference ClaimReview Fact-Check Corpus

- **Dataset Name**: Reference ClaimReview Fact-Check Corpus (`data/claim_reviews/reference_claim_reviews.json`)
- **Source**: Aggregated from schema.org ClaimReview markups published by accredited fact-checking signatories of the International Fact-Checking Network (IFCN), including PolitiFact, PIB Fact Check, Snopes, and Reuters Fact Check.
- **Task**: Evidence-grounded claim retrieval and stance verification.
- **Labels / Fields**:
  - `claim`: Canonical phrasing of the analyzed public claim.
  - `publisher`: Fact-checking organization.
  - `domain`: Web domain of the publisher.
  - `url`: Direct source citation URL.
  - `rating`: Textual fact-checker rating (e.g., "False", "Misleading", "Debunked").
  - `stance`: Standardized 3-class NLI stance (`SUPPORTS`, `REFUTES`, `NEUTRAL`).
  - `snippet`: Explanatory excerpt explaining the verification reasoning.
  - `date`: Publication timestamp (ISO-8601).
- **Size**: Seeded reference index with real-world viral claims and scalable via Google Fact Check Tools API (`CompositeEvidenceRetriever`).
- **Preprocessing**:
  - Lowercased token extraction and punctuation removal.
  - Jaccard and containment indexing for offline retrieval.
  - Normalization of diverse fact-checker rating terms into standard stance labels.
- **Limitations**:
  - Offline reference slice covers common benchmark viral claims; live external API requires network connectivity and API keys for long-tail real-time news.
- **Licensing & Usage**: Data sourced from public ClaimReview structured data markups permitted for non-commercial academic research and fact-checking transparency.

---

## 2. Text Baseline Misinformation Benchmark

- **Dataset Name**: Text Baseline Misinformation Benchmark (`data/benchmark/text_baseline_benchmark.json`)
- **Source**: Curated from historical verified true news wires (Reuters, PIB, Nature) and fabricated sensationalist claims (standard health hoaxes, conspiracy theories, and financial scams).
- **Task**: Binary fake news classification (`0 = Legitimate / Real`, `1 = Fake / Sensational`).
- **Size**: 26 annotated samples (16 in-domain training pairs, 10 out-of-domain evaluation pairs).
- **Preprocessing**:
  - Unicode NFKC normalization.
  - Whitespace collapse.
  - Sublinear TF-IDF vectorization with unigram and bigram features (`ngram_range=(1, 2)`).
- **Split Strategy**:
  - **Train Split**: Balanced 8 Real / 8 Fake samples representing explicit lexical markers.
  - **Test Split**: Balanced 5 Real / 5 Fake out-of-domain samples containing subtle paraphrasing and scientific reporting to evaluate out-of-domain generalizability.
- **Empirical Baseline Performance**:
  - In-Domain Training: Accuracy = 1.000, Macro F1 = 1.000, ECE = 0.399.
  - Out-of-Domain Held-Out: Accuracy = 0.700, Precision = 0.750, Recall = 0.600, Macro F1 = 0.697, ECE = 0.184.
- **Scientific Finding**:
  - The drop in accuracy from 100% to 70% highlights the fundamental flaw of purely text-based lexical classifiers (unseen or carefully written misinformation easily bypasses simple keyword models), directly justifying this project's **evidence-grounded retrieval architecture**.
- **Limitations**:
  - Small sample size designed for lightweight deterministic unit testing, continuous integration, and rapid local evaluation without heavy GPU resources.
- **Licensing**: Open academic research dataset.
