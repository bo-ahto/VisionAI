# T4-E012 출처 편향 점검

- 날짜: 2026-05-15
- 연결 가설: T4-C6
- 상태: 완료
- 목적: source를 모델 피처로 사용하지 않는 전제에서 출처별 데이터 품질 차이를 확인

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_raw_collected.csv`
- 보조 입력:
  - `data/track4_price_consistency_audit.csv`
  - `data/track4_size_consistency_audit.csv`
  - `data/track4_medium_support_consistency_audit.csv`
  - `data/track4_duplicate_consistency_audit.csv`
- 감사 결과 CSV: `data/track4_source_bias_audit.csv`
- 감사 요약 JSON: `data/track4_source_bias_audit_summary.json`
- 요약 문서: `docs/track4/audits/source_bias_audit.md`

## 2. 주요 결과

| 출처 | rows | 가격 있음 | 가격 중앙값 | 1억 초과 | 가격 이슈 | 크기 이슈 | 재료 이슈 | 중복 flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Artsy | `30,046` | `11,118` | `4,140,000` | `140` | `19,122` | `373` | `793` | `1,323` |
| Artue | `2,783` | `2,783` | `2,785,900` | `7` | `8` | `7` | `85` | `267` |
| Gallery primary | `292` | `292` | `20,336,700` | `57` | `57` | `1` | `1` | `0` |
| Saatchi | `21,721` | `21,721` | `2,559,900` | `772` | `772` | `20` | `317` | `1,803` |

## 3. 해석

- 출처별 가격 결측률과 가격대가 크게 다름
- Gallery primary는 행 수는 작지만 가격대가 높음
- Artsy는 가격 없는 행이 많아 학습 후보 제외가 많음
- Saatchi는 데이터 수가 많고 가격이 대부분 있으나 고가 flag가 존재함
- 이런 차이는 작품 자체의 입력 정보가 아니라 수집 경로 차이임

## 4. 결론

- 채택: source는 모델 입력 피처에서 제외
- 채택: source는 원본 추적, 품질 감사, 중복 처리에만 사용
- 보류: source별 가격대 차이를 직접 보정하는 방식은 운영 재현성이 없어 사용하지 않음
- 반영: 최종 feature 후보 파일에서는 source 계열 컬럼을 제외

## 5. 다음 작업

- `T4-C7` 갤러리 메타데이터 점검 진행
- 이후 `cleaned_v2` 생성 시 source는 관리 컬럼으로만 유지
