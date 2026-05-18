# T5-E024 Cold 이름 중복 및 엄격 Cold 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H27
- 목적: Cold test에 train과 같은 작가명이 섞여 Cold 성능이 과대평가됐는지 확인
- 사용 데이터: `track5_train.csv`, `track5_test_cold.csv`, T5-E010 예측값
- 사용 스크립트: `scripts/track5/run_t5_e022_e025_audit_closure.py`
- 결과 파일: `data/track5/results/t5_e022_e025_audit_closure_metrics.json`

## 실험 방법

- Cold 기준은 기존처럼 `artist_key`가 train에 없는 경우로 확인
- 추가로 `artist_name_ko`, `artist_name_ko_orig`가 train에 있는지 확인
- 이름까지 겹치지 않는 그룹을 `strict cold`로 분리
- 이름이 겹치는 그룹과 strict cold의 오차를 비교

## 주요 결과

- Cold test의 train artist_key 겹침: `0`
- 이름 중복 행 수: `126`
- 이름 중복 작가 수: `15`
- strict cold median APE: `0.3928`
- strict cold p95 APE: `2.0458`
- 이름 중복 그룹 median APE: `0.3668`
- 이름 중복 그룹 p95 APE: `1.0866`

## 해석

- artist_key 기준 Cold 분리는 지켜졌음
- 다만 이름 기준 중복은 일부 존재함
- 이름 중복 그룹이 strict cold보다 쉬운 구간으로 보임
- 전체 Cold 결론은 strict cold에서도 거의 유지되므로 이름 중복이 성능을 만든 주원인은 아님

## 결론

- 상태: 검증 완료
- Cold 평가는 앞으로 `artist_key`뿐 아니라 `artist_name_ko` 기준 strict cold도 함께 보고해야 함
- 다음 split 생성 시 Cold 후보 작가는 이름 기준 중복까지 제외하는 보완이 필요함
