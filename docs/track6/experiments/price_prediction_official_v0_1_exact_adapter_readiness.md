# 공식 v0.1 정확 adapter readiness 감사

- 작성일: 2026-06-12T16:49:08
- 목적: 보고서 기준 Warm/Cold 최종 모델을 raw 입력 서비스에 exact parity로 붙일 수 있는지 점검

## 1. 결론

- Warm 최종층 fixed-test replay 가능: 예
- Warm exact raw adapter 가능: 아니오
- Cold 최종층 fixed-test replay 가능: 예
- Cold exact raw adapter 가능: 아니오
- 현재 서비스 연결 수준: `report_final_layer_proxy`
- 다음 승격 조건: 원 상류 모델을 raw-input 아티팩트로 재동결하거나 재학습해 fixed-test parity를 통과해야 함

## 2. Warm

| 항목 | 결과 |
|---|---|
| PP258 최종층 replay | 가능 |
| 지표 일치 | 예 |
| 최대 가격 차이 | 1.4901161193847656e-08 |
| PP252 feature detail | 있음 |
| 저장 모델 파일 | 0개 |
| 상류 일부 refreeze | 완료 |
| exact raw adapter | 불가 |

Warm exact raw adapter blocker:

- 방향 분류와 Huber 잔차는 refreeze 후보로 저장되었습니다.
- 다만 PP252 기준 후보와 PP252 안정 후보를 원시 입력에서 만드는 직전 후보 생성 adapter가 아직 남아 있습니다.
- 따라서 현재 산출물만으로는 신규 사용자 입력에 대해 PP252 원 상류 컬럼 전체를 exact parity로 생성할 수 없습니다.

## 3. Cold

| 항목 | 결과 |
|---|---|
| v0.3 후처리 replay | 가능 |
| 후처리 파일 | 있음 |
| 검색 delta lookup | 있음 |
| raw v0.2 predictor | 있음 |
| 상류 일부 refreeze | 완료 |
| row-level feature store | 있음 (32766건) |
| fixed-test feature store replay | 가능 |
| fixed-test feature store hit rate | 1.0 |
| 신규 입력 cache/default feature pipeline | 가능 |
| exact raw adapter | 불가 |

Cold exact raw adapter blocker:

- PP-Y2/PP-Y16/QR1 주요 상류 모델은 refreeze 후보로 저장되었습니다.
- fixed-test 행은 row-level feature store와 source_artwork_id/artwork_url lookup으로 exact parity를 통과했습니다.
- 신규 입력은 search snapshot, 전시/갤러리 cache, missing/default fallback 순서로 deterministic하게 피처를 생성합니다.
- 다만 feature cache에 없는 신규 작가의 검색/전시/갤러리 정보를 실시간 수집하고 검수해 같은 스키마로 저장하는 live collection pipeline은 아직 남아 있습니다.
- raw 실행 가능한 v0.2 predictor는 검색 피처를 제거한 별도 운영 변형이라 v0.3 fixed-test parity와 동일하지 않습니다.

## 4. 다음 작업

| 순서 | 작업 | 산출물 |
|---|---|---|
| 1 | Warm PP252 상류 모델 재동결 | PP252 기준/안정/방향/Huber raw predictor bundle |
| 2 | Warm fixed-test parity 검증 | PP258 stored metrics와 동일한 재현 보고서 |
| 3 | Cold fixed-test feature store replay 유지 | `artwork_url`/`source_artwork_id` 기준 exact parity 감사 결과 |
| 4 | 신규 입력용 Cold live feature collection pipeline 구축 | feature cache에 없는 작가의 검색/전시/갤러리 피처 수집·검수·저장 |
| 5 | 서비스 adapter 승격 | `report_model_adapter` 상태로 API 전환 |
