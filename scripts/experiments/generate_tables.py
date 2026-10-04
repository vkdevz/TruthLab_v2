import json
from pathlib import Path


def generate_latex_tables():
    comp_file = Path("docs/experiments/comparative_results.json")
    if not comp_file.exists():
        print("Comparative results not found. Run run_benchmarks.py first.")
        return

    with open(comp_file) as f:
        comp_data = json.load(f)

    base = comp_data["baseline_text_only"]
    prop = comp_data["proposed_evidence_system"]

    latex_comp_table = f"""\\begin{{table}}[ht]
\\centering
\\caption{{Empirical Comparison: Conventional Text-Only Baseline vs. Proposed Multimodal Evidence Verification System}}
\\label{{tab:main_results}}
\\begin{{tabular}}{{lcccc}}
\\hline
\\textbf{{Model Architecture}} & \\textbf{{Binary Acc.}} & \\textbf{{Binary F1}} & \\textbf{{5-Class Acc.}} & \\textbf{{5-Class F1}} \\\\
\\hline
Baseline Text-Only (TF-IDF + LR) & {base['binary_accuracy']:.4f} & {base['macro_f1']:.4f} & N/A & N/A \\\\
\\textbf{{Proposed Evidence-Aware (Ours)}} & \\textbf{{{prop['binary_accuracy']:.4f}}} & \\textbf{{{prop['binary_macro_f1']:.4f}}} & \\textbf{{{prop['five_class_accuracy']:.4f}}} & \\textbf{{{prop['five_class_macro_f1']:.4f}}} \\\\
\\hline
\\textbf{{Relative Performance Delta ($\\Delta$)}} & +{prop['binary_accuracy'] - base['binary_accuracy']:.4f} & +{comp_data['f1_improvement']:.4f} & --- & --- \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""

    out_tex = Path("docs/paper/tables/table_main_results.tex")
    out_tex.parent.mkdir(parents=True, exist_ok=True)
    with open(out_tex, "w") as f:
        f.write(latex_comp_table)

    print("Generated LaTeX table at:", out_tex)
    print("\nLaTeX Preview:\n")
    print(latex_comp_table)


if __name__ == "__main__":
    generate_latex_tables()
