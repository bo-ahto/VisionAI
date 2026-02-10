# Model Evaluation & Metrics Report

모델 평가를 수행하고 메트릭 리포트를 생성한다.

## Workflow Steps

1. **모델 로드**
   - 체크포인트 경로 확인 및 로드
   - 모델 아키텍처와 가중치 매칭 검증

2. **평가 데이터 준비**
   - 테스트/검증 데이터셋 로드
   - 전처리 파이프라인 적용

3. **추론 실행**
   - 배치 추론 수행
   - 예측 결과 수집

4. **메트릭 계산**
   - Task별 메트릭: Accuracy, Precision, Recall, F1, mAP
   - Confusion matrix 생성
   - 클래스별 성능 분석

5. **리포트 생성**
   - 정량적 메트릭 요약 테이블
   - 시각화 (PR curve, ROC curve, 예측 샘플)
   - 개선 제안 사항

## Usage
```
/project:eval $ARGUMENTS
```
`$ARGUMENTS`에 모델 체크포인트 경로 또는 평가 config를 전달한다.
