"""Unit tests for Research Table Generation (Commit 16).
"""

from pathlib import Path
from research.tables.generate_tables import generate_all_research_tables


def test_research_table_generation(tmp_path):
    res = generate_all_research_tables(output_dir=tmp_path)
    assert res["status"] == "success"
    assert len(res["tables_generated"]) == 7

    for tid in res["tables_generated"]:
        assert (tmp_path / "markdown" / f"{tid}.md").exists()
        assert (tmp_path / "csv" / f"{tid}.csv").exists()
        assert (tmp_path / "latex" / f"{tid}.tex").exists()

    assert Path("docs/experiments/RESEARCH_TABLES.md").exists()
