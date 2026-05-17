# Track 4 Warm 재검증 split

- 목적: 기존 `track4_test_warm.csv`가 137건으로 작아 Warm 최종 성능 판단이 흔들릴 수 있는 문제를 보완
- 원칙: 기존 Track 4 split은 보존하고, Warm 재검증용 split만 별도 생성
- 기준: 기존 Cold validation/test 작가는 제외하고 Warm 후보 작가에서 반복 holdout 생성
- 저장 방식: train CSV를 seed별로 복제하지 않고, 평가 holdout membership과 seed별 평가 CSV만 저장
- 재현 명령: `python3 scripts/track4/run_t4_e053_warm_recheck_split_revalidation.py`

## 결과 요약

- seed 수: `5`
- 평균 평가 rows: `534.4`
- 평균 평가 작가 수: `217.0`
- Warm median APE 평균: `0.1687`
- Warm median APE 표준편차: `0.0103`
- Warm p95 APE 평균: `0.9379`

## 생성 파일

- `warm_recheck_split_membership.csv`: seed별 Warm 평가 holdout row membership
- `warm_recheck_summary.json`: split 생성 설정과 결과 요약
- `seed_*_warm_eval.csv`: seed별 Warm 평가 rows
