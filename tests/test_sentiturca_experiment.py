from pathlib import Path

import pytest

from experiments.sentiturca_berturk import (
    DATASET_REVISION,
    MASK_VARIANTS,
    MODEL_REVISION,
    fit_decision_calibration,
    mask_text,
    masked_examples,
)
from sagduyu.text_normalization import TurkishTextNormalizer


@pytest.mark.parametrize("variant", MASK_VARIANTS)
def test_sentence_masks_round_trip_through_normalization(variant: str) -> None:
    normalizer = TurkishTextNormalizer()
    original = "Bu düşünce gerçekten salak ve anlamsız."
    masked = mask_text(original, variant)

    assert masked != original
    assert normalizer.normalize(masked) == normalizer.normalize(original)


def test_masked_examples_keep_each_parent_in_the_same_evaluation_group() -> None:
    texts, labels, attacks = masked_examples(["Birinci örnek", "İkinci örnek"], [0, 2])

    assert len(texts) == len(labels) == len(attacks) == 2 * len(MASK_VARIANTS)
    assert labels[: len(MASK_VARIANTS)] == [0] * len(MASK_VARIANTS)
    assert labels[len(MASK_VARIANTS) :] == [2] * len(MASK_VARIANTS)
    assert attacks[: len(MASK_VARIANTS)] == list(MASK_VARIANTS)


def test_dataset_and_model_revisions_are_pinned() -> None:
    assert len(DATASET_REVISION) == 40
    assert len(MODEL_REVISION) == 40


def test_decision_calibration_uses_validation_signals_deterministically() -> None:
    np = pytest.importorskip("numpy")
    labels = [0] * 20 + [1] * 10 + [2] * 60 + [3] * 10
    generator = np.random.default_rng(42)
    logits = generator.normal(0.0, 0.2, size=(len(labels), 4))
    for row, label in enumerate(labels):
        logits[row, label] += 1.0
    logits[:, 3] += 0.8

    first = fit_decision_calibration(logits, labels, ["offensive", "hate", "neutral", "civilized"])
    second = fit_decision_calibration(logits, labels, ["offensive", "hate", "neutral", "civilized"])

    assert first == second
    assert (
        first["validation_calibrated"]["macro_f1"] >= first["validation_uncalibrated"]["macro_f1"]
    )
    assert first["validation_calibrated"]["binary_warning"]["false_positive_rate"] <= 0.10


def test_cloud_notebook_contains_no_saved_execution_output() -> None:
    notebook = Path("notebooks/SentiTurca_BERTurk.ipynb").read_text(encoding="utf-8")

    assert '"execution_count": null' in notebook
    assert '"outputs": []' in notebook
    assert "/kaggle/working" in notebook
    assert "/content" in notebook
