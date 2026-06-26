# 모델 학습과 운영 모델 변경 수명주기

작성일: 2026-06-26

## 1. 문서 목적

이 문서는 가격 예측 모델을 새로 학습하거나 기존 joblib 모델 번들을 운영 모델로 교체할 때의 기준 절차를 정의한다.

수집, 표준화, NANT 분류, snapshot 생성은 모델 학습의 입력을 만드는 단계다. 모델 학습과 운영 모델 변경은 별도 단계이며, 새 snapshot이 승인되어도 운영 모델은 자동으로 바뀌지 않는다.

## 2. 핵심 결정

- 학습 입력은 `approved` snapshot의 parquet export만 사용한다.
- 수집 DB나 `normalized_*_staging`을 모델 학습 코드가 직접 읽지 않는다.
- 운영 route는 `warm`과 `cold`로 고정한다. routine training은 같은 route의 고정 model family를 새 snapshot/export로 다시 학습해 `model_version`만 올리는 작업이다.
- model family, 알고리즘, route 판단, feature contract, serving input/output contract를 바꾸는 일은 운영 학습이 아니라 별도 개발 작업으로 처리한다.
- 모델 학습 결과는 먼저 `candidate`로 등록한다.
- `candidate` 모델은 운영 배포할 수 없다.
- validation/test 검증, fixed-test parity, API smoke를 통과한 모델만 `approved`로 전환한다.
- `approved` 모델만 `price_model_deployment`의 active deployment가 될 수 있다.
- route별 active deployment는 1개만 허용한다.
- 롤백을 위해 직전 active 모델 artifact와 feature store는 삭제하지 않는다.

M1 최초 연결은 재학습 자동화가 아니라 기존 Warm joblib와 Cold k80 joblib 번들을 registry/deployment에 등록해 active deployment로 두는 방식이다. 이후 routine training job도 같은 Warm/Cold model family 안에서 성능이 더 좋은 버전을 만들고, 검증 후 model version을 올리는 절차만 담당한다.

## 3. 전체 흐름

```text
approved snapshot
  -> snapshot parquet export + manifest
  -> model_training_job 생성
  -> 고정된 Warm/Cold feature contract로 feature generation
  -> 같은 model family 재학습 및 train/validation/test 평가
  -> artifact/joblib bundle 생성
  -> price_model_registry(candidate) 등록
  -> 검증 gate 통과
  -> price_model_registry(approved) 전환
  -> price_model_deployment(promote)
  -> API smoke / prediction log 확인
  -> 운영 모니터링 또는 rollback
```

기존 joblib 모델을 가져오는 경우에는 학습 단계 대신 import job을 사용한다.

```text
approved snapshot 또는 기준 manifest
  -> imported joblib artifact 검증
  -> fixed-test parity
  -> price_model_registry(candidate) 등록
  -> approved 전환
  -> price_model_deployment(promote)
```

## 4. 단계별 기준

### 4.1 Snapshot 준비

모델 학습 또는 import 등록에는 아래 값이 필요하다.

| 항목 | 기준 |
|---|---|
| `training_snapshot_id` | 신규 학습은 `artwork_snapshot.status=approved`인 snapshot. 기존 legacy joblib import는 NULL 가능하되 `source_cutoff_at`과 import manifest 필수 |
| `snapshot_export_id` | parquet export와 manifest가 생성된 export ID |
| `source_cutoff_at` | snapshot 또는 import manifest의 원천 데이터 기준일 |
| `rules_version` | snapshot 생성에 사용한 정규화/필터 규칙 버전 |
| `nant_mapping_version_id` | snapshot에 적용된 NANT active mapping version |
| `feature_generation_version` | feature 생성 코드/규칙 버전 |

