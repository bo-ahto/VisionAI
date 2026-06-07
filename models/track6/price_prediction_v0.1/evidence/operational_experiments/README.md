# v0.1 운영 보정 실험 관리 기준

## 1. 목적

- `price_prediction_v0.1` 모델을 운영 적용 후보로 고정한 상태에서, 후속 보정 실험을 별도로 추적한다.
- 운영 기본 모델과 실험 중인 보정 후보가 섞이지 않도록 관리한다.
- 실험 결과가 좋아 보여도, 재현성과 반복 검증을 통과하기 전에는 v0.1 기본 정책으로 승격하지 않는다.

## 2. 폴더 역할

| 위치 | 역할 |
| --- | --- |
| `models/track6/price_prediction_v0.1/operational` | 현재 서비스 테스트에 사용하는 v0.1 운영 산출물 |
| `models/track6/price_prediction_v0.1/evidence/experiments` | v0.1 모델 선정의 핵심 근거가 된 과거 실험 산출물 |
| `models/track6/price_prediction_v0.1/evidence/operational_experiments` | v0.1 적용 이후 추가 보정, 오류 분석, 운영 검증 실험 인덱스 |
| `experiments/track6` | 전체 실험 원본 작업 폴더 |

## 3. 관리 원칙

- 기존 `experiments/track6` 실험 폴더는 원본 위치에 둔다.
- v0.1 패키지 안에는 원본을 무리하게 복사하지 않고, 요약 문서와 참조 경로를 남긴다.
- v0.1 운영 기본값을 바꾸는 실험은 반드시 별도 실험 번호를 부여한다.
- 신규 데이터 `0604`는 라벨 정합성 검증 전까지 운영 감사 데이터로 사용한다.
- 신규 데이터 결과만으로 보정값을 학습해 v0.1 기본 모델에 반영하지 않는다.
- 보정 후보는 기존 split, 반복 split, 작가 단위 재학습 검증을 순서대로 통과해야 한다.

## 4. 후속 보정 실험 폴더 양식

```text
OP-V01-CAL-XX_short_name/
  experiment_plan.md
  scripts/
  outputs/
  reports/
  artifacts/
  logs/
```

| 하위 폴더 | 내용 |
| --- | --- |
| `experiment_plan.md` | 실험 목적, 기준 모델, 보정식, 채택 기준 |
| `scripts` | 전처리, 예측, 평가, 리포트 생성 스크립트 |
| `outputs` | 예측값, 지표, 오류 분석 CSV |
| `reports` | 사람이 읽는 결과 보고서 |
| `artifacts` | 보정 테이블, 정책 파일, 모델 파일 |
| `logs` | 실행 로그 |

## 5. 채택 기준

- 기존 test split에서 MdAPE, MAPE, p95_APE 중 최소 2개 이상 개선되어야 한다.
- MAPE 개선만 보고 채택하지 않는다. MdAPE와 p95_APE가 크게 나빠지면 제외한다.
- Warm은 작가별 기존 거래가 있으므로 점가격 개선과 함께 가격 범위 안정성도 본다.
- Cold는 신규 작가 일반화가 핵심이므로 작가 단위 반복 검증을 더 중요하게 본다.
- 0604 신규 데이터는 운영 시뮬레이션 성격이므로, 라벨 이상치와 고가/저가 구간을 별도 표시한다.

## 6. 실험 인덱스

| 실험 ID | 실험 내용 | 현재 판단 | 결과 문서 |
| --- | --- | --- | --- |
| OP-V01-CAL-07 | PP-AMW6 Warm 작가 메타 잔차 보정 후보를 v0.1 운영 0604 출력 기준으로 재검증 | `service_primary` 기준 소폭 개선. 운영 기본값 즉시 교체가 아니라 추가 검증 후보로 유지 | `OP-V01-CAL-07_warm_amw6_operational_revalidation/reports/result_report.md` |
| OP-V01-CAL-08 | 추천 보정 후보를 통합 비교. 작가 메타, 생년대, 유사 작품 기반 가격 피처 저비중 결합과 조합 후보를 같은 0604 기준에서 비교 | 균형형 1순위는 `meta_plus_birth_cap007`. MAPE/p95 방어 목적은 `meta_birth_svc_w010`, `birth_svc_w010`도 후보로 유지 | `OP-V01-CAL-08_recommended_correction_policy_compare/reports/result_report.md` |
