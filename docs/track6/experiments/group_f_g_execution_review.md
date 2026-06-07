# Group F/G 작가 메타 조합 실험 실행 전 검토

- 작성일: `2026-05-27`
- 기준 split: `data/track6_split_with_year_type_edition_size_artist_name`
- 선행 조건: Group E 작가 변수 단독 실험 결과 확인 후 진행
- 공통 작품 기본 피처 묶음: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support`

## 1. 전제 확인

- 필요한 피처는 최신 split feature 파일에 존재한다.
- 작가 메타는 `_track6_row_id` 기준으로 보강 완료했다.
- 전시 횟수는 `artist_exhibition_solo_count`, `artist_exhibition_group_count`, `artist_exhibition_fair_count`로 표준화했다.
- `artist_meta_source` 같은 출처 피처는 학습에 사용하지 않는다.
- 가격/라벨/출처 URL 누수 검사는 통과했다.

## 2. Group F 검토

| 실험 | 제안 피처 | 실행 판단 | 조정 필요 사항 |
|---|---|---|---|
| F1 | `artist_meta_birth_year + artist_exhibition_solo_count + artist_exhibition_group_count + artist_exhibition_fair_count` | 실행 가능 | `career_stage` 대신 실제 전시 횟수를 사용. 생년과 전시 횟수 각각의 결측 flag 포함 권장 |
| F2 | `artist_meta_total_works + artist_meta_for_sale_works + artist_meta_followers + artist_meta_is_p1` | 실행 가능 | 활동량+인지도 조합 효과 실험으로 정의 |
| F3 | `artist_meta_birth_year + 전시 횟수 3종 + artist_meta_nationality` | 실행 가능 | 기본 작가 프로필 묶음으로 정의 |
| F4 | F2와 동일 피처 | 수정 필요 | F2와 중복. `artist_meta_available_count`, `artist_meta_completeness_score`, 결측 flag를 추가한 정보량 실험으로 바꾸는 것을 권장 |
| F5 | F1~F4 전체 작가 메타 묶음 | 실행 가능 | 작가명 없이 전체 작가 메타만으로 가격 예측 가능한지 확인 |

## 3. Group F 권장 정리안

| 실험 | 사용 피처 | 목적 |
|---|---|---|
| F1 | `artist_meta_birth_year + artist_exhibition_*_count` | 세대와 전시 경력 조합이 가격대 차이를 설명하는지 확인 |
| F2 | `artist_meta_total_works + artist_meta_for_sale_works + artist_meta_followers + artist_meta_is_p1` | 활동량과 인지도 조합이 시장 노출 효과를 설명하는지 확인 |
| F3 | `artist_meta_birth_year + artist_exhibition_*_count + artist_meta_nationality` | 생년/경력/국적을 합친 기본 작가 프로필 효과 확인 |
| F4 | `F2 + artist_meta_available_count + artist_meta_completeness_score + 주요 missing flag` | 활동량/인지도 정보와 정보량이 예측 신뢰도에 도움 되는지 확인 |
| F5 | `F3 + F4` | 작가명 없이 전체 작가 메타 묶음만으로 예측력이 생기는지 확인 |

## 4. Group G 검토

| 실험 | 제안 피처 | 실행 판단 | 해석 주의 |
|---|---|---|---|
| G1 | 기본 피처 묶음 vs 기본 피처 묶음 + `artist_name_ko` | 실행 가능 | 기존 C6와 유사. Warm 중심 해석 |
| G2 | 기본 피처 묶음 vs 기본 피처 묶음 + `artist_works_log` | 실행 가능 | Cold는 신규 작가라 `artist_works_log=0`, Warm 중심 해석 |
| G3 | 기본 피처 묶음 vs 기본 피처 묶음 + `artist_meta_birth_year` | 실행 가능 | 결측 flag 포함 권장 |
| G4 | 기본 피처 묶음 vs 기본 피처 묶음 + 전시 횟수 3종 | 실행 가능 | 전시 횟수 이상값 표준화 완료 |
| G5 | 기본 피처 묶음 vs 기본 피처 묶음 + `artist_meta_nationality` | 실행 가능 | 국적 표본 수 편차 확인 필요 |
| G6 | 기본 피처 묶음 vs 기본 피처 묶음 + `artist_meta_total_works + artist_meta_for_sale_works` | 실행 가능 | 플랫폼/수집 시점 의존성 해석 주의 |
| G7 | 기본 피처 묶음 vs 기본 피처 묶음 + `artist_meta_followers + artist_meta_is_p1` | 실행 가능 | `is_p1` 값 편차가 작을 수 있음 |
| G8 | 기본 피처 묶음 vs 기본 피처 묶음 + 기본 프로필 묶음 | 실행 가능 | F3의 작품 조건 통제 버전 |
| G9 | 기본 피처 묶음 vs 기본 피처 묶음 + 전체 작가 메타 묶음 | 실행 가능 | F5의 작품 조건 통제 버전 |
| G10 | 기본 피처 묶음 + `artist_works_log` 구간별 라우팅 | 별도 코드 필요 | 단순 피처 추가가 아니라 Warm/Cold fallback 정책 실험 |

## 5. Group G 해석 기준

- G1~G9는 “작품 기본 피처 묶음 대비 추가 개선이 있는가”를 본다.
- 핵심 비교는 같은 모델 안에서 `baseline`과 `+작가 변수`의 MdAPE, RMSE(log), p95 APE 차이다.
- Warm과 Cold는 결과를 합치지 않는다.
- 작가명 또는 `artist_works_log`가 들어간 G1/G2는 Warm 중심으로 해석한다.
- 작가 메타만 추가하는 G3~G9는 Cold에서도 운영 가능성이 있다. 단 실제 서비스에서 작가 DB로 확보 가능해야 한다.
- G10은 모델 선택이 아니라 라우팅 정책 실험이므로 별도 폴더/코드로 관리한다.

## 6. 중복 및 정리 필요 항목

- F2와 F4는 현재 원문 기준으로 중복이다.
  - F4는 정보량/결측 flag까지 포함하는 실험으로 수정 권장.
- G1은 기존 `C6_artist_name_plus_artwork_basic`과 유사하다.
  - 최신 split 기준으로 재실행하거나 기존 결과를 참조할 수 있다.
- G10은 기존 `T6-E101_low_history_artist_routing`과 목적이 유사하다.
  - 최신 split과 Group E/G 결과 기준으로 재검증 권장.
- 과거 `T6-E083~T6-E093` 계열 일지는 일부 유사하지만, 현재는 보강된 split과 고정 실행기 기준으로 다시 정리하는 편이 낫다.

## 7. 실행 가능 결론

- F1, F2, F3, F5는 바로 실행 가능하다.
- F4는 중복 제거를 위해 정보량 피처 포함 버전으로 수정 후 실행하는 것이 맞다.
- G1~G9는 공통 실행기로 실행 가능하다.
- G10은 별도 라우팅 실험 코드가 필요하다.
- Group F/G 실행 전 Group E 단독 실험 결과를 먼저 생성해야 한다.

