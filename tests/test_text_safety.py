from sagduyu.text_safety import CourtesyChecker, CourtesyLevel


def test_clean_text_does_not_warn() -> None:
    result = CourtesyChecker().assess("Bu fikre katılmıyorum, başka bir çözüm önerebiliriz.")

    assert result.level is CourtesyLevel.CLEAR
    assert result.risk_score == 0
    assert result.should_warn is False
    assert result.warning is None
    assert result.matches == []
    assert result.user_may_continue is True


def test_masked_term_is_explained_without_blocking_user() -> None:
    result = CourtesyChecker().assess("Bu fikri s 4 l 4 k buluyorum.")

    assert result.level is CourtesyLevel.REVIEW
    assert result.should_warn is True
    assert result.normalized_text == "bu fikri salak buluyorum"
    assert "separated_letters" in result.transformations
    assert "leetspeak" in result.transformations
    assert [match.canonical_form for match in result.matches] == ["salak"]
    assert result.user_may_continue is True
    assert "otomatik yaptırım" in result.disclaimer


def test_multiple_matches_combine_without_exceeding_score_limit() -> None:
    result = CourtesyChecker().assess("Aptal ve ş e r e f s i z")

    assert result.level is CourtesyLevel.HIGH_RISK
    assert 80 <= result.risk_score <= 100
    assert {match.canonical_form for match in result.matches} == {"aptal", "serefsiz"}


def test_term_matching_respects_word_boundaries() -> None:
    result = CourtesyChecker().assess("Bu metin salaklık kavramını eleştiriyor.")

    assert result.should_warn is False
