# H44-H47 우선순위 후속 실험 기록

- 실험 ID: `H44_H47_priority_followups`
- 날짜: 2026-05-14
- 목적:
- H34~H43 이후 바로 이어서 확인할 가치가 높은 서비스 적용 가설 검증
- 저이력 Warm, Cold 3D 중간 부피, high-risk 가격 범위, Warm 신뢰도 등급 확인
- 실행 스크립트:
- [`scripts/track3/h44_h47_priority_followups.py`](/Users/bo/VisionAI/scripts/track3/h44_h47_priority_followups.py:1)
- 결과 파일:
- [`data/track3_h44_h47_priority_followups_results.json`](/Users/bo/VisionAI/data/track3_h44_h47_priority_followups_results.json:1)

## 1. 사용 데이터

- 학습 데이터:
- `data/release_split/track3_train.csv`
- Warm 평가:
- `data/release_split/track3_test_warm.csv`
- Cold 평가:
- `data/release_split/track3_test_cold.csv`

## 2. 사용 모델

- Warm 기준:
- H31 LightGBM 후보
- 비교용 Warm fallback:
- 작가명/작가 이력 제거한 구조-only LightGBM
- Cold 기준:
- H32 LAD 조건부 fallback
- 비교용 Cold 정책:
- 3D 중간 부피 구간만 기본 Cold 모델로 되돌리는 예외 정책

## 3. H44 결과

- 가설:
- Warm 저이력 작가에는 일반 Warm 모델보다 보수적 fallback이 더 안정적일 것이다
- 실험 방법:
- 작가 학습 작품 수 `1건`, `1~3건`, `4건 이상` 구간으로 나눔
- H31 Warm 모델과 구조-only fallback 모델을 비교함
- 결과:
- 작가 1건 구간:
- H31 `0.2466`
- 구조-only fallback `0.5015`
- fallback 악화 `+0.2549`
- 작가 1~3건 구간:
- H31 `0.1608`
- 구조-only fallback `0.5167`
- fallback 악화 `+0.3559`
- 판단:
- 저이력 Warm에서도 구조-only fallback은 기각
- 저이력 문제는 모델 교체보다 신뢰도 경고/가격 범위로 처리하는 편이 적절함

## 4. H45 결과

- 가설:
- Cold 3D 중간 부피 구간은 3D fallback보다 기본 Cold 모델이 더 안정적일 것이다
- 실험 방법:
- Cold 3D를 부피 기준 `low`, `mid`, `high`로 나눔
- H32 fallback과 `mid volume만 기본 Cold 모델`로 되돌리는 정책을 비교함
- 결과:
- 3D mid:
- H32 `0.2238`
- mid 예외 정책 `0.1912`
- 개선 `-0.0327`
- 전체 Cold:
- H32 `0.2786`
- mid 예외 정책 `0.2765`
- 개선 `-0.0022`
- 주의:
- median APE는 개선됐지만, 3D mid의 p90/p95 오차는 일부 커짐
- 판단:
- H45는 조건부 예외 후보
- 바로 최종 채택하기보다 p90/p95와 within-50%까지 함께 보고 결정해야 함

## 5. H46 결과

- 가설:
- High-risk 작품에는 가격 범위를 넓게 주는 방식이 실제 포함률을 개선할 것이다
- 실험 방법:
- Warm high-risk:
- 저이력 작가, 3D, 초대형 호수 중 하나라도 해당
- Cold high-risk:
- 3D, 대형 호수, 대형 면적 중 하나라도 해당
- low-risk 기준 오차폭을 high-risk에 그대로 적용한 경우와 high-risk 전용 오차폭을 비교함
- Warm 결과:
- high-risk coverage `0.7088 -> 0.7997`
- high-risk 전용 폭을 쓰면 포함률 개선
- Cold 결과:
- low-risk 폭 `0.9701`
- high-risk 폭 `0.6677`
- high-risk 전용 폭의 coverage `0.8000`
- 해석:
- 현재 Cold high-risk 정의는 너무 넓고 low-risk가 오히려 더 어려운 구간을 포함함
- 판단:
- Warm high-risk 가격 범위 확대는 부분 채택 가능
- Cold high-risk 기준은 재설계 필요

## 6. H47 결과

- 가설:
- `artist_works_log`만으로도 Warm 신뢰도 등급을 만들 수 있을 것이다
- 실험 방법:
- 작가 학습 작품 수 기준으로 A/B/C/D 등급을 나눔
- 각 등급별 Warm median APE를 비교함
- 결과:
- A: 51건 이상
- median APE `0.0621`
- B: 11~50건
- median APE `0.0759`
- C: 4~10건
- median APE `0.1350`
- D: 1~3건
- median APE `0.1608`
- 판단:
- 작가 이력 수가 줄어들수록 오차가 단계적으로 커짐
- Warm 신뢰도 등급 후보로 사용 가능

## 7. 결론

- H44:
- 기각
- 저이력 Warm도 구조-only fallback보다 H31 유지가 낫다
- H45:
- 조건부 후보
- Cold 3D 중간 부피 구간은 기본 Cold 모델 예외 적용 가능성이 있다
- H46:
- 부분 검증
- Warm high-risk 가격 범위 확대는 유효
- Cold high-risk 정의는 재조정 필요
- H47:
- 채택 후보
- 작가 이력 수 기반 Warm 신뢰도 등급을 만들 수 있다

## 8. 다음 할 일

- H45:
- median APE뿐 아니라 p90/p95, within-50%까지 포함한 채택 기준 재검토
- H46:
- Cold high-risk 조건을 더 좁게 재설계
- H47:
- Warm 출력 정책에 A/B/C/D 신뢰도 등급 연결
- 운영안:
- H31/H32 모델 정책에 H45, H47을 반영할지 최종 검토
