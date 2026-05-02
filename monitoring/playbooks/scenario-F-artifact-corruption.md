# Scenario F — artifact corruption / version skew

**Severity**: manual (no auto-trigger — fail-closed primary defense)
**Trigger**: 없음 (Grafana 만 — Panel 11 `artifact_version_consistency`).
**Spec**: `docs/v3_5_step4_drift_monitoring.md` §5.6 (코덱스 P1 fix)

## Primary defense (fail-closed)

서버 startup 시 predictor 가 5-file bundle + `model_target` 검증. mismatch 면
RuntimeError → instance 시작 X → LB 자동 제외. 이 동작 자체가 **1차 방어선**.

따라서 이 playbook 이 trigger 되는 case 는:
- fail-closed 우회된 경우 (예: artifact 가 syntactically valid 지만 의미상 corrupt)
- multi-instance 간 artifact_version skew (일부 instance 만 새 artifact 받음)

## Detection signals

- dashboard Panel 11 (artifact_version_consistency): `distinct_artifact_versions > 1`
  안에서 worker 별 row 노출.
- dashboard Panel 10 (model_variant_distribution): 의도와 다른 % (예: rollout 5%
  인데 25% traffic 의 v3.5 variant — deploy bug).
- Panel 12 (cache_epoch_age) — 한 server_instance 의 cache_epoch + artifact_version
  불일치 (이전 deploy 의 artifact 그대로 남음).

## Immediate action (수동)

자동 trigger 없음 — **operator 가 dashboard 모니터링 중 발견**.

1. Panel 11 에서 mismatch instance 식별 (server_instance / worker_instance_id).
2. 그 instance 즉시 LB 제거 (drain):
   ```bash
   kubectl drain <node> --ignore-daemonsets
   # 또는 ALB target group 에서 instance deregister
   ```
3. 정상 instance 만으로 트래픽 처리.

## Diagnosis

**1. instance 별 artifact 검증**:
```bash
for pod in $(kubectl get pods -l app=visionai-api -o name); do
    kubectl exec $pod -- sha256sum /app/models/integrated_v3_5_v_year_saatchi_warm_*.{cbm,json}
done
```

mismatch sha256 → 그 instance 의 artifact 가 corrupt 또는 outdated.

**2. predict_logs 의 분포**:
```sql
-- 최근 1h 의 artifact_version 별 traffic share
SELECT artifact_version, server_instance, worker_instance_id,
       COUNT(*) AS n, MIN(timestamp), MAX(timestamp)
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1, 2, 3
ORDER BY 1, 2;
```

3개 이상 distinct artifact_version 보이면 deploy 중 race / partial rollout.

**3. MODEL_VARIANT env 확인**:
```bash
for pod in $(kubectl get pods -l app=visionai-api -o name); do
    kubectl exec $pod -- printenv MODEL_VARIANT
done
```

MODEL_VARIANT 와 실제 load 된 model_target JSON 의 mismatch 가능성. fail-closed
가 동작했으면 instance 시작 X 였어야 함 — 만약 active 상태면 startup 검증 누락
가능성 (predictor.load_models 의 model_target 검증 logic 점검).

## Remediation

1. **mismatch instance drain** + 정상 instance 만으로 트래픽.
2. **재배포**: 정확한 artifact 로 통일 (deploy tool 의 atomic rollout 정책 검토).
3. **deploy tool 의 partial rollout 차단**: Argo CD / Spinnaker 의 wave 단위
   atomic 전환 강제.
4. cache_epoch + artifact_version 불일치 — instance restart 자동 trigger 가
   해결 (cache_epoch 갱신).

## Resolution

- Panel 11 의 mismatch row 0건.
- Panel 10 의 model_variant 분포가 rollout 정책 (5% 또는 1%) 와 일치.
- 모든 instance 의 sha256 동일.

## Post-mortem (필수)

1. **deploy tool 의 atomic rollout 정책**: instance 별 partial rollout 가능성
   차단.
2. **MODEL_VARIANT env 와 model_target 일치 자동화**: build pipeline 이 두
   값을 함께 빌드.
3. **artifact pinning**: artifact registry 의 immutable tag (sha256-based)
   사용 여부 검토.
4. **fail-closed 의 우회 경로 확인**: predictor.load_models 가 어떤 corner case
   에서 invalid artifact 를 통과시켰는지.
