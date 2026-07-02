# Cold 가격 예측 운영 모델 상세 리포트

작성일: 2026-06-10  
대상 모델: Cold 운영 예측 v0.5, 이종 모델 결합 기반 p95 방어 옵션  
재현 파일 위치: 13장 참고

## 1. 결론 요약

현재 Cold 운영 모델은 Warm 모델처럼 작가의 과거 거래 이력을 직접 기준가로 잡는 구조가 아니다. Cold는 학습 데이터에 같은 작가 이력이 없거나 충분하지 않은 신규 작가 상황을 가정하므로, 작품의 물리 조건과 매체 조건, 비작가 그룹 통계, 분위 예측 구간을 이용해 참고 예측가격과 방어 예측가격을 함께 산출한다.

핵심 판단은 아래와 같다.

- Cold에서 가장 좋은 전체 지표 기준은 검색 피처를 포함한 연구 기준 예측가격이다.
- 운영용 원천 입력 실행 환경에서는 외부 검색 피처 없이 실행 가능한 v0.5 모델을 p95 방어 옵션으로 둔다.
- v0.5는 전체 지표를 모두 이기는 모델이 아니라, 기존 운영 v0.2 방어 예측가격보다 큰 오차 구간을 줄이는 목적별 옵션이다.
- Warm식 `기준가 + 보정값` 구조도 추가 실험했지만, validation 개선이 fixed test로 안정적으로 전이되지 않아 최종 운영 경로에는 넣지 않는다.

전체 계산 순서도는 아래와 같다.

주의할 점은 아래 순서도가 `v0.5 검색 피처 미사용 운영 옵션`의 계산 흐름이라는 점이다. 현재 Cold fixed test 전체 지표 기준 1순위인 `검색 피처 포함 연구 기준 예측가격`은 검색 캐시와 작가 단위 검색 보정 lookup을 사용하는 별도 연구 기준이며, 상세 계산 흐름은 3.1장에서 따로 설명한다.

```text
[작품 입력 정보]
        |
        v
[Cold 기본 피처 생성]
  - 크기: 폭, 높이, 깊이, 면적, 로그면적, 화면비
  - 작품 조건: 매체, 지지체, 3D 후보 여부
  - 파생 버킷: 크기 구간, 지지체 x 크기 구간
        |
        v
[LightGBM 분위 예측]
  - 하위 분위 로그가격
  - 보수 분위 로그가격
  - 중앙 분위 로그가격
  - 상위 분위 로그가격
        |
        v
[비작가 그룹 통계 생성]
  - 매체/지지체/크기 조건별 과거 가격 통계
  - 조건이 희소하면 더 넓은 그룹으로 fallback
        |
        v
[Huber 그룹통계 예측]
  - 작품 피처 + 비작가 그룹 통계로 선형 안정 예측가격 생성
        |
        v
[대표 Cold 로그가격 생성]
  - 중앙 분위 예측 70%
  - Huber 그룹통계 예측 30%
        |
        v
[p95 방어 조건 판단]
  - 예측 구간 폭이 넓은가?
  - 대표가가 보수 분위보다 충분히 높은가?
        |
        v
[Cold 방어 로그가격 생성]
  - 위험 조건이 아니면 대표 로그가격 유지
  - 위험 조건이면 대표 로그가격과 보수 분위 로그가격을 50:50으로 낮춰 결합
        |
        v
[Cold 가격 = exp(Cold 로그가격)]
```

기존 Cold fixed test 기준 성능은 다음과 같다.

| 예측가격 | 성격 | MdAPE | MAPE | p95 APE | RMSE log |
|---|---|---:|---:|---:|---:|
| 검색 피처 포함 연구 기준 예측가격 | 전체 지표 기준 1순위 | 0.409820 | 0.849260 | 2.346465 | 0.850259 |
| 기존 운영 v0.2 방어 예측가격 | 이전 검색 피처 미사용 방어 기준 | 0.485162 | 1.177120 | 4.122299 | 0.937146 |
| v0.5 대표 예측가격 | LightGBM 분위 + Huber 그룹통계 결합 | 0.485651 | 1.213803 | 4.217550 | - |
| v0.5 방어 예측가격 | v0.5 대표 예측가격에 p95 방어 적용 | 0.482170 | 1.179011 | 3.649028 | 0.935354 |

v0.5 방어 예측가격은 기존 운영 v0.2 방어 예측가격 대비 p95 APE를 `4.122299 -> 3.649028`로 줄였다. 감소율은 약 `11.5%`다. 다만 검색 피처 포함 연구 기준 예측가격보다는 MAPE와 p95 APE가 모두 높으므로, v0.5를 Cold 전체 최종 승자라고 표현하면 안 된다. 이 모델의 정확한 역할은 `검색 피처 없이 원천 입력만으로 실행 가능한 p95 방어 목적의 운영 옵션`이다.

## 1.1 용어 정리

| 용어 | 뜻 |
|---|---|
| Cold | 같은 작가의 학습 이력이 없거나 충분하지 않은 신규 작가 예측 상황 |
| Warm | 같은 작가의 과거 거래 이력이 있어 작가별 기준 가격을 더 직접적으로 사용할 수 있는 상황 |
| 로그가격 | 가격에 자연로그 `log()`를 적용한 값. 모델 내부 계산은 대부분 로그가격에서 수행한다 |
| 최종 가격 | 로그가격에 지수함수 `exp()`를 적용해 원 단위 가격으로 되돌린 값 |
| 분위 예측 | 하나의 가격만 예측하지 않고 하위/중앙/상위 가격 구간을 따로 예측하는 방식 |
| LightGBM | Light Gradient Boosting Machine. 트리 여러 개를 순차적으로 쌓아 비선형 패턴을 학습하는 모델 |
| 예측 구간 폭 | 상위 분위 로그가격에서 하위 분위 로그가격을 뺀 값. 클수록 불확실성이 크다 |
| Huber 회귀 | 큰 오차 row의 영향을 일반 선형회귀보다 덜 받도록 만든 robust regression |
| 비작가 그룹 통계 | artist_key를 쓰지 않고 매체, 지지체, 크기 조건만으로 만든 과거 가격 통계 |
| 대표 예측가격 | 일반 상황에서 표시할 중심 예측가격 |
| 방어 예측가격 | 큰 오차 위험이 높은 row에서 대표 예측가격을 보수적으로 낮춘 가격 |
| p95 APE | absolute percentage error의 95퍼센타일 값. 상위 5% 큰 오차를 보는 지표 |
| RMSE log | 로그가격 기준 root mean squared error. 로그가격 오차의 평균제곱근 |
| fixed test | 후보 선택에 쓰지 않고 마지막 확인에만 사용하는 고정 테스트셋 |

