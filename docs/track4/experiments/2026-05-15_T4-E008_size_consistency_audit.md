# T4-E008 크기 정합성 감사

- 날짜: 2026-05-15
- 연결 가설: T4-C2
- 상태: 완료
- 목적: Track 4 원본 보존 통합본에서 크기값을 면적/호수/3D 피처로 사용할 수 있는지 확인

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_raw_collected.csv`
- 입력 행 수: `54,842`
- 감사 결과 CSV: `data/track4_size_consistency_audit.csv`
- 감사 요약 JSON: `data/track4_size_consistency_audit_summary.json`
- 요약 문서: `docs/track4/audits/size_consistency_audit.md`

## 2. 실행 방법

- 스크립트: `scripts/track4/audit_size_consistency.py`
- 출처별 크기 원본 컬럼을 읽어 표준 width/height/depth 후보를 생성함
- width/height 결측, 0 이하, 1000cm 초과, 초소형/초대형 면적, 극단 비율을 flag로 기록함
- depth가 있는 작품은 `has_depth`로 표시함
- depth가 짧은 변의 50% 이상이면 `is_3d_candidate`로 표시함

## 3. 사용한 크기 컬럼

- Saatchi: `saatchi__dimensions_cm`
- Artsy: `artsy__dimensions_cm`, `artsy__width_cm`, `artsy__height_cm`, `artsy__depth_cm`
- Artue: `artue__Width (cm)`, `artue__Height (cm)`, `artue__Depth (cm)`
- Gallery primary: `gallery_primary__size_raw`, `gallery_primary__width`, `gallery_primary__height`

## 4. 주요 결과

- 전체 행: `54,842`
- 크기 정상 후보: `54,441`
- 크기 이슈 후보: `401`
- width 결측: `97`
- height 결측: `93`
- aspect ratio 10 초과: `80`
- 면적 10cm2 미만: `31`
- 면적 1,000,000cm2 초과: `33`
- depth 100cm 초과: `176`
- width 1000cm 초과: `36`
- height 1000cm 초과: `39`

## 5. 출처별 결과

| 출처 | 전체 | 정상 | 이슈 | 면적 중앙값 | 면적 최대 | depth 있음 | 3D 후보 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Artsy | `30,046` | `29,673` | `373` | `4,260` | `2,500,000,000` | `7,125` | `1,924` |
| Artue | `2,783` | `2,776` | `7` | `3,445` | `160,000` | `1,672` | `87` |
| Gallery primary | `292` | `291` | `1` | `5,071` | `420,000` | `0` | `0` |
| Saatchi | `21,721` | `21,701` | `20` | `3,595` | `162,709` | `21,721` | `41` |

## 6. 해석

- 대부분의 행은 width/height 기반 면적 피처를 만들 수 있음
- 원형 작품의 `diameter` 표기는 `width=height=diameter`로 처리하면 결측을 줄일 수 있음
- Artsy에 극단적인 크기값이 집중되어 있어 파싱 오류 또는 설치/대형 작품 후보 확인이 필요함
- Saatchi는 dimensions 문자열에 depth가 대부분 들어 있어 `has_depth`가 과하게 넓게 잡힐 수 있음
- depth는 곧바로 3D 확정값으로 쓰지 말고 `3D 후보` 또는 보조 피처로 관리하는 것이 안전함
- Gallery primary의 `unit` 컬럼은 에디션 정보가 들어가 있어 크기 단위로 사용하면 안 됨

## 7. 결론

- 채택: 크기 클렌징 규칙을 다음 단계 데이터 생성에 반영
- 제외 또는 검토 규칙:
  - width/height가 없으면 크기 기반 피처 생성 대상에서 제외
  - width/height가 0 이하이면 기본 학습 후보에서 제외
  - `area_cm2 < 10`이면 기본 학습 후보에서 제외
  - `area_cm2 > 1,000,000`이면 기본 학습 후보에서 제외하고 초대형 별도 검토
  - width/height/depth가 1000cm 초과이면 수동 검토 후보로 관리
- 유지 규칙:
  - `aspect_ratio > 10`은 즉시 제외하지 않고 `is_extreme_aspect_ratio` flag로 관리
  - `depth_cm > 0`은 `has_depth`로 관리
  - depth가 짧은 변의 50% 이상이면 `is_3d_candidate`로 관리

## 8. 다음 작업

- `T4-C4` 작가명 정합성 감사 진행
- 이후 `cleaned_v2` 생성 시 크기 규칙을 코드로 고정
- `is_extreme_aspect_ratio`, `is_3d_candidate`, `size_outlier_flag`가 성능에 미치는 영향은 피처 실험에서 검증
