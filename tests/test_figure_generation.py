"""Unit tests for Research Figure Generation (Commit 17).
"""

from pathlib import Path
from research.figures.generate_figures import generate_all_figures


def test_figure_generation_execution(tmp_path):
    fig_dir = tmp_path / "figures"
    docs_dir = tmp_path / "docs_figures"
    res = generate_all_figures(figures_dir=fig_dir, docs_figures_dir=docs_dir)

    assert res["status"] == "success"
    assert len(res["figures"]) == 5

    for fig_name in res["figures"]:
        assert (fig_dir / fig_name).exists()
        assert (docs_dir / fig_name).exists()
        assert (fig_dir / fig_name).stat().st_size > 1000
