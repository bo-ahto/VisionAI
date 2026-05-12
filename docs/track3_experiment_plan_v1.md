# Track 3 실험 계획서 v1

- 목적: 작품 가격 예측 모델을 만들기 위한 실험 기준 정리
- 핵심 방향: 모델을 급하게 만들기보다, 믿을 수 있는 실험 틀을 먼저 고정
- 적용 범위: 데이터셋 고정, 입력 변수 검토, 모델 비교, 최종 평가

## 1. 문서 목적

- Track 1, 2에서는 실험 기준이 자주 흔들렸음
- 데이터 나누기 기준, 변수 선택 기준, 모델 비교 기준이 한 번에 정리되지 않았음
- Track 3에서는 아래 4가지를 먼저 고정함
- 어떤 데이터를 학습에 쓸지 정함
- 어떤 데이터를 성능 확인용으로 남길지 정함
- 어떤 입력 변수를 후보로 볼지 정함
- 어떤 순서로 실험할지 정함

## 2. Track 3의 목표

- 작품 1건의 정보를 보고 가격을 예측하는 모델 구축
- 처음 보는 작가와 이미 본 작가를 나누어 평가
- 실제 운영에서 다시 만들 수 있는 변수만 사용
- 실험 결과를 문서로 남겨 최종 모델 선택 이유를 설명 가능하게 만듦

## 3. 문제 정의

### 3.1 예측 대상

- 입력 단위: 작품 1건
- 예측 대상: 작품 가격
- 학습 목표값: `ln_price_krw_unified`
- 해석용 가격: `price_krw_unified`
- 로그 가격을 쓰는 이유
- 가격 분포가 한쪽으로 치우쳐 있음
- 로그값이 학습을 더 안정적으로 만듦

### 3.2 예측 상황 구분

- `Warm`
- 학습 데이터에 이미 나온 작가의 새 작품 가격 예측
- `Cold`
- 학습 데이터에 한 번도 나오지 않은 작가의 작품 가격 예측
- 원칙
- Warm과 Cold는 난이도가 다름
- 성능을 합쳐서 한 숫자로만 판단하지 않음

## 4. 실험 진행 원칙

- 데이터를 먼저 고정하고 모델 실험을 시작함
- 입력 변수는 한 번에 많이 바꾸지 않음
- 변수는 하나씩 추가하며 효과 확인
- Warm 성능과 Cold 성능을 항상 따로 기록
- 최고 점수 하나보다 반복 실험 시 안정성을 더 중요하게 봄
- 최종 확인용 데이터는 실험 중간에 참고하지 않음

## 5. 데이터 사용 계획

### 5.1 공식 기준 데이터

- Track 3 공식 기준 데이터
- [`data/release_split/track3_train.csv`](/Users/bo/VisionAI/data/release_split/track3_train.csv)
- [`data/release_split/track3_test_warm.csv`](/Users/bo/VisionAI/data/release_split/track3_test_warm.csv)
- [`data/release_split/track3_test_cold.csv`](/Users/bo/VisionAI/data/release_split/track3_test_cold.csv)
- 용도
- `track3_train.csv`: 학습 전용
- `track3_test_warm.csv`: Warm 평가 전용
- `track3_test_cold.csv`: Cold 평가 전용

### 5.2 현재 데이터 구성

- `track3_train.csv`
- 34,859개 작품
- 1,966명 작가
- `track3_test_warm.csv`
- 1,717개 작품
- 1,717명 작가
- `track3_test_cold.csv`
- 3,561개 작품
- 200명 작가

### 5.3 데이터 분리 상태 점검

- 학습 데이터와 Cold 평가 데이터의 작가가 겹치지 않음
- Warm 평가 데이터의 작가는 모두 학습 데이터에 남아 있음
- Warm 평가는 작가당 1작품씩 따로 분리
- Cold 평가는 완전히 처음 보는 작가 기준으로 구성
- 판단
- 현재 `release_split`은 Track 3 공식 평가 기준으로 사용 가능

### 5.4 기준 문서

