# Track 4 데이터 산출물 구조

- 목적: Track 4 모델 실험 결과와 재사용 산출물을 폴더 기준으로 분리
- 주의: 대용량 CSV/JSON은 `.gitignore` 정책상 기본적으로 커밋하지 않음

## 폴더 역할

- `results/`
- 모델 실험별 결과 JSON/CSV 저장
- 예: `T4-E022_baseline_metrics.json`

- `models/`
- 실험용 모델 파일 저장
- 배포 후보가 되기 전까지는 로컬 산출물로 관리

- `predictions/`
- validation/test 예측 결과 저장

- `figures/`
- 실험 설명용 차트나 이미지 저장

## 현재 기준 원천 산출물

- 현재 클렌징/감사/split CSV는 기존 파이프라인 호환성을 위해 `data/track4_*.csv`, `data/track4_split/`에 유지함
- 모델 실험 결과부터는 `data/track4/results/` 하위에 저장함