## 1.2 내부 ID 대응표

본문에서는 실험 번호보다 기능이 드러나는 이름을 우선 사용한다. 내부 ID는 재현 파일이나 코드와 대조할 때만 참고한다.

| 문서용 이름 | 내부 추적 ID | 기능적 의미 |
|---|---|---|
| 검색 피처 포함 연구 기준 예측가격 | COLD_BASE_RESEARCH_V1, v0.3 guard+search | 검색 피처까지 포함한 Cold 연구 기준 예측가격. fixed test 전체 지표 기준 가장 강함 |
| 기존 운영 방어 예측가격 | COLD_BASE_OPERATIONAL_V1, v0.2 defense | 이전 검색 피처 미사용 운영 방어 기준 |
| LightGBM 분위 예측가격 | LGB Quantile 5-seed 평균 | 하위/중앙/상위 가격 구간을 예측하는 트리 기반 분위 모델 |
| Huber 그룹통계 예측가격 | Huber 그룹통계 6구성 평균 | 작품 조건과 비작가 그룹 통계를 사용하는 선형 안정 예측가격 |
| v0.5 대표 예측가격 | LightGBM 분위 예측 + Huber 그룹통계 결합 | 중앙 분위 예측 70%와 Huber 그룹통계 예측 30%를 결합한 중심 예측가격 |
| v0.5 방어 예측가격 | v0.5 defense | 위험 조건에서 대표 예측가격을 보수 분위 가격 쪽으로 낮춘 p95 방어 목적 예측가격 |
| Cold 동적 보정 게이트 실험 | PP-CGATE1 | Warm식 기준가+보정값 구조를 Cold에 적용해 본 실험. fixed test 전이가 약해 최종 제외 |

## 2. 모델 성격

Cold v0.5 모델은 단일 모델 하나가 가격을 끝까지 직접 산출하는 구조가 아니다. 서로 성격이 다른 두 예측 계열을 결합하고, 큰 오차 가능성이 높을 때만 보수적 방어 처리를 적용한다.

- LightGBM 분위 모델은 비선형 패턴과 예측 불확실성을 잡는다.
- Huber 그룹통계 모델은 매체, 지지체, 크기 조건의 안정적인 가격 기준을 보완한다.
- 대표 예측가격은 중앙 분위 예측가격을 기본으로 두고 Huber 그룹통계 예측가격을 30% 반영한다.
- 방어 예측가격은 예측 구간 폭이 넓고 대표 예측가격이 보수 분위보다 높게 나온 row에서만 낮춰 적용한다.
- 가격 범위는 하위 분위와 상위 분위 예측을 `exp()`로 되돌려 제공한다.

Warm 모델과 가장 큰 차이는 `artist_key` 사용 방식이다. Warm은 같은 작가의 과거 거래 이력이 있으므로 작가별 기준선을 직접 활용할 수 있다. Cold는 신규 작가 상황이므로 artist_key를 직접 기준가 피처로 쓰지 않고, 작품 조건과 비작가 그룹 통계로 가격 수준을 추정한다.

## 2.1 단계별 사용 모델과 적용 위치

| 순서 | 단계 | 사용 모델 또는 방법 | 적용 방식 | 역할 |
|---:|---|---|---|---|
| 1 | Cold 피처 생성 | 크기 파서, 매체 파서, 학습 기준 버킷 생성 규칙 | 원천 입력에서 모델 피처 생성 | 운영 입력을 모델이 사용할 수 있는 형태로 변환 |
| 2 | 분위 예측 | LightGBM Quantile, 5개 seed 평균 | `q10`, `q40`, `q50`, `q90` 로그가격 예측 | 중심 가격과 가격 범위, 불확실성 폭 생성 |
| 3 | 비작가 그룹 통계 생성 | 매체/지지체/크기 조건 fallback ladder | 조건별 과거 가격 통계를 row에 붙임 | artist_key 없이 가격 기준 통계 제공 |
| 4 | 안정 예측 | Huber 회귀 6구성 평균 | 작품 피처와 그룹 통계로 로그가격 예측 | 선형적이고 안정적인 가격 보정 축 생성 |
| 5 | 대표 예측가격 생성 | 고정 가중 결합 | 중앙 분위 예측 70% + Huber 그룹통계 예측 30% | 일반 표시용 중심 예측가격 |
| 6 | p95 방어 조건 판단 | 예측 구간 폭과 보수 분위 gap 조건 | 불확실성이 큰 row를 판별 | 큰 오차 가능성이 높은 row만 방어 적용 |
| 7 | 방어 예측가격 생성 | 보수적 50:50 이동 | 대표 예측가격 50% + 보수 분위 예측 50% | 과대 예측 위험을 낮춘 방어 예측가격 |
| 8 | 가격 변환 | 지수함수 `exp()` | 로그가격을 KRW 가격으로 변환 | 사용자에게 표시할 가격 생성 |

CatBoost 계열과 Warm식 보정층도 실험에서 검토했다. 그러나 Cold에서는 신규 작가 리스크 때문에 validation에서 좋아 보인 보정이 fixed test로 안정적으로 전이되지 않았다. 따라서 최종 문서에서는 CatBoost나 Warm식 잔차 보정을 직접 계산 경로에 포함하지 않는다.

## 3. 사용 데이터와 재현 기준

