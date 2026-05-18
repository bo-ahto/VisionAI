# T6-E001 strict split 생성 및 검증

- 날짜: 2026-05-18
- 관련 가설: T6-H1
- 상태: 검증 완료
- 사용 데이터: `data/track4_primary_market_feature_candidates_v1.csv`
- 사용 스크립트: `scripts/track6/create_track6_splits.py`
- 결과: `docs/track6/dataset/split_report.md`

## 실험 목적

- Track5에서 남은 Cold 이름 중복, Warm 저이력, 1작가 1작품 평가 문제를 split 단계에서 보완
- validation/test를 먼저 충분히 확보하고 규모를 근접하게 맞춘 뒤 남은 데이터를 train으로 구성

## 핵심 결과

- train rows: `26,686`
- val_warm rows/artists: `526` / `180`
- test_warm rows/artists: `601` / `206`
- val_cold rows/artists: `2,956` / `160`
- test_cold rows/artists: `3,342` / `200`
- Cold train 이름 중복: val `0`, test `0`
- Stable Warm 평가 작가 최소 train 작품 수: val `5`, test `5`
- 주의: `5작품` 기준은 Warm/Cold 구분 기준이 아니라 Stable Warm 평가 안정성 기준

## 결론

- split 상태: `pass`
- 상태가 `pass`이면 이 split을 Track6 기준 데이터셋으로 고정
- 이후 T6-E002부터 모든 모델 실험은 이 split 기준으로 실행
