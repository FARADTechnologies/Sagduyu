from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import platform
import random
import re
import shutil
import time
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

DATASET_NAME = "turkish-nlp-suite/SentiTurca"
DATASET_CONFIG = "hate"
DATASET_REVISION = "1c60b26c0a2ec776b7fd7f9deba7f9f84cd296b8"
MODEL_NAME = "dbmdz/bert-base-turkish-cased"
MODEL_REVISION = "b6e1de16c983e0f2c70664591ea3f22810072608"
MASK_VARIANTS = ("separated", "zero_width", "leetspeak")
RISK_LABELS = frozenset({0, 1})

MINIMUM_ORIGINAL_MACRO_F1 = 0.55
MAXIMUM_BINARY_FALSE_POSITIVE_RATE = 0.10
MAXIMUM_MASKED_MACRO_F1_DROP = 0.05
MINIMUM_MASKED_NORMALIZATION_GAIN = 0.10

WORD_PATTERN = re.compile(r"[^\W\d_]{4,}", flags=re.UNICODE)
REVERSE_LEET_MAP = str.maketrans(
    {
        "a": "4",
        "e": "3",
        "i": "1",
        "o": "0",
        "s": "5",
        "t": "7",
        "A": "4",
        "E": "3",
        "İ": "1",
        "O": "0",
        "S": "5",
        "T": "7",
    }
)


def mask_text(text: str, variant: str) -> str:
    if variant not in MASK_VARIANTS:
        raise ValueError(f"unsupported mask variant: {variant}")

    def transform(match: re.Match[str]) -> str:
        word = match.group()
        if variant == "separated":
            return ".".join(word) + ","
        if variant == "zero_width":
            return "\u200b".join(word)
        return word.translate(REVERSE_LEET_MAP)

    return WORD_PATTERN.sub(transform, text)


def masked_examples(texts: list[str], labels: list[int]) -> tuple[list[str], list[int], list[str]]:
    variants: list[str] = []
    repeated_labels: list[int] = []
    attack_names: list[str] = []
    for text, label in zip(texts, labels, strict=True):
        for variant in MASK_VARIANTS:
            variants.append(mask_text(text, variant))
            repeated_labels.append(label)
            attack_names.append(variant)
    return variants, repeated_labels, attack_names


def classification_metrics(
    y_true: list[int],
    y_pred: list[int],
    label_names: list[str],
    latency_ms_per_item: float,
    warning_predictions: list[bool] | None = None,
) -> dict[str, Any]:
    from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(len(label_names))),
        zero_division=0,
    )
    warning = binary_warning_metrics(
        [label in RISK_LABELS for label in y_true],
        warning_predictions
        if warning_predictions is not None
        else [label in RISK_LABELS for label in y_pred],
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "binary_warning": warning,
        "per_class": {
            name: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, name in enumerate(label_names)
        },
        "latency_ms_per_item": latency_ms_per_item,
    }


def binary_warning_metrics(actual_risk: list[bool], predicted_risk: list[bool]) -> dict[str, float]:
    true_negative = sum(
        not actual and not predicted
        for actual, predicted in zip(actual_risk, predicted_risk, strict=True)
    )
    false_positive = sum(
        not actual and predicted
        for actual, predicted in zip(actual_risk, predicted_risk, strict=True)
    )
    true_positive = sum(
        actual and predicted for actual, predicted in zip(actual_risk, predicted_risk, strict=True)
    )
    false_negative = sum(
        actual and not predicted
        for actual, predicted in zip(actual_risk, predicted_risk, strict=True)
    )
    return {
        "precision": true_positive / max(1, true_positive + false_positive),
        "recall": true_positive / max(1, true_positive + false_negative),
        "false_positive_rate": false_positive / max(1, false_positive + true_negative),
    }


