# Track 6 클렌징 검토 요약

- 생성일: `2026-05-18`
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- 목적: Track6 split 전 학습 후보와 작가명/동명이인 상태 확인

## 1. 후보 데이터

- 전체 입력 rows: `54,842`
- Track4 학습 후보 rows: `34,219`
- Track6 후보 rows: `34,219`
- 작가 key 수: `2,159`
- 한글 작가명 결측 rows: `0`
- 원본 한글명 결측 rows: `0`

## 2. 작가명/동명이인

- 원본 한글명 기준 여러 artist_key가 있는 이름 수: `101`
- `is_homonym=True` rows: `1,197`
- `artist_entity_suffix` 사용 rows: `1,197`
- 해석: 동명이인 후보는 split 검증에서 이름 기준 중복 제거 대상으로 함께 관리함

## 3. 재료/지지체

- `medium_category` unknown rows: `26`
- `support_category` unknown rows: `2,783`
- 해석: unknown은 즉시 제외하지 않고 후속 Cold/Warm 위험 구간으로 관리함

## 4. 출처별 후보 rows

| 출처 | rows |
|---|---:|
| `saatchi` | `20,531` |
| `artsy` | `10,722` |
| `artue` | `2,680` |
| `gallery_primary` | `286` |
