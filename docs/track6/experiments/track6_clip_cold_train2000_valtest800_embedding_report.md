# Track6 CLIP 임베딩 파일럿 결과

- 생성 시각: 2026-06-04 04:10:31
- 목적: Track6 `_track6_row_id` 기준으로 이미지 임베딩을 생성할 수 있는지 확인한다.
- 대상 split: `train, val_cold, test_cold`
- 대상 출처: `saatchi, artsy`
- split/출처별 샘플 수 설정: `{'default_per_split_source': 200, 'train': 1000, 'val_cold': 200, 'test_cold': 200, 'val_warm': 200, 'test_warm': 200}`
- 모델: `ViT-B-32` / pretrained `openai`
- 실행 장치: `mps`

## 결과

- 대상 이미지 수: 2800
- 성공 이미지 수: 2788
- 실패 이미지 수: 12
- 성공률: 0.9957
- 임베딩 shape: `(2788, 512)`
- 임베딩 파일: `data/track6/image_multimodal/track6_clip_cold_train2000_valtest800_embeddings.npy`
- 인덱스 파일: `data/track6/image_multimodal/track6_clip_cold_train2000_valtest800_index.csv`
- 실패 파일: `data/track6/image_multimodal/track6_clip_cold_train2000_valtest800_failures.csv`

## 해석

- 이 파일럿이 성공하면 전체 Track6 이미지 임베딩 추출로 확장할 수 있다.
- 인덱스 파일에 `_track6_row_id`가 남기 때문에 기존 `idx` 기반 임베딩보다 안전하게 split 데이터와 결합할 수 있다.
- 다음 단계는 Cold 기준 이미지 단독 모델과 정형 피처 + 이미지 결합 모델을 비교하는 것이다.
