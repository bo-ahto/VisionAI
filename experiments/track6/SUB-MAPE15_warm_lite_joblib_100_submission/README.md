# 가격 예측 모델 100건 제출 패키지

생성 시각: `2026-06-22T13:15:55`

이 폴더는 가격 예측 모델 성능 평가를 위해 학습에 활용되지 않은 작품 100건 시험 데이터,
정답 라벨, 모델 번들, 실행 스크립트, 결과 문서를 포함한다.

## 성능 결과

| n | MdAPE | MAPE | p95 APE | RMSE log | 목표 |
|---:|---:|---:|---:|---:|---|
| 100 | 0.018259 | 0.046893 | 0.164429 | 0.113631 | MAPE 15% 이하 |

## 실행 명령

```bash
pip install -r requirements.txt
python3 scripts/01_check_test_data_not_trained.py
python3 scripts/02_run_price_mape_test.py
```

## 문서

- `reports/05_test_tools.md`
- `reports/06_client_supplied_data_script_terms.md`
- `reports/07_test_criteria_procedure.md`
- `outputs/train_test_leakage_audit.json`
