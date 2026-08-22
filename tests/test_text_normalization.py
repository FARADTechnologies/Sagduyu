import pytest

from sagduyu.text_normalization import TurkishTextNormalizer, generate_masked_variants


@pytest.mark.parametrize(
    "masked",
    [
        "salak",
        "S A L A K",
        "s.a.l.a.k",
        "s*a*l*a*k",
        "s\u200ba\u200bl\u200ba\u200bk",
        "s4l4k",
        "sаlаk",
        "salaaaak",
    ],
)
def test_supported_masks_have_the_same_canonical_form(masked: str) -> None:
    assert TurkishTextNormalizer().normalize(masked) == "salak"


def test_turkish_case_and_word_boundaries_are_preserved() -> None:
    result = TurkishTextNormalizer().analyze("İYİ bir çözüm; ışık güçlü.")

    assert result.normalized_text == "iyi bir cozum isik guclu"
    assert "turkish_diacritics" in result.transformations
    assert result.original_length > 0


def test_normal_numbers_are_not_rewritten_as_leetspeak() -> None:
    assert TurkishTextNormalizer().normalize("Toplantı 2026 yılında saat 14.30'da") == (
        "toplanti 2026 yilinda saat 14 30 da"
    )


def test_variant_generator_is_deterministic_and_normalizable() -> None:
    first = generate_masked_variants("salak")
    second = generate_masked_variants("salak")

    assert first == second
    assert set(first) == {
        "plain",
        "spaced",
        "dotted",
        "starred",
        "zero_width",
        "leetspeak",
        "repeated",
    }
    assert {TurkishTextNormalizer().normalize(value) for value in first.values()} == {"salak"}


def test_empty_variant_term_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one letter or number"):
        generate_masked_variants("***")
