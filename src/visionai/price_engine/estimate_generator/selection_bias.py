"""유찰 selection bias 보정 — 저유동성 작가 구간 확장.

낙찰 데이터만 사용하는 모델은 유찰 작품의 가격을 과소/과대추정할 수 있다.
유찰률이 높은 작가/그룹에 대해 예측 구간을 확장하고 신뢰도를 하향한다.

기획서 7장 #12, 개발기획서 1-4.
"""
from __future__ import annotations

_EXPANSION_FACTOR = 1.3
_ARTIST_UNSOLD_THRESHOLD = 0.50
_GROUP_UNSOLD_THRESHOLD = 0.40


def adjust_for_selection_bias(
    price_low: float,
    price_mid: float,
    price_high: float,
    artist_unsold_rate: float | None,
    group_unsold_rate: float | None,
    confidence_grade: str,
) -> tuple[float, float, float, str]:
    """저유동성 작가 예측 구간 확장 + 신뢰도 하향.

    조건: artist_unsold_rate > 50% OR group_unsold_rate > 40%

    보정:
    - 예측 구간 1.3배 확장: mid 기준으로 low/high를 넓힘
    - 신뢰도 C등급 이하로 하향

    Args:
        price_low: 예측 하한.
        price_mid: 예측 중앙.
        price_high: 예측 상한.
        artist_unsold_rate: 작가 유찰률 (None이면 무시).
        group_unsold_rate: 그룹 유찰률 (None이면 무시).
        confidence_grade: 현재 신뢰도 등급 ('A'/'B'/'C'/'D').

    Returns:
        (adjusted_low, adjusted_mid, adjusted_high, adjusted_grade)
    """
    needs_adjustment = False
    if artist_unsold_rate is not None and artist_unsold_rate > _ARTIST_UNSOLD_THRESHOLD:
        needs_adjustment = True
    if group_unsold_rate is not None and group_unsold_rate > _GROUP_UNSOLD_THRESHOLD:
        needs_adjustment = True

    if not needs_adjustment:
        return price_low, price_mid, price_high, confidence_grade

    # 비대칭 구간 확장: low/high 각각 mid 기준으로 독립 확장
    # low → mid 거리와 mid → high 거리를 각각 1.3배
    low_dist = price_mid - price_low
    high_dist = price_high - price_mid
    adjusted_low = price_mid - low_dist * _EXPANSION_FACTOR
    adjusted_high = price_mid + high_dist * _EXPANSION_FACTOR

    # 음수 방지
    adjusted_low = max(adjusted_low, 0.0)

    # 신뢰도 하향: A/B → C, C/D 유지
    grade_map = {"A": "C", "B": "C", "C": "C", "D": "D"}
    adjusted_grade = grade_map.get(confidence_grade, confidence_grade)

    return adjusted_low, price_mid, adjusted_high, adjusted_grade
