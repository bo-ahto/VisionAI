# Warm joblib high-confidence MAPE15 submission

이 폴더는 `models/track6/warm_lite_unified_current_joblib_v0.1_candidate` 모델을 기준으로 만든 제출용 고신뢰 Warm 평가 패키지다.

실행:

```bash
MPLCONFIGDIR=/private/tmp python3 scripts/track6/build_warm_joblib_high_confidence_submission.py
```

주요 결과는 `reports/result_report.md`와 `outputs/warm_joblib_submission_metrics.json`에서 확인한다.

패키지 내부 모델과 테스트 데이터를 이용해 다시 검증:

```bash
MPLCONFIGDIR=/private/tmp python3 experiments/track6/SUB-MAPE15_warm_lite_joblib_high_confidence_submission/scripts/run_high_confidence_test.py
```
