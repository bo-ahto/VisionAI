# Track 6 난트 기준 재료/도구 보강 보고서

- 생성일: `2026-05-18`
- 정제 데이터: `data/track6/track6_feature_candidates_name_corrected.csv`
- 참고 파일: `data/track6/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv`
- 출력: `data/track6/track6_feature_candidates_name_corrected.csv`
- 전체 rows: `54,842`

## 1. 추가 컬럼

- `collected_material_raw`: 수집 원문 재료
- `nant_material_idx`: 난트 기준 95개 재료/도구 조합 idx
- `nant_support`: 난트 기준 재료/지지체
- `nant_tool`: 난트 기준 도구/매체
- `nant_material_note`: 참고표 비고
- `nant_material_match_method`: 매칭 방식

## 2. 매칭 방식

- `exact_reference`: 참고표의 `수집 재료`와 원문 재료가 정확히 매칭됨
- `rule_material_parse`: exact 매칭 실패 후 영문/한글 재료 표현을 규칙으로 해석함
- `nant_material_idx`는 6049개 원문 조합 idx가 아니라 왼쪽 95개 난트 기준 조합 idx를 사용함
- `unmatched`: 참고표와 규칙으로도 분류되지 않아 검토 목록으로 분리함

## 3. 매칭 결과

| method | rows |
|---|---:|
| `rule_material_parse` | `35,675` |
| `exact_reference` | `18,539` |
| `unmatched` | `628` |

## 4. 출처별 결과

| source | rows | exact | rule | unmatched |
|---|---:|---:|---:|---:|
| `artsy` | `30,046` | `17,178` | `12,284` | `584` |
| `artue` | `2,783` | `1,196` | `1,552` | `35` |
| `gallery_primary` | `292` | `130` | `160` | `2` |
| `saatchi` | `21,721` | `35` | `21,679` | `7` |

## 5. 주의

- 참고표 exact 매칭이 가장 신뢰도가 높음
- rule 기반 매칭은 영문 표기 문제를 줄이기 위한 보조 기준이므로 `nant_material_match_method`로 구분함
- 미매칭 원문 재료 검토 파일: `data/track6/quality/track6_nant_material_unmatched_review.csv`
- 미매칭은 사람이 참고표에 추가한 뒤 이 스크립트를 다시 실행하는 방식으로 관리
- `nant_` 컬럼은 현재 feature export에서 기본 제외되며, 별도 가설 실험에서 명시적으로 사용할 예정