| 구분 | 내용 |
|---|---|
| 학습 및 검증 기준 | 기존 Cold train/validation/test split |
| 최종 비교 기준 | 기존 Cold fixed test 3,099건 |
| 제출용 데이터 사용 여부 | 사용하지 않음 |
| 0604 데이터 사용 여부 | Cold 실험 기준에서는 사용하지 않음 |
| v0.5 채택 목적 | 기존 운영 v0.2 대비 p95 방어 개선 |
| 최종 제외한 보정 실험 | Cold 동적 보정 게이트 실험은 validation 개선 후 fixed test 악화로 제외 |

고정 Cold 기준 성능은 다음과 같다.

| 예측가격 | split | n | MdAPE | MAPE | p95 APE | within 30% | 50% 초과 오차율 |
|---|---|---:|---:|---:|---:|---:|---:|
| 검색 피처 포함 연구 기준 예측가격 | test | 3,099 | 0.409820 | 0.849260 | 2.346465 | 0.374314 | 0.415295 |
| 기존 운영 v0.2 방어 예측가격 | test | 3,099 | 0.485162 | 1.177120 | 4.122299 | 0.287512 | 0.481446 |
| v0.5 방어 예측가격 | test | 3,099 | 0.482170 | 1.179011 | 3.649028 | 0.295257 | 0.487254 |

## 3.1 검색 피처 포함 연구 기준 예측가격 상세

검색 피처 포함 연구 기준 예측가격은 현재 문서의 v0.5 운영 옵션과 다른 계산 경로다. 이 기준은 Cold fixed test에서 전체 지표가 가장 좋았기 때문에 비교 기준 1순위로 둔다.

다만 이 기준은 원천 작품 정보만으로 바로 실행되는 v0.5 운영 옵션이 아니다. 상류에서 미리 만든 검색 피처와 작가 단위 검색 보정 lookup을 사용한다.

전체 흐름은 아래와 같다.

```text
[작품 입력 정보 + 작가명]
        |
        v
[작가명 기반 검색 피처 조회]
  - 실시간 검색이 아니라 저장된 검색 피처 캐시 사용
  - 검색 결과 제목, 요약, URL, 도메인을 작가 단위로 집계
        |
        v
[검색 피처 포함 LightGBM 분위 예측]
  - 작품 피처
  - 작가 메타 피처
  - 검색 카운트/문맥/품질/동명이인 위험 피처
  - 검색 x 작품/작가 상호작용 피처
        |
        v
[예측 구간 폭 계산]
  - 예측구간폭 = 상위분위_로그가격 - 하위분위_로그가격
        |
        v
[예측 구간 폭 기반 대표가 안정화]
  - 예측구간폭 구간별 out-of-fold 잔차 중앙값 보정
  - 보정 상한 cap = ±0.25 로그
        |
        v
[1차 연구 대표 로그가격]
        |
        v
[qwidth/gap guard]
  - 예측구간폭이 넓고 대표가가 q40보다 높게 튄 row를 q40 쪽으로 50% 낮춤
        |
        v
[작가 단위 검색 delta 추가]
  - gallery/museum 검색 source group 기반 보정 lookup
  - lookup에 없는 작가는 delta 0
        |
        v
[검색 피처 포함 연구 기준 로그가격]
        |
        v
[검색 피처 포함 연구 기준 가격 = exp(연구 기준 로그가격)]
```

### 3.1.1 검색 피처가 만들어지는 방식

검색 피처는 작품별 이미지나 작품 설명을 직접 검색한 값이 아니라, 작가명 기준 검색 결과를 작가 단위로 집계한 값이다.

초기 Cold 검색 기반 후보의 원천 파일은 아래와 같다.

| 구분 | 파일 또는 산출물 | 역할 |
|---|---|---|
| 초기 검색 피처 캐시 | `data/track6/external_search/track6_artist_search_pilot_features.csv` | PP-Y2/PP-Y18 계열의 검색 피처 입력 |
| 초기 검색 원문 | `data/track6/external_search/track6_artist_search_pilot_raw.jsonl` | 작가명 검색 결과 원문 |
| 운영형 검색 스냅샷 | `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv` | H20~H28 계열 검색 보정 실험 입력 |
| 운영형 검색 표준화 결과 | `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv` | provider/source group/context flag 계산용 |
| v0.3 작가 단위 검색 보정 lookup | `models/track6/cold_prediction_v0.3/config/search_delta_lookup_v0_3.json` | guard 이후 더하는 작가별 검색 보정값 |

검색 결과는 아래처럼 작가 단위 피처로 요약된다.

```text
작가명 검색 결과
  -> 검색 결과 row 수
  -> 고유 도메인 수
  -> 미술 문맥 결과 수
  -> 전시 문맥 결과 수
  -> 갤러리/미술관 문맥 결과 수
  -> 시장/거래 문맥 결과 수
  -> 동명이인 위험 문맥 결과 수
  -> 작가명 일치 비율
  -> 검색 품질 점수
  -> 검색 품질 등급
  -> 동명이인 위험 등급
```

검색 품질 점수는 최신 운영형 검색 스냅샷 기준으로 아래 요소를 조합해 해석한다.

```text
검색품질점수 =
  0.30 * 미술문맥비율
+ 0.20 * 신뢰도메인비율
+ 0.15 * 전시문맥비율
+ 0.15 * 시장/거래문맥비율
+ 0.10 * 최근결과비율
+ 0.10 * provider커버리지점수
+ 0.10 * 작가명일치비율
- 0.30 * 동명이인위험비율
```

등급 기준은 아래와 같다.

| 등급 | 기준 | 의미 |
|---|---|---|
| high | 검색품질점수 0.70 이상, 동명이인 위험 0.20 미만 | 비교적 안정적인 검색 신호 |
| medium | 검색품질점수 0.45 이상, 동명이인 위험 0.40 미만 | 참고 가능하지만 검수 필요 |
| low | 위 기준 미달 | 가격 보정에는 주의가 필요한 검색 신호 |
| missing | 검색 결과 없음 | 검색 신호 없음 |

### 3.1.2 연구 기준 예측가격에 들어간 검색 피처 묶음

연구 기준의 뿌리인 `검색 전체 피처 + 외부 상호작용 LightGBM 분위 예측` 계열은 아래 피처 묶음을 사용했다.

