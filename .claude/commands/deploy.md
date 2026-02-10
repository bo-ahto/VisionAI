# Model Deployment Checklist

모델 배포 준비 상태를 점검하고 배포 아티팩트를 생성한다.

## Checklist

### 1. 모델 준비
- [ ] 최종 모델 체크포인트 선정
- [ ] 모델 성능 메트릭 확인 (threshold 충족)
- [ ] ONNX 또는 TorchScript 변환
- [ ] 변환 후 정확도 검증 (원본 대비)

### 2. 추론 코드
- [ ] 추론 파이프라인 코드 정리
- [ ] 배치/단일 추론 지원
- [ ] 입력 검증 및 에러 핸들링
- [ ] 타입 힌트 및 docstring 완비

### 3. 의존성
- [ ] 최소 의존성 목록 확인
- [ ] Python 버전 호환성 확인
- [ ] GPU/CPU 호환성 확인

### 4. 테스트
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 엣지 케이스 테스트 (빈 입력, 잘못된 형식)
- [ ] 성능 벤치마크 (latency, throughput)

### 5. 문서화
- [ ] API 인터페이스 문서
- [ ] 모델 카드 (성능, 제한사항, 편향)
- [ ] 배포 가이드

## Usage
```
/project:deploy $ARGUMENTS
```
`$ARGUMENTS`에 배포 대상 모델 또는 환경 (staging/production)을 전달한다.
