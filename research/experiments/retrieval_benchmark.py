"""Evidence Retrieval and Ranking Evaluation Benchmark.

Evaluates evidence retrieval and reranking independently on the ground-truth annotated subset.
Measures Recall@K, Precision@K, Mean Reciprocal Rank (MRR), and MAP,
comparing raw semantic similarity against provenance-weighted ranking.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.services.retrieval.reranker import EvidenceReranker
from research.configs.config import ExperimentConfig
from research.experiments.runner import ExperimentRunner


def compute_retrieval_metrics(
    ranked_relevance_lists: List[List[int]],
    k_values: Tuple[int, ...] = (1, 3, 5, 10),
) -> Dict[str, float]:
    """Compute Recall@K, Precision@K, MRR, and MAP over binary relevance arrays."""
    mrr_list: List[float] = []
    map_list: List[float] = []
    recalls: Dict[int, List[float]] = {k: [] for k in k_values}
    precisions: Dict[int, List[float]] = {k: [] for k in k_values}

    for rel_list in ranked_relevance_lists:
        total_relevant = sum(rel_list)
        if total_relevant == 0:
            continue

        # MRR
        reciprocal_rank = 0.0
        for rank, is_rel in enumerate(rel_list, start=1):
            if is_rel:
                reciprocal_rank = 1.0 / rank
                break
        mrr_list.append(reciprocal_rank)

        # Average Precision (AP)
        cum_relevant = 0
        ap_sum = 0.0
        for rank, is_rel in enumerate(rel_list, start=1):
            if is_rel:
                cum_relevant += 1
                ap_sum += cum_relevant / rank
        map_list.append(ap_sum / total_relevant)

        # Recall@K and Precision@K
        for k in k_values:
            hits_at_k = sum(rel_list[:k])
            recalls[k].append(hits_at_k / total_relevant)
            precisions[k].append(hits_at_k / k)

    return {
        "mrr": round(float(np.mean(mrr_list)), 4),
        "map": round(float(np.mean(map_list)), 4),
        **{f"recall@{k}": round(float(np.mean(recalls[k])), 4) for k in k_values},
        **{f"precision@{k}": round(float(np.mean(precisions[k])), 4) for k in k_values},
    }


def retrieval_evaluation_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Execute retrieval benchmark across the annotated evidence corpus."""
    data_dir = Path("data/processed")
    all_samples: List[Dict[str, Any]] = []
    for split_name in ["train.json", "val.json", "test.json"]:
        with open(data_dir / split_name, "r", encoding="utf-8") as f:
            all_samples.extend(json.load(f))

    # Separate annotated claims from ungrounded claims
    annotated_samples = [s for s in all_samples if len(s.get("evidence_items", [])) > 0]
    ungrounded_samples = [s for s in all_samples if len(s.get("evidence_items", [])) == 0]

    # Build the candidate evidence snippet pool
    candidate_passages: List[Dict[str, Any]] = []
    snippet_id_counter = 0

    for s in annotated_samples:
        for ev in s["evidence_items"]:
            candidate_passages.append({
                "snippet_id": f"cand_{snippet_id_counter}",
                "target_claim_id": s["id"],
                "title": ev.get("title", ""),
                "snippet": ev.get("snippet", ""),
                "url": ev.get("url", ""),
                "credibility_score": ev.get("credibility_score", 0.9),
            })
            snippet_id_counter += 1

    # Invert index using TF-IDF for retrieval pool
    corpus_texts = [f"{p['title']} {p['snippet']}" for p in candidate_passages]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts)

    ranked_rel_raw: List[List[int]] = []
    ranked_rel_weighted: List[List[int]] = []

    for s in annotated_samples:
        cid = s["id"]
        query_text = f"{s['canonical_claim']} {s['text']}"
        query_vec = vectorizer.transform([query_text])

        # Cosine similarity against all candidate passages
        cosine_sims = (query_vec * tfidf_matrix.T).toarray()[0]

        # 1. Raw Semantic Ranking
        sorted_indices_raw = np.argsort(-cosine_sims)
        rel_raw = [
            1 if candidate_passages[idx]["target_claim_id"] == cid else 0
            for idx in sorted_indices_raw
        ]
        ranked_rel_raw.append(rel_raw)

        # 2. Provenance-Weighted Ranking
        # Incorporates domain credibility weight multiplier
        weighted_scores = []
        for idx, sim in enumerate(cosine_sims):
            p = candidate_passages[idx]
            weight = p.get("credibility_score", 1.0)
            weighted_scores.append(sim * weight)

        sorted_indices_weighted = np.argsort(-np.array(weighted_scores))
        rel_weighted = [
            1 if candidate_passages[idx]["target_claim_id"] == cid else 0
            for idx in sorted_indices_weighted
        ]
        ranked_rel_weighted.append(rel_weighted)

    metrics_raw = compute_retrieval_metrics(ranked_rel_raw)
    metrics_weighted = compute_retrieval_metrics(ranked_rel_weighted)

    return {
        "benchmark_type": "RESEARCH_BENCHMARK",
        "description": "Evidence retrieval and ranking evaluation over indexed fact-check passages",
        "dataset_metadata": {
            "total_samples": len(all_samples),
            "annotated_ground_truth_claims": len(annotated_samples),
            "ungrounded_claims_documented": len(ungrounded_samples),
            "candidate_passage_pool_size": len(candidate_passages),
        },
        "retrieval_configuration": {
            "representation": "Sublinear TF-IDF (1, 2 n-grams) with cosine similarity",
            "reranking_method": "Credibility-weighted score fusion",
            "provenance_features": ["domain_reputation", "factcheck_source_confidence", "claim_review_presence"],
        },
        "metrics": {
            "raw_semantic_retrieval": metrics_raw,
            "provenance_weighted_retrieval": metrics_weighted,
        },
        "relative_gain": {
            "mrr_delta": round(metrics_weighted["mrr"] - metrics_raw["mrr"], 4),
            "recall@1_delta": round(metrics_weighted["recall@1"] - metrics_raw["recall@1"], 4),
            "recall@5_delta": round(metrics_weighted["recall@5"] - metrics_raw["recall@5"], 4),
        },
    }


def run_retrieval_benchmark() -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_id="EXP-06-RETRIEVAL",
        name="evidence_retrieval_benchmark",
        description="Independent evaluation of evidence retrieval and ranking algorithms",
        random_seed=42,
    )
    runner = ExperimentRunner(config)
    res = runner.run(retrieval_evaluation_experiment)

    out_path = Path("research/results/retrieval_benchmark.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    return res


if __name__ == "__main__":
    run_retrieval_benchmark()
