# T6-E001C feature/label 분리 파이프라인

- 날짜: 2026-05-18
- 관련 가설: T6-H1
- 상태: 검증 완료
- 사용 데이터: Track6 name-corrected split
- 사용 스크립트: `scripts/track6/export_feature_label_splits.py`
- 결과 문서: `docs/track6/dataset/feature_label_pipeline_report.md`
- manifest: `data/track6/manifests/track6_feature_label_manifest.json`

## 실험 목적

- 가격 정보 노출을 줄이기 위해 모델 입력 파일과 정답 가격 파일을 물리적으로 분리
- KRW 가격 외에도 raw price, currency, amount, sale 계열 컬럼을 feature 파일에서 차단
- Warm과 Cold 모델이 서로 다른 feature 파일을 읽도록 분리

## 핵심 결과

- 전체 상태: `pass`
- Warm feature 파일 누수 의심 컬럼: `0`
- Cold feature 파일 누수 의심 컬럼: `0`
- Warm feature 컬럼 수: `17`
- Cold feature 컬럼 수: `14`
- label 파일 컬럼 수: `12`

## 분리 기준

- feature 파일에서 제거:
  - `price_krw`
  - `ln_price_krw`
  - `is_high_price_candidate`
  - `price`, `krw`, `usd`, `currency`, `amount`, `sold`, `sale`, `cost`, `fee` 패턴 컬럼
  - 출처/URL/이미지/수집 추적 컬럼
- Warm feature:
  - 작가 내부 식별자인 `artist_key`, train 기준 작가 이력 수는 유지
  - 원문 작가명, 동명이인 메타, title은 제거
- Cold feature:
  - 작가 식별/작가명/작가 이력 컬럼을 모두 제거

## 결론

- 이후 모델 학습/예측은 full split이 아니라 `features/warm`, `features/cold` 파일을 기준으로 진행
- 정답 가격은 평가 스크립트에서만 `labels` 파일로 읽음
- test labels는 최종 후보 확정 후 최종 평가에만 사용
