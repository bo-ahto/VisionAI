# PP-G5 외부 DB + 후보정 결합 검증

- 목적: 신규 외부 데이터 또는 검색/소셜 지표가 후처리 이후 추가 개선에 필요한지 판단한다.
- 실행 기준: 기존 컬럼 재사용이 아니라 신규/보강 데이터가 있을 때만 모델 성능 실험을 실행한다.
- 현재 상태: `blocked_existing_meta_only`
- 판단: artist meta 후보 컬럼은 있으나 PP-G 요구사항은 신규/보강 외부 DB이므로 기존 컬럼 재사용으로 실행하지 않음

## 필요한 컬럼

- `external_artist_db_bundle_pred_log`
- `postprocessing_candidate_pred_log`

## 현재 누락 컬럼

- `external_artist_db_bundle_pred_log`
- `postprocessing_candidate_pred_log`