| 피처 묶음 | 포함 피처 예시 | 의미 |
|---|---|---|
| 작품 물리 피처 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate` | 작품 크기와 형태 |
| 작품 재료/지지체 피처 | `medium_category`, `support_category`, `size_bucket`, `support_size_bucket` | 매체, 지지체, 크기 구간 |
| 작가 기본 메타 | `artist_meta_birth_year`, `artist_meta_career_stage`, `artist_meta_nationality`, `artist_meta_nationality_ko` | 생년, 활동 세대, 국적 |
| 작가 활동/인기도 메타 | `artist_meta_total_works`, `artist_meta_for_sale_works`, `artist_meta_followers`, `artist_meta_for_sale_ratio` | 작품 수, 판매 중 작품 수, 팔로워, 판매 비율 |
| 작가 메타 로그/결측 flag | `artist_meta_total_works_log`, `artist_meta_followers_log`, `artist_meta_birth_year_missing` 등 | 값의 스케일 완화와 결측 여부 |
| 검색 카운트 | `search_result_count`, `search_source_count` | 수집된 검색 결과 수와 고유 출처 수 |
| 검색 문맥 카운트 | `search_art_context_count`, `search_exhibition_context_count`, `search_gallery_context_count`, `search_market_context_count`, `search_homonym_context_count` | 미술/전시/갤러리/시장/동명이인 문맥 수 |
| 검색 비율 | `search_art_match_ratio`, `search_exhibition_ratio`, `search_source_ratio` | 검색 결과 중 유효 문맥 비율 |
| 검색 품질 | `search_quality_score`, `search_quality_grade`, `search_collected_flag`, `search_success_flag` | 검색 결과 신뢰도와 수집 성공 여부 |
| 검색 로그 변환 | `search_result_count_log`, `search_art_context_count_log`, `search_exhibition_context_count_log`, `search_source_count_log` | 검색 카운트의 로그 변환 |
| 동명이인 위험 | `search_homonym_risk_grade` | 작가명 검색 결과가 다른 인물과 섞일 위험 |
| 검색 상호작용 피처 | `search_quality_x_log_area`, `search_art_match_x_followers_log`, `search_exhibition_x_career_stage`, `search_size_quality_bucket` | 검색 신호와 작품 크기/작가 인기도/세대의 조합 효과 |

즉, 이 연구 기준은 단순히 “검색 결과가 많으면 가격이 높다”는 모델이 아니다. 작품 조건, 작가 메타, 검색 문맥 품질, 동명이인 위험, 검색 신호와 작품/작가 피처의 상호작용까지 함께 본다.

### 3.1.3 PP-Y18 대표 로그가격 계산

문서용 변수명으로 정리하면 PP-Y18 대표 로그가격은 아래처럼 이해할 수 있다.

```text
검색기반_하위분위_로그가격,
검색기반_중앙분위_로그가격,
검색기반_상위분위_로그가격
  = LightGBM_분위모델(
      작품피처
      + 작가메타피처
      + 검색피처
      + 검색상호작용피처
    )

검색기반_예측구간폭
  = 검색기반_상위분위_로그가격 - 검색기반_하위분위_로그가격
```

그 다음 예측 구간 폭을 구간화하고, validation out-of-fold 잔차 중앙값으로 작은 보정을 더한다.

```text
예측구간폭_구간 = bucket(검색기반_예측구간폭)

구간별_잔차중앙값
  = median(actual_log - 검색기반_중앙분위_로그가격)
    within same 예측구간폭_구간

구간별_보정값
  = clip(구간별_잔차중앙값, -0.25, +0.25)

PP-Y18_대표로그가격
  = 검색기반_중앙분위_로그가격 + 구간별_보정값
```

여기서 `out-of-fold`는 해당 row를 학습하지 않은 fold에서 나온 검증 예측값을 사용한다는 뜻이다. 이 장치는 validation 잔차 보정이 같은 row를 다시 외우는 과적합을 줄이기 위한 것이다.

PP-Y18 대표 로그가격의 fixed test 성능은 다음과 같다.

| 예측가격 | MdAPE | MAPE | p95 APE |
|---|---:|---:|---:|
| PP-Y18 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 |

### 3.1.4 qwidth/gap guard 계산

PP-Y18 대표 로그가격은 다시 qwidth/gap guard를 통과한다. guard는 대표 로그가격이 보수 분위보다 높고 예측 구간 폭도 넓은 경우, 과대 예측 위험을 줄이기 위해 보수 분위 쪽으로 50% 낮추는 방어층이다.

```text
guard_적용조건 =
  (검색기반_예측구간폭 >= 1.4612207078910142)
  AND (PP-Y18_대표로그가격 - 보수분위_로그가격 >= 0.07715547281151025)
  AND (보수분위_로그가격 < PP-Y18_대표로그가격)
```

조건이 꺼져 있으면 guard 이후 로그가격은 PP-Y18 대표 로그가격과 같다.

```text
guard_로그가격 = PP-Y18_대표로그가격
```

조건이 켜져 있으면 대표 로그가격과 보수 분위 로그가격을 50:50으로 섞는다.

```text
guard_로그가격
  = 0.50 * PP-Y18_대표로그가격
  + 0.50 * 보수분위_로그가격
```

guard 단독 fixed test 성능은 다음과 같다.

| 예측가격 | MdAPE | MAPE | p95 APE |
|---|---:|---:|---:|
| PP-Y18 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 |
| guard 로그가격 | 0.417765 | 0.963963 | 2.537708 |

### 3.1.5 작가 단위 검색 delta 계산

마지막으로 작가 단위 검색 보정 delta를 더한다. 이 delta는 실시간 검색값이 아니라 `h23_gallery_museum_median_cap0.2` 계열에서 만든 작가별 frozen lookup이다.

이 보정은 검색 결과 중 갤러리/미술관 source group 비중이 가격 잔차와 관련이 있는지 본 것이다. 값은 작가별로 저장되어 있고, 범위는 로그가격 기준 대략 `-0.20`에서 `+0.20` 사이로 제한되어 있다.

```text
작가검색_delta =
  search_delta_lookup[artist_key]
  if artist_key exists in lookup

작가검색_delta = 0
  if artist_key does not exist in lookup