`generated` snapshot은 빌드가 끝났다는 뜻일 뿐이므로 신규 학습 입력으로 쓰지 않는다. 데이터 관리자가 서빙 승인해 `approved`가 된 snapshot만 신규 학습 입력으로 쓴다. 기존 legacy joblib import처럼 로컬 snapshot이 없는 경우에는 import manifest에 `source_cutoff_at`, 원 학습 데이터 설명, artifact hash를 기록한다.

### 4.2 Training job 생성

학습은 `model_training_job`으로 추적한다.

필수 입력:

- route: `warm`, `cold`
- training snapshot/export. legacy import는 source manifest
- training profile: 예: `warm_lite_joblib`, `cold_k80_conservative`
- model family: route별 고정 family. routine training에서 변경 금지
- feature generation version
- training code version 또는 git SHA
- baseline model version
- 요청자와 요청 사유

상태:

| 상태 | 의미 |
|---|---|
| `requested` | 학습 요청 생성 |
| `running` | 학습 실행 중 |
| `succeeded` | artifact와 평가 리포트 생성 완료 |
| `failed` | 학습 실패 |
| `cancelled` | 실행 전 또는 실행 중 취소 |

같은 `(route, training_snapshot_id, training_profile, feature_generation_version)` 조합은 중복 실행될 수 있으나, 각 job은 별도 `training_job_id`와 artifact hash를 가진다. 재실행은 덮어쓰지 않고 새 job으로 남긴다.

routine training에서 `route`, `model_family`, serving input/output schema를 바꾸면 안 된다. 이를 바꾸려면 별도 개발 ticket에서 feature/serving adapter/parity fixture를 함께 변경하고, 이 문서의 운영 학습 절차가 아니라 개발 배포 절차를 따른다.

### 4.3 Feature generation

feature 생성은 학습 job 안에서 snapshot parquet를 입력으로 수행한다.

반드시 기록할 값:

- feature column list
- feature schema hash
- 결측 처리 규칙
- NANT feature 사용 여부와 mapping version
- Warm/Cold route 판단 기준
- train/validation/test split id

routine training에서는 feature schema hash가 해당 route의 approved contract와 같아야 한다. feature schema hash가 바뀌면 같은 모델의 단순 버전업이 아니므로 candidate 승인 대상에서 제외하고, 별도 개발 작업으로 feature/serving contract 변경을 진행한다.

### 4.4 모델 학습 또는 import

새로 학습하는 경우:

- snapshot export를 읽어 feature를 만든다.
- train/validation/test split을 고정한다.
- 모델 artifact를 만든다.
- artifact URI, SHA-256, metrics JSON, evaluation report URI를 저장한다.

기존 joblib 번들을 import하는 경우:

- artifact URI와 SHA-256을 계산한다.
- model manifest 또는 model card를 등록한다.
- fixed-test parity를 돌린다.
- training job은 `training_profile=imported_joblib` 또는 동등한 import profile로 남긴다.

M1 기준:

- Warm: `warm_lite_unified_current_joblib_v0.1_candidate`
- Cold: `cold_k80_conservative_official_v0.1_candidate`
- 두 모델 모두 joblib smoke와 fixed-test parity를 통과해야 registry/deployment seed에 넣는다.

### 4.5 Candidate 등록

학습 또는 import가 성공하면 `price_model_registry`에 `candidate`로 등록한다.

등록 값:

- `model_version`
- `route`
- `model_family`
- `model_contract_version`
- `training_job_id`
- `training_snapshot_id`
- `snapshot_export_id`
- `feature_generation_version`
- `training_code_version`
- `artifact_uri`
- `artifact_sha256`
- `feature_schema_hash`
- `metrics_json`
- `gate_results_json`
- `parity_report_uri`

`candidate` 등록은 운영 반영이 아니다. 운영 API는 `candidate` 모델을 사용하지 않는다.

### 4.6 검증 gate

모델 승인 전 최소 검증:

