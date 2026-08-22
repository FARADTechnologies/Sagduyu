import json
from pathlib import Path


def test_len_experiment_script_is_valid_python() -> None:
    path = Path("experiments/len_gnn_challenger.py")
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_len_notebook_has_no_stored_results_and_runs_versioned_experiment() -> None:
    notebook = json.loads(Path("notebooks/LEN_GNN_Challenger.ipynb").read_text(encoding="utf-8"))
    code = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
    )

    assert notebook["nbformat"] == 4
    assert all(cell.get("outputs", []) == [] for cell in notebook["cells"])
    assert all(cell.get("execution_count") is None for cell in notebook["cells"])
    assert "len_gnn_challenger.py" in code
    assert "11,23,37" in code
    assert "len_results.json" in code


def test_gnn_acceptance_thresholds_are_locked() -> None:
    source = Path("experiments/len_gnn_challenger.py").read_text(encoding="utf-8")

    assert "GNN_MIN_MACRO_F1_GAIN = 0.02" in source
    assert "GNN_MAX_FPR_INCREASE = 0.01" in source
