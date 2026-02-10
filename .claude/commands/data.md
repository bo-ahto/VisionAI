# Dataset Preparation & Validation

데이터셋 준비, 검증, 분석 워크플로우를 실행한다.

## Workflow Steps

1. **데이터 탐색**
   - 데이터 소스 확인 (경로, 형식, 크기)
   - 샘플 데이터 시각화
   - 파일 형식 및 인코딩 검증

2. **품질 검증**
   - 누락/손상 파일 탐지
   - 라벨 일관성 검사
   - 클래스 분포 분석 (불균형 탐지)
   - 이상치 탐지

3. **전처리 파이프라인**
   - 리사이즈, 정규화, 포맷 변환
   - Train/Val/Test 분할
   - Augmentation 전략 설계

4. **통계 리포트**
   - 데이터셋 크기, 클래스 수, 이미지 해상도 분포
   - 클래스별 샘플 수 히스토그램
   - 데이터 품질 스코어

## Usage
```
/project:data $ARGUMENTS
```
`$ARGUMENTS`에 데이터셋 경로 또는 작업 유형 (prepare/validate/analyze)을 전달한다.
