# Track6 dataset handover

- 작성일: 2026-06-19
- 목적: 가격 예측 모델 학습/검증/테스트 데이터셋 생성 흐름과 frozen 기준을 다른 팀원이 추적/재현할 수 있게 정리
- 범위: 원본 소스 -> 정제/보정 코드 -> Track6 split/features/labels -> 모델 번들 frozen split

## 바로 볼 파일

1. `01_source_to_final_dataset_lineage.md`
   - 전체 데이터셋 생성 흐름
   - 원본 소스, 실행 코드, 중간 산출물, 최종 산출물 매핑
2. `02_koreanization_and_homonym_handling.md`
   - 한글화 처리와 split 전 동명이인 표시/차단 기준
3. `03_reproduction_commands.md`
   - 재현 실행 순서
   - 실행 전 확인해야 할 입력 파일
4. `dataset_lineage_manifest.csv`
   - 단계별 source/code/output을 표 형태로 정리

## 핵심 결론

- 1차 원본은 `data/saatchi_cleaned.csv`, `data/artsy_kr_artworks.csv`, `data/artue_테스트_가격포함.csv`, `data/1차 시장 데이터 - 전달본_260504.csv`이다.
- Track4 파이프라인이 이 원본들을 raw 통합, 가격/크기/작가/재료/중복 감사, cleaned_v2, feature 후보로 만든다.
- Track6는 Track4 feature 후보에 한글명 수동 보정과 작가 메타 보강을 적용한 뒤 split을 새로 생성한다.
- `data/track6_split/`은 split 생성 스크립트의 작업용 산출물이다.
- Track6 모델 학습/평가에 실제 사용한 기준 데이터셋은 모델 번들 내부 frozen copy인 `models/track6/price_prediction_v0.1/data/training/track6_split/`이다.
- 특정 시점의 `data/track6_split/`을 모델 번들로 복사해 frozen split으로 고정한 뒤, 이후 성능표와 재현 검증은 이 frozen split을 기준으로 한다.
- Cold feature 파일은 `artist_key`, 같은 작가 train 이력 수를 제거해 같은 작가 이력 누수를 차단한다.
- 운영/API 연결 단계는 이 인수인계 범위에서 제외한다.
