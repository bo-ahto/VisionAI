# Track6 이미지 멀티모달 실험 투두 리스트

- 목적: 작품 이미지 정보를 정형 피처와 결합해 가격 예측 정확도를 개선할 수 있는지 검증한다.
- 배경: `Deep Learning for Art Market Valuation` 계열 접근은 작품 이미지 임베딩과 작가/작품 정형 피처를 함께 사용한다.
- 우선순위: Cold 성능 개선 가능성 확인을 1순위로 둔다.
- 이유: Cold는 작가 판매 이력이 부족해, 크기/재료/작가 메타만으로 설명되지 않는 시각적 차이가 남을 가능성이 크다.

## 1. 진행 순서

| 순서 | 상태 | 작업 | 산출물 | 판단 기준 |
|---|---|---|---|---|
| 1 | 완료 | Track6 이미지 URL 커버리지 확인 | `track6_image_multimodal_readiness_report.md` | split별 이미지 URL 보유율 확인 |
| 2 | 완료 | 기존 이미지 임베딩 재사용 가능성 확인 | `track6_existing_embedding_audit.json` | Track6 row와 직접 매칭되는 키 존재 여부 확인 |
| 3 | 완료 | Track6 이미지 매니페스트 생성 | `track6_image_manifest.csv` | `_track6_row_id` 기준 이미지 실험 입력표 생성 |
| 4 | 완료 | 이미지 URL 샘플 다운로드 검증 | `track6_image_url_health_sample.csv` | Saatchi/Artsy 샘플 다운로드 성공률 확인 |
| 5 | 완료 | Track6 전용 CLIP 임베딩 추출 파일럿 | `track6_clip_pilot_embeddings.npy`, `track6_clip_pilot_index.csv` | `_track6_row_id`와 임베딩 1:1 매칭 확인 |
| 6 | 파일럿 완료 | Cold 이미지 단독 모델 실험 | `IMG-P1`, `IMG-P2`, `IMG-P3` metrics | 이미지 단독은 MdAPE 기준으로 약함 |
| 7 | 전체 확장 완료 | Cold 정형 피처 + 이미지 결합 실험 | `IMG-P1`, `IMG-P2`, `IMG-P3`, `IMG-P4` metrics | test MAPE/p95 개선 신호는 있으나 IMG-P4 validation 악화 확인 |
| 8 | 대기 | 이미지 없는 샘플 fallback 정책 실험 | missing-image fallback metrics | 이미지 없는 행에서 기존 정형 모델로 안정적으로 대체되는지 확인 |
| 9 | 대기 | Warm 확장 실험 | Warm image-combo metrics | Warm에서도 이미지 결합이 과적합 없이 개선되는지 확인 |
| 10 | 대기 | 최종 보고서화 | 모델/피처/이미지 결합 해석 보고서 | 상사용 보고서에 쓸 근거 정리 |

## 2. 현재까지 확인된 사실

- Track6 전체 행 수: 33,892건.
- 이미지 URL 보유 행 수: 30,946건.
- 전체 이미지 URL 보유율: 약 91.3%.
- Cold test 이미지 URL 보유율: 약 93.2%.
- Warm test 이미지 URL 보유율: 약 87.0%.
- Saatchi/Artsy 이미지 URL 샘플 다운로드 성공률: 100%.
- Artue/Gallery Primary는 현재 split 기준 이미지 URL이 없어 이미지 임베딩 실험에서는 fallback 대상임.
- Track6 전용 CLIP 파일럿 임베딩: 6건 모두 성공.
- 파일럿 임베딩 shape: `(6, 512)`.
- Cold 600건 파일럿 임베딩: 600/600 성공.
- Cold train 확장 파일럿 임베딩: 1,400건 대상 중 1,392건 성공, 8건 실패.
- Cold train 2,000건 확장 파일럿 임베딩: 2,800건 대상 중 2,788건 성공, 12건 실패.
- Cold 전체 이미지 가능 임베딩: 29,970건 대상 중 29,788건 성공, 182건 실패.
- IMG-P1 결과: train 200건 기준 정형+CLIP PCA32가 샘플 정형 기준보다 validation/test 모두 개선.
- IMG-P2 결과: train 992건 기준 정형+CLIP PCA16/32가 샘플 정형 기준보다 개선.
- IMG-P3 결과: test에서는 정형+CLIP PCA32가 샘플 정형 기준보다 MdAPE/MAPE/p95_APE를 개선했지만, validation에서는 정형 기준보다 악화됨.
- IMG-P4 결과: 전체 이미지 가능 표본에서 test MAPE/p95_APE 개선은 유지됐지만 validation에서는 정형 기준보다 악화됨.
- 따라서 이미지 결합은 가능성이 있지만, 기본 모델 채택보다 tail 오차 방어/잔차 보정/조건부 적용 후보로 보는 것이 적절함.
- 기존 CLIP/ResNet 임베딩 파일은 존재함.
- 기존 임베딩 인덱스는 `idx` 기준임.
- Track6 기준 키는 `_track6_row_id`, `image_url`, `artwork_url`임.
- 따라서 기존 임베딩은 숫자 overlap이 있어도 Track6 작품과 직접 연결하면 안 됨.
- 안전한 방향은 Track6 전용 이미지 임베딩을 새로 생성하는 것임.

