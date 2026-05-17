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
| T4-H1 | T4-G1 | 새 데이터셋에서도 작품 구조 정보만으로 Warm / Cold 기본 예측이 가능할 것이다 | 작가 피처 없이 구조-only baseline을 만들고 Warm / Cold validation 성능을 분리 비교 | `track4_train`, `val_warm`, `val_cold` | `medium_category`, `support_category`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate` | 단순 중앙값 baseline, Track 3 기준 성능 | Warm/Cold median APE가 단순 baseline보다 개선 | 부분 검증 | validation 1회 | Huber 기준 Warm `0.4148`, Cold `0.3567`로 단순 중앙값보다 개선 | T4-E023 | test 확인 전까지 기준 baseline으로 사용 |
| T4-H2 | T4-G2 | Warm에서는 작가 정보와 train 기준 작가 이력 피처가 성능을 개선할 것이다 | 구조-only Warm 모델과 작가 피처 추가 모델을 비교 | `track4_train`, `val_warm` | 구조 피처 + `artist_key`, `artist_works_log` | H1 Warm 구조-only | Warm median APE 개선, p95 APE 악화 없음 | 부분 검증 | validation 1회 | 작가 key 포함 시 Warm median APE `0.2697`로 구조-only `0.4619`보다 개선 | T4-E024 | 반복 검증 필요 |
| T4-H3 | T4-G2 | Warm 작가 이력 피처는 예측 시점 이전 정보만으로 계산해도 성능이 유지될 것이다 | train 기준 집계 피처와 temporal-safe 대체 피처를 비교 | `track4_train`, `val_warm` | `artist_works_log`, 작가별 train-only 통계 후보 | H2 작가 피처 모델 | 성능 유지 또는 소폭 하락 이내, 누수 없음 | 예정 | 미검증 | Track 4 핵심 검증 필요 | - | 날짜/연도 기반 안전성 검토 |
| T4-H4 | T4-G3 | Cold에서는 robust 선형 계열이 트리 모델보다 더 안정적일 것이다 | LAD/Quantile/Huber/Ridge와 LightGBM/XGBoost/CatBoost를 같은 피처로 비교 | `track4_train`, `val_cold` | 작가 피처 제외 구조 피처 | H1 Cold 구조-only | Cold median APE와 p95 APE가 가장 낮은 후보 확인 | 부분 검증 | validation 1회 | Quantile median APE `0.3486`, Huber p95 APE `1.2373`으로 robust 선형 계열 우세 | T4-E025 | support/3D 피처 실험 후 재확인 |
| T4-H5 | T4-G4 | 출처/갤러리 피처를 제외해도 운영 가능한 피처만으로 baseline 성능을 만들 수 있을 것이다 | source/gallery 없이 운영 가능 피처만 사용한 모델과 금지 피처 포함 탐색 모델을 비교하지 않고 감사만 유지 | `track4_feature_candidates` | source/gallery 제외 피처 | 데이터 품질 검토 | 금지 피처가 모델 입력에 없음 | 부분 검증 | 데이터 검증 | 데이터셋에서는 제외 원칙 반영 완료 | T4-E020 | 모델 학습 코드에서 재확인 |
| T4-H6 | T4-G4 | 지지체 unknown이 많아 support 피처는 바로 채택보다 ablation으로 검증해야 한다 | support 포함/제외, unknown bucket 처리 방식을 비교 | `track4_train`, `val_warm`, `val_cold` | `support_category`, `medium_support_bucket` | H1/H2/H4 baseline | Warm/Cold 중 한쪽 악화 시 분리 적용 | 부분 검증 | validation 1회 | Warm은 support 유지, Cold는 support 제외가 median APE 기준 유리 | T4-E026 | risk segmentation에서 재확인 |
| T4-H7 | T4-G5 | 크기 파싱 보완 후 면적/비율 피처는 안정적으로 사용할 수 있을 것이다 | 보완 전/후 품질 리포트와 size 관련 피처 성능을 비교 | `track4_train`, validation split | `log_area`, `aspect_ratio`, `has_depth` | 보완 전 품질 검토 | 파생값 불일치 0, 극단 비율 학습 후보 0 | 부분 검증 | 데이터 검증 | 데이터셋 기준 통과, 성능 영향은 미검증 | T4-E020 | size 피처 ablation |
| T4-H8 | T4-G5 | 3D 작품은 2D와 다른 피처 또는 별도 모델이 필요할 것이다 | 2D/3D slice별 오차를 비교하고 depth/volume 피처 추가 효과 확인 | `track4_train`, `val_warm`, `val_cold` | `depth_cm`, `has_depth`, `is_3d_candidate`, volume 후보 | H1/H4 baseline | 3D slice p95 APE 개선 | 부분 검증 | validation 1회 | Cold 3D median APE가 2D보다 높아 별도 관리 필요 | T4-E027 | tail risk 보완 필요 |
| T4-H9 | T4-G5 | Cold는 전체 적용보다 저위험 구간에 제한할 때 더 실용적일 것이다 | Cold를 2D/3D, 대형, unknown, 가격대 구간으로 나눠 성능과 tail risk 확인 | `val_cold`, `test_cold` | 위험 구간 flag | Cold 전체 성능 | 저위험 구간 median/p95 APE 개선, coverage 폭 감소 | 부분 검증 | validation 1회 | low risk median APE `0.3400`, high risk `0.7080`으로 구간 차이 확인 | T4-E030 | 가격 범위 calibration 필요 |
| T4-H10 | T4-G2 | Warm / Cold 라우팅은 작가 존재 여부뿐 아니라 train 작품 수 기준을 둘 때 더 안정적일 수 있다 | 작가 작품 수 threshold 1/3/5/10 기준으로 Warm/Cold 재분류 성능 비교 | `track4_train`, `val_warm`, `val_cold` | `artist_works_count_train` | 기본 라우팅 | 저이력 Warm p95 APE 개선 | 검증 완료 | validation 1회 | threshold를 높이면 Warm 성능이 악화되어 기본 라우팅 유지 | T4-E029 | 신뢰도 기준으로만 재활용 |
| T4-H11 | T4-G7 | 단일 가격보다 가격 범위와 신뢰도 등급을 함께 제공하는 방식이 더 안전하다 | validation 예측 오차로 interval coverage와 범위 폭 계산 | validation split | 모델 예측값, 오차 구간 | 단일 가격 출력 | coverage 목표 달성, 범위 폭 허용 가능 | 예정 | 미검증 | 서비스 UX 판단 필요 | - | calibration 실험 |
| T4-H12 | T4-G8 | Track 4 최종 후보는 성능, 운영 가능성, 재현 가능성을 모두 만족해야 한다 | 후보 모델별 성능표, 금지 피처 점검, 재학습 명령, 결과 파일을 묶어 검토 | validation/test split | 최종 후보 피처 | Track 3 baseline, Track 4 baseline | 성능/설명/재현 조건 충족 | 예정 | 미검증 | 최종 단계 가설 | - | H1~H11 이후 진행 |
| T4-H13 | T4-G3, T4-G4 | 재료를 더 세분화하면 Cold 성능이 개선될 수 있지만 희소 재료는 묶어야 안정적일 것이다 | oil/acrylic/mixed/media/print 등 재료 flag와 rare bucket을 추가해 Cold ablation | `track4_train`, `val_cold` | `medium_category`, 재료 flag, rare medium bucket | H1/H4 Cold baseline | Cold median APE 개선, rare 구간 p95 APE 악화 없음 | 보류 | validation 1회 | material flag 개선 폭이 작아 단독 채택 근거 부족 | T4-E032 | 조합 피처에서 재검토 |
| T4-H14 | T4-G4, T4-G5 | 지지체 unknown은 단순 결측이 아니라 오차와 신뢰도에 영향을 주는 신호일 수 있다 | support unknown을 포함/제외/flag 처리한 모델을 Warm/Cold에서 비교 | `track4_train`, `val_warm`, `val_cold` | `support_category`, `is_support_unknown`, `medium_support_bucket` | H6 support ablation | unknown flag 추가 시 성능 또는 위험 구간 설명력 개선 | 부분 검증 | validation 1회 | Cold support unknown median APE가 known보다 높아 위험 flag 후보로 유지 | T4-E026 | 신뢰도/출력 정책 실험에 연결 |
| T4-H15 | T4-G4, T4-G6 | 크기 피처는 많이 넣기보다 대표 조합으로 줄이는 것이 더 안정적일 수 있다 | width/height/log_area/aspect_ratio/ho 조합을 줄이거나 늘려 Warm/Cold 성능 비교 | `track4_train`, `val_warm`, `val_cold` | `log_area`, `aspect_ratio`, `estimated_ho`, `has_depth` | 전체 크기 피처 모델 | 피처 수를 줄여도 median APE 유지, p95 APE 악화 없음 | 예정 | 미검증 | Track 3의 크기 중복 이슈를 Track 4 클렌징 후 재검증 | - | size feature reduction |
| T4-H16 | T4-G5 | 3D/depth/volume 피처는 전체 작품에 일괄 적용하지 않고 3D 후보에만 조건부 적용해야 안정적일 것이다 | 2D/3D slice별로 depth/volume/longest edge 피처 적용 여부 비교 | `track4_train`, `val_warm`, `val_cold` | `depth_cm`, `has_depth`, `is_3d_candidate`, volume 후보 | H8 3D baseline | 3D p95 APE 개선, 2D median APE 악화 없음 | 부분 검증 | validation 1회 | depth 피처 전체 일괄 적용은 개선 제한적 | T4-E027 | 조건부 전략 재설계 |
| T4-H17 | T4-G5, T4-G7 | Cold는 저위험/고위험 구간을 나누면 서비스 가능한 범위를 더 명확히 정할 수 있다 | 3D, 대형, unknown, 희소 재료, 극단 가격 후보별 Cold 오차와 범위 폭 비교 | `val_cold`, `test_cold` | 위험 flag, 모델 예측값, 오차 | Cold 전체 평균 정책 | 저위험 구간에서 median APE와 범위 폭 개선 | 부분 검증 | validation 1회 | 위험 flag 2개 이상 high 그룹은 단일 가격 신뢰 낮음 | T4-E030 | coverage/범위 폭 검증 필요 |
| T4-H18 | T4-G7 | 가격 범위는 test가 아니라 validation/calibration 기준으로 정해야 운영 재현성이 있다 | validation 오차로 범위를 정하고 test에서 coverage와 폭을 확인 | validation/test split | 예측값, calibration 오차 | test 직접 보정 방식 금지 | 목표 coverage 유지, 범위 폭 과대 확대 없음 | 부분 검증 | validation→test | Warm coverage `0.8102`는 목표 근접, Cold coverage `0.6900`은 부족 | T4-E031 | Cold calibration 재설계 |
| T4-H19 | T4-G2, T4-G5 | Warm에서도 작가 학습 작품 수가 적으면 Cold에 가까운 위험을 보일 수 있다 | train 작품 수 1/3/5/10 구간별 Warm 오차를 비교 | `track4_train`, `val_warm`, `test_warm` | `artist_works_count_train`, `artist_works_log` | Warm 전체 성능 | 저이력 Warm 구간의 p95 APE와 범위 폭 확인 | 부분 검증 | validation 1회 | 저이력은 위험 신호지만 Cold 모델 라우팅은 불리 | T4-E029 | 가격 범위/신뢰도 실험에 연결 |
| T4-H20 | T4-G2, T4-G4 | 작가명 자체보다 train 기준 작가 이력 피처가 Warm에서 더 운영 안정적일 수 있다 | `artist_key` categorical 모델과 count/stat 기반 모델을 비교 | `track4_train`, `val_warm` | `artist_key`, `artist_works_log`, train-only 작가 통계 후보 | H2 Warm 작가 모델 | 작가명 제외 모델이 성능 유지 또는 안정성 개선 | 부분 검증 | validation 1회 | 이력 피처만으로는 구조-only보다 악화, 작가 key 유지 필요 | T4-E024 | 반복 검증 및 동명이인 정책 확인 |
| T4-H21 | T4-G1, T4-G8 | 하나의 공유 모델보다 Warm/Cold 분리 모델이 Track 4에서도 더 안정적일 것이다 | 같은 운영 피처로 공유 모델과 Warm/Cold 전용 모델을 비교 | `track4_train`, validation split | 공통 운영 피처, Warm 전용 피처 | H1/H2/H4 후보 | Warm/Cold 중 한쪽 큰 악화 없이 분리 모델 우세 | 부분 검증 | 내부 반복 5회 | Warm에서 분리 정책 median APE 평균 `0.3559`, 공유 모델 `0.5325`보다 우세 | T4-E028 | 라우팅 threshold 실험 필요 |
| T4-H22 | T4-G6 | Warm validation rows가 작기 때문에 단일 split 성능보다 반복 검증 평균이 더 믿을 만할 것이다 | seed/split을 바꿔 반복 검증하고 median APE 평균과 표준편차 확인 | `track4_train`, validation split | 후보 피처셋 | 단일 validation 점수 | 반복 평균 성능 안정, 순위 뒤집힘 여부 확인 | 부분 검증 | 내부 반복 5회 | Cold median APE 표준편차 `0.0454`로 split 민감도 확인 | T4-E028 | 반복 검증을 후속 실험 기본 절차로 유지 |
| T4-H23 | T4-G4, T4-G6 | 출처별 분포 차이는 피처로 쓰지 않더라도 감사 slice로 확인해야 한다 | source별 성능/결측/가격 분포를 평가만 하고 모델 입력에서는 제외 | validation/test split | source는 분석용 slice만 사용 | source 미사용 모델 | 특정 출처에서만 좋은 모델을 걸러냄 | 예정 | 미검증 | 운영에서는 출처가 없으므로 학습 피처 사용 금지 유지 | - | source slice audit |
| T4-H24 | T4-G7, T4-G8 | 입력 정보가 부족하거나 위험 조건이면 단일 가격 대신 범위/경고 출력이 더 적절하다 | 정보량 점수와 위험 flag별 오차를 비교해 출력 정책 후보 작성 | validation split | `missing_count`, completeness score, 위험 flag | 단일 가격 출력 | 고위험 구간의 경고 기준 설명 가능 | 부분 검증 | validation 1회 | high risk 그룹은 낮은 신뢰도/넓은 범위 표시 후보 | T4-E030 | calibration 실험에서 범위 수치화 |
| T4-H25 | T4-G8 | 모델 학습 전 금지 피처 manifest를 검사하면 source/gallery 누수를 줄일 수 있다 | 학습 스크립트에서 금지 컬럼 포함 여부를 자동 검사 | 모델 학습 입력 | forbidden feature manifest | 수동 점검 | 금지 피처 포함 시 학습 중단 | 예정 | 미검증 | 운영 재현성 관리 장치 필요 | - | feature manifest 구현 |
| T4-H26 | T4-G5, T4-G7 | 고가 작품 후보는 일반 작품보다 오차와 가격 범위가 크게 달라 별도 위험 정책이 필요하다 | 가격 상위 구간별 Warm/Cold 오차와 범위 폭 비교 | validation/test split | 가격 구간 flag, 예측값 | 전체 구간 성능 | 고가 구간 오차가 크면 신뢰도 경고 후보로 분리 | 부분 검증 | validation 1회 | 고가 후보 4건 median APE `0.9591`, 표본 작아 보류 | T4-E030 | test/추가 데이터로 재확인 |
| T4-H27 | T4-G3, T4-G5 | Cold 2D와 Cold 3D는 같은 모델보다 조건부 fallback이 더 안정적일 수 있다 | Cold 2D 기본 모델과 Cold 3D 전용 보완 모델을 조건부 결합 | `val_cold`, `test_cold` | 2D/3D flag, 3D 전용 피처 | Cold 단일 모델 | Cold 전체 median APE 유지, 3D p95 APE 개선 | 보류 | validation 1회 | 3D median APE는 개선됐지만 3D p95 APE가 크게 악화 | T4-E027 | tail risk 제어 후 재실험 |
| T4-H28 | T4-G4, T4-G5 | 재료와 크기를 조합한 피처는 단독 피처보다 일부 약점 구간을 더 잘 설명할 수 있다 | `medium_size_bucket`, `large_oil`, `small_print` 등 조합 피처 추가 후 ablation | `track4_train`, validation split | medium-size/support combo | 단독 피처 모델 | Warm/Cold 한쪽 개선 시 모델별 분리 적용 | 예정 | 미검증 | Track 3 H14 계열을 Track 4 운영 피처로 재검증 | - | combo feature 실험 |
| T4-H29 | T4-G7 | 신뢰도 점수는 출처가 아니라 작가 이력 수, 정보 완성도, 위험 flag로 만들 수 있다 | confidence score 후보를 만들고 오차/coverage와 상관 확인 | validation split | artist count, completeness, risk flags | 신뢰도 없음 | 낮은 신뢰도 그룹에서 실제 오차가 높게 나타남 | 부분 검증 | validation→test | Warm low_history와 Cold risk group별 coverage 차이 확인 | T4-E031 | 정책 기준 세분화 |
| T4-H30 | T4-G8 | 최종 Track 4 운영 후보는 데이터 파이프라인, 학습 스크립트, 예측 schema가 함께 고정되어야 한다 | 최종 후보 산출물 목록과 재현 명령을 묶어 dry-run 확인 | 최종 후보 파일 | 최종 schema, 모델 artifact | 문서만 존재 | 새 데이터 추가 후 같은 명령으로 재생성 가능 | 예정 | 미검증 | 최종 운영 이관 전 필수 조건 | - | production package dry-run |