| Gate | 목적 |
|---|---|
| data contract | snapshot/export/feature schema가 기대값과 맞는지 확인 |
| model family lock | route별 고정 model family와 serving contract가 유지되는지 확인 |
| validation/test metrics | 기준 성능이 baseline 대비 허용 범위인지 확인 |
| fixed-test parity | 기존 검증 fixture에서 예측 경로가 재현되는지 확인 |
| API smoke | serving adapter가 artifact를 로드하고 응답하는지 확인 |
| prediction log | `model_version`, `deployment_id`, `route` 기록이 남는지 확인 |
| rollback readiness | 직전 active deployment로 돌아갈 수 있는지 확인 |

검증 결과는 `gate_results_json`과 report URI에 남긴다. gate 실패 모델은 `rejected`로 전환하고 운영 배포하지 않는다.

### 4.7 모델 승인

데이터 관리자가 검증 리포트를 확인한 뒤 `candidate` 모델을 `approved` 또는 `rejected`로 전환한다.

승인 시 기록:

- 승인자
- 승인시각
- 승인 사유
- 주요 metric 요약
- baseline model version
- known limitation

`approved`는 "운영 배포 가능" 상태이지 "현재 운영 중" 상태가 아니다. 현재 운영 중 여부는 `price_model_deployment.deployment_status=active`만 기준으로 본다.

동일 route의 `approved` 전환은 같은 `model_family`와 `model_contract_version` 안에서의 버전업만 허용한다. 새 알고리즘, 새 route, 새 feature schema, 새 serving contract는 운영 승인으로 처리하지 않는다.

### 4.8 운영 승격

운영 승격은 `price_model_deployment`에서 처리한다.

승격 절차:

1. 대상 `model_version`이 `approved`인지 확인한다.
2. 같은 route의 현재 active deployment를 조회한다.
3. 같은 트랜잭션에서 기존 active를 `inactive`으로 전환한다.
4. 신규 active deployment row를 생성한다.
5. serving adapter가 새 artifact SHA-256을 검증하고 로드한다.
6. API smoke를 실행한다.
7. 예측 로그가 새 `deployment_id`로 남는지 확인한다.

승격 실패 시 신규 deployment는 active로 남기지 않는다. 이미 active가 바뀐 뒤 API smoke에서 실패하면 즉시 rollback action을 실행한다.

### 4.9 롤백

롤백은 이전에 검증된 `approved` 모델로 active deployment를 되돌리는 절차다.

롤백 조건 예:

- API smoke 실패
- 예측 응답 장애
- latency 급증
- 고정 fixture 예측값 이상
- 운영자가 확인한 가격 품질 이상

롤백도 새 deployment 이벤트로 남긴다. 과거 deployment row를 삭제하거나 덮어쓰지 않는다.

## 5. DB 구현 기준

### 5.1 model_training_job

| 컬럼 | 설명 |
|---|---|
| `training_job_id` | 학습 job PK |
| `route` | `warm`, `cold` |
| `job_status` | `requested`, `running`, `succeeded`, `failed`, `cancelled` |
| `training_profile` | 학습/import profile |
| `model_family` | route별 고정 model family. routine training에서는 변경 금지 |
| `model_contract_version` | serving input/output 및 feature contract 버전 |
| `training_snapshot_id` | 신규 학습에 사용할 approved snapshot. legacy import는 NULL 가능 |
| `snapshot_export_id` | parquet export ID |
| `source_cutoff_at` | snapshot 또는 import manifest의 원천 데이터 기준일 |
| `source_manifest_uri` | legacy import 또는 외부 artifact의 원 학습 데이터/모델 manifest |
| `baseline_model_version` | 비교 기준 모델 |
| `feature_generation_version` | feature 생성 버전 |
| `training_code_version` | 학습 코드 git SHA 또는 버전 |
| `requested_by` / `requested_at` | 요청자와 요청시각 |
| `started_at` / `finished_at` | 실행 시각 |
| `artifact_uri` | 생성/import된 artifact 위치 |
| `artifact_sha256` | artifact 무결성 hash |
| `feature_schema_hash` | feature schema hash |
| `metrics_json` | 학습/검증 지표 |
| `gate_results_json` | gate별 통과/실패 결과 |
| `resulting_model_version` | 성공 시 등록된 model version cache. registry 연결의 주 링크는 `price_model_registry.training_job_id` |
| `error_json` | 실패 사유 |

