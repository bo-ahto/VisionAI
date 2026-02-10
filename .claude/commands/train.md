# Model Training Workflow

모델 학습 워크플로우를 실행한다. 학습 설정 검증부터 체크포인트 저장까지 전체 과정을 안내한다.

## Workflow Steps

1. **설정 검증**
   - 학습 config 파일 확인 (하이퍼파라미터, 경로)
   - GPU/CUDA 가용성 체크
   - 데이터셋 경로 및 무결성 확인

2. **환경 준비**
   - 의존성 확인 (`pip list` 대비 pyproject.toml)
   - W&B 또는 로깅 설정 확인
   - 시드 고정 상태 확인

3. **학습 실행**
   - 학습 스크립트 실행 명령 생성
   - 학습 진행 모니터링 방법 안내
   - OOM 발생 시 대응 전략 제공

4. **결과 검증**
   - 체크포인트 파일 확인
   - 학습 로그 분석 (loss curve, metrics)
   - 최적 체크포인트 식별

## Usage
```
/project:train $ARGUMENTS
```
`$ARGUMENTS`에 학습 대상 모델 또는 config 경로를 전달한다.
