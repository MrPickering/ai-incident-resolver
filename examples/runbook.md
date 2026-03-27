# Runbook: Disk Space Exhaustion on prod-web-03

**Incident ID:** INC-001
**Severity:** Critical
**Root Cause:** Debug logging filling /var/log at ~50GB/hr

## 1. Immediate Mitigation

> Stop the bleeding — free disk space and restore the checkout service.

### Step 1.1: Check current disk usage

```bash
ssh prod-web-03 'df -h /var/log'
```
Expected output:
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G  490G   10G  98% /var/log
```

### Step 1.2: Remove old rotated log files

```bash
ssh prod-web-03 'sudo find /var/log -name "*.log.[0-9]*" -mtime +1 -delete && df -h /var/log'
```
Expected output:
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G  450G   50G  90% /var/log
```

### Step 1.3: Truncate the oversized debug log

```bash
ssh prod-web-03 'sudo truncate -s 0 /var/log/checkout-api.log && df -h /var/log'
```
Expected output:
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G   40G  460G   8% /var/log
```

### Step 1.4: Restart the checkout API

```bash
ssh prod-web-03 'sudo systemctl restart checkout-api && sleep 5 && sudo systemctl status checkout-api'
```
Expected output:
```
● checkout-api.service - Checkout API
     Active: active (running) since ...
```

## 2. Root Cause Fix

### Step 2.1: Disable debug logging

```bash
ssh prod-web-03 'sudo sed -i "s/LOG_LEVEL=DEBUG/LOG_LEVEL=INFO/" /etc/checkout-api/config.env'
ssh prod-web-03 'sudo sed -i "s/SQL_QUERY_LOGGING=true/SQL_QUERY_LOGGING=false/" /etc/checkout-api/config.env'
```
Expected output: No output (successful edit).

### Step 2.2: Restart to apply configuration

```bash
ssh prod-web-03 'sudo systemctl restart checkout-api && sleep 5 && curl -s localhost:8080/health | python3 -m json.tool'
```
Expected output:
```json
{
    "status": "healthy",
    "version": "2.14.3"
}
```

### Step 2.3: Configure log rotation with size limits

```bash
ssh prod-web-03 'cat <<EOF | sudo tee /etc/logrotate.d/checkout-api
/var/log/checkout-api.log {
    daily
    rotate 7
    maxsize 1G
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF'
```
Expected output: The configuration file contents echoed back.

## 3. Verification Steps

### Step 3.1: Verify disk space is healthy

```bash
ssh prod-web-03 'df -h /var/log'
```
Expected: Usage below 50%.

### Step 3.2: Verify checkout API is responding

```bash
curl -s https://checkout.example.com/health | python3 -m json.tool
```
Expected: `{"status": "healthy"}`

### Step 3.3: Verify log level is INFO

```bash
ssh prod-web-03 'grep LOG_LEVEL /etc/checkout-api/config.env'
```
Expected: `LOG_LEVEL=INFO`

### Step 3.4: Monitor log growth rate

```bash
ssh prod-web-03 'watch -n 60 "du -sh /var/log/checkout-api.log"'
```
Expected: Log file growing at < 100MB/hr (vs 50GB/hr before).

## 4. Prevention Measures

- [ ] Add log level validation to CI/CD pipeline — reject DEBUG in production configs
- [ ] Set disk usage alerts at 70% (warning) and 85% (critical) thresholds
- [ ] Configure size-based log rotation (maxsize 1GB) for all application logs
- [ ] Add disk space as a health check dependency
- [ ] Create deployment checklist that includes log level verification

## 5. Rollback Plan

If the service is still unhealthy after the fix:

```bash
# Stop the service
ssh prod-web-03 'sudo systemctl stop checkout-api'

# Restore previous configuration backup
ssh prod-web-03 'sudo cp /etc/checkout-api/config.env.bak /etc/checkout-api/config.env'

# Start the service
ssh prod-web-03 'sudo systemctl start checkout-api'

# Verify
ssh prod-web-03 'sudo systemctl status checkout-api'
```

If disk space is still an issue, consider mounting additional storage:

```bash
# Attach and mount temporary volume
ssh prod-web-03 'sudo mkdir -p /mnt/log-overflow && sudo mount /dev/xvdf1 /mnt/log-overflow'
ssh prod-web-03 'sudo mv /var/log/checkout-api.log* /mnt/log-overflow/'
```
