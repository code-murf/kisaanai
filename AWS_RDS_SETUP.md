# 🗄️ AWS RDS PostgreSQL Setup Guide

Add a PostgreSQL database on AWS RDS for your KisaanAI application.

## Why AWS RDS?

- ✅ Fully managed by AWS
- ✅ Automatic backups
- ✅ Easy scaling
- ✅ High availability
- ✅ Same region as EC2 (low latency)
- ✅ Free tier available

## Option 1: Quick Setup (Free Tier)

### Step 1: Create RDS Database (10 minutes)

1. **Go to AWS Console** → **RDS** → **Create database**

2. **Choose Database Creation Method**:
   - Select: **Standard create**

3. **Engine Options**:
   - Engine type: **PostgreSQL**
   - Version: **PostgreSQL 15.x** (latest)

4. **Templates**:
   - Select: **Free tier** (for testing)
   - Or: **Production** (for production use)

5. **Settings**:
   ```
   DB instance identifier: kisaanai-db
   Master username: postgres
   Master password: [Create strong password - save it!]
   Confirm password: [Same password]
   ```

6. **Instance Configuration** (Free Tier):
   ```
   DB instance class: db.t3.micro (Free tier eligible)
   Storage type: General Purpose SSD (gp3)
   Allocated storage: 20 GB
   ```

7. **Connectivity**:
   ```
   Virtual private cloud (VPC): Same as your EC2 instance
   Public access: Yes (for now, we'll secure it later)
   VPC security group: Create new
   Security group name: kisaanai-db-sg
   Availability Zone: Same as EC2 (eu-north-1a)
   ```

8. **Database Authentication**:
   - Select: **Password authentication**

9. **Additional Configuration**:
   ```
   Initial database name: kisaanai
   Backup retention: 7 days
   Enable encryption: Yes
   Enable Enhanced monitoring: No (to save costs)
   Enable auto minor version upgrade: Yes
   ```

10. **Click "Create database"**

Wait 5-10 minutes for database to be created.

### Step 2: Configure Security Group

1. **Go to RDS** → **Databases** → **kisaanai-db**
2. **Click on VPC security group** link
3. **Edit inbound rules**
4. **Add rule**:
   ```
   Type: PostgreSQL
   Protocol: TCP
   Port: 5432
   Source: Custom
   Value: [Your EC2 security group ID]
   Description: Allow from EC2
   ```
5. **Save rules**

### Step 3: Get Database Connection Details

1. **Go to RDS** → **Databases** → **kisaanai-db**
2. **Copy these details**:
   ```
   Endpoint: kisaanai-db.xxxxxxxxxx.eu-north-1.rds.amazonaws.com
   Port: 5432
   Master username: postgres
   Database name: kisaanai
   ```

### Step 4: Update Your Application

**On your local machine**, update `.env.production`:

```bash
# Replace Supabase with RDS
DATABASE_URL=postgresql://postgres:YOUR_RDS_PASSWORD@kisaanai-db.xxxxxxxxxx.eu-north-1.rds.amazonaws.com:5432/kisaanai

# Remove Supabase variables (optional)
# SUPABASE_URL=...
# SUPABASE_ANON_KEY=...
```

**On EC2**, update the `.env` file:

```bash
ssh -i kisaanai.pem ubuntu@13.53.186.103

cd kisaanai
nano .env
```

Update:
```bash
DATABASE_URL=postgresql://postgres:YOUR_RDS_PASSWORD@kisaanai-db.xxxxxxxxxx.eu-north-1.rds.amazonaws.com:5432/kisaanai
```

Save and restart:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

## Option 2: Docker Compose with PostgreSQL (Simpler)

Add PostgreSQL directly to your Docker Compose setup on EC2.

### Update docker-compose.prod.yml

Add this to your `docker-compose.prod.yml`:

```yaml
services:
  # ... existing services ...

  postgres:
    image: postgres:15-alpine
    container_name: kisaanai-postgres
    environment:
      POSTGRES_DB: kisaanai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "-E UTF8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    # ... existing config ...
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/kisaanai
      # ... other env vars ...

volumes:
  postgres_data:
    driver: local
```

### Create Database Initialization Script

Create `init.sql` in project root:

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create tables (add your schema here)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    district VARCHAR(50),
    village VARCHAR(50),
    role VARCHAR(20) DEFAULT 'farmer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commodities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    unit VARCHAR(20) DEFAULT 'quintal',
    aliases TEXT[]
);

CREATE TABLE IF NOT EXISTS mandis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    district VARCHAR(50),
    state VARCHAR(50),
    location GEOGRAPHY(POINT),
    contact VARCHAR(15),
    operating_hours JSONB,
    facilities TEXT[]
);

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    commodity_id INT REFERENCES commodities(id),
    mandi_id INT REFERENCES mandis(id),
    date DATE NOT NULL,
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    modal_price DECIMAL(10,2),
    arrivals INT,
    UNIQUE(commodity_id, mandi_id, date)
);

CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    commodity_id INT REFERENCES commodities(id),
    district VARCHAR(50),
    forecast_date DATE NOT NULL,
    predicted_price DECIMAL(10,2),
    confidence_lower DECIMAL(10,2),
    confidence_upper DECIMAL(10,2),
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_price_history_date ON price_history(date);
CREATE INDEX idx_price_history_commodity ON price_history(commodity_id);
CREATE INDEX idx_forecasts_date ON forecasts(forecast_date);
CREATE INDEX idx_mandis_location ON mandis USING GIST(location);

-- Insert sample data
INSERT INTO commodities (name, category, unit) VALUES
    ('Wheat', 'Cereals', 'quintal'),
    ('Rice', 'Cereals', 'quintal'),
    ('Potato', 'Vegetables', 'quintal'),
    ('Tomato', 'Vegetables', 'quintal'),
    ('Onion', 'Vegetables', 'quintal')
ON CONFLICT DO NOTHING;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### Deploy with PostgreSQL

```bash
# On EC2
cd kisaanai

# Update .env
nano .env
```

Set:
```bash
DB_PASSWORD=your_secure_password_here
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## Comparison: RDS vs Docker PostgreSQL

| Feature | AWS RDS | Docker PostgreSQL |
|---------|---------|-------------------|
| **Cost** | ~$15-30/month (after free tier) | Free (uses EC2 resources) |
| **Setup** | More complex | Simple |
| **Backups** | Automatic | Manual |
| **Scaling** | Easy | Manual |
| **Maintenance** | Managed by AWS | You manage |
| **Performance** | Dedicated resources | Shares EC2 resources |
| **High Availability** | Multi-AZ option | Single instance |
| **Best For** | Production | Development/Testing |

## Recommendation

- **For Hackathon/Demo**: Use Docker PostgreSQL (Option 2)
- **For Production**: Use AWS RDS (Option 1)

## Cost Estimate

### AWS RDS Free Tier (12 months)
- **db.t3.micro**: 750 hours/month (free)
- **Storage**: 20 GB (free)
- **Backups**: 20 GB (free)
- **After free tier**: ~$15-30/month

### Docker PostgreSQL
- **Cost**: $0 (uses EC2 resources)
- **Storage**: Uses EC2 disk space
- **Backups**: Manual (can use scripts)

## Database Backup Script

Create `backup-db.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"

mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres kisaanai > $BACKUP_DIR/kisaanai_$DATE.sql

# Keep only last 7 backups
ls -t $BACKUP_DIR/kisaanai_*.sql | tail -n +8 | xargs rm -f

echo "Backup completed: kisaanai_$DATE.sql"
```

Setup cron job:
```bash
chmod +x backup-db.sh
crontab -e
```

Add:
```
0 2 * * * /home/ubuntu/kisaanai/backup-db.sh
```

## Database Monitoring

### Check Database Status

```bash
# Docker PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT version();"

# Check connections
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT pg_size_pretty(pg_database_size('kisaanai'));"
```

### AWS RDS Monitoring

1. Go to RDS → Databases → kisaanai-db
2. Click "Monitoring" tab
3. View:
   - CPU Utilization
   - Database Connections
   - Free Storage Space
   - Read/Write IOPS

## Troubleshooting

### Can't connect to RDS

**Check security group**:
- Ensure EC2 security group is allowed
- Verify endpoint and port are correct

**Test connection from EC2**:
```bash
sudo apt install postgresql-client -y
psql -h kisaanai-db.xxxxxxxxxx.eu-north-1.rds.amazonaws.com -U postgres -d kisaanai
```

### Docker PostgreSQL not starting

**Check logs**:
```bash
docker-compose -f docker-compose.prod.yml logs postgres
```

**Check disk space**:
```bash
df -h
```

**Reset database**:
```bash
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

## Migration from Supabase to AWS

If you want to migrate existing data:

```bash
# Export from Supabase
pg_dump "postgresql://postgres:[PASSWORD]@db.yjdmobzdaeznstzeinod.supabase.co:5432/postgres" > supabase_backup.sql

# Import to AWS RDS
psql -h kisaanai-db.xxxxxxxxxx.eu-north-1.rds.amazonaws.com -U postgres -d kisaanai < supabase_backup.sql

# Or import to Docker PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d kisaanai < supabase_backup.sql
```

---

**Recommendation for Hackathon**: Use Docker PostgreSQL (Option 2) - it's simpler and free!

**For Production**: Upgrade to AWS RDS later for better reliability and backups.