def evaluate_demo_baseline(texts: list[str], labels: list[int]) -> dict[str, Any]:
    from sagduyu.text_safety import CourtesyChecker

    checker = CourtesyChecker()
    started = time.perf_counter()
    predictions = [checker.assess(text).should_warn for text in texts]
    latency = (time.perf_counter() - started) * 1000 / max(1, len(texts))
    return {
        "four_class_metrics": None,
        "binary_warning": binary_warning_metrics(
            [label in RISK_LABELS for label in labels], predictions
        ),
        "latency_ms_per_item": latency,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_manifest(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): sha256_file(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def prepare_texts(texts: list[str], normalized: bool) -> list[str]:
    if not normalized:
        return texts
    from sagduyu.text_normalization import TurkishTextNormalizer

    normalizer = TurkishTextNormalizer()
    return [normalizer.normalize(text) for text in texts]


def predict_texts(
    trainer: Any,
    tokenizer: Any,
    texts: list[str],
    labels: list[int],
    max_length: int,
) -> tuple[Any, float]:
    from datasets import Dataset

    dataset = Dataset.from_dict({"text": texts, "label": labels})
    tokenized = dataset.map(
        lambda batch: tokenizer(
            batch["text"], truncation=True, max_length=max_length, padding=False
        ),
        batched=True,
        remove_columns=["text"],
    )
    started = time.perf_counter()
    output = trainer.predict(tokenized)
    latency = (time.perf_counter() - started) * 1000 / max(1, len(tokenized))
    return output.predictions, latency


def calibrated_predictions(
    logits: Any,
    class_biases: list[float],
    risk_threshold: float,
) -> tuple[list[int], list[bool]]:
    import numpy as np

    adjusted = np.asarray(logits, dtype=np.float64) + np.asarray(class_biases)
    predictions = np.argmax(adjusted, axis=-1).tolist()
    shifted = adjusted - adjusted.max(axis=1, keepdims=True)
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    risk_scores = probabilities[:, sorted(RISK_LABELS)].sum(axis=1)
    warnings = (risk_scores >= risk_threshold).tolist()
    return predictions, warnings


def fit_decision_calibration(
    logits: Any,
    labels: list[int],
    label_names: list[str],
    maximum_false_positive_rate: float = MAXIMUM_BINARY_FALSE_POSITIVE_RATE,
) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import accuracy_score, f1_score

    values = np.asarray(logits, dtype=np.float64)
    targets = np.asarray(labels, dtype=np.int64)
    reference_label = Counter(labels).most_common(1)[0][0]
    biases = np.zeros(values.shape[1], dtype=np.float64)

    def score(candidate_biases: Any) -> tuple[float, float]:
        predictions = np.argmax(values + candidate_biases, axis=-1)
        return (
            float(f1_score(targets, predictions, average="macro", zero_division=0)),
            float(accuracy_score(targets, predictions)),
        )

    for step, radius in ((0.5, 4.0), (0.1, 0.6), (0.02, 0.12)):
        for label_index in range(values.shape[1]):
            if label_index == reference_label:
                continue
            best_biases = biases.copy()
            best_score = score(best_biases)
            for offset in np.arange(-radius, radius + step / 2, step):
                candidate = biases.copy()
                candidate[label_index] += float(offset)
                candidate_score = score(candidate)
                if candidate_score > best_score:
                    best_biases = candidate
                    best_score = candidate_score
            biases = best_biases

    adjusted = values + biases
    shifted = adjusted - adjusted.max(axis=1, keepdims=True)
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    risk_scores = probabilities[:, sorted(RISK_LABELS)].sum(axis=1)
    actual_risk = np.isin(targets, list(RISK_LABELS))
    candidate_thresholds = np.unique(risk_scores)
    best_threshold = 1.0
    best_warning_score = (-1.0, -1.0, -1.0)
    for threshold in candidate_thresholds:
        predicted_risk = risk_scores >= threshold
        warning = binary_warning_metrics(actual_risk.tolist(), predicted_risk.tolist())
        if warning["false_positive_rate"] > maximum_false_positive_rate:
            continue
        f1 = (
            2
            * warning["precision"]
            * warning["recall"]
            / max(1e-12, warning["precision"] + warning["recall"])
        )
        warning_score = (f1, warning["recall"], -warning["false_positive_rate"])
        if warning_score > best_warning_score:
            best_warning_score = warning_score
            best_threshold = float(threshold)

    uncalibrated_predictions = np.argmax(values, axis=-1).tolist()
    calibrated_labels, calibrated_warnings = calibrated_predictions(
        values, biases.tolist(), best_threshold
    )
    return {
        "method": "validation_class_bias_and_risk_threshold_v1",
        "reference_label": label_names[reference_label],
        "class_biases": {name: float(biases[index]) for index, name in enumerate(label_names)},
        "risk_threshold": best_threshold,
        "validation_uncalibrated": classification_metrics(
            labels, uncalibrated_predictions, label_names, 0.0
        ),
        "validation_calibrated": classification_metrics(
            labels,
            calibrated_labels,
            label_names,
            0.0,
            warning_predictions=calibrated_warnings,
        ),
    }


def evaluate_texts(
    trainer: Any,
    tokenizer: Any,
    texts: list[str],
    labels: list[int],
    label_names: list[str],
    max_length: int,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    import numpy as np

    logits, latency = predict_texts(trainer, tokenizer, texts, labels, max_length)
    if calibration is None:
        predictions = np.argmax(logits, axis=-1).tolist()
        return classification_metrics(labels, predictions, label_names, latency)
    biases = [calibration["class_biases"][name] for name in label_names]
    predictions, warnings = calibrated_predictions(logits, biases, calibration["risk_threshold"])
    return classification_metrics(
        labels,
        predictions,
        label_names,
        latency,
        warning_predictions=warnings,
    )


def create_trainer(
    model: Any,
    tokenizer: Any,
    train_dataset: Any,
    validation_dataset: Any,
    class_weights: list[float],
    output_dir: Path,
    seed: int,
    epochs: float,
    train_batch_size: int,
    eval_batch_size: int,
    learning_rate: float,
) -> Any:
    import numpy as np
    import torch
    from sklearn.metrics import f1_score
    from transformers import DataCollatorWithPadding, Trainer, TrainingArguments

    class WeightedTrainer(Trainer):
        def compute_loss(
            self,
            model: Any,
            inputs: dict[str, Any],
            return_outputs: bool = False,
            num_items_in_batch: Any | None = None,
        ) -> Any:
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            weights = torch.tensor(class_weights, device=outputs.logits.device)
            loss = torch.nn.functional.cross_entropy(outputs.logits, labels, weight=weights)
            return (loss, outputs) if return_outputs else loss

    def compute_metrics(output: Any) -> dict[str, float]:
        predictions = np.argmax(output.predictions, axis=-1)
        return {
            "macro_f1": float(
                f1_score(output.label_ids, predictions, average="macro", zero_division=0)
            )
        }

    arguments: dict[str, Any] = {
        "output_dir": str(output_dir / "training"),
        "num_train_epochs": epochs,
        "learning_rate": learning_rate,
        "per_device_train_batch_size": train_batch_size,
        "per_device_eval_batch_size": eval_batch_size,
        "gradient_accumulation_steps": 4,
        "weight_decay": 0.01,
        "warmup_ratio": 0.1,
        "logging_steps": 100,
        "save_strategy": "epoch",
        "load_best_model_at_end": True,
        "metric_for_best_model": "macro_f1",
        "greater_is_better": True,
        "save_total_limit": 1,
        "seed": seed,
        "data_seed": seed,
        "fp16": torch.cuda.is_available(),
        "report_to": [],
        "dataloader_num_workers": 2,
    }
    evaluation_parameter = (
        "eval_strategy"
        if "eval_strategy" in inspect.signature(TrainingArguments.__init__).parameters
        else "evaluation_strategy"
    )
    arguments[evaluation_parameter] = "epoch"
    trainer_arguments: dict[str, Any] = {
        "model": model,
        "args": TrainingArguments(**arguments),
        "train_dataset": train_dataset,
        "eval_dataset": validation_dataset,
        "data_collator": DataCollatorWithPadding(tokenizer=tokenizer),
        "compute_metrics": compute_metrics,
    }
    if "processing_class" in inspect.signature(Trainer.__init__).parameters:
        trainer_arguments["processing_class"] = tokenizer
    else:
        trainer_arguments["tokenizer"] = tokenizer
    return WeightedTrainer(
        **trainer_arguments,
    )


def run_configuration(
    dataset: Any,
    tokenizer: Any,
    label_names: list[str],
    normalized: bool,
    seed: int,
    checkpoint_root: Path,
    max_length: int,
    epochs: float,
    train_batch_size: int,
    eval_batch_size: int,
    learning_rate: float,
    model_revision: str,
    reuse_checkpoint: bool,
) -> dict[str, Any]:
    import numpy as np
    import torch
    from transformers import AutoModelForSequenceClassification

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    mode = "normalized" if normalized else "raw"
    output_dir = checkpoint_root / f"{mode}-seed-{seed}"
    split_texts = {
        split: prepare_texts(list(dataset[split]["text"]), normalized)
        for split in ("train", "validation", "test")
    }

    def tokenize_split(split: str) -> Any:
        values = dataset[split].remove_columns(
            [column for column in dataset[split].column_names if column not in {"text", "label"}]
        )
        values = values.remove_columns("text").add_column("text", split_texts[split])
        return values.map(
            lambda batch: tokenizer(
                batch["text"], truncation=True, max_length=max_length, padding=False
            ),
            batched=True,
            remove_columns=["text"],
        )

    train_dataset = tokenize_split("train")
    validation_dataset = tokenize_split("validation")
    counts = Counter(int(label) for label in dataset["train"]["label"])
    total = sum(counts.values())
    class_weights = [
        total / (len(label_names) * counts[index]) for index in range(len(label_names))
    ]
    checkpoint_available = (output_dir / "config.json").exists()
    if reuse_checkpoint and checkpoint_available:
        model = AutoModelForSequenceClassification.from_pretrained(output_dir)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            revision=model_revision,
            num_labels=len(label_names),
            id2label={index: name for index, name in enumerate(label_names)},
            label2id={name: index for index, name in enumerate(label_names)},
        )
    trainer = create_trainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        validation_dataset=validation_dataset,
        class_weights=class_weights,
        output_dir=output_dir,
        seed=seed,
        epochs=epochs,
        train_batch_size=train_batch_size,
        eval_batch_size=eval_batch_size,
        learning_rate=learning_rate,
    )
    if not (reuse_checkpoint and checkpoint_available):
        trainer.train()

    validation_texts = split_texts["validation"]
    validation_labels = [int(label) for label in dataset["validation"]["label"]]
    validation_logits, _ = predict_texts(
        trainer,
        tokenizer,
        validation_texts,
        validation_labels,
        max_length,
    )
    calibration = fit_decision_calibration(validation_logits, validation_labels, label_names)

    test_texts = list(dataset["test"]["text"])
    test_labels = [int(label) for label in dataset["test"]["label"]]
    uncalibrated_original = evaluate_texts(
        trainer,
        tokenizer,
        prepare_texts(test_texts, normalized),
        test_labels,
        label_names,
        max_length,
    )
    original = evaluate_texts(
        trainer,
        tokenizer,
        prepare_texts(test_texts, normalized),
        test_labels,
        label_names,
        max_length,
        calibration,
    )
    masked_texts, masked_labels, attack_names = masked_examples(test_texts, test_labels)
    masked = evaluate_texts(
        trainer,
        tokenizer,
        prepare_texts(masked_texts, normalized),
        masked_labels,
        label_names,
        max_length,
        calibration,
    )
    per_attack = {
        attack: evaluate_texts(
            trainer,
            tokenizer,
            prepare_texts(
                [
                    text
                    for text, name in zip(masked_texts, attack_names, strict=True)
                    if name == attack
                ],
                normalized,
            ),
            [
                label
                for label, name in zip(masked_labels, attack_names, strict=True)
                if name == attack
            ],
            label_names,
            max_length,
            calibration,
        )
        for attack in MASK_VARIANTS
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    if not (reuse_checkpoint and checkpoint_available):
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
    (output_dir / "decision_calibration.json").write_text(
        json.dumps(calibration, indent=2) + "\n", encoding="utf-8"
    )
    shutil.rmtree(output_dir / "training", ignore_errors=True)
    return {
        "mode": mode,
        "seed": seed,
        "class_weights": class_weights,
        "training_reused": reuse_checkpoint and checkpoint_available,
        "calibration": calibration,
        "uncalibrated_original": uncalibrated_original,
        "original": original,
        "masked": masked,
        "per_attack": per_attack,
        "masked_macro_f1_drop": original["macro_f1"] - masked["macro_f1"],
        "artifacts": artifact_manifest(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SentiTurca BERTurk dayanıklılık deneyi")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--modes", default="raw,normalized")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--train-batch-size", type=int, default=32)
    parser.add_argument("--eval-batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--dataset-revision", default=DATASET_REVISION)
    parser.add_argument("--model-revision", default=MODEL_REVISION)
    parser.add_argument(
        "--reuse-checkpoints",
        action="store_true",
        help="Mevcut model checkpoint'lerini yeniden eğitmeden değerlendir",
    )
    args = parser.parse_args()

    import datasets
    import torch
    import transformers
    from datasets import load_dataset
    from transformers import AutoTokenizer

    seeds = [int(value) for value in args.seeds.split(",")]
    modes = [value.strip() for value in args.modes.split(",")]
    if not set(modes) <= {"raw", "normalized"}:
        raise ValueError("modes must contain raw and/or normalized")

    dataset = load_dataset(
        DATASET_NAME,
        DATASET_CONFIG,
        revision=args.dataset_revision,
    )
    label_names = list(dataset["train"].features["label"].names)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=args.model_revision)
    test_texts = list(dataset["test"]["text"])
    test_labels = [int(label) for label in dataset["test"]["label"]]
    masked_test_texts, masked_test_labels, _ = masked_examples(test_texts, test_labels)
    demo_baseline = {
        "method": "transparent_demo_baseline_v1",
        "scope": "binary warning only; not a four-class context model",
        "original": evaluate_demo_baseline(test_texts, test_labels),
        "masked": evaluate_demo_baseline(masked_test_texts, masked_test_labels),
    }
    runs = [
        run_configuration(
            dataset=dataset,
            tokenizer=tokenizer,
            label_names=label_names,
            normalized=mode == "normalized",
            seed=seed,
            checkpoint_root=args.checkpoint_dir,
            max_length=args.max_length,
            epochs=args.epochs,
            train_batch_size=args.train_batch_size,
            eval_batch_size=args.eval_batch_size,
            learning_rate=args.learning_rate,
            model_revision=args.model_revision,
            reuse_checkpoint=args.reuse_checkpoints,
        )
        for mode in modes
        for seed in seeds
    ]
    by_mode = {mode: [run for run in runs if run["mode"] == mode] for mode in modes}
    means = {
        mode: {
            "original_macro_f1": mean(run["original"]["macro_f1"] for run in mode_runs),
            "masked_macro_f1": mean(run["masked"]["macro_f1"] for run in mode_runs),
            "original_binary_fpr": mean(
                run["original"]["binary_warning"]["false_positive_rate"] for run in mode_runs
            ),
            "masked_binary_fpr": mean(
                run["masked"]["binary_warning"]["false_positive_rate"] for run in mode_runs
            ),
        }
        for mode, mode_runs in by_mode.items()
    }
    normalized = means.get("normalized")
    raw = means.get("raw")
    gate = None
    if normalized is not None and raw is not None:
        masked_drop = normalized["original_macro_f1"] - normalized["masked_macro_f1"]
        masked_gain = normalized["masked_macro_f1"] - raw["masked_macro_f1"]
        gate = {
            "minimum_original_macro_f1": MINIMUM_ORIGINAL_MACRO_F1,
            "maximum_binary_false_positive_rate": MAXIMUM_BINARY_FALSE_POSITIVE_RATE,
            "maximum_masked_macro_f1_drop": MAXIMUM_MASKED_MACRO_F1_DROP,
            "minimum_masked_normalization_gain": MINIMUM_MASKED_NORMALIZATION_GAIN,
            "observed_masked_macro_f1_drop": masked_drop,
            "observed_masked_normalization_gain": masked_gain,
            "accepted": (
                normalized["original_macro_f1"] >= MINIMUM_ORIGINAL_MACRO_F1
                and normalized["original_binary_fpr"] <= MAXIMUM_BINARY_FALSE_POSITIVE_RATE
                and masked_drop <= MAXIMUM_MASKED_MACRO_F1_DROP
                and masked_gain >= MINIMUM_MASKED_NORMALIZATION_GAIN
            ),
        }

    report = {
        "protocol_version": "1",
        "dataset": {
            "name": DATASET_NAME,
            "config": DATASET_CONFIG,
            "revision": args.dataset_revision,
            "license": "CC-BY-SA-4.0",
            "splits": {split: len(dataset[split]) for split in dataset},
            "label_names": label_names,
        },
        "model": {
            "name": MODEL_NAME,
            "revision": args.model_revision,
            "license": "MIT",
        },
        "mask_variants": list(MASK_VARIANTS),
        "seeds": seeds,
        "hyperparameters": {
            "epochs": args.epochs,
            "max_length": args.max_length,
            "train_batch_size": args.train_batch_size,
            "eval_batch_size": args.eval_batch_size,
            "learning_rate": args.learning_rate,
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "datasets": datasets.__version__,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "runs": runs,
        "mean": means,
        "demo_baseline": demo_baseline,
        "acceptance_gate": gate,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