- 데이터 분리 기준 참고 문서
- [`data/release_split/README.md`](/Users/bo/VisionAI/data/release_split/README.md:1)
- [`data/release_split/split_metadata.json`](/Users/bo/VisionAI/data/release_split/split_metadata.json:1)
- [`scripts/track3/split_for_release.py`](/Users/bo/VisionAI/scripts/track3/split_for_release.py:1)

## 6. 내부 검증용 데이터 사용 계획

- 개발 중간 실험용 데이터 묶음
- [`data/track3_splits/outer_holdout_artists.json`](/Users/bo/VisionAI/data/track3_splits/outer_holdout_artists.json)
- [`data/track3_splits/cold_folds.json`](/Users/bo/VisionAI/data/track3_splits/cold_folds.json)
- [`data/track3_splits/warm_splits.json`](/Users/bo/VisionAI/data/track3_splits/warm_splits.json)
- 용도
- 변수 추가 실험
- 모델 비교
- 반복 검증
- 세부 설정값 조정
- 역할 구분
- `track3_splits`: 개발 중간 실험용
- `release_split`: 최종 성능 확인용

## 7. 데이터 새어 나감 방지 원칙

- 의미
- 원래 학습할 때 알면 안 되는 정보가 모델에 들어가는 문제
- 잘못된 예
- 테스트 데이터까지 합쳐서 작가별 작품 수를 셈
- 전체 데이터를 보고 범주 목록을 만듦
- 테스트 데이터 분포를 본 뒤 변수를 수정함
- 지켜야 할 규칙
- 모델 학습은 항상 `train`만 사용
- 범주형 값 목록도 `train`만 보고 정함
- 크기 조정, 구간 나누기, 집계 변수 계산도 `train`만 보고 수행
- `artist_works_log` 같은 파생 변수는 split 이후 다시 계산
- `test_warm`, `test_cold`는 학습에 쓰지 않고 성능 확인에만 사용

## 8. 입력 변수 설계 원칙

### 8.1 기본 원칙

- 최종 입력 변수는 아래 조건을 만족해야 함
- 실제 운영에서 다시 만들 수 있어야 함
- 가격 정보가 뒤에서 새어 들어가면 안 됨
- 특정 데이터 출처에만 과하게 기대면 안 됨
- 의미 설명이 가능해야 함
- 반복 실험에서도 비슷한 개선 효과가 나와야 함

### 8.2 현재 핵심 변수 후보

- `medium_category`
- `support_category`
- `depth_cm`
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- 의미
- 작품의 재료, 바탕, 크기, 비율, 호수 같은 구조적 정보

### 8.2-1 크기 관련 변수 묶음 검토

- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `depth_cm`
- 해석 원칙
- 이 5개는 모두 완전히 다른 역할의 변수는 아님
- `width_cm`, `height_cm`, `log_area`, `estimated_ho`는 같은 크기 축을 다른 방식으로 표현한 후보군으로 봄
- `depth_cm`는 입체성, 깊이, 3D 특성을 설명하는 별도 축으로 봄
- 검토 원칙
- 크기 관련 변수를 모두 동시에 유지하는 것이 목표가 아님
- 같은 정보를 여러 방식으로 중복 입력하고 있을 가능성을 함께 검토함
- 최종 모델에서는 일부만 남기거나 대표 조합으로 축소하는 방향도 포함함
- 예시
- `width_cm + height_cm`
- `log_area`
- `estimated_ho`
- `log_area + estimated_ho`
- `log_area + depth_cm`
- 목적
- 어떤 크기 표현 방식이 가장 단순하고 안정적으로 작동하는지 비교하기 위함

### 8.3 추가로 시험할 변수

- `aspect_ratio`
- 가로와 세로 비율
- `medium_ho_bucket`
- 재료와 호수 구간을 합친 변수
- `artist_works_log`
- 학습 데이터에서 해당 작가가 몇 번 등장했는지를 반영한 변수

### 8.3-1 추가 파생 변수 확대 계획

