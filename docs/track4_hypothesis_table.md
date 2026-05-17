# Track 4 가설 상태표

- 목적: Track 4 모델 실험 가설을 세부 목표별로 관리
- 기준일: 2026-05-17
- 작성 방식: 개조식
- 원칙: 데이터셋 구성/검증은 `T4-D` 체크포인트로 분리하고, 아래 표에는 모델 실험 가설만 둠

## 1. 세부 목표

| 목표 ID | 세부 목표 | 설명 |
|---|---|---|
| T4-G1 | 기본 예측 가능성 확인 | 새 Track 4 데이터셋에서 작품 구조 정보만으로 가격 예측 baseline이 성립하는지 확인 |
| T4-G2 | Warm 성능 개선 | 이미 학습 데이터에 등장한 작가의 새 작품 예측 성능을 개선 |
| T4-G3 | Cold 성능 개선 | 처음 보는 작가의 작품 가격을 작가 정보 없이 안정적으로 예측 |
| T4-G4 | 운영 가능 피처 선정 | 실제 서비스 입력에서 다시 만들 수 있는 피처만 남김 |
| T4-G5 | 약점 구간 보완 | 3D, 대형, 저이력, unknown 재료/지지체 등 오차가 큰 구간을 보완 |
| T4-G6 | 모델 안정성 확인 | split, seed, 피처 조합이 바뀌어도 성능이 유지되는지 확인 |
| T4-G7 | 가격 범위/신뢰도 대응 | 단일 가격만으로 부족한 경우 가격 범위와 신뢰도 표시 기준을 정함 |
| T4-G8 | 최종 운영 정책 결정 | Warm / Cold 라우팅, 모델, 피처, 출력 정책을 최종 후보로 정리 |

## 2. 가설 상태표

