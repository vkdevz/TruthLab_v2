# Baseline Experiment Protocol & Metric Benchmark
## Multimodal Evidence-Aware Misinformation Verification System

---

## 1. Baseline Model Architecture

The Phase 3 Text Fake-News Baseline represents the conventional academic and industry paradigm of closed-book lexical text classification:
- **Feature Representation**: Term Frequency-Inverse Document Frequency (TF-IDF) with sublinear term-frequency scaling, unigram + bigram combinations ($n \in [1, 2]$), English stopword pruning, and top 10,000 feature capping.
- **Classification Head**: L2-regularized Logistic Regression ($C = 1.0$) with calibrated sigmoid probability output.
- **Decision Boundary**:
  $$P(\text{Fake} \mid x) = \sigma(\mathbf{w}^T \cdot \text{TFIDF}(x) + b)$$
  $$\text{Prediction} = \begin{cases} \text{FAKE}, & \text{if } P(\text{Fake} \mid x) \ge 0.50 \\ \text{REAL}, & \text{otherwise} \end{cases}$$

---

## 2. Theoretical Flaw of Closed-Book Lexical Baselines

Conventional text classifiers learn correlations between sensational vocabulary and the `Fake` label:
- Words like *"SHOCKING"*, *"SECRET"*, *"MIRACLE"*, *"WHISTLEBLOWER"* receive large positive weights favoring `FAKE`.
- Administrative words like *"meeting"*, *"announced"*, *"spokesperson"* receive negative weights favoring `REAL`.

### The Fundamental Vulnerability
1. **Adversarial Evocation / Plain Phrasing**: A completely false claim written in calm, official language (e.g. *"The Ministry announced that water supplies contain microscopic tracking chips"*) is classified as **REAL** by the baseline because it lacks sensationalist tokens.
2. **Sensational Truth**: Legitimate breaking news written with urgent vocabulary is misclassified as **FAKE**.
3. **Zero Fact Verification**: The model has zero access to external world facts, Wikipedia, or news consensus.

This empirical gap directly validates the core thesis inquiry ($RQ_1$): **Evidence-grounded retrieval is required for robust truth assessment.**
