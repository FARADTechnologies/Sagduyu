from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import time
from pathlib import Path
from statistics import mean

GNN_MIN_MACRO_F1_GAIN = 0.02
GNN_MAX_FPR_INCREASE = 0.01


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_label(stem: str, labels: dict[str, int]) -> int:
    candidates = (stem, stem.removesuffix("_fulldata"), stem[:-9])
    for candidate in candidates:
        if candidate in labels:
            return int(labels[candidate])
    raise KeyError(f"label not found for graph: {stem}")


def load_graphs(dataset_dir: Path):
    import networkx as nx
    import torch
    from networkx.readwrite import json_graph
    from torch_geometric.data import Data

    labels = json.loads((dataset_dir / "graph_labels.json").read_text(encoding="utf-8"))
    graphs = []
    names = []
    for path in sorted(dataset_dir.glob("*.json")):
        if path.stem.startswith("graph_labels"):
            continue
        try:
            label = resolve_label(path.stem, labels)
        except KeyError:
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        graph = nx.DiGraph(json_graph.node_link_graph(raw))
        mapping = {node: index for index, node in enumerate(graph.nodes())}
        graph = nx.relabel_nodes(graph, mapping)
        x = torch.tensor(
            [graph.nodes[node]["node_attr"] for node in graph.nodes()],
            dtype=torch.float32,
        )
        edges = list(graph.edges())
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        graphs.append(Data(x=x, edge_index=edge_index, y=torch.tensor([label])))
        names.append(path.name)
    if len(graphs) < 4 or len({int(graph.y.item()) for graph in graphs}) < 2:
        raise ValueError("LEN directory must contain at least four labeled graphs and two classes")
    return graphs, names


def aggregate_features(graphs):
    import numpy as np

    rows = []
    for graph in graphs:
        nodes = int(graph.num_nodes)
        edges = int(graph.num_edges)
        possible = max(1, nodes * (nodes - 1))
        values = graph.x.detach().cpu().numpy()
        rows.append(
            [
                nodes,
                edges,
                edges / possible,
                edges / max(1, nodes),
                *np.nan_to_num(values.mean(axis=0)).tolist(),
                *np.nan_to_num(values.std(axis=0)).tolist(),
            ]
        )
    return np.asarray(rows, dtype=float)


def metrics(y_true, y_pred, latency_ms: float) -> dict[str, float]:
    from sklearn.metrics import f1_score, precision_score, recall_score

    true_negative = sum(
        actual == 0 and predicted == 0 for actual, predicted in zip(y_true, y_pred, strict=True)
    )
    false_positive = sum(
        actual == 0 and predicted == 1 for actual, predicted in zip(y_true, y_pred, strict=True)
    )
    return {
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "false_positive_rate": false_positive / max(1, false_positive + true_negative),
        "latency_ms_per_graph": latency_ms,
    }


def run_baseline(graphs, train_indices, test_indices, seed: int):
    from sklearn.ensemble import HistGradientBoostingClassifier

    features = aggregate_features(graphs)
    labels = [int(graph.y.item()) for graph in graphs]
    model = HistGradientBoostingClassifier(random_state=seed, max_iter=150, max_depth=5)
    model.fit(features[train_indices], [labels[index] for index in train_indices])
    started = time.perf_counter()
    predictions = model.predict(features[test_indices]).tolist()
    latency = (time.perf_counter() - started) * 1000 / len(test_indices)
    return metrics([labels[index] for index in test_indices], predictions, latency)


def run_gcn(graphs, train_indices, test_indices, seed: int, epochs: int):
    import numpy as np
    import torch
    import torch.nn.functional as functional
    from torch.nn import Linear
    from torch.optim import Adam
    from torch_geometric.loader import DataLoader
    from torch_geometric.nn import GCNConv, global_mean_pool

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    class GCN(torch.nn.Module):
        def __init__(self, input_features: int) -> None:
            super().__init__()
            self.first = GCNConv(input_features, 64)
            self.second = GCNConv(64, 64)
            self.output = Linear(64, 2)

        def forward(self, batch):
            values = functional.relu(self.first(batch.x, batch.edge_index))
            values = functional.dropout(values, p=0.35, training=self.training)
            values = functional.relu(self.second(values, batch.edge_index))
            return self.output(global_mean_pool(values, batch.batch))

    model = GCN(int(graphs[0].num_node_features)).to(device)
    optimizer = Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    train_loader = DataLoader(
        [graphs[index] for index in train_indices], batch_size=4, shuffle=True
    )
    test_loader = DataLoader([graphs[index] for index in test_indices], batch_size=1, shuffle=False)
    for _ in range(epochs):
        model.train()
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            loss = functional.cross_entropy(model(batch), batch.y.view(-1))
            loss.backward()
            optimizer.step()

    model.eval()
    predictions = []
    actual = []
    started = time.perf_counter()
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            predictions.extend(model(batch).argmax(dim=1).cpu().tolist())
            actual.extend(batch.y.view(-1).cpu().tolist())
    latency = (time.perf_counter() - started) * 1000 / len(test_indices)
    return metrics(actual, predictions, latency), str(device)


def main() -> None:
    parser = argparse.ArgumentParser(description="LEN açıklanabilir taban ve GCN rakip deneyi")
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", default="11,23,37")
    parser.add_argument("--epochs", type=int, default=40)
    args = parser.parse_args()

    import torch
    from sklearn.model_selection import StratifiedShuffleSplit

    graphs, graph_names = load_graphs(args.dataset_dir)
    labels = [int(graph.y.item()) for graph in graphs]
    seed_values = [int(value) for value in args.seeds.split(",")]
    runs = []
    devices = set()
    for seed in seed_values:
        splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        train_indices, test_indices = next(splitter.split(graph_names, labels))
        if set(train_indices) & set(test_indices):
            raise RuntimeError("graph leakage detected")
        baseline = run_baseline(graphs, train_indices, test_indices, seed)
        gcn, device = run_gcn(graphs, train_indices, test_indices, seed, args.epochs)
        devices.add(device)
        runs.append({"seed": seed, "baseline": baseline, "gcn": gcn})

    baseline_f1 = mean(run["baseline"]["macro_f1"] for run in runs)
    baseline_fpr = mean(run["baseline"]["false_positive_rate"] for run in runs)
    gcn_f1 = mean(run["gcn"]["macro_f1"] for run in runs)
    gcn_fpr = mean(run["gcn"]["false_positive_rate"] for run in runs)
    accepted = (
        gcn_f1 - baseline_f1 >= GNN_MIN_MACRO_F1_GAIN
        and gcn_fpr <= baseline_fpr + GNN_MAX_FPR_INCREASE
    )
    report = {
        "protocol_version": "1",
        "dataset": "LEN-Small",
        "archive_sha256": sha256_file(args.archive),
        "graph_count": len(graphs),
        "split_unit": "independent_graph",
        "seeds": seed_values,
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "devices": sorted(devices),
        },
        "runs": runs,
        "mean": {
            "baseline_macro_f1": baseline_f1,
            "baseline_false_positive_rate": baseline_fpr,
            "gcn_macro_f1": gcn_f1,
            "gcn_false_positive_rate": gcn_fpr,
        },
        "acceptance_gate": {
            "minimum_macro_f1_gain": GNN_MIN_MACRO_F1_GAIN,
            "maximum_fpr_increase": GNN_MAX_FPR_INCREASE,
            "accepted": accepted,
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