- 현재 후보 외에도 운영 입력값에서 다시 계산 가능한 의미 있는 파생 변수를 추가 검토함
- 목적
- 피처 수를 무작정 늘리는 것이 목적이 아님
- 의미가 있고 운영에서 재현 가능한 파생 변수 후보를 넓게 검토하기 위함
- 추가 검토 후보
- `ho_bucket`
- 호수를 몇 개 구간으로 나눈 변수
- `medium_support_combo`
- 재료와 바탕의 조합 변수
- `max_side_cm`
- 긴 변의 길이
- `is_square_like`
- 정방형에 가까운지 여부
- `area_depth_interaction`
- 면적과 깊이의 결합 변수
- 검토 원칙
- 운영에서 다시 계산 가능한 피처만 후보로 둠
- 의미 설명이 가능한 피처만 후보로 둠
- Warm / Cold 각각에서 성능 개선 여부를 따로 확인함
- 같은 정보를 중복 표현하는 피처는 최종 단계에서 정리함

### 8.4 Warm 전용 변수

- `artist_name_ko`
- 설명
- 이미 학습에 등장한 작가를 구분하는 데 도움
- Warm에서는 유용할 수 있음
- Cold에서는 직접 사용하기 어려움

### 8.5 주의할 변수

- `source_platform`
- 과거 데이터 분석에는 참고가 될 수 있음
- 실제 운영 입력에서는 출처를 안정적으로 알기 어려움
- 따라서 최종 모델 입력 변수에서는 제외
- 필요하면 사후 분석 참고용으로만 제한

## 9. Track 3에서 답해야 할 질문

- 작품의 기본 정보만으로도 가격 예측이 가능한가
- 처음 보는 작가일 때 어떤 변수들이 실제로 도움이 되는가
- 이미 본 작가일 때 작가 정보가 얼마나 성능을 높여 주는가
- 변수를 추가할수록 진짜로 좋아지는가
- 복잡도만 늘어나는 것은 아닌가
- 최종 모델이 Warm과 Cold 모두에서 납득 가능한 성능을 보이는가

## 10. 실험 순서

### 10.1 1단계: 데이터 기준 고정

- `release_split`을 공식 기준으로 고정
- `track3_splits`는 개발용 실험 기준으로 유지
- 실험 도중 데이터 나누기 기준을 자주 바꾸지 않음
- 목적
- 실험 기준이 흔들리지 않게 하기 위함

### 10.2 2단계: 기본 모델 만들기

- 가장 단순한 비교 기준 모델 먼저 설정
- 예시
- Cold: 단순 회귀 또는 LAD 계열
- Warm: 기본 트리 모델
- 목적
- 이후 더 좋은 방법과 비교할 출발점 마련

### 10.3 3단계: 기본 변수 성능 확인

- 핵심 변수만 넣고 Warm과 Cold 성능 확인
- 점검 항목
- 현재 변수만으로 어느 정도 맞출 수 있는지
- 결측 처리에 문제는 없는지
- 변수 계산 방식이 안정적인지

### 10.4 4단계: 변수 추가 실험

- 변수를 한 번에 많이 넣지 않음
- 순서대로 추가하면서 효과 확인
- 권장 순서
- 기본 변수만 사용
- `aspect_ratio` 추가
- `medium_ho_bucket` 추가
- `artist_works_log` 추가
- Warm에서 `artist_name_ko` 추가
- 각 실험마다 기록할 내용
- 무엇을 추가했는지
- 성능이 얼마나 좋아졌는지
- Warm과 Cold에서 모두 좋아졌는지
- 복잡도가 늘어난 만큼 가치가 있는지

### 10.5 5단계: 모델 방식 비교

- 입력 변수 구성이 어느 정도 정해진 뒤 진행
- 비교 후보 예시
- LAD
- LightGBM
- XGBoost
- CatBoost
- 2단계 모델
- 혼합형 모델
- 원칙
- 모델 방식과 변수 구성을 동시에 크게 바꾸지 않음

### 10.6 6단계: 세부 설정값 조정

