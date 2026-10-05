# Research Infrastructure & Reproducibility Framework

This directory houses the formal, reproducible research evaluation pipeline for the **Multimodal Evidence-Aware Misinformation Verification System**.

## Structure

```
research/
├── configs/           # Strongly typed configurations for experiments and benchmarks
├── experiments/       # Experiment runners and benchmark drivers
├── results/           # Raw machine-readable benchmark outputs (JSON)
├── artifacts/         # Serialized model weights, embeddings, and preprocessed indices
├── tables/            # Exported research tables (Markdown, LaTeX, CSV)
└── figures/           # Publication-grade evaluation plots
```

## Reproducibility Guarantees

1. **Deterministic Random Seeds**: Every run explicitly fixes random seeds across Python `random`, NumPy `np.random`, and `PYTHONHASHSEED`.
2. **Environment Metadata Capture**: Every experiment logs exact runtime metadata:
   - Operating system and kernel
   - CPU architecture and core counts
   - Exact Git commit SHA, branch, and working-tree dirty status
   - Python version and installed package versions
3. **No Fabricated Benchmarks**: All scores in `results/` are calculated live from real dataset samples using standard evaluation metrics.

## Running Experiments

To run the framework smoke check:
```bash
python -m research.experiments.smoke_experiment
```
