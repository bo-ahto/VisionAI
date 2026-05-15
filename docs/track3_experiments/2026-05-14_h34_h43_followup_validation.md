# H34-H43 후속 검증 기록

- 실험 ID: `H34_H43_followup_validation`
- 날짜: 2026-05-14
- 목적:
- H31 Warm 후보와 H32 Cold 후보를 서비스 정책 관점에서 추가 검증
- 새 가설 H34~H43을 실제 release split 기준으로 확인
- 결과 파일:
- [`data/track3_h34_h43_followup_validation_results.json`](/Users/bo/VisionAI/data/track3_h34_h43_followup_validation_results.json:1)
- 실행 스크립트:
- [`scripts/track3/h34_h43_followup_validation.py`](/Users/bo/VisionAI/scripts/track3/h34_h43_followup_validation.py:1)

## 1. 사용 데이터

- 학습 데이터:
- `data/release_split/track3_train.csv`
- Warm 평가:
- `data/release_split/track3_test_warm.csv`
- Cold 평가:
- `data/release_split/track3_test_cold.csv`

## 2. 사용 모델과 피처

- Warm 기준 모델:
- H31 Warm 후보
- LightGBM
- `artist_name_ko`
- `artist_works_log`
- 작가별 과거 로그가격 통계
- 호수/3D 파생 피처
- Cold 기준 모델:
- H32 Cold 후보
- LAD 계열 `QuantileRegressor(quantile=0.5, alpha=0.0)`
- 2D 작품은 기본 Cold 모델
- 3D 작품은 3D 피처 포함 모델
- 비교 모델:
- H31형 단일 공유 LightGBM 모델
- 작가명만 사용한 Warm 모델
- 작가 이력만 사용한 Warm 모델
- 작가명+작가 이력 Warm 모델
- Cold feature group ablation 모델

## 3. 핵심 결과

- Warm 기준 성능:
- H31 Warm 후보 median APE: `0.1084`
- Cold 기준 성능:
- H32 조건부 fallback median APE: `0.2786`
- 단일 공유 모델:
- H31형 LightGBM을 Cold에 그대로 적용하면 Cold median APE `0.5938`
- Warm/Cold 분리 정책이 단일 모델보다 안전함

## 4. 가설별 결과

### H34. Cold 3D 조건부 모델은 특정 3D 구간에서 효과가 클 것이다

- 3D 전체:
- median APE 개선 `-0.0572`
- 3D low volume:
- 개선 `-0.0981`
- 3D mid volume:
- 악화 `+0.0327`
- 3D high volume:
- 개선 `-0.0346`
- 3D large ho:
- 개선 `-0.0719`
- 판단:
- 3D fallback은 전체적으로 유효함
- 단, 중간 부피 3D 구간은 악화 신호가 있어 추가 slice 분석 가치가 있음

### H35. Warm/Cold 분리 모델이 단일 모델보다 안정적일 것이다

- 분리 정책:
- Warm median APE `0.1084`
- Cold median APE `0.2786`
- 단일 H31형 공유 모델:
- Cold median APE `0.5938`
- 판단:
- 단일 모델 통합은 현재 기준 기각
- Warm/Cold 분리 정책 유지

### H36. Warm은 작가 학습 작품 수가 적은 구간에서 불안정할 수 있다

- 작가 학습 작품 수 1건:
- Warm median APE `0.2466`
- 2~3건:
- `0.1310`
- 4~10건:
- `0.1350`
- 11~50건:
- `0.0759`
- 51건 이상:
- `0.0621`
- 판단:
- 작가 이력이 적을수록 Warm 오차가 커짐
- 저이력 작가는 신뢰도 경고 또는 보수적 가격 범위가 필요함

### H37. 작가 학습 이력 수는 Warm 예측 오차와 관련 있다