- 모델 종류와 입력 변수가 어느 정도 정해진 뒤 진행
- 조정 예시
- 학습 속도
- 트리 개수
- 리프 수
- 규제 강도
- 의미
- 이미 괜찮아 보이는 모델을 더 다듬는 과정

### 10.7 7단계: 최종 후보 고르기

- 확인 기준
- Warm 성능
- Cold 성능
- 여러 번 실험했을 때 흔들림 정도
- 운영에서 다시 만들 수 있는지
- 설명 가능성

### 10.8 8단계: 공식 평가

- 최종 후보만 아래 데이터로 성능 확인
- `track3_test_warm.csv`
- `track3_test_cold.csv`
- 이 결과를 Track 3 공식 성능으로 기록

## 11. 평가 방법

### 11.1 기본 평가 지표

- `median APE`
- 대표 오차율
- `MAPE`
- 평균 오차율
- `RMSE(log)`
- 로그 가격 기준 오차
- `Within-30%`
- 실제 가격과 30% 이내로 맞춘 비율
- `Within-50%`
- 실제 가격과 50% 이내로 맞춘 비율

### 11.2 결과 기록 방식

- 결과는 아래처럼 나누어 기록
- Warm 성능
- Cold 성능
- 필요하면 전체 참고 수치
- 필요하면 보조 분석으로만 추가 확인
- 출처별 차이
- 가격 구간별 차이
- 원칙
- 단일 평균만 적는 방식은 피함
- 핵심 판단 기준은 Warm / Cold 성능으로 유지

## 12. 실험 기록 방식

- 각 실험은 아래 형식으로 남김
- 실험 번호
- 날짜
- 실험 목적
- 확인하려는 가설
- 사용한 데이터 버전
- 사용한 데이터 나누기 기준
- 사용한 입력 변수
- 사용한 모델
- 주요 설정값
- Warm 결과
- Cold 결과
- 해석
- 결론
- 다음 할 일
- 결론 표기 방식
- 채택
- 보류
- 중단

## 13. 최종 모델 선택 기준

- Warm과 Cold 모두에서 일정 수준 이상의 성능을 보여야 함
- 반복 실험에서 결과가 크게 흔들리지 않아야 함
- 실제 운영에서도 같은 변수를 다시 만들 수 있어야 함
- 데이터 새어 나감 문제가 없어야 함
- 모델 구조와 변수 계산 방식이 설명 가능해야 함
- 모델 파일과 관련 결과물을 다시 저장하고 불러올 수 있어야 함

## 14. 현재 한계와 주의사항

- 실제 운영 입력에서는 출처를 안정적으로 알기 어려워 `source_platform`을 모델 입력에 넣기 어려움
- 시간 순서대로 나눈 데이터가 아니므로, 시간이 지나도 잘 맞는지는 아직 확인되지 않음
- Cold 평가 데이터는 학습 데이터보다 가격 분포가 조금 낮을 수 있음
- Warm 평가는 작가당 1건이라 개별 작가 해석보다 전체 평균 해석에 더 적합함
- 가격대 역시 운영 입력 변수로는 사용할 수 없으므로, 필요 시 결과 해석용 보조 분석으로만 제한함

## 14-A. F1~F6 실험 결과 요약 (2026-05-13 추가)

### 운영 baseline
- `v1.2`: Cold LAD 0.301 / Warm Tuned LightGBM 0.208 (release_split test 기준)
- 데이터: release_split v3 (PR16e), 학습 11 cols, depth feature는 `depth_cm`만 (PR15)

### 실험 결과표

