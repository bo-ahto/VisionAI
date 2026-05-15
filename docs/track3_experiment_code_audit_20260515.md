# Track 3 실험 코드 감사

- 작성일: 2026-05-15
- 목적: 지금까지 진행한 Track 3 실험이 가설 의도에 맞게 실행됐는지 점검
- 검토 범위: `scripts/track3/h*.py`, `data/track3_h*_*.json`, `docs/track3_experiments/*.md`
- 검토 기준: 학습/테스트 분리, 가설별 비교군 충족, 피처 ablation 범위, 결과 문서화 여부, 운영 채택 전 재검증 필요 지점

## 전체 판정

| 항목 | 판정 | 내용 |
|---|---|---|
| 스크립트 문법 | 이상 없음 | `python3 -m py_compile scripts/track3/h*.py` 통과 |
| 결과 파일 생성 | 이상 없음 | `h*.py`의 `OUT_PATH` 결과 파일이 모두 존재 |
| 학습/평가 분리 | 대체로 이상 없음 | 주요 모델은 `track3_train.csv`로 학습하고 `track3_test_warm.csv`, `track3_test_cold.csv`로 평가 |
| 가설별 실험 충족 | 대체로 충족 | H13, H14, H19-H28 등은 여러 variant로 ablation 수행 |
| 운영 채택 주의 | 필요 | 가격 범위 calibration, Cold 3D 중간 부피 예외, 작가 이력 피처는 운영 전 별도 재검증 필요 |

## 확인된 정상 사항

| 구분 | 확인 내용 |
|---|---|
| 데이터 split | Warm/Cold 학습 데이터는 별도 파일이 아니라 동일한 `track3_train.csv`를 사용하고, 평가만 Warm/Cold test로 분리함 |
| Cold 모델 | 작가명과 작가 과거 가격 통계를 제외하고 작품 구조 피처 중심으로 학습함 |
| Warm 모델 | 학습 데이터에 존재하는 작가 기준으로 작가명, 작가 작품 수, 작가 가격 통계 피처를 추가함 |
| H13 | 재료 flag, 재료 희소도, flag+희소도 조합을 모두 비교함 |
| H14 | 크기-재료 조합 category, 조합 flag, 전체 조합을 모두 비교함 |
| H19-H22 | 호수 세분화, 대형 호수 flag, 면적-호수 불일치, `log_ho`, 전체 조합을 비교함 |
| H23-H25 | 크기 구간, 3D 부피/변 길이, 재료 내 상대 크기를 비교함 |
| H26-H28 | `width_cm`, `height_cm`, `log_area`, `estimated_ho`, `aspect_ratio` 축소안을 여러 variant로 비교함 |
| H31 | 약한 Warm baseline이 아니라 H17 Warm champion 기준으로 호수/3D 피처를 다시 검증함 |
| H32 | Cold 3D 피처를 전체 Cold에 일괄 적용하지 않고 3D 작품에만 조건부 적용함 |
| H66-H67 | Warm 후보 개선은 multi-seed로 재검증함 |
| H68 | Warm 사용 기준을 1건, 3건, 5건 이상으로 비교해 routing 기준을 검증함 |

## 주의가 필요한 사항

| 이슈 | 영향 | 현재 판단 | 권장 조치 |
|---|---|---|---|
| 가격 범위 calibration이 test residual로 계산됨 | test set에서 본 오차폭을 그대로 운영 정책으로 쓰면 과적합 가능 | H11, H18, H46, H51, H52, H69는 실험/진단 근거로는 가능하지만 운영용 calibration으로는 아직 부족 | train 내부 calibration split 또는 cross-validation 기반 conformal calibration으로 재검증 |
| H45/H49의 Cold 3D 중간 부피 기준이 cold test quantile에서 나옴 | test 분포를 보고 조건을 만든 셈이라 운영 routing 기준으로 바로 쓰기 어려움 | 진단용 slice 분석으로는 유효하지만 production rule로는 미완성 | train 분포 기준 quantile 또는 고정 도메인 기준으로 threshold 재정의 후 재평가 |
| 작가 이력 가격 통계가 날짜 없이 full train 기준으로 계산됨 | 실제 예측 시점 이후 거래가 작가 통계에 섞일 가능성 | 현재 split 기준 실험은 맞지만 temporal-safe 운영 검증은 아님 | 거래일/등록일 컬럼 확보 후 작가 통계를 예측 시점 이전 데이터만으로 재계산 |
| H60 medium/support 조합 정리는 `min_count=100`만 테스트 | 희소 조합 정리 방식의 전체 grid 검증은 아님 | 현재 결과가 악화라 채택하지 않는 판단은 가능 | 다시 볼 경우 `min_count=20/50/100/200` grid로 재실험 |
| H13/H14 일부 피처 실험은 single-seed 성격 | 작은 개선/악화는 seed 영향 가능 | 큰 방향성 판단은 가능하지만 미세한 차이 채택에는 부족 | 채택 후보가 생긴 경우 H66 방식처럼 multi-seed 재검증 |
| H15는 실제 결측이 0건 | 결측 패턴 피처 실험 자체가 성립하지 않음 | 보류 판정이 맞음 | 운영 입력 로그 또는 인위적 masking 실험과 분리 관리 |
| H16은 날짜 컬럼 부재 | 작가 이력 피처의 운영 안전성 결론 불가 | 보류 판정이 맞음 | 날짜 컬럼 확보 전까지 작가 가격 통계는 “성능 후보”로만 표기 |

