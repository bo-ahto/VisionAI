"""K-Auction 추정가 관행 호 단위 라운딩.

Model-B 출력 전용. Model-A(가격 구간)에는 적용하지 않는다.
Half-up rounding (시장 관행: 0.5는 올림).
"""
from __future__ import annotations

import math


def round_to_market_unit(price: float) -> int:
    """K-Auction 추정가 관행에 맞춰 half-up 라운딩.

    Python 기본 round()는 banker's rounding (half-even)이므로,
    시장 관행에 맞게 half-up (0.5 → 올림)을 사용한다.

    | 가격대         | 라운딩 단위 |
    |----------------|------------|
    | < 100만        | 10만       |
    | 100만~500만    | 50만       |
    | 500만~1,000만  | 100만      |
    | 1,000만~5,000만| 500만      |
    | 5,000만~1억    | 1,000만    |
    | 1억 이상       | 5,000만    |

    Args:
        price: 원화 금액 (float).

    Returns:
        라운딩된 금액 (int). 음수 입력은 0 반환.
    """
    if price <= 0:
        return 0

    if price < 1_000_000:
        unit = 100_000
    elif price < 5_000_000:
        unit = 500_000
    elif price < 10_000_000:
        unit = 1_000_000
    elif price < 50_000_000:
        unit = 5_000_000
    elif price < 100_000_000:
        unit = 10_000_000
    else:
        unit = 50_000_000

    return int(math.floor(price / unit + 0.5) * unit)
