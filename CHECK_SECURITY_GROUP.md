# 🔒 AWS Security Group Configuration

## CRITICAL: Your ports are not accessible from the internet!

The test shows that ports 80, 3000, and 8000 are not reachable. This is likely because your AWS Security Group doesn't allow inbound traffic.

## How to Fix Security Group

### Step 1: Go to AWS Console
1. Open https://console.aws.amazon.com/ec2/
2. Click on "Instances" in the left menu
3. Find your instance: `i-01f435b0fbf6498d2` (Kisaanai)
4. Click on the instance

### Step 2: Edit Security Group
1. Click on the "Security" tab
2. Under "Security groups", click on the security group link (e.g., `sg-xxxxx`)
3. Click "Edit inbound rules"

### Step 3: Add These Rules

Click "Add rule" for each of these:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Nginx/Frontend |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend Direct |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Backend API |
| HTTPS | TCP | 443 | 0.0.0.0/0 | SSL (optional) |

### Step 4: Save Rules
1. Click "Save rules"
2. Wait 10 seconds for changes to apply

### Step 5: Test Again
Run this on your Windows machine:
```powershell
.\test-live-deployment.ps1
```

## Visual Guide

### Before (Blocked):
```
Internet → [Security Group BLOCKS] → EC2 Instance
```

### After (Open):
```
Internet → [Security Group ALLOWS ports 80,3000,8000] → EC2 Instance
```

## Quick Test Commands

After fixing security group, test these URLs in your browser:

1. **Frontend:** http://13.53.186.103
2. **Backend Health:** http://13.53.186.103:8000/health
3. **API Docs:** http://13.53.186.103:8000/docs
4. **Commodities API:** http://13.53.186.103:8000/api/v1/commodities

## Troubleshooting

### If ports still not accessible after security group fix:

1. **Check if containers are running on EC2:**
   ```bash
   ssh -i kisaanai.pem ubuntu@13.53.186.103
   cd kisaanai
   sudo docker-compose -f docker-compose.prod.yml ps
   ```
   
   Expected: 4 containers running

2. **Check if ports are listening:**
   ```bash
   sudo netstat -tulpn | grep -E '80|3000|8000'
   ```
   
   Expected: Ports 80, 3000, 8000 should be LISTEN

3. **Check logs:**
   ```bash
   sudo docker-compose -f docker-compose.prod.yml logs
   ```

4. **Restart services:**
   ```bash
   sudo docker-compose -f docker-compose.prod.yml restart
   ```

## Common Issues

### Issue: "Connection timed out"
**Cause:** Security group not configured
**Fix:** Add inbound rules as shown above

### Issue: "Connection refused"
**Cause:** Services not running
**Fix:** Check containers are running with `docker ps`

### Issue: "502 Bad Gateway"
**Cause:** Backend not ready yet
**Fix:** Wait 2-3 minutes for services to start

---

**IMPORTANT:** You MUST configure the security group for the deployment to be accessible from the internet!