## 3. 실험 설계 원칙

- 학습/검증/테스트 split은 기존 Track6 고정 split을 그대로 사용.
- test 결과를 보고 임베딩 차원, 모델, 결합 가중치를 다시 고르지 않음.
- 이미지 URL이 없는 샘플은 별도 결측 flag를 두고 정형 피처 모델로 fallback.
- 이미지 출처별 편향을 확인하기 위해 Saatchi/Artsy/Artue/Gallery Primary를 분리 기록.
- 이미지 임베딩은 원본 이미지를 서비스에 저장하거나 노출하지 않고, 수치 벡터만 실험에 사용.
- Cold에서 개선이 확인된 뒤 Warm으로 확장.

## 4. 1차 파일럿 실험 구성

| 실험 | 내용 | 기대 확인값 |
|---|---|---|
| IMG-P0 | 이미지 URL 다운로드 샘플 검증 | 출처별 다운로드 성공률, 실패 사유 |
| IMG-P1 | CLIP 이미지 임베딩 단독 + LightGBM/Ridge | 이미지 자체가 가격 신호를 갖는지 확인 |
| IMG-P2 | Cold 기존 정형 피처 + CLIP PCA 32 | 기존 Cold 모델 대비 개선 여부 확인 |
| IMG-P3 | Cold train 2,000건, validation/test 각 400건 기준 정형 피처 + CLIP PCA 16/32/64 | train 확대 후 개선 신호가 유지되는지 확인 |
| IMG-P4 | Cold 이미지 가능 전체 표본 기준 정형 피처 + CLIP PCA 16/32/64 | validation 기준으로 채택 가능한지 재검증 |
| IMG-P5 | 이미지 결측 fallback | 이미지 없는 샘플의 안정성 확인 |

## 5. 후속 확장 후보

- CLIP과 ResNet 임베딩 비교.
- PCA 차원 16/32/64/128 비교.
- Cold 전용 이미지 결합 모델과 Warm 전용 이미지 결합 모델 분리.
- 이미지 임베딩을 CatBoost에 직접 넣는 방식과 LightGBM에 넣는 방식 비교.
- 이미지 임베딩 기반 유사 작품 검색을 서비스 비교 표본 후보로 활용할 수 있는지 검토.
- 이미지 출처별 성능 차이 확인.
- 이미지가 가격 자체를 맞히는지, 아니면 출처/촬영 품질 같은 간접 신호를 학습하는지 점검.

## 6. 다음 작업

- `IMG-P0` 이미지 URL 샘플 다운로드 검증은 완료.
- Track6 전용 CLIP 임베딩 추출 스크립트 작성과 6건 파일럿은 완료.
- 캐시/이어하기 구조 보강은 완료.
- Cold Saatchi/Artsy 이미지 가능 전체 CLIP 임베딩 생성과 IMG-P4 재검증은 완료.
- 다음은 이미지 없는 행의 fallback 정책을 검증.
- 이후 CLIP 단순 결합 대신 residual 보정, 신뢰도 보정, 조건부 적용 구간 탐색으로 전환.
