# Incident Report: Disk Space Exhaustion — prod-web-03

**Incident ID:** INC-001
**Date:** 2024-01-15
**Severity:** Critical
**Duration:** 2 hours 3 minutes (03:22 UTC — 05:25 UTC)
**Status:** Resolved

## Executive Summary

A deployment of checkout-api v2.14.3 on January 14 left debug logging enabled in production, generating approximately 50GB/hour of verbose SQL query logs. This filled the /var/log partition within 9 hours, causing cascading failures that took down the checkout service for over 2 hours during early morning traffic.

## Impact

- **Duration:** 2 hours 3 minutes (2024-01-15 03:22 UTC to 05:25 UTC)
- **Affected Services:** checkout-api (primary), log ingestion pipeline, nginx reverse proxy
- **Affected Host:** prod-web-03
- **User Impact:** ~2,400 failed checkout attempts; users received 500 and 502 errors
- **Revenue Impact:** Estimated $18,000 in lost transactions during outage window
- **Data Impact:** Log ingestion gap from 03:19 to 05:25 UTC (2+ hours of logs lost from Elasticsearch)

## Timeline

| Time (UTC) | Event |
|---|---|
| Jan 14, 18:00 | checkout-api v2.14.3 deployed with `LOG_LEVEL=DEBUG` and `SQL_QUERY_LOGGING=true` |
| Jan 14, 18:05 | Log rotation runs normally (log file 45MB at time) |
| Jan 14, 19:00 | Disk usage at 42% — no alerts |
| Jan 15, 00:00 | Disk usage hits 90% — warning threshold |
| Jan 15, 00:05 | Log rotation fails: checkout-api.log is 48GB, exceeds maxsize |
| Jan 15, 02:15 | Slow log writes begin (450ms, expected <10ms) |
| Jan 15, 03:10 | First "No space left on device" error |
| Jan 15, 03:15 | Nginx error log writes fail, starts buffering in memory |
| Jan 15, 03:18 | Checkout API returning 500 errors (can't create temp files) |
| Jan 15, 03:22 | **ALERT:** Filesystem 2% remaining on prod-web-03 |
| Jan 15, 03:23 | **ALERT:** P99 latency at 12.5s, log ingestion rejected |
| Jan 15, 03:24 | **PAGERDUTY:** Checkout API incident created |
| Jan 15, 03:25 | OOM kill of checkout-api; restart fails (can't write PID file) |
| Jan 15, 03:45 | On-call engineer begins investigation |
| Jan 15, 04:10 | Root cause identified: debug logging filling disk |
| Jan 15, 04:15 | Debug log truncated, disk space recovered |
| Jan 15, 04:20 | Log level changed to INFO, service restarted |
| Jan 15, 05:25 | Service fully recovered, all alerts cleared |

## Root Cause

The deployment of checkout-api v2.14.3 included configuration changes that enabled debug-level logging (`LOG_LEVEL=DEBUG`) and verbose SQL query logging (`SQL_QUERY_LOGGING=true`). These settings were intended for the staging environment but were included in the production deployment configuration.

The verbose logging generated approximately 50GB/hour of log data, primarily detailed SQL query logs for every database operation. The 500GB `/var/log` partition filled from 42% to 98% in approximately 9 hours. When the disk became full, cascading failures occurred:

1. Log rotation failed (file too large at 48GB)
2. Disk I/O saturated at 95%
3. Application couldn't create temp files for request processing
4. Nginx couldn't write error logs, started buffering in memory
5. Elasticsearch rejected log ingestion (write rejected)
6. Checkout API returned 500 errors for all requests
7. Process was OOM-killed and couldn't restart (PID file write failed)

## Resolution

1. Truncated the 48GB debug log file to free disk space
2. Changed `LOG_LEVEL` from `DEBUG` to `INFO` in production config
3. Disabled `SQL_QUERY_LOGGING` in production config
4. Restarted checkout-api service
5. Configured size-based log rotation (maxsize 1GB) for checkout-api logs
6. Verified service health and normal log growth rate

## Action Items

| # | Action | Owner | Due Date | Priority |
|---|--------|-------|----------|----------|
| 1 | Add log level validation to CI/CD pipeline — reject DEBUG in production | Platform Team | 2024-01-22 | P1 |
| 2 | Configure size-based log rotation (maxsize 1GB) on all application servers | SRE Team | 2024-01-19 | P1 |
| 3 | Add disk usage alerts at 70% (warning) and 85% (critical) | SRE Team | 2024-01-19 | P1 |
| 4 | Separate staging and production config files in deployment pipeline | Dev Team | 2024-01-26 | P2 |
| 5 | Add disk space as a health check dependency | Dev Team | 2024-01-26 | P2 |
| 6 | Create deployment checklist including log level verification | Dev Lead | 2024-01-29 | P3 |
| 7 | Implement structured logging with automatic level enforcement | Platform Team | 2024-02-09 | P3 |

## Lessons Learned

1. **Debug logging in production is a ticking time bomb.** Even brief debug logging sessions should be time-boxed and require explicit approval with automatic revert.

2. **Health checks must validate critical dependencies.** The existing health check returned HTTP 200 without checking disk space, masking the degraded state from the load balancer.

3. **Disk alerting thresholds were too high.** The 90% warning threshold left insufficient time to respond. A 70% warning would have given 3+ hours of additional response time.

4. **Log rotation needs size limits, not just time limits.** Time-based rotation is insufficient when log volume can spike by orders of magnitude.

5. **Configuration separation matters.** Staging and production configurations should be clearly separated in the deployment pipeline to prevent environment-specific settings from leaking across environments.