- `artist_works_log`와 APE Spearman 상관:
- `-0.2423`
- 해석:
- 음수이므로 작가 이력이 많을수록 오차가 줄어드는 경향
- 판단:
- `artist_works_log`는 단순 성능 피처뿐 아니라 신뢰도 피처 후보로도 가치 있음

### H38. 작가명보다 구조화된 작가 이력 피처가 운영 안정성이 높을 것이다

- 작가명만 사용:
- Warm median APE `0.2273`
- 작가 이력만 사용:
- `0.1120`
- 작가명+작가 이력:
- `0.1002`
- 판단:
- 작가 이력 피처가 작가명 단독보다 훨씬 강함
- 작가명+이력이 가장 좋지만, 운영 채택 전에는 H16 temporal-safe 조건 해결 필요

### H39. 대형 작품은 별도 보정이 필요할 수 있다

- Warm 대형 호수:
- median APE `0.1151`
- Warm 초대형 호수:
- `0.1574`
- Cold 대형 호수:
- `0.4448`
- Cold 초대형 호수:
- `0.5412`
- 판단:
- Warm보다 Cold 대형/초대형 작품의 오차가 큼
- Cold 대형 작품은 가격 범위 확대 또는 경고 대상 후보

### H40. Cold에서는 크기/형태 피처가 재료보다 중요할 것이다

- Cold full:
- median APE `0.3163`
- 재료 제거:
- `0.4112`
- 크기/호수 제거:
- `0.4809`
- 형태 제거:
- `0.3393`
- 판단:
- 재료도 중요하지만 크기/호수 제거 시 악화가 더 큼
- Cold 기본 모델에서 크기/호수 피처는 유지해야 함

### H41. 현재 후보는 반복 실행에서도 안정적일 것이다

- H31 Warm 3 seed 평균:
- 약 `0.1090`
- H31 이번 평균 예측 기준:
- `0.1084`
- H32 Cold:
- deterministic LAD 기준 `0.2786`
- 판단:
- H31/H32 후보의 현재 순위는 유지됨

### H42. 큰 오차 작품은 사전에 탐지 가능한 패턴이 있다

- Warm 오차 상위 10%:
- 작가 학습 작품 수 중앙값 `3`
- 3D 비율 `62.1%`
- Cold 오차 상위 10%:
- 3D 비율 `72.8%`
- 대형 호수 비율 `26.6%`
- log_area 중앙값 `8.79`
- 판단:
- 큰 오차는 3D, 대형, 낮은 작가 이력 쪽에 몰리는 경향
- high-risk flag 후보로 관리 가능

### H43. 단일 가격보다 가격 범위 제시가 더 안전할 수 있다

- Warm 90% 단순 로그 오차폭:
- `0.666`
- Cold 90% 단순 로그 오차폭:
- `1.070`
- 판단:
- Cold는 같은 신뢰 수준을 주려면 가격 범위가 훨씬 넓어짐
- 최종 서비스 출력은 단일 가격 + 신뢰도/가격 범위 형태가 더 안전함
- 단, 현재 값은 단순 참고용이며 최종 calibration은 별도 필요

## 5. 결론

- 채택:
- Warm/Cold 분리 정책 유지
- H31 Warm 후보 유지
- H32 Cold 3D 조건부 fallback 유지
- 작가 이력 피처는 Warm 핵심 피처 및 신뢰도 피처 후보로 유지
- Cold 대형/3D 작품은 high-risk 후보로 관리
- 보류:
- Cold 3D fallback을 더 좁은 조건으로 제한할지 여부
- 가격 범위 출력의 최종 calibration
- 중단:
- Warm/Cold 단일 공유 모델 통합

## 6. 다음 할 일

- H34 후속:
- 3D 중간 부피 구간에서 fallback 악화 원인 확인
- H36/H37 후속:
- 저이력 Warm 작가에 대한 신뢰도 점수 설계
- H39/H42 후속:
- Cold 대형/3D high-risk flag를 production 출력 정책에 연결
- H43 후속:
- 최종 후보 확정 후 prediction interval calibration 재실행
