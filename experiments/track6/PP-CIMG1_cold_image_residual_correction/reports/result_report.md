# PP-CIMG1 Cold 이미지 residual 보정

- 이미지 커버리지: validation 0.921 / test 0.931 (미커버 행 보정 0)

## 신호 예측력 감사 (validation OOF, 작가 경계 일반화)

{
 "research": {
  "oof_corr_pred_vs_actual_residual": 0.08293787844707164,
  "corr_std_over_resid_std": 0.4178221470510678
 },
 "operational": {
  "oof_corr_pred_vs_actual_residual": 0.06005828703703987,
  "corr_std_over_resid_std": 0.39009792236269697
 }
}

## validation OOF 상위 후보

{
 "research": [],
 "operational": []
}

## artist 반복 holdout 게이트

(OOF 통과 후보 없음)

## fixed test 최종 확인

     target candidate    MdAPE    MAPE  p95_APE
   research      base 0.409820 0.84926 2.346465
operational      base 0.485162 1.17712 4.122299