### 5.2 price_model_registry 보강

`price_model_registry`에는 `training_job_id`, `model_family`, `model_contract_version`, `feature_schema_hash`, `gate_results_json`, `registration_source`를 포함한다.

`registration_source` 값:

| 값 | 의미 |
|---|---|
| `training_job` | 내부 학습 job 결과 |
| `imported_joblib` | 외부/기존 joblib bundle import |
| `manual_seed` | 초기 seed 또는 migration 등록 |

### 5.3 price_model_deployment

기존 원칙을 유지한다.

- route별 active deployment는 1개
- active 전환은 트랜잭션으로 처리
- previous active는 `inactive` 또는 rollback 이력으로 보존
- 운영 모델 판단 기준은 registry가 아니라 deployment active row

## 6. API 구현 기준

필요 endpoint:

| Endpoint | 목적 | 권한 |
|---|---|---|
| `POST /api/v1/admin/model-training/jobs` | 학습/import job 생성 | 데이터 분석가 |
| `GET /api/v1/admin/model-training/jobs` | job 목록 조회 | 운영 담당자 |
| `GET /api/v1/admin/model-training/jobs/{training_job_id}` | job 상세/로그/리포트 조회 | 운영 담당자 |
| `POST /api/v1/admin/model-versions/{model_version}/decision` | candidate 승인/반려 | 데이터 관리자 |
| `POST /api/v1/admin/model-deployments` | approved 모델 승격/롤백/retire | 데이터 관리자 |
| `GET /api/v1/admin/model-deployments/current` | 현재 active deployment 확인 | 운영 담당자 |

## 7. 어드민 화면 기준

모델 운영 화면은 아래 영역을 포함한다.

- 현재 active deployment
- 학습/import job 목록과 상태
- candidate 모델 목록
- 모델 상세 metric/gate/parity report
- candidate 승인/반려 버튼
- approved 모델 승격 버튼
- rollback 대상 선택
- active deployment의 training snapshot 또는 import manifest cutoff/as_of 표시

## 8. 테스트 기준

필수 테스트:

- approved snapshot이 아닌 snapshot으로 training job 생성 불가
- succeeded job만 candidate model 등록 가능
- candidate 모델은 deployment promote 불가
- routine candidate의 `model_family` 또는 `feature_schema_hash`가 route contract와 다르면 approve 불가
- approved 모델만 promote 가능
- route별 active deployment 1개 제약
- promote 후 prediction log에 새 `deployment_id` 기록
- rollback 후 current deployment가 이전 모델로 돌아감
- artifact SHA-256 mismatch 시 serving adapter 로드 실패
- M1 Warm/Cold joblib smoke와 fixed-test parity 통과

## 9. 개발 범위

M1:

- 기존 Warm joblib와 Cold k80 joblib를 import/seed 방식으로 registry에 등록
- fixed-test parity와 serving smoke 통과
- active deployment seed 생성
- public prediction API가 active deployment 기준으로 응답
- prediction log에 `model_version`, `deployment_id`, `route` 기록

M2:

- admin에서 training/import job 생성
- candidate 승인/반려
- model operation 화면에서 metric/gate/parity report 확인
- 운영 승격/롤백 전체 UI 제공

범위 밖:

- Warm/Cold 외 route 추가
- model family/알고리즘 교체
- feature schema 변경
- serving adapter 입출력 계약 변경

위 항목은 운영 학습이 아니라 별도 개발 작업으로 처리한다.

후속 고도화:

- 주기적 자동 재학습
- 자동 challenger 비교
- canary 트래픽 분리
- 성능 임계 자동 rollback