```

최종 검색 피처 포함 연구 기준 로그가격은 아래와 같다.

```text
검색피처포함_연구기준_로그가격
  = guard_로그가격 + 작가검색_delta

검색피처포함_연구기준_가격_KRW
  = exp(검색피처포함_연구기준_로그가격)
```

검색 delta lookup의 주요 특성은 아래와 같다.

| 항목 | 값 |
|---|---:|
| lookup 작가 수 | 372 |
| test 검색 커버리지 | 1.000 |
| delta 최솟값 | -0.2000 |
| delta 최댓값 | +0.2000 |
| delta 평균 | -0.0301 |

이 최종 연구 기준 예측가격의 fixed test 성능은 아래와 같다.

| 예측가격 | MdAPE | MAPE | p95 APE |
|---|---:|---:|---:|
| PP-Y18 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 |
| guard 로그가격 | 0.417765 | 0.963963 | 2.537708 |
| 검색 delta만 추가한 로그가격 | 0.412921 | 0.875749 | 2.937449 |
| guard + 검색 delta 연구 기준 로그가격 | 0.409820 | 0.849260 | 2.346465 |

정리하면, 검색 피처 포함 연구 기준 예측가격은 아래 식으로 요약된다.

```text
검색피처포함_연구기준_로그가격
  = Guard(
      PP-Y18_대표로그가격,
      보수분위_로그가격,
      검색기반_예측구간폭
    )
  + 작가검색_delta

PP-Y18_대표로그가격
  = LightGBM_검색포함_중앙분위_로그가격
  + clip(
      median_out_of_fold_residual_by_qwidth_bin,
      -0.25,
      +0.25
    )
```

따라서 “검색 피처 포함 연구 기준 예측가격”은 검색 피처를 직접 넣은 분위 모델, 예측 불확실성 기반 guard, 작가 단위 검색 문맥 보정이 순차적으로 결합된 기준 예측가격이다.

### 3.1.6 최고 성능 연구 기준 재현 확인

검색 피처 포함 연구 기준 예측가격은 `v0.5` 운영 옵션이 아니라 `v0.3 guard+search` 경로이므로, 별도 재현 확인을 수행했다.

재현 확인은 아래 입력 파일을 다시 읽어 같은 test 3,099건 기준으로 수행했다.

| 입력 | 파일 | 역할 |
|---|---|---|
| PP-Y18 대표 예측 | `experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv` | 검색 피처 포함 LightGBM 분위 모델의 대표 로그가격 |
| PP-Y2 예측구간폭 보강값 | `experiments/track6/PP-Y2_cold_lgbq_search_external_combo/outputs/predictions.csv` | PP-Y18 파일에 비어 있는 `quantile_width_log`를 기존 실험과 동일하게 보강 |
| q40 분위 후보 | `experiments/track6/PP-QR1_cold_quantile_regression_alpha_grid/outputs/predictions.csv` | guard 임계값 계산과 보수 분위 이동에 사용 |
| 검색 delta 후보 | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/candidate_predictions.csv` | `h23_gallery_museum_median_cap0.2` 기반 작가 단위 검색 보정값 |
| 기록 지표 | `experiments/track6/PP-COLD-DEFENSE1_cold_guard_search_layer_combination/outputs/test_metrics.csv` | 기존 실험에서 기록된 최고 성능 지표 |

재현 절차는 아래와 같다.

```text
[상류 예측 파일 재로딩]
  PP-Y18 대표 로그가격
  + PP-Y2 예측구간폭 보강
  + QR1 CatBoost q40 / LightGBM q40
  + H28 검색 delta 후보
        |
        v
[validation 기준 guard 임계값 재계산]
  qwidth_q67 = 1.4612207078910142
  gap_q50    = 0.07715547281151025
        |
        v
[v0.3 후처리기 적용]
  shipped_postprocessor = apply_cold_postprocess_v0_3.py
        |
        v
[독립 계산식과 비교]
  guard_로그가격 = 독립 guard 계산
  검색delta = frozen lookup 또는 H28 원천 delta
  최종로그가격 = guard_로그가격 + 검색delta
        |
        v
[기록된 PP-COLD-DEFENSE1 지표와 비교]
```

검증 결과는 모두 통과했다.

| 검증 항목 | 결과 |
|---|---:|
| test row 수 | 3,099 |
| validation row 수 | 2,753 |
| 검색 lookup 작가 수 | 372 |
| test 검색 커버리지 | 1.000000 |
| validation에서 재계산한 guard 임계값 차이 | 0.000e+00 |
| v0.3 후처리기와 독립 계산식의 로그가격 최대 차이 | 0.000e+00 |
| frozen lookup delta와 H28 원천 delta의 test 최대 차이 | 2.665e-15 |
| 재계산 지표와 기록 지표의 최대 차이 | 1.110e-16 |
| 전체 재현 통과 여부 | true |

재현된 지표는 아래와 같다.

| 후보 | 재현 MdAPE | 기록 MdAPE | 재현 MAPE | 기록 MAPE | 재현 p95 APE | 기록 p95 APE |
|---|---:|---:|---:|---:|---:|---:|
| PP-Y18 대표 로그가격 | 0.424663 | 0.424663 | 0.991042 | 0.991042 | 3.305298 | 3.305298 |
| guard 로그가격 | 0.417765 | 0.417765 | 0.963963 | 0.963963 | 2.537708 | 2.537708 |
| guard + 검색 delta 연구 기준 로그가격 | 0.409820 | 0.409820 | 0.849260 | 0.849260 | 2.346465 | 2.346465 |

따라서 현재 문서의 `검색 피처 포함 연구 기준 예측가격` 수치는 별도 검증 스크립트로 재현 가능하다. 실행 명령은 아래와 같다.

```bash
python3 scripts/track6/verify_cold_best_research_reproducibility.py
```

검증 결과 파일은 아래에 저장된다.

```text
models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_check.json
models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_metrics.csv
```

## 4. 직접 입력 피처

Cold v0.5 모델이 직접 사용하는 입력은 원천 작품 정보에서 계산 가능한 작품 조건 피처다. 작가별 과거 거래를 전제로 하는 Warm 유사작품 피처나 artist_key 가격 기준선은 사용하지 않는다.

