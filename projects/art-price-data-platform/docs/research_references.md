# Research References

이 제품 repo는 `VisionAI` 연구/실험 repo에서 분리한다. 연구 산출물 전체를 복사하지 않고, 제품 구현에 필요한 기준 문서, 작은 seed/fixture, 선택 모델 manifest만 가져온다.

## Source

| 항목 | 값 |
|---|---|
| source repo | `/Users/bo/VisionAI` |
| source branch | `exp/track6-price-prediction` |
| source commit at split | `e3006fb8e2d401e39656cdc7c92541cc1cd74416` |

## Reference Policy

- `data/track6*`, `experiments/track6*`, 대용량 `models/track6*` 산출물은 새 repo에 직접 복사하지 않는다.
- 모델/데이터 산출물은 object storage 또는 artifact registry에 저장하고, Git에는 `artifact_uri`, `sha256`, `model_card`, `source_commit`만 남긴다.
- 새 repo 코드/route/image/fixture 경로에는 과거 실험 트랙명을 새 이름으로 사용하지 않는다.
- 연구 결과가 제품 구현 근거가 될 때는 해당 VisionAI path와 commit을 이 문서 또는 model manifest에 남긴다.

## Initial References

| 용도 | VisionAI 기준 |
|---|---|
| Warm M1/D3-D4 후보 | `models/track6/warm_lite_unified_current_joblib_v0.1_candidate` |
| Cold M1/D3-D4 후보 | `models/track6/cold_v03_research_upstream_refreeze_candidate` 및 `cold_k80_conservative_official_v0.1_candidate` freeze 산출물 |
| 과거 cold 참고 산출물 | `models/track6/cold_prediction_v0.5_operational` |
| NANT seed | `projects/art-price-data-platform/docs/k-artmarket 1차 데이터 정제 - 실험데이터분류(데이터 수정).csv` |
