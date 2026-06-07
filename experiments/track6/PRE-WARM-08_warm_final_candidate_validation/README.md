# Track6 PRE-WARM-08 Warm 최종 후보 validation/OOF 비교

- 목적: PRE-WARM-07에서 남긴 Warm 후보를 validation, test, train OOF 기준으로 비교하여 후처리 기준 Warm 모델 후보를 확정한다.
- 결과 HTML: `outputs/result_sheet.html`
- 결과 CSV: `outputs/result_sheet.csv`
- 예측 CSV: `outputs/predictions.csv`

## Validation 순위

| 순위 | 후보 | 운영성 | MdAPE | p95_APE | RMSE_log |
|---:|---|---|---:|---:|---:|
| 1 | `PRE-WARM-08A: final artifact base_existing_combo` | `current_artifact_compatible` | `0.2124` | `1.3191` | `0.6445` |
| 2 | `PRE-WARM-08D: compact artist_key size + ho interaction` | `artist_key_compatible` | `0.2260` | `1.4768` | `0.6718` |
| 3 | `PRE-WARM-08C: compact artist_name size + artist works` | `requires_artist_name_ko_feature_export` | `0.2299` | `1.4667` | `0.6727` |
| 4 | `PRE-WARM-08B: compact artist_name size + artist works no aspect` | `requires_artist_name_ko_feature_export` | `0.2305` | `1.4835` | `0.6732` |

## Test 순위

| 순위 | 후보 | MdAPE | p95_APE | RMSE_log |
|---:|---|---:|---:|---:|
| 1 | `PRE-WARM-08B: compact artist_name size + artist works no aspect` | `0.2208` | `1.9234` | `0.6229` |
| 2 | `PRE-WARM-08C: compact artist_name size + artist works` | `0.2221` | `1.9218` | `0.6233` |
| 3 | `PRE-WARM-08D: compact artist_key size + ho interaction` | `0.2271` | `1.8977` | `0.6239` |
| 4 | `PRE-WARM-08A: final artifact base_existing_combo` | `0.2274` | `2.0128` | `0.6091` |

## OOF 순위

| 순위 | 후보 | MdAPE | p95_APE | RMSE_log |
|---:|---|---:|---:|---:|
| 1 | `PRE-WARM-08D: compact artist_key size + ho interaction` | `0.1834` | `1.2608` | `0.6026` |
| 2 | `PRE-WARM-08A: final artifact base_existing_combo` | `0.1942` | `1.2478` | `0.5854` |
| 3 | `PRE-WARM-08C: compact artist_name size + artist works` | `0.1981` | `1.3207` | `0.6055` |
| 4 | `PRE-WARM-08B: compact artist_name size + artist works no aspect` | `0.1987` | `1.3162` | `0.6060` |

## 데이터 정합성 메모

- `train`: label metadata에서 보강한 컬럼 = `-`
- `validation`: label metadata에서 보강한 컬럼 = `artist_name_ko`
- `test`: label metadata에서 보강한 컬럼 = `-`

## 판단

- 최종 판단은 validation MdAPE를 우선한다.
- test 결과는 기존 관측 성능이 유지되는지 확인하는 보조 근거로만 사용한다.
- `artist_name_ko` 후보가 채택되려면 validation/test feature export에 `artist_name_ko`를 명시적으로 포함하도록 데이터 파이프라인을 수정해야 한다.
- 운영 정합성을 우선하면 `artist_key` 기반 후보를 별도 최종 후보로 유지한다.

## 최종 해석

- validation 기준 1위는 현재 final artifact와 호환되는 `PRE-WARM-08A: final artifact base_existing_combo`다.
- test 기준 1위는 `PRE-WARM-08B: compact artist_name size + artist works no aspect`지만, validation에서는 4위다.
- OOF MdAPE 기준 1위는 `PRE-WARM-08D: compact artist_key size + ho interaction`이고, OOF p95/RMSE_log 기준으로는 `PRE-WARM-08A`가 안정적이다.
- 따라서 test 성능만 보고 Warm 기준 모델을 compact `artist_name_ko` 후보로 교체하는 것은 위험하다.
- 현재 후처리 실험의 기준 모델은 `PRE-WARM-08A`를 유지하는 것이 가장 보수적이다.
- 단, `PRE-WARM-08D`는 운영용 `artist_key`를 사용하면서 OOF MdAPE와 test p95가 좋아 tail 안정성 후보로 유지한다.
- `PRE-WARM-08B/C`는 test MdAPE가 좋지만 validation feature 파일에 `artist_name_ko`가 없어 feature export 정합성 수정 전에는 최종 운영 후보로 확정하지 않는다.

## 후처리 기준 결정

- Warm 기본 후처리 기준 모델: `PRE-WARM-08A: final artifact base_existing_combo`
- Warm 보조 비교 후보: `PRE-WARM-08D: compact artist_key size + ho interaction`
- 보류 후보: `PRE-WARM-08B/C`
  - 이유: test 성능은 좋지만 validation 성능이 낮고 `artist_name_ko` feature export 정합성 수정이 필요함
- PP-A1-W는 `PRE-WARM-08A` 기준으로 우선 실행한다.
- PP-A3-W 크기 구간 보정은 `PRE-WARM-08A`와 `PRE-WARM-08D` 모두에서 비교한다.
- PP-A5-W 작가 학습량 보정은 `artist_works_log`를 쓰는 `PRE-WARM-08B/C`를 바로 채택하기보다, `PRE-WARM-08A` 기준의 slice 분석으로 먼저 확인한다.

## 추가 보완 필요

- Huber 일부 OOF fold에서 `max_iter=3000` 수렴 경고가 발생했다.
- 최종 artifact를 다시 빌드하기 전 `max_iter=3000/5000/8000` 민감도 실험을 권장한다.
- `artist_name_ko` 후보를 계속 검토하려면 validation/test warm feature export에 `artist_name_ko`를 명시적으로 포함하도록 split feature 생성 파이프라인을 수정해야 한다.
