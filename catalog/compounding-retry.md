# AP-5: Compounding Retry

## Shape
Multiple independent retry mechanisms exist for the same operation path. Each layer retries independently, multiplying total attempts: 3 app retries x 3 queue retries = 9 attempts instead of 3.

## Detection
Run failure-mode checklist step 5 (retry amplification). Count how many layers can retry the same logical operation. If more than one, check whether they're for genuinely different failure modes or overlapping.

## Symptoms
- Operation executes far more times than the configured retry count
- Recovering service gets hammered by compounded retries
- Retry logs show nested retry patterns (retry-within-retry)

## Fix
Assign retry responsibility to exactly one layer per failure class. Other layers should fail-fast or propagate. If multiple layers must retry, ensure they cover strictly different failure modes (e.g., pre-dispatch queue retries vs post-dispatch application retries) and document the boundary between them.
