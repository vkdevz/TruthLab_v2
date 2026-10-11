# Viva Voce Defense Master Demonstration Script
## Multimodal Evidence-Aware Misinformation Verification System (`TruthLab_v2`)

> **Author**: Pankaj Kumar  
> **Degree / Venue**: B.Tech / M.Tech Major Project Defense & Viva Examination  
> **Session Time**: ~15–20 Minutes (5 min Pitch + 5 min Live Demo + 10 min Examiner Q&A)

---

## 1. The 60-Second Opening Hook

> *"Good morning, respected examiners and faculty members.*  
> *Today, I present the **Multimodal Evidence-Aware Misinformation Verification System**.*  
>  
> *The central problem in contemporary automated fake-news detection is that existing systems act as **closed-book binary classifiers**. They inspect superficial writing style—looking for exclamation marks, emotional polarity, or sensationalist words. In the real world, this paradigm fails completely:*  
> *1. Fabricated hoaxes are frequently articulated in calm, sober, official-sounding language.*  
> *2. Authentic breaking news during disasters is urgent and alarming.*  
> *3. Over 80% of visual disinformation online is not sophisticated deepfakes, but **cheapfakes**—authentic, unaltered photographs or videos paired with false, out-of-context, or recycled captions.*  
>  
> *Our contribution is a unified, **evidence-grounded modular system** that ingests plain text, URLs, images, and video. It extracts testable atomic claims, retrieves external authoritative citations, evaluates NLI logical stances, decouples temporal event dates, computes media forensics, and produces a calibrated 5-class verdict with directed evidence graphs and epistemic uncertainty telemetry.*  
>  
> *Let me demonstrate how this functions across five live scenarios."*

---

## 2. Deterministic Live Demonstration Script

Launch the system before the examiners enter:
```bash
# Terminal 1: Backend API
./.venv/bin/uvicorn backend.app.main:app --port 8000

# Terminal 2: Interactive Workbench UI
cd frontend && npm run dev
```
Open browser at: `http://localhost:5173`

---

### Demo Scenario 1: Refutation Dominance (Viral Hoax)
- **Goal**: Demonstrate how the system detects falsehood through authoritative fact-checks and displays directional refutation.
- **Action**: Click the preset button: **`India 5G Ban Hoax`**
  - Payload: *"The Indian Ministry of Communications has officially banned all 5G network services nationwide."*
- **Click**: `Verify Text`
- **What to highlight to examiners**:
  1. **Verdict Banner**: `CONTRADICTED` with **94.1% Calibrated Confidence** and **LOW Uncertainty**.
  2. **Interactive Evidence Graph**: Switch to the **🕸️ Evidence Graph** view. Point out the central red target proposition connected by a **Red Arrow** to the **PIB Fact Check / Department of Telecommunications** citation node.
  3. **Evidentiary Refutation Dominance**: Explain that external authoritative consensus directly refutes the proposition ($r_{\text{refute}} \ge 0.65$), completely superseding lexical priors.

---

### Demo Scenario 2: Evidentiary Corroboration (Scientific Fact)
- **Goal**: Demonstrate positive evidence grounding on scientific discoveries.
- **Action**: Click the preset button: **`James Webb Discovery`**
  - Payload: *"NASA's James Webb Space Telescope confirmed detection of atmospheric carbon dioxide on exoplanet WASP-39b."*
- **Click**: `Verify Text`
- **What to highlight to examiners**:
  1. **Verdict Banner**: `SUPPORTED` with **92.0% Calibrated Confidence**.
  2. **Graph View**: Point out the **Green Arrow** (`SUPPORTS`) connecting the official NASA / Space Telescope Science Institute citation to the proposition.
  3. **NLI Marginals**: Switch to `Citations List` and show the probabilistic marginal distribution: `Supp: 92% • Ref: 3% • Neut: 5%`.

---

### Demo Scenario 3: Temporal Decoupling (Recycled "Cheapfake" News)
- **Goal**: Demonstrate temporal reasoning catching recycled historical news.
- **Action**: Click the preset button: **`2020 Recycled Curfew`**
  - Payload: *"Breaking right now: Curfew announced across the entire state due to health emergency!"*