| 입력 피처 | 생성 방식 | 역할 |
|---|---|---|
| `width_cm` | 작품 크기 문자열에서 폭을 cm 단위로 파싱 | 작품 물리 크기 |
| `height_cm` | 작품 크기 문자열에서 높이를 cm 단위로 파싱 | 작품 물리 크기 |
| `depth_cm` | 깊이가 있으면 cm 단위로 파싱, 없으면 0 | 3D 후보 또는 입체 작품 조건 |
| `area_cm2` | 일반 2D는 `width_cm * height_cm`, 3D도 대표 표면 면적 기준 | 작품 크기 수준 |
| `log_area` | `area_cm2 > 0`이면 `log(area_cm2)` | 크기 효과를 로그 스케일로 완화 |
| `aspect_ratio` | 2D는 긴 변 / 짧은 변. 3D 일부 패턴은 높이 / 폭 | 작품 형태 비율 |
| `has_depth` | `depth_cm > 0` 여부 | 깊이 정보 존재 여부 |
| `is_3d_candidate` | 크기 파서가 3D로 판단하거나 category가 sculpture/installation 등인 경우 | 3D 가능성 |
| `medium_category` | medium 문자열을 oil, acrylic, mixed_media 등 모델 범주로 변환 | 매체 효과 |
| `support_category` | medium 문자열을 canvas, paper, panel 등 지지체 범주로 변환 | 지지체 효과 |
| `medium_support_bucket` | `medium_category + "__" + support_category` | 매체와 지지체 조합 |
| `size_bucket` | 학습 데이터의 `log_area` 분위 기준으로 q1~q5 생성 | 크기 구간 |
| `support_size_bucket` | `support_category + "__" + size_bucket` | 지지체와 크기 조합 |

### 4.1 크기 피처 생성식

크기 문자열 예시는 `53 x 45.5`, `31 x 13 x 22`, `20F`, `20호`, `diameter 30` 같은 형태다. 크기 파서는 입력 패턴에 따라 폭, 높이, 깊이, 면적을 만든다.

```text
2D 크기 입력:
  width_cm  = 첫 번째 숫자
  height_cm = 두 번째 숫자
  area_cm2  = width_cm * height_cm
  aspect_ratio = max(width_cm, height_cm) / min(width_cm, height_cm)

3D 크기 입력:
  height_cm, width_cm, depth_cm = 세 숫자에서 파서 규칙으로 배치
  area_cm2 = height_cm * width_cm
  has_depth = True

면적 로그:
  log_area = log(area_cm2)  if area_cm2 > 0
```

호수 입력은 F 타입 캔버스 규격표를 기준으로 cm 크기로 변환한다. P/M/S 타입이 입력되어도 현재 파서는 F 타입 규격으로 근사하고, 원본 타입 정보는 보존한다.

### 4.2 버킷 피처 생성식

`size_bucket`은 운영 입력 자체의 분포로 매번 다시 만들지 않는다. 학습 데이터에서 계산한 `log_area` 분위 경계를 고정해 사용한다.

```text
size_bucket =
  q1 if log_area is in the smallest 20% range
  q2 if log_area is in the next 20% range
  q3 if log_area is in the middle 20% range
  q4 if log_area is in the next 20% range
  q5 if log_area is in the largest 20% range
  "__MISSING__" if log_area is missing

support_size_bucket = support_category + "__" + size_bucket
medium_support_bucket = medium_category + "__" + support_category
```

이 버킷들은 실제 가격을 보지 않고 입력 작품 조건만으로 계산된다. 따라서 운영 시 정답 가격 없이도 재현 가능하다.

## 5. 비작가 그룹 통계 생성

Cold는 작가별 과거 가격을 직접 사용할 수 없으므로, 매체/지지체/크기 조합으로 과거 가격 통계를 만든다. 이 통계는 Huber 그룹통계 예측가격의 핵심 입력이다.

그룹 통계 fallback 순서는 다음과 같다.

| 우선순위 | 그룹 조건 | 최소 표본 기준 | 테이블 크기 | 의미 |
|---:|---|---:|---:|---|
| 1 | `medium_support_bucket + size_bucket` | 30 | 84 | 매체/지지체/크기가 모두 같은 가장 구체적 그룹 |
| 2 | `medium_category + support_category + size_bucket` | 30 | 84 | 매체/지지체/크기 조건을 개별 컬럼으로 본 그룹 |
| 3 | `medium_category + size_bucket` | 50 | 35 | 지지체 조건을 빼고 매체와 크기만 본 넓은 그룹 |
| 4 | 전체 global fallback | - | 1 | 위 조건에 충분한 표본이 없을 때 쓰는 전체 기준 |

각 그룹에서 붙는 통계는 다음과 같다.

| 그룹 통계 피처 | 의미 |
|---|---|
| `grp_log_price_median` | 그룹 로그가격 중앙값 |
| `grp_log_price_q25` | 그룹 로그가격 25퍼센타일 |
| `grp_log_price_q75` | 그룹 로그가격 75퍼센타일 |
| `grp_log_price_iqr` | 그룹 로그가격 사분위 범위 |
| `grp_unit_area_median` | 그룹 단위면적당 로그가격 중앙값 |
| `grp_unit_area_iqr` | 그룹 단위면적당 로그가격 사분위 범위 |
| `grp_n_log` | 그룹 표본 수의 로그값 |
| `grp_match_level` | 어떤 fallback 단계에서 매칭됐는지 나타내는 값 |

그룹 단위면적 통계는 작품 크기와 결합해 가격 기준을 보완한다.

```text
그룹_가격_프록시 = 그룹_단위면적_로그가격_중앙값 + max(log_area, 0)
```

이 값은 “이 매체/지지체/크기 조건의 작품이라면 어느 정도 가격대가 자연스러운가”를 artist_key 없이 추정하는 기준값이다.

## 6. LightGBM 분위 예측

LightGBM 분위 예측은 하나의 점 가격만 내지 않고 여러 가격 구간을 예측한다. v0.5는 각 분위마다 5개 seed 모델을 학습하고 평균을 낸다.