| 실험 | 가설 | 검증 protocol | 결과 |
|---|---|---|---|
| F1 (PR20/21) | 크기 변수 단순화 (width/height/log_area/estimated_ho 중복) | 5 seeds mini → release_split confirm | **reject** — V1_log_ho는 Cold 동등이지만 Warm tail risk 증가 (max_ape +24%, catastrophic 16%) |
| F2 (PR22/23) | 새 파생 변수 4개 (medium_support_combo / max_side_cm / is_square_like / area_depth_interaction) | 5 seeds mini → release_split confirm | **reject** — 4개 모두. F1_combo는 mini에서 신호(4/5 seeds) 있었으나 release_split에서 반전 (false positive) |
| F3 (PR24) | Warm 모델 가족 변경 (CatBoost vs LightGBM) | 5 seeds mini | **reject** — CatBoost 5/5 seeds 패배 (med Δ +0.069) |
| F4 (PR25) | rare-artist Warm/Cold blend (1건/2건 작가에 Cold blend) | 5 seeds mini | **reject** — 모든 blend variant 0/5 seeds 개선, WR 5-16% (대부분 row 악화) |
| F5-B (PR28/29) | Cold KNN retrieval blend | frozen benchmark → release_split confirm | **reject** — frozen 신호 release_split에서 반전. 분해 분석상 rare cold artist + mixed/ink + 양극단 크기에선 도움이나 작가 분포 imbalance로 일반화 불가 |
| F6 (PR26) | Frozen Cold Benchmark 인프라 구축 | seed-free stratified | **구축 완료** — `data/track3_splits/frozen_mini_cold.csv` + V0 baseline cache + loader |
| F5 step 1 (PR27) | Cold 약점 영역 식별 | release_split test 분해 | **완료** — Artue, pigment/mixed/other, 고가, 대형(50+호), 2D 회화에서 weak |

### 검증 protocol의 가치
- F2/F5-B에서 mini → release_split 반전 두 번 발생
- 2단계 protocol이 false positive 정확히 차단
- frozen benchmark + Cohen's d 한계도 확인 (heavy-tail outlier에 부적합)

### Codex 종합 진단 (반복 확인)
- 현 baseline `v1.2`는 가설 공간 안에서 **강한 plateau**
- 단순 feature 추가, 모델 가족 변경, rare-artist 라우팅 변경은 모두 negative
- 추가 ROI는 **모델 미세조정보다 데이터 축 확장 (시간 split, 추가 작가, source 안정화)**에서 더 큼

## 14-B. Track 3 종결 선언 (2026-05-13)

- **상태**: CLOSED (운영 baseline `v1.2` 유지 확정)
- **운영 artifact**: `data/production/track3_cold_lad.joblib`, `track3_warm_lgb.txt`, `track3_metadata.json`
- **공식 평가 결과**: Cold 0.301 / Warm 0.208 (release_split test, PR16f)
- **변경 후 운영 시점**: 향후 실험 없이 운영 안정화 단계로 이행

### 다음 단계 (Codex 권고 순서)

1. **운영 안정화 + 모니터링** (단기)
2. **데이터 축 확장** (중기, 알고리즘보다 ROI 큼)
   - 시간 split 가능 데이터 확보
   - Cold artist 확장 데이터
   - source 안정화 (운영 입력 가능성)
3. **regime fallback (F5-A)** — 저비용 guardrail로만, 우선순위 낮음
4. **재모델링 보류** — 새 데이터 충분히 확보되기 전엔 추가 모델 실험 ROI 낮음

## 15. Track 3 최종 산출물

- 데이터셋 설명 문서
- 데이터 분리 기준 문서
- 입력 변수 목록 문서
- 변수 추가 실험 결과표
- 모델 비교표
- 최종 모델 설명 문서
- 운영용 모델 파일 목록
- 한계와 다음 과제 문서

## 16. 결론

- Track 3에서는 먼저 데이터와 평가 기준을 고정함
- 그 위에서 입력 변수와 모델을 차례대로 검증함
- `release_split`은 공식 평가 기준으로 사용
- `track3_splits`는 개발 중간 실험용으로 사용
- 전체 진행 순서
- 데이터 기준 고정
- 기본 모델 설정
- 핵심 변수 확인
- 변수 추가 실험
- 모델 방식 비교
- 세부 설정 조정
- 최종 후보 선택
- Warm/Cold 공식 평가
- 결과 문서화 및 운영용 파일 정리
- 핵심 메시지
- 좋은 결과 하나를 우연히 만드는 것이 목적이 아님
- 왜 그 결과가 나왔는지 설명 가능한 방식으로 모델을 만드는 것이 목적임