- **Click**: `Verify Text`
- **What to highlight to examiners**:
  1. **Verdict Banner**: `OUTDATED`.
  2. **The Innovation**: Explain to examiners: *"A standard search engine finds authentic 2020 articles stating 'Curfew announced!'. A naive classifier would call this 'TRUE'. Our Temporal Verifier decouples the **event occurrence date** (March 2020) from the **present-tense framing** ('Breaking right now'), calculating $\Delta_t > 180$ days to correctly flag it as `OUTDATED`."*

---

### Demo Scenario 4: Scientific Epistemic Humility (Unindexed Claim)
- **Goal**: Demonstrate that the system withholds speculation when evidence is absent.
- **Action**: Click the preset button: **`Unindexed Rumor`**
  - Payload: *"My local neighbor's cousin invented an invisible flying bicycle last night in his garage."*
- **Click**: `Verify Text`
- **What to highlight to examiners**:
  1. **Verdict Banner**: `INSUFFICIENT_EVIDENCE` with **HIGH Uncertainty**.
  2. **The Principle**: Explain: *"This enforces the **Scientific Humility Principle**. Unlike closed-book LLMs that hallucinate plausible answers, our system computes Evidence Sufficiency $S(\mathcal{E})$. When $S(\mathcal{E}) < 1.20$, the system explicitly declares insufficient knowledge, refusing to speculate."*

---

### Demo Scenario 5: URL Ingestion & Anti-SSRF Defense
- **Goal**: Demonstrate safe URL ingestion and security engineering.
- **Action**: Click the preset button: **`Article URL (Anti-SSRF)`**
  - Payload: `https://en.wikipedia.org/wiki/James_Webb_Space_Telescope`
- **Click**: `Verify URL`
- **What to highlight to examiners**:
  1. **Security Gateway**: Point out that the URL was pre-resolved via DNS, inspected against RFC 1918 private subnets, cloud metadata (`169.254.169.254`), and port whitelists before Trafilatura extracted the article body.

---

## 3. High-Stakes Examiner Questions & Bulletproof Answers

### Q1: Why did you not simply use an LLM (e.g. ChatGPT / Claude) with a prompt?
> **Answer**:  
> *"LLM prompting in misinformation verification suffers from three fatal flaws:*  
> *1. **Knowledge Cutoffs**: Closed-book LLMs cannot verify breaking events that occurred after their training date.*  
> *2. **Hallucinations & Sycophancy**: LLMs invent citations or mirror user biases.*  
> *3. **Miscalibration**: LLMs output uncalibrated probabilities, expressing high confidence even when wrong.*  
> *Our architecture decouples knowledge storage from reasoning: knowledge is dynamically retrieved from verified indices at query time, and confidence is calibrated via post-hoc Temperature Scaling ($T=1.85$)."*

---

### Q2: Why a 5-Class Verdict Taxonomy instead of Binary True/False?
> **Answer**:  
> *"Real-world misinformation is rarely binary. If a 2020 lockdown article is reposted in 2026, is it 'True' because it happened, or 'False' because it isn't happening now? Binary classifiers cannot distinguish between outright fabrication and temporal recycling (`OUTDATED`), nor can they represent empirical epistemic limits (`INSUFFICIENT_EVIDENCE`). Our 5-class taxonomy captures the full lifecycle of real-world claims."*

---

### Q3: How do you prove that your system actually outperforms baselines?
> **Answer**:  
> *"We evaluated our system against a standard TF-IDF + Logistic Regression text baseline on a balanced 5-class benchmark dataset ($N=60$):*  
> - *Baseline 5-Class Accuracy: **0.5333** | Proposed System: **0.7333** (**+20.0% improvement**).*  
> - *Baseline Macro-F1: **0.5282** | Proposed System: **0.6652** (**+13.7% improvement**).*  
> - *Binary Directional Accuracy: **0.7073** vs **0.9024** (**+19.5% improvement**).*  
> - *We proved statistical significance using **McNemar's Exact Test**, yielding a two-tailed $p$-value of **$p = 0.0193 < 0.05$**."*