| 가설 ID | 세부 목표 | 가설 요약 | 연구 방법 | 사용 데이터 | 핵심 피처 | 비교 기준 | 성공 기준 | 현재 상태 | 검증 강도 | 현재 판단 | 관련 실험 | 후속 필요 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T4-H1 | T4-G1 | 새 데이터셋에서도 작품 구조 정보만으로 Warm / Cold 기본 예측이 가능할 것이다 | 작가 피처 없이 구조-only baseline을 만들고 Warm / Cold validation 성능을 분리 비교 | `track4_train`, `val_warm`, `val_cold` | `medium_category`, `support_category`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate` | 단순 중앙값 baseline, Track 3 기준 성능 | Warm/Cold median APE가 단순 baseline보다 개선 | 예정 | 미검증 | 아직 모델 미실행 | - | baseline 스크립트 작성 |
| T4-H2 | T4-G2 | Warm에서는 작가 정보와 train 기준 작가 이력 피처가 성능을 개선할 것이다 | 구조-only Warm 모델과 작가 피처 추가 모델을 비교 | `track4_train`, `val_warm` | 구조 피처 + `artist_key`, `artist_works_log` | H1 Warm 구조-only | Warm median APE 개선, p95 APE 악화 없음 | 예정 | 미검증 | 아직 모델 미실행 | - | Warm 작가 피처 ablation |
| T4-H3 | T4-G2 | Warm 작가 이력 피처는 예측 시점 이전 정보만으로 계산해도 성능이 유지될 것이다 | train 기준 집계 피처와 temporal-safe 대체 피처를 비교 | `track4_train`, `val_warm` | `artist_works_log`, 작가별 train-only 통계 후보 | H2 작가 피처 모델 | 성능 유지 또는 소폭 하락 이내, 누수 없음 | 예정 | 미검증 | Track 4 핵심 검증 필요 | - | 날짜/연도 기반 안전성 검토 |
| T4-H4 | T4-G3 | Cold에서는 robust 선형 계열이 트리 모델보다 더 안정적일 것이다 | LAD/Quantile/Huber/Ridge와 LightGBM/XGBoost/CatBoost를 같은 피처로 비교 | `track4_train`, `val_cold` | 작가 피처 제외 구조 피처 | H1 Cold 구조-only | Cold median APE와 p95 APE가 가장 낮은 후보 확인 | 예정 | 미검증 | 아직 모델 미실행 | - | Cold 모델 비교 스크립트 작성 |
| T4-H5 | T4-G4 | 출처/갤러리 피처를 제외해도 운영 가능한 피처만으로 baseline 성능을 만들 수 있을 것이다 | source/gallery 없이 운영 가능 피처만 사용한 모델과 금지 피처 포함 탐색 모델을 비교하지 않고 감사만 유지 | `track4_feature_candidates` | source/gallery 제외 피처 | 데이터 품질 검토 | 금지 피처가 모델 입력에 없음 | 부분 검증 | 데이터 검증 | 데이터셋에서는 제외 원칙 반영 완료 | T4-E020 | 모델 학습 코드에서 재확인 |
| T4-H6 | T4-G4 | 지지체 unknown이 많아 support 피처는 바로 채택보다 ablation으로 검증해야 한다 | support 포함/제외, unknown bucket 처리 방식을 비교 | `track4_train`, `val_warm`, `val_cold` | `support_category`, `medium_support_bucket` | H1/H2/H4 baseline | Warm/Cold 중 한쪽 악화 시 분리 적용 | 예정 | 미검증 | unknown 비율 높음 | - | support ablation |
| T4-H7 | T4-G5 | 크기 파싱 보완 후 면적/비율 피처는 안정적으로 사용할 수 있을 것이다 | 보완 전/후 품질 리포트와 size 관련 피처 성능을 비교 | `track4_train`, validation split | `log_area`, `aspect_ratio`, `has_depth` | 보완 전 품질 검토 | 파생값 불일치 0, 극단 비율 학습 후보 0 | 부분 검증 | 데이터 검증 | 데이터셋 기준 통과, 성능 영향은 미검증 | T4-E020 | size 피처 ablation |
| T4-H8 | T4-G5 | 3D 작품은 2D와 다른 피처 또는 별도 모델이 필요할 것이다 | 2D/3D slice별 오차를 비교하고 depth/volume 피처 추가 효과 확인 | `track4_train`, `val_warm`, `val_cold` | `depth_cm`, `has_depth`, `is_3d_candidate`, volume 후보 | H1/H4 baseline | 3D slice p95 APE 개선 | 예정 | 미검증 | depth 큰 작품이 남아 별도 확인 필요 | - | 3D slice 실험 |
| T4-H9 | T4-G5 | Cold는 전체 적용보다 저위험 구간에 제한할 때 더 실용적일 것이다 | Cold를 2D/3D, 대형, unknown, 가격대 구간으로 나눠 성능과 tail risk 확인 | `val_cold`, `test_cold` | 위험 구간 flag | Cold 전체 성능 | 저위험 구간 median/p95 APE 개선, coverage 폭 감소 | 예정 | 미검증 | Cold 운영 범위 결정에 필요 | - | Cold risk segmentation |
| T4-H10 | T4-G2 | Warm / Cold 라우팅은 작가 존재 여부뿐 아니라 train 작품 수 기준을 둘 때 더 안정적일 수 있다 | 작가 작품 수 threshold 1/3/5/10 기준으로 Warm/Cold 재분류 성능 비교 | `track4_train`, `val_warm`, `val_cold` | `artist_works_count_train` | 기본 라우팅 | 저이력 Warm p95 APE 개선 | 예정 | 미검증 | 운영 라우팅 후보 | - | 라우팅 threshold 실험 |
| T4-H11 | T4-G7 | 단일 가격보다 가격 범위와 신뢰도 등급을 함께 제공하는 방식이 더 안전하다 | validation 예측 오차로 interval coverage와 범위 폭 계산 | validation split | 모델 예측값, 오차 구간 | 단일 가격 출력 | coverage 목표 달성, 범위 폭 허용 가능 | 예정 | 미검증 | 서비스 UX 판단 필요 | - | calibration 실험 |
| T4-H12 | T4-G8 | Track 4 최종 후보는 성능, 운영 가능성, 재현 가능성을 모두 만족해야 한다 | 후보 모델별 성능표, 금지 피처 점검, 재학습 명령, 결과 파일을 묶어 검토 | validation/test split | 최종 후보 피처 | Track 3 baseline, Track 4 baseline | 성능/설명/재현 조건 충족 | 예정 | 미검증 | 최종 단계 가설 | - | H1~H11 이후 진행 |
