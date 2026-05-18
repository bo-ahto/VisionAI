# Track 6 가설 상태표

- 목적: Track6 실험 가설을 세부 목표별로 관리
- 기준일: 2026-05-18
- 작성 방식: 개조식
- 원칙: split 기준을 먼저 고정하고, 이후 모델/피처 실험만 진행

## 1. 세부 목표

| 목표 ID | 세부 목표 | 설명 |
|---|---|---|
| T6-G1 | 최종 split 기준 고정 | Cold 이름 중복과 Warm 저이력 문제를 split 단계에서 줄임 |
| T6-G2 | 기본 예측 가능성 확인 | 구조-only baseline으로 Track6 split의 기본 난이도 확인 |
| T6-G3 | Warm 성능 개선 | 작가 이력 정보가 있는 상황에서 Warm 모델 최적화 |
| T6-G4 | Cold 성능 개선 | 신규 작가 상황에서 작가 정보 없이 Cold 모델 최적화 |
| T6-G5 | 운영 가능 피처 선정 | 실제 서비스 입력에서 만들 수 있는 피처만 유지 |
| T6-G6 | 모델 안정성 확인 | validation/test 및 반복 split에서 성능 유지 확인 |
| T6-G7 | 신뢰도/가격 범위 정책 | 단일 가격이 위험한 구간을 식별하고 표시 정책 설계 |
| T6-G8 | 최종 운영 후보 확정 | Warm/Cold 모델, 피처, 라우팅, 출력 정책을 확정 |

## 2. 가설 상태표

| 가설 ID | 세부 목표 | 가설 요약 | 연구 방법 | 사용 데이터 | 핵심 피처 | 비교 기준 | 성공 기준 | 현재 상태 | 검증 강도 | 현재 판단 | 관련 실험 | 후속 필요 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T6-H1 | T6-G1 | strict cold와 Stable Warm 기준을 적용한 Track6 split이 최종 보고 기준으로 더 적합할 것이다 | Track3/4/5 방법을 반영해 클렌징 후보를 확정하고 validation/test 우선 split으로 한글명, 동명이인, Stable Warm train 작품 수, Cold 이름 중복, 작가당 평가 작품 수, 컬럼 품질, feature/label 분리를 검증 | Track6 name-corrected split | split metadata, column quality metadata, feature/label manifest | Track5 split | Cold 이름 중복 0, Stable Warm train 최소 작품 수 기준 충족, 평가셋 최소 rows 충족, 1작가 1작품 비율 기록, 컬럼 품질 fail 0, feature 누수 컬럼 0 | 검증 완료 | split + 컬럼 품질 + feature/label 검증 | split `pass`, 컬럼 품질 fail 0 / review 14, feature/label `pass`, val/test 규모 기준 통과 | T6-E001, T6-E001B, T6-E001C | T6-E003/T6-E004 진행 |
| T6-H2 | T6-G2 | Track6 split에서도 작품 구조 정보만으로 기본 예측이 가능할 것이다 | 작가 피처 없이 구조-only baseline을 Warm/Cold validation에서 평가 | Track6 name-corrected split | 구조 피처 | 중앙값 baseline | median APE가 중앙값 baseline보다 개선 | 검증 완료 | validation baseline 검증 | Warm `hist_gbdt_ordinal` median APE `0.4579`, Cold `lightgbm_basic` median APE `0.4029` | T6-E002 | T6-E003/T6-E004 진행 |
| T6-H3 | T6-G3 | Warm에서는 작가 식별 정보와 train 기준 작가 이력 피처가 성능을 개선할 것이다 | 구조-only, artist_key, artist history를 단계별 비교 | Track6 name-corrected split | 작가 피처 | 구조-only Warm | Warm median APE 개선 | 검증 완료 | Warm validation ablation | 구조-only `0.4986` → best `0.2737` (`structure_plus_artist_key`), 개선 `0.2248` | T6-E003 | T6-E004/T6-E005 진행 |
| T6-H4 | T6-G4 | Cold에서는 robust 선형 계열이 복잡한 트리 모델보다 안정적일 것이다 | Huber, Ridge, quantile tree, LightGBM, XGBoost, CatBoost 비교 | Track6 name-corrected split | Cold 구조 피처 | 구조-only baseline | Cold median/p95 개선 | 검증 완료 | Cold validation 모델 비교 | median best `hist_quantile_ordinal` `0.3903`, p95 best `huber_onehot` `1.4674` | T6-E004 | T6-E005 진행 |
| T6-H5 | T6-G5 | 크기/재료/지지체 조합 피처는 일부 구간 성능을 개선할 수 있다 | 기본 피처에 운영 가능 조합 피처를 하나씩 추가하고 Warm/Cold validation 성능 비교 | Track6 name-corrected split | size_bucket, shape_bucket, medium_size_bucket, support_size_bucket | 기본 피처셋 | median 또는 p95 개선 | 검증 완료 | Warm/Cold validation feature ablation | Warm best `0.2665` (`base_medium_size`), Cold median best `0.3782` (`base`), Cold p95 best `1.3835` (`base_size_shape`) | T6-E005 | T6-E006 진행 |
| T6-H6 | T6-G6 | 최종 후보는 validation뿐 아니라 test에서도 같은 방향의 성능을 보여야 한다 | validation에서 고른 후보만 test에 적용 | Track6 split | 최종 후보 피처 | validation 성능 | test 성능 급락 없음 | 예정 | 미실행 | 후보 선정 후 진행 | T6-E006~E007 | - |
| T6-H7 | T6-G7 | Cold는 위험 구간을 나누어 신뢰도 경고를 제공해야 실무적으로 해석 가능하다 | unknown, 대형, 3D, 저정보량 구간별 오차 비교 | Track6 split | risk flags | Cold 전체 | 위험 구간 오차가 명확히 높음 | 예정 | 미실행 | 후보 선정 후 진행 | T6-E008 | - |
| T6-H8 | T6-G8 | 최종 운영 후보는 성능, 운영 가능성, 설명 가능성, 재현 가능성을 모두 만족해야 한다 | 최종 모델, 피처, 전처리, manifest 생성 | Track6 artifacts | artifact manifest | 파일 누락 없음 | manifest ready | 예정 | 미실행 | 모든 실험 후 진행 | T6-E009 | - |