```text
하위분위_로그가격   = mean(LightGBM_q10_seed0 ... LightGBM_q10_seed4)
보수분위_로그가격   = mean(LightGBM_q40_seed0 ... LightGBM_q40_seed4)
중앙분위_로그가격   = mean(LightGBM_q50_seed0 ... LightGBM_q50_seed4)
상위분위_로그가격   = mean(LightGBM_q90_seed0 ... LightGBM_q90_seed4)

예측구간폭 = 상위분위_로그가격 - 하위분위_로그가격
```

여기서 `q10`, `q40`, `q50`, `q90`은 가격 분포의 분위 위치를 뜻한다. `q50`은 중심 가격 역할을 하고, `q10`과 `q90`은 가격 범위 역할을 한다. `q40`은 대표 예측가격이 높게 튀었을 때 낮춰 잡기 위한 보수적 기준으로 사용한다.

## 7. Huber 그룹통계 예측

Huber 그룹통계 예측은 LightGBM과 다른 성격의 안정 예측축이다. 트리 기반 모델이 잡는 비선형 패턴과 달리, Huber는 선형 구조를 유지하면서 큰 오차 row의 영향을 줄인다.

입력 구성은 아래와 같다.

```text
작품 크기 피처:
  width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio,
  has_depth, is_3d_candidate

비작가 그룹 통계:
  grp_price_proxy,
  grp_log_price_median, grp_log_price_q25, grp_log_price_q75,
  grp_log_price_iqr,
  grp_unit_area_median, grp_unit_area_iqr,
  grp_n_log, grp_match_level

범주형 피처:
  medium_category, support_category, size_bucket
```

v0.5에서는 Huber 구성을 6개 만들고 평균을 사용한다.

```text
Huber_그룹통계_로그가격
  = mean(Huber_구성0, Huber_구성1, Huber_구성2,
         Huber_구성3, Huber_구성4, Huber_구성5)
```

6개 구성은 거의 같은 기본 피처를 쓰되, 일부 구성에서는 가격 사분위 통계나 단위면적 사분위 통계를 줄여 더 단순한 선형 기준도 함께 평균에 넣는다. 목적은 한 가지 구성에 과도하게 의존하지 않고 안정적인 보조 예측축을 만드는 것이다.

## 8. 대표 Cold 예측가격 계산

대표 Cold 로그가격은 LightGBM 중앙 분위 예측가격을 기준으로 Huber 그룹통계 예측가격을 30% 반영한다.

```text
대표_Cold_로그가격
  = 중앙분위_로그가격 + 0.30 * (Huber_그룹통계_로그가격 - 중앙분위_로그가격)

같은 식을 가중 평균으로 쓰면:

대표_Cold_로그가격
  = 0.70 * 중앙분위_로그가격
  + 0.30 * Huber_그룹통계_로그가격
```

이 식의 의미는 다음과 같다.

- LightGBM 중앙 분위 예측이 기본 중심값이다.
- Huber 그룹통계 예측은 기준 가격을 안정화하는 보조축이다.
- Huber 쪽으로 30%만 이동하므로, 트리 모델의 중심 예측을 완전히 대체하지 않는다.

## 9. p95 방어 예측가격 계산

대표 예측가격이 항상 최종 출력으로 적합한 것은 아니다. 예측 구간 폭이 매우 넓고 대표 예측가격이 보수 분위보다 충분히 높으면, 큰 과대 예측 위험이 있다고 판단한다.

방어 조건은 아래 세 조건을 모두 만족할 때 켜진다.

```text
예측구간폭 >= 1.746419630237291
대표_Cold_로그가격 - 보수분위_로그가격 >= 0.12551019342109804
보수분위_로그가격 < 대표_Cold_로그가격
```

조건이 꺼져 있으면 방어 예측가격은 대표 예측가격과 같다.

```text
Cold_방어_로그가격 = 대표_Cold_로그가격
```

조건이 켜져 있으면 대표 예측가격을 보수 분위 쪽으로 50% 낮춘다.

```text
Cold_방어_로그가격
  = 0.50 * 대표_Cold_로그가격
  + 0.50 * 보수분위_로그가격
```

가격 단위 출력은 아래처럼 계산한다.

```text
Cold_방어_가격_KRW = max(exp(Cold_방어_로그가격), 1,000)
Cold_가격범위_하한_KRW = max(exp(하위분위_로그가격), 1,000)
Cold_가격범위_상한_KRW = max(exp(상위분위_로그가격), 1,000)
```

`1,000`원 하한은 로그가격을 가격으로 되돌릴 때 비정상적으로 낮은 가격이 표시되지 않도록 하는 최소 클립이다.

## 10. Warm식 보정 실험을 최종 경로에서 제외한 이유

Cold에도 Warm처럼 `기준가 + 보정값` 구조를 적용해 볼 수 있는지 확인했다. 최근 추가한 Cold 동적 보정 게이트 실험은 검색 피처 포함 연구 기준 예측가격을 기준가로 두고, v0.5/v0.2/guard/qwidth 후보 방향으로 제한된 보정을 적용했다.

실험 결과는 다음과 같다.

| 항목 | validation 변화 | fixed test 변화 |
|---|---:|---:|
| MdAPE | -0.000069 | +0.016689 |
| MAPE | -0.007962 | +0.038384 |
| p95 APE | -0.325901 | +0.094688 |

validation에서는 p95 APE가 크게 좋아졌지만, fixed test에서는 MAPE와 p95 APE가 모두 악화됐다. 따라서 이 보정은 현재 운영 경로에 넣지 않는다.

해석은 다음과 같다.

- Warm은 같은 작가의 과거 거래가 있어 보정 방향을 더 안정적으로 잡을 수 있다.
- Cold는 신규 작가 상황이라 보정 방향이 validation의 특정 작가/구간에 맞춰질 위험이 크다.
- Cold에서는 강한 단일 보정보다 대표 예측가격, 방어 예측가격, 가격 범위를 분리해 제공하는 정책이 더 안정적이다.

## 11. CatBoost와 다른 후보를 최종 경로에서 제외한 이유