## 가설별 실험 충족도

| 가설 범위 | 충족도 | 검토 결과 |
|---|---|---|
| H1 | 충족 | 크기 대표 표현 단순화는 기존 PR20/PR21/H1 기록에서 비교 완료 |
| H2-H4 | 충족 | 구조-only Cold, Warm 작가 피처, 파생 피처 효과를 foundation 실험으로 비교 |
| H5-H6 | 충족 | 선형/트리 및 robust 선형 계열 비교 완료 |
| H7-H8 | 충족 | Cold 2D fallback은 release split에서 재검증 후 중단 |
| H9 | 충족 | masking 학습이 clean 성능을 해치는지까지 비교 |
| H10-H12 | 부분 충족 | 성능 검증은 됐지만 날짜 없는 작가 이력 통계라 운영 안전성은 H16에 종속 |
| H13-H14 | 충족 | 변수 추가 실험이 여러 variant로 구성됨 |
| H15-H16 | 보류 타당 | 데이터 조건상 실험 불가를 감사로 확인 |
| H17-H18 | 부분 충족 | H17은 multi-seed로 충분, H18은 calibration data 분리 전까지 진단용 |
| H19-H28 | 충족 | 크기/호수/3D/상대 크기/축소 ablation이 충분히 구성됨 |
| H29-H33 | 충족 | Warm/Cold 피처 분리와 최종 후보 재검증 진행 |
| H34-H43 | 충족 | 분리 모델, 약점 slice, 신뢰도 후보를 후속 검증 |
| H44-H47 | 부분 충족 | 저이력 fallback과 가격 범위는 검증, H45 중간 부피 기준은 test-derived라 재검증 필요 |
| H48-H60 | 부분 충족 | 정책/피처 후속 검증은 됐지만 H49/H51/H52는 운영 전 별도 calibration 필요 |
| H61-H67 | 충족 | 모델 개선 후보와 Warm retune은 multi-seed까지 확인 |
| H68 | 충족 | Warm routing threshold를 1/3/5건 기준으로 비교 |
| H69 | 부분 충족 | H46을 닫는 진단 결과는 충분하지만 운영용 가격 범위는 별도 calibration split 필요 |

## 재실험 우선순위

| 우선순위 | 대상 | 이유 | 제안 실험 |
|---|---|---|---|
| 1 | 가격 범위 calibration | 현재 test residual 기반이라 운영 정책으로 바로 쓰기 어려움 | train에서 calibration fold를 분리해 H69 범위 재계산 |
| 2 | H45/H49 Cold 3D 중간 부피 예외 | 조건 기준이 cold test quantile 기반 | train 기준 volume quantile 또는 고정 threshold로 다시 평가 |
| 3 | H16 temporal-safe 작가 이력 | Warm 최적 후보의 핵심 피처가 작가 가격 통계임 | 날짜 컬럼 확보 후 예측 시점 이전 데이터만 사용해 H10/H17/H66 재검증 |
| 4 | H60 희소 조합 정리 | 한 개 기준값만 확인 | `min_count` grid를 둔 ablation |
| 5 | H13/H14 채택 후보 재확인 | single-seed 미세 차이 방지 | 채택 후보가 다시 생길 때만 multi-seed 재검증 |

## 재검증 반영 결과

| 대상 | 재검증 실험 | 결과 |
|---|---|---|
| 가격 범위 calibration | `H70_H72_operational_revalidation` | 내부 calibration split 기준에서도 Warm 전체 coverage `0.821`, Cold 전체 coverage `0.855`로 조건별 가격 범위 정책 유지 가능 |
| Cold 3D 중간 부피 예외 | `H70_H72_operational_revalidation` | train 기준 threshold 적용 시 전체 Cold median APE와 p95가 모두 악화되어 미채택 |
| H60 combo grid | `H70_H72_operational_revalidation` | `min_count=20/50/100/200/500` 모두 H32보다 median APE가 악화되어 미채택 |
| H16 temporal-safe 작가 이력 | 미실행 | 날짜 컬럼 부재로 여전히 재검증 불가 |

## 결론

| 결론 | 내용 |
|---|---|
| 코드 이상 여부 | 현재까지 확인한 `h*.py` 실험 코드는 문법 오류와 결과 파일 누락은 없음 |
| 학습/테스트 방식 | 대부분의 모델 실험은 train으로 학습하고 warm/cold test로 평가하는 구조가 맞음 |
| 가설 충족 여부 | 핵심 feature ablation은 여러 variant로 수행되어 “일부만 빼고 끝낸” 수준은 아님 |
| 가장 큰 리스크 | 가격 범위와 일부 slice 기준이 test set에서 계산되어 운영 정책으로 바로 쓰기에는 부족 |
| 다음 조치 | 모델 성능 후보는 유지하되, 운영 정책 후보는 calibration split과 temporal-safe 데이터 확보 후 닫는 것이 맞음 |
