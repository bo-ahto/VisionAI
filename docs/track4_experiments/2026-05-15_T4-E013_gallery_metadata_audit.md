# T4-E013 갤러리 메타데이터 점검

- 날짜: 2026-05-15
- 연결 가설: T4-C7
- 상태: 완료
- 목적: 갤러리명과 티어 기준표 매칭 가능성을 확인하고 모델 피처 사용 여부를 판단

## 1. 사용 데이터

- 입력 데이터: `data/track4_artist_consistency_audit.csv`
- 티어 기준표: `data/art_gallery_tier_list_v3.xlsx - 전체 리스트.csv`
- 감사 결과 CSV: `data/track4_gallery_metadata_audit.csv`
- 감사 요약 JSON: `data/track4_gallery_metadata_audit_summary.json`
- 요약 문서: `docs/track4_gallery_metadata_audit.md`

## 2. 주요 결과

- 전체 행: `54,842`
- 티어 매칭 행: `331`
- 갤러리명 결측 행: `2,783`
- 티어 미매칭 행: `51,728`

## 3. 해석

- 기준표 직접 매칭률이 낮음
- 출처별 갤러리명 표기와 기준표 명칭이 많이 다름
- 일부 출처는 갤러리명 자체가 없거나 판매 플랫폼명 성격이 강함
- 실제 운영에서 갤러리 정보를 항상 입력받을 수 있는지도 불확실함

## 4. 결론

- 보류: 갤러리명/티어는 기본 모델 피처에서 제외
- 유지: `gallery_name_raw`는 원본 추적용으로 보존
- 유지: `gallery_tier_validated`는 기준표 매칭이 된 경우만 보조 컬럼으로 보존
- 후속: 갤러리 DB가 별도로 정리되면 독립 실험으로 검증

## 5. 다음 작업

- 감사 결과를 반영해 `cleaned_v2` 생성
- 최종 feature 후보 파일에서는 갤러리/티어를 기본 입력 피처에서 제외