Cold 실험에서는 CatBoost, LightGBM, Huber, 혼합 blend, 게이트 보정 계열을 모두 검토했다. 최종 v0.5 경로에는 LightGBM 분위 예측과 Huber 그룹통계 예측만 직접 들어간다.

| 후보 방향 | 확인한 역할 | 최종 판단 |
|---|---|---|
| CatBoost 단독 또는 보정 | 비선형 패턴 포착 후보 | 일부 구간 장점은 있었지만 fixed test와 반복 안정성 기준에서 최종 경로로 채택하지 않음 |
| LightGBM 단독 중앙 예측 | Cold 중심 예측 후보 | 비선형 패턴을 잘 잡지만 p95 방어가 부족해 단독 운영 후보로 두지 않음 |
| LightGBM 분위 예측 | 중심값과 가격 범위 동시 생성 | 최종 v0.5의 핵심 축으로 채택 |
| Huber 그룹통계 예측 | 안정적인 비작가 기준 가격 보완 | 최종 v0.5의 보조 축으로 채택 |
| Warm식 동적 보정 | 기준가 위에 제한 보정 적용 | validation 개선이 fixed test로 전이되지 않아 제외 |

현재 Cold에서 가장 설득력 있는 구조는 `LightGBM 분위 예측 + Huber 그룹통계 안정화 + p95 방어 조건`이다. 이는 성능을 크게 튀게 만드는 구조보다, 신규 작가 상황에서 과대 확신을 줄이는 구조에 가깝다.

## 12. 운영 해석

Cold 예측값은 Warm 예측값과 같은 확신도로 설명하면 안 된다. 운영 화면이나 보고서에서는 아래처럼 구분하는 것이 적절하다.

| 출력 항목 | 권장 표현 | 설명 |
|---|---|---|
| 대표 예측가격 | Cold 참고 예측가격 | 일반 상황에서의 중심 예측값 |
| 방어 예측가격 | Cold 보수 예측가격 | 큰 오차 위험이 높은 row에서 p95 방어를 위해 낮춘 예측값 |
| 가격 범위 | 예측 가능 가격 범위 | 하위 분위와 상위 분위 기반 범위 |
| 신뢰도 | Warm보다 낮게 표시 | 같은 작가 거래 이력이 없으므로 예측 불확실성이 큼 |

상사 보고 시 핵심 문장은 다음처럼 잡는 것이 좋다.

```text
Cold 모델은 신규 작가를 대상으로 하므로 Warm처럼 작가별 기준가를 직접 세우기 어렵습니다.
그래서 작품 크기, 매체, 지지체, 크기 구간을 기반으로 LightGBM 분위 예측을 만들고,
여기에 비작가 그룹 통계를 사용한 Huber 안정 예측을 30% 섞어 대표 가격을 만듭니다.
예측 구간이 넓고 과대 예측 위험이 큰 경우에는 대표 가격을 q40 보수 분위 쪽으로 50% 낮춰
p95 큰 오차를 방어합니다.
```

## 13. 재현 파일 위치

| 구분 | 위치 |
|---|---|
| 최고 성능 연구 기준 검증 스크립트 | `scripts/track6/verify_cold_best_research_reproducibility.py` |
| 최고 성능 연구 기준 검증 결과 | `models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_check.json` |
| 최고 성능 연구 기준 재현 지표 | `models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_metrics.csv` |
| Cold v0.3 후처리기 | `models/track6/cold_prediction_v0.3/predict/apply_cold_postprocess_v0_3.py` |
| Cold v0.3 guard/search 파라미터 | `models/track6/cold_prediction_v0.3/config/cold_postprocess_params_v0_3.json` |
| Cold v0.3 검색 delta lookup | `models/track6/cold_prediction_v0.3/config/search_delta_lookup_v0_3.json` |
| Cold v0.3 상류 재현 파일 목록 | `models/track6/cold_prediction_v0.3/reproduction/upstream_sources.json` |
| Cold v0.5 예측기 | `models/track6/cold_prediction_v0.5_operational/predict/predict_cold_operational_v0_5.py` |
| Cold v0.5 결합 파라미터 | `models/track6/cold_prediction_v0.5_operational/config/blend_params_v0_5.json` |
| Cold v0.5 정책 파일 | `models/track6/cold_prediction_v0.5_operational/config/cold_model_policy_v0_5.json` |
| Cold v0.5 release note | `models/track6/cold_prediction_v0.5_operational/reports/cold_artifact_release_v0_5.md` |
| Cold base lock 리포트 | `experiments/track6/PP-CBASE1_cold_base_lock/reports/cold_base_lock.md` |
| Cold base 고정 rows | `experiments/track6/PP-CBASE1_cold_base_lock/outputs/fixed_cold_base_rows.csv` |
| Cold v0.5 근거 실험 | `experiments/track6/PP-CBOOST3_cold_hetero_blend_gate_retry/reports/result_report.md` |
| Cold Warm식 보정 제외 근거 | `experiments/track6/PP-CGATE1_cold_dual_output_dynamic_gate/reports/result_report.md` |

## 14. 최종 판단

현재 Cold 모델은 Warm 모델처럼 “운영 예측가격 1개를 강하게 확정”하는 방식보다, `대표 예측가격 + 방어 예측가격 + 넓은 가격 범위`를 함께 제공하는 방식이 맞다.

최종 운영 설명은 아래처럼 정리한다.

- 검색 피처 포함 연구 기준 예측가격은 Cold fixed test 전체 지표에서 가장 강하다.
- v0.5는 검색 피처 없이 원천 입력만으로 실행 가능한 p95 방어 옵션이다.
- v0.5 방어 예측가격은 기존 운영 v0.2 대비 p95 APE를 약 11.5% 줄인다.
- v0.5가 검색 피처 포함 연구 기준 예측가격을 대체하는 것은 아니다.
- Warm식 보정층은 Cold에서 fixed test 전이가 약해 현재 최종 경로에서 제외한다.
- Cold 운영 출력은 단일 확정 가격보다 참고 예측가격, 보수 예측가격, 예측 범위를 함께 보여주는 구성이 적절하다.
