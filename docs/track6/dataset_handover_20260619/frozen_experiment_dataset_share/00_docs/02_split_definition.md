# Track6 split 정의

## 1. train

`track6_train.csv`는 모델 학습에 사용하는 데이터다.

주요 조건:

- 가격 label이 있음
- 작가 식별 정보가 있음
- 크기, 면적, 로그 면적 등 기본 작품 피처가 있음
- 학습 후보로 통과한 row
- validation/test로 빠진 작품과 동일 작품으로 볼 수 있는 중복 후보는 제거

## 2. Warm validation/test

Warm 평가는 같은 작가의 과거 가격 이력을 사용할 수 있는 상황을 평가한다.

기존 실험의 Stable Warm 기준:

- 평가 작품의 작가가 train에 존재
- 평가 작품을 제외하고도 train 안에 같은 작가 작품이 최소 5건 이상 남음
- 평가 작품은 train에 직접 들어가지 않음

따라서 Warm 성능은 “같은 작가의 과거 가격 이력을 사용할 수 있는 입력”에 대한 성능이다.

## 3. Cold validation/test

Cold 평가는 같은 작가 가격 이력을 직접 사용할 수 없는 상황을 평가한다.

기존 실험의 Cold 기준:

- 평가 작가의 `artist_key`가 train에 없음
- 평가 작가의 `artist_name_ko`가 train에 없음
- 평가 작가의 `artist_name_ko_orig`가 train에 없음
- split 이후 `artist_works_log > 0`인 Cold row가 없어야 함

이 기준은 같은 작가 이력이 Cold feature로 새어 들어가는 것을 막기 위한 것이다.

## 4. Warm과 Cold를 같은 표에서 볼 때 주의점

Warm과 Cold는 같은 난이도의 문제가 아니다.

- Warm은 같은 작가의 과거 가격 이력을 사용할 수 있다.
- Cold는 같은 작가 가격 이력을 직접 사용할 수 없다.

따라서 Warm과 Cold의 성능 수치는 “전체 모델이 각각의 입력 상황에서 어느 정도 동작하는지”를 보여주는 값이지, 두 경로를 단순 우열 비교하는 값은 아니다.

## 5. feature/label 파일 관계

각 split CSV는 작품의 원본 추적 컬럼과 모델 후보 컬럼을 함께 가진 full split 파일이다.

모델 학습/평가에서는 여기서 feature와 label을 분리해 사용한다.

```text
features/warm/
features/cold/
labels/
```

label 파일은 실제 가격과 로그 가격을 담는다.

feature 파일은 Warm/Cold 경로별로 사용할 수 있는 입력 컬럼만 담는다.