---

### Q4: What is your formula for Evidence Sufficiency $S(\mathcal{E})$?
> **Answer**:  
> *"We compute evidence sufficiency as the credibility-weighted sum of retrieval scores across all retrieved passages:*  
> $$S(\mathcal{E}) = \sum_{e \in \mathcal{E}} \text{Score}(e, c) \times w_{\text{domain}}(e)$$  
> *where $w_{\text{domain}} \in [0.5, 2.0]$ represents publisher reputation (e.g. 1.6 for official fact-checkers like WHO/Reuters). If $S(\mathcal{E}) < 1.20$, the sufficiency gate halts speculative classification and assigns `INSUFFICIENT_EVIDENCE`."*

---

### Q5: What is Temperature Scaling and why did you use $T=1.85$?
> **Answer**:  
> *"Neural networks and ensemble models are notoriously overconfident. Temperature scaling is a post-hoc calibration technique that softens logits without changing the predicted class ranking:*  
> $$\hat{p}_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$  
> *By tuning $T=1.85$ on our validation set, we reduced the **Expected Calibration Error (ECE)** from **0.2241 down to 0.0800** ($\Delta \text{ECE} = -0.1441$), ensuring that a confidence score of 80% empirically corresponds to an 80% accuracy probability."*

---

### Q6: How does your multimodal pipeline detect cheapfakes?
> **Answer**:  
> *"A cheapfake occurs when an unaltered photograph is recirculated with a fake caption. If we only ran image forensics (ELA), the image would pass as pristine!*  
> *Our late-fusion engine extracts OCR text from the image, retrieves external citations for the caption's proposition, and checks for cross-modal disparity. When external evidence refutes the caption while the image shows authentic compression, the disparity triggers `MISLEADING` with detailed provenance notes."*

---

### Q7: What are Server-Side Request Forgery (SSRF) attacks and how did you prevent them?
> **Answer**:  
> *"When a system fetches arbitrary user-submitted URLs, an attacker can input internal cloud URLs like `http://169.254.169.254/latest/meta-data/` to steal AWS/GCP credentials or scan internal LAN networks.*  
> *We implemented a strict Anti-SSRF gateway that pre-resolves the domain via DNS, blocks private IPv4/IPv6 CIDR subnets (RFC 1918, CGNAT `100.64.0.0/10`, link-local), enforces a port whitelist `{80, 443, 8080, 8443}`, caps redirects at 3 hops, and limits responses to 5 MB."*

---

### Q8: What are the main limitations of your system?
> **Answer**:  
> *"In accordance with scientific integrity:*  
> *1. **Query-time Index Dependence**: The system cannot verify claims if no reputable organization has published reporting on the topic.*  
> *2. **Language Scope**: Currently evaluated on English-language corpora; multilingual claims require translated embeddings.*  
> *3. **Probabilistic Forensics**: Error Level Analysis (ELA) and synthetic frequency heuristics are auxiliary indicators, not legally admissible proof of manipulation.*  
> *The system is designed as an explainable decision-support tool, not an autonomous censorship oracle."*

---

## 4. Emergency Viva Troubleshooting

| Issue during Demo | Cause | Solution |
| :--- | :--- | :--- |
| **Backend port 8000 busy** | Previous process running | Run `lsof -ti:8000 \| xargs kill -9` and restart uvicorn. |
| **No Internet Connection** | University Wi-Fi dropped | The system automatically falls back to the **Local ClaimReview Index** (all 60 benchmark claims and presets work 100% offline). |
| **Examiner asks to see tests** | Verification inquiry | Run `./.venv/bin/pytest tests/ -v` (demonstrating all 121 tests passing). |
| **Examiner asks to see paper** | Academic rigor check | Open [`docs/paper/RESEARCH_PAPER.md`](file:///Users/pankajkumar/Desktop/Major%20Project/v2/docs/paper/RESEARCH_PAPER.md) or LaTeX files in `docs/paper/`. |
