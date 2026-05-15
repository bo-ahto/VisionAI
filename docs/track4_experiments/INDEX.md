# Track 4 실험 기록 인덱스

- 목적: Track 4 개별 실험 기록을 한눈에 관리
- 정렬 기준: 최신 실험이 위로 오도록 관리

| 날짜 | 실험 ID | 연결 가설 | 상태 | 요약 | 기록 |
|---|---|---|---|---|---|
| 2026-05-15 | T4-E016 | T4-C1~T4-C7 | 완료 | cleaned_v2 전체 94개 컬럼 값 정합성 재점검, 파생값 계산 불일치 0건 확인 | [기록](2026-05-15_T4-E016_column_value_consistency_audit.md) |
| 2026-05-15 | T4-E015 | T4-H0 | 완료 | Track 4 Warm/Cold split 생성, `artist_name_ko` 포함 train `28,930`건 확보 | [기록](2026-05-15_T4-E015_split_generation.md) |
| 2026-05-15 | T4-E014 | T4-C1~T4-C7 | 완료 | 감사 결과 반영 `cleaned_v2` 생성, 학습 후보 `34,239`건과 한글 작가명 `54,840`건 확보 | [기록](2026-05-15_T4-E014_cleaned_v2_generation.md) |
| 2026-05-15 | T4-E013 | T4-C7 | 완료 | 갤러리 메타데이터 점검, 티어 직접 매칭 `331`건으로 기본 피처 제외 판단 | [기록](2026-05-15_T4-E013_gallery_metadata_audit.md) |
| 2026-05-15 | T4-E012 | T4-C6 | 완료 | 출처 편향 점검, source는 모델 피처 제외 원칙 재확인 | [기록](2026-05-15_T4-E012_source_bias_audit.md) |
| 2026-05-15 | T4-E011 | T4-C5 | 완료 | 중복 정합성 감사, 같은 출처 의미 중복 `954`그룹과 출처 간 엄격 중복 `4`그룹 확인 | [기록](2026-05-15_T4-E011_duplicate_consistency_audit.md) |
| 2026-05-15 | T4-E010 | T4-C3 | 완료 | 재료/지지체 1차 매핑 감사, 재료 정상 후보 `53,646`건 확인 | [기록](2026-05-15_T4-E010_medium_support_consistency_audit.md) |
| 2026-05-15 | T4-E009 | T4-C4 | 완료 | 작가명 정합성 감사, split 후보 작가 key `3,033`개와 artist master 후보 `120`명 확인 | [기록](2026-05-15_T4-E009_artist_consistency_audit.md) |
| 2026-05-15 | T4-E008 | T4-C2 | 완료 | raw collected 기준 크기 정합성 감사, 정상 후보 `54,441`건 확인 | [기록](2026-05-15_T4-E008_size_consistency_audit.md) |
| 2026-05-15 | T4-E007 | T4-C1 | 완료 | raw collected 기준 가격 정합성 감사, 정상 후보 `34,883`건 확인 | [기록](2026-05-15_T4-E007_price_consistency_audit.md) |
| 2026-05-15 | T4-E006 | T4-H0 | 완료 | raw collected 기반 클렌징 실험 계획 수립 | [기록](2026-05-15_T4-E006_cleaning_experiment_plan.md) |
| 2026-05-15 | T4-E005 | T4-H0 | 완료 | 원본 컬럼 보존 raw collected `54,842`건 생성 | [기록](2026-05-15_T4-E005_raw_collected_union.md) |
| 2026-05-15 | T4-E004 | T4-H0 | 완료 | raw 통합본에서 원본 수집값/파싱값/파생값/관리값 구분 | [기록](2026-05-15_T4-E004_raw_column_provenance.md) |
| 2026-05-15 | T4-E003 | T4-H0 | 완료 | cleaned v1 생성, 학습 후보 `32,343`건 및 갤러리 티어 기준표 매칭 `1,231`건 확인 | [기록](2026-05-15_T4-E003_primary_market_cleaned_v1.md) |
| 2026-05-15 | T4-E002 | T4-H0 | 완료 | raw 통합본 컬럼 감사, 가격/크기/연도 이상값 확인 | [기록](2026-05-15_T4-E002_primary_market_column_audit.md) |
| 2026-05-15 | T4-E001 | T4-H0 | 1차 완료 | 1차 시장 raw 통합본 `33,276`건 생성 | [기록](2026-05-15_T4-E001_primary_market_raw_union.md) |
| 2026-05-15 | - | - | 준비 | Track 4 문서 구조 생성 | - |
