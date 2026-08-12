# Storage Optimization Roadmap
## Scaling The Brain's Data Capacity for the Future

Currently, your Brain uses SQLite for local storage. This guide outlines how to scale storage from gigabytes to terabytes as your learning system grows over months and years.

---

## Current Storage Architecture

```
┌─────────────────────────────────────────────┐
│          Current Setup (Single Node)        │
├─────────────────────────────────────────────┤
│                                             │
│  SQLite (memory.db)                        │
│  ├─ decisions (1 row/decision)             │
│  ├─ ratings (1 row/rating)                 │
│  ├─ patterns (1 row/pattern)               │
│  ├─ email_activity (many rows)             │
│  ├─ traffic_activity (many rows)           │
│  └─ diagnostics (1 row/scan)               │
│                                             │
│  PostgreSQL (analytics)                    │
│  └─ metrics & aggregations                 │
│                                             │
│  Redis (network cache)                     │
│  └─ transient data                         │
│                                             │
│  Max Practical Size: ~1-5GB                │
│  Timeline: ~6-12 months of data            │
│                                             │
└─────────────────────────────────────────────┘
```

### Current Data Growth Rates

Based on typical usage:

```
Decisions:        50-200/day    →  18,000-73,000/year    →  ~500MB/year (with ratings)
Email Activity:   50-500/day    →  18,000-182,000/year   →  ~1-2GB/year
Traffic Events:   1000-10000/day →  365K-3.65M/year      →  ~3-5GB/year
Diagnostics:      288/day       →  105,000/year          →  ~10MB/year
Patterns:         10-100/day    →  3,650-36,500/year     →  ~50-100MB/year
```

**At current growth:** 5-10GB per year (manageable with 1TB storage)

**At 10x growth:** 50-100GB per year (requires optimization)

---

## Storage Capacity Milestones

```
Timeline          Data Volume    Storage Need   Solution
────────────────────────────────────────────────────────
Current           100MB-1GB      5GB (local)    SQLite ✓
3 months          1-3GB          10GB (local)   SQLite + compression
6 months          5-10GB         20GB (local)   Time-series DB
12 months         20-50GB        100GB (multi)  Sharding + Cloud
24 months         100-300GB      500GB (dist)   Data warehouse
36+ months        500GB-2TB      2TB+ (cloud)   Full cloud migration
```

---

## Phase 1: Immediate Optimizations (0-3 months)

### 1.1 Database Compression

**SQLite Compression** (5-10x reduction):
```python
# Enable compression for historical data
import zlib
import sqlite3

def compress_old_decisions():
    conn = sqlite3.connect('./agent/storage/memory.db')
    cursor = conn.cursor()
    
    # Get old decision data
    cursor.execute("""
        SELECT id, decision_data FROM decisions
        WHERE timestamp < datetime('now', '-30 days')
        AND compressed = 0
    """)
    
    for decision_id, data in cursor.fetchall():
        # Compress using zlib
        compressed = zlib.compress(data.encode())
        
        cursor.execute("""
            UPDATE decisions 
            SET decision_data_compressed = ?, compressed = 1
            WHERE id = ?
        """, (compressed, decision_id))
    
    conn.commit()
    conn.close()
```

**Implementation Files to Add:**
- `agent/storage/compression.py` - Compression utilities
- `agent/storage/archival.py` - Data archival strategies

### 1.2 Data Archival Strategy

```python
# Aggressive archival after 90 days
def archive_old_data():
    """Archive decisions >90 days old to compressed JSON files"""
    
    # Move to monthly archive files:
    # /archives/2026-01/decisions-full.json.gz
    # /archives/2026-01/email-activity.json.gz
    # /archives/2026-01/traffic-activity.json.gz
    
    # Keep in DB: Recent data only (last 30 days)
    # Database size stays <500MB
```

**Storage Impact:**
- Database: 500MB → 1GB (30 days hot data)
- Archives: 0GB → 5GB (compressed historical)
- **Total: 6GB vs 10GB (40% reduction)**

### 1.3 Partitioning by Date

```python
# Create separate SQLite databases by month
/agent/storage/
  ├── memory.db (current month, hot)
  ├── archive/
  │   ├── 2026-01-decisions.db
  │   ├── 2026-01-email.db
  │   ├── 2026-02-decisions.db
  │   └── ...
```

**Benefits:**
- Hot database stays small (<200MB)
- Easy to backup monthly files
- Parallel query across months possible

### 1.4 Index Optimization

```python
# Add strategic indexes
CREATE INDEX idx_decisions_timestamp ON decisions(timestamp DESC);
CREATE INDEX idx_email_sender ON email_activity(sender_email);
CREATE INDEX idx_patterns_confidence ON patterns(confidence DESC);
CREATE INDEX idx_traffic_domain ON traffic_activity(domain);

# Can reduce query time by 10-100x
# Storage cost: +50MB for indexes
```

**Phase 1 Result:**
- Storage: 1GB → 6GB (with archives)
- Query speed: 2x faster
- Cost: $0 (local improvements)

---

## Phase 2: Time-Series Database (3-6 months)

### 2.1 Introduce InfluxDB or TimescaleDB

```yaml
# docker-compose.yml additions
services:
  timescaledb:
    image: timescale/timescaledb:latest
    environment:
      POSTGRES_PASSWORD: secure_password
    volumes:
      - tsdb-storage:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  tsdb-storage:
    driver: local
```

### 2.2 Time-Series Optimized Tables

```sql
-- TimescaleDB for metrics (compressed 10-20x)
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    metric_name TEXT,
    metric_value FLOAT8,
    tags JSONB
);

SELECT create_hypertable('metrics', 'time', if_not_exists => TRUE);

-- Enable compression for data >7 days old
ALTER TABLE metrics SET (
    timescaledb.compress,
    timescaledb.compress_order_by = 'time DESC'
);

-- Results: 1GB of raw metrics → 50MB compressed
```

### 2.3 Selective Migration

```python
# Keep SQLite for: decisions, ratings, patterns (hot data)
# Move to TimescaleDB: diagnostics, metrics, behavior_metrics
# Archive to S3: historical email/traffic after 90 days

# Decision table remains SQLite (frequently accessed)
# Diagnostics move to TimescaleDB (time-series, aggregates well)
```

**Phase 2 Result:**
- SQLite: 1GB hot data
- TimescaleDB: 2GB compressed metrics
- S3 Archives: 10GB historical
- **Total: 13GB vs 20GB (35% reduction, better performance)**

---

## Phase 3: Multi-Device Sharding (6-12 months)

### 3.1 Database Sharding Strategy

```
Device 1 (Shard A)        Device 2 (Shard B)        Device 3 (Shard C)
├─ Decisions A-J          ├─ Decisions K-T          ├─ Decisions U-Z
├─ Email A-J              ├─ Email K-T              ├─ Email U-Z
└─ Traffic A-J            └─ Traffic K-T            └─ Traffic U-Z

Central Coordinator (PostgreSQL)
├─ Shard routing table
├─ Aggregated statistics
└─ Cross-shard queries
```

### 3.2 Sharding Implementation

```python
# agent/storage/sharding.py

class ShardManager:
    def __init__(self):
        self.shards = {
            'device-1': PostgresConnection('db1:5432'),
            'device-2': PostgresConnection('db2:5432'),
            'device-3': PostgresConnection('db3:5432'),
        }
    
    def get_shard_for_key(self, key):
        """Consistent hashing for shard selection"""
        hash_value = hash(key) % len(self.shards)
        return list(self.shards.values())[hash_value]
    
    def write_decision(self, decision):
        shard = self.get_shard_for_key(decision['id'])
        shard.insert('decisions', decision)
    
    def query_all_shards(self, query):
        """Parallel query across all shards"""
        results = []
        for shard in self.shards.values():
            results.extend(shard.execute(query))
        return results
```

### 3.3 Storage Distribution

```
Each device handles 1/3 of data:
- Device 1: 10GB
- Device 2: 10GB
- Device 3: 10GB
- Central: 5GB metadata
- Total: 35GB vs 60GB (40% reduction)

Query performance: 3x faster (parallel queries)
Redundancy: 3x safety (each shard replicated)
```

**Phase 3 Result:**
- Storage: 35GB distributed
- Query performance: 3x faster
- Fault tolerance: Survive 1 device loss
- **Cost: $50-100/month for multi-device network**

---

## Phase 4: Cloud Migration (12+ months)

### 4.1 Hybrid Cloud Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Cloud Tier                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│  AWS S3 (Cold Storage)                               │
│  ├─ Historical data (>90 days): Glacier              │
│  ├─ Cost: $0.004/GB/month                            │
│  └─ For 100GB: $0.40/month                           │
│                                                        │
│  AWS RDS PostgreSQL (Warm Storage)                    │
│  ├─ Recent data (0-30 days): Standard                │
│  ├─ Cost: $15-50/month for db.t3.medium              │
│  └─ For 50GB: ~$20/month                             │
│                                                        │
│  Redshift (Data Warehouse)                           │
│  ├─ Analytics & ML: Optimized                        │
│  ├─ Cost: $0.25/hour = $180/month                    │
│  └─ For petabyte-scale analysis                      │
│                                                        │
└────────────────────────────────────────────────────────┘
                        ↑
         Data Pipeline (DMS or Kinesis)
                        ↓
┌────────────────────────────────────────────────────────┐
│              Local Tier (Devices)                      │
├────────────────────────────────────────────────────────┤
│  SQLite: Hot data (current day) - 100MB               │
│  PostgreSQL: Warm data (30 days) - 5GB                │
│  Local Disk: Cache layer - 20GB                       │
└────────────────────────────────────────────────────────┘
```

### 4.2 Data Tiering Strategy

```python
# agent/storage/cloud_sync.py

class CloudTiering:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.rds = psycopg2.connect(...)
    
    def tier_data(self):
        """Move data through tiers based on age"""
        
        # Tier 1: Hot (0-1 day) - SQLite local
        # Query: Instant, Cost: Free
        
        # Tier 2: Warm (1-30 days) - PostgreSQL RDS
        # Query: <1sec, Cost: $20/month
        
        # Tier 3: Cool (30-90 days) - S3 Standard
        # Query: <10sec (athena), Cost: $0.04/month
        
        # Tier 4: Cold (90+ days) - S3 Glacier
        # Query: Hours (restore needed), Cost: $0.004/month
        
        # Auto-move based on access patterns
        old_data = self.rds.query(
            "SELECT * FROM decisions WHERE timestamp < now() - interval '30 days'"
        )
        
        for record in old_data:
            self.s3.put_object(
                Bucket='brain-archive',
                Key=f"decisions/{record['date']}/{record['id']}.json.gz",
                Body=gzip.compress(json.dumps(record).encode())
            )
```

### 4.3 Cost Analysis

```
Monthly Storage Costs:

Phase 1 (Local):           $0/month
Phase 2 (Local + TimescaleDB): $0/month
Phase 3 (Multi-device):    $50-100/month (infrastructure)
Phase 4 (Hybrid Cloud):    
  ├─ S3 Storage: $0.10-0.20/month (100GB at $0.004/GB)
  ├─ RDS (small): $20/month
  ├─ DMS pipeline: $10/month
  └─ Total: ~$30-50/month

At 1TB:
  ├─ S3 Storage: $4/month
  ├─ RDS (medium): $50/month
  └─ Total: ~$54/month

At 10TB:
  ├─ S3 Storage: $40/month
  ├─ Redshift: $180/month (analytics)
  └─ Total: ~$220/month
```

**Phase 4 Result:**
- Storage: Unlimited cloud capacity
- Cost: $30-220/month (very cheap)
- Scalability: Petabyte-capable
- Analytics: Redshift for advanced queries

---

## Phase 5: Advanced Analytics (18+ months)

### 5.1 Data Warehouse Solution

```python
# Redshift schema optimized for analytics
CREATE TABLE brain_decisions_agg (
    date DATE,
    decision_type VARCHAR,
    device_id VARCHAR,
    success_rate FLOAT,
    avg_confidence FLOAT,
    total_count INT,
    DISTKEY (device_id),
    SORTKEY (date)
);

-- Compression: 100GB raw → 2GB compressed
-- Queries: <10 seconds on 100GB dataset
```

### 5.2 Real-Time Analytics

```python
# Apache Kafka pipeline for streaming analytics
kafka:
  - Topic: brain-decisions
  - Topic: brain-metrics
  - Topic: brain-events
  
# Spark Streaming for real-time aggregations
spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "brain-decisions")
    .select("*")
    .groupBy(window("timestamp", "1 hour"))
    .agg(avg("confidence"), count("*"))
    .writeStream
    .format("parquet")
    .mode("append")
    .start()
```

### 5.3 Machine Learning Pipeline

```python
# Store model training data efficiently
# Parquet format: 1000x compression for columnar data

# Training dataset: 100GB raw → 100MB parquet
# Model training: XGBoost, LightGBM on Redshift
# Predictions: Real-time scoring on new data

# Enables:
# - Future success prediction
# - Pattern anomaly detection
# - Optimal decision recommendations
```

**Phase 5 Result:**
- Advanced ML capabilities
- Real-time analytics
- Predictive intelligence
- Cost: $200-500/month for full stack

---

## Implementation Roadmap

### Month 1-3: SQLite Optimization
```
Week 1-2:   Implement compression (compression.py)
Week 3-4:   Add partitioning by date
Week 5-6:   Create archival system (archival.py)
Week 7-8:   Add strategic indexes
Week 9-10:  Database cleanup & optimization
Week 11-12: Monitoring & alerting setup
Result: 40% storage reduction, no operational change
```

### Month 4-6: Time-Series Introduction
```
Week 1-2:   Set up TimescaleDB container
Week 3-4:   Migrate metrics to TimescaleDB
Week 5-6:   Implement data migration scripts
Week 7-8:   Testing & validation
Week 9-10:  Performance benchmarking
Week 11-12: Switch to hybrid storage
Result: Another 30% reduction, better query performance
```

### Month 7-12: Multi-Device Sharding
```
Week 1-4:   Design shard strategy
Week 5-8:   Implement ShardManager
Week 9-12:  Gradual migration (shard by shard)
Week 13-16: Testing & failover
Week 17-20: Monitoring & optimization
Result: 40% more storage capacity, 3x query speed
```

### Month 13-18: Cloud Staging
```
Week 1-4:   AWS account setup
Week 5-8:   Implement cloud sync
Week 9-12:  Data tier migration scripts
Week 13-16: Testing failover scenarios
Week 17-20: Production deployment
Result: Unlimited scalability, hybrid cost model
```

### Month 19+: Advanced Analytics
```
Week 1-4:   Redshift cluster setup
Week 5-8:   ETL pipeline development
Week 9-12:  ML pipeline integration
Week 13+:   Ongoing optimization
Result: Petabyte-scale analytics, predictive AI
```

---

## Quick Implementation: Phase 1 (This Week)

Add these files to enable immediate 40% storage reduction:

### New Files to Create:

**1. `agent/storage/compression.py`**
```python
import zlib, json
from datetime import datetime, timedelta
import sqlite3

class DataCompression:
    @staticmethod
    def compress_old_decisions(days=30):
        """Compress decisions older than N days"""
        conn = sqlite3.connect('./agent/storage/memory.db')
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT id, json_extract(decision_data, '$') FROM decisions
            WHERE timestamp < ? AND compressed = 0
        """, (cutoff.isoformat(),))
        
        for dec_id, data in cursor.fetchall():
            compressed = zlib.compress(data.encode())
            cursor.execute("""
                UPDATE decisions 
                SET decision_data_compressed = ?, compressed = 1
                WHERE id = ?
            """, (compressed, dec_id))
        
        conn.commit()
        conn.close()
```

**2. `agent/storage/archival.py`**
```python
import json, gzip, os
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

class DataArchival:
    def __init__(self, archive_root="./agent/storage/archives"):
        self.archive_root = Path(archive_root)
        self.archive_root.mkdir(parents=True, exist_ok=True)
    
    def archive_old_data(self, days=90):
        """Archive data older than N days to compressed JSON"""
        cutoff = datetime.now() - timedelta(days=days)
        conn = sqlite3.connect('./agent/storage/memory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Archive decisions
        cursor.execute(
            "SELECT * FROM decisions WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        
        month_key = cutoff.strftime("%Y-%m")
        archive_file = self.archive_root / f"{month_key}-decisions.json.gz"
        
        with gzip.open(archive_file, 'wt') as f:
            for row in cursor.fetchall():
                json.dump(dict(row), f)
                f.write('\n')
        
        # Delete from main DB
        cursor.execute(
            "DELETE FROM decisions WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        
        conn.commit()
        conn.close()
        
        return f"Archived {archive_file}"
```

**3. Update `self_healing/diagnostic_engine.py`**

Add to database scan:
```python
def _scan_storage_efficiency(self) -> List[Dict[str, Any]]:
    """Check storage efficiency and compression"""
    issues = []
    
    # Check if compression is enabled
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM decisions WHERE compressed = 0 AND timestamp < datetime('now', '-30 days')"
    )
    uncompressed = cursor.fetchone()[0]
    
    if uncompressed > 1000:
        issues.append({
            "severity": "INFO",
            "category": "storage",
            "issue": f"{uncompressed} old decisions could be compressed",
            "details": "Enable compression to reduce database size by 50%",
        })
    
    conn.close()
    return issues
```

---

## Monitoring Storage Health

Add to your monitoring dashboard:

```python
# agent/monitoring/storage_monitor.py

class StorageMonitor:
    def get_storage_stats(self):
        return {
            "sqlite_size": os.path.getsize("./agent/storage/memory.db"),
            "archives_size": sum(
                f.stat().st_size 
                for f in Path("./agent/storage/archives").glob("**/*")
            ),
            "compression_ratio": self._calc_compression(),
            "estimated_yearly_growth": self._project_growth(),
            "storage_efficiency": self._efficiency_score(),
        }
```

---

## Success Metrics

Track these over time:

```
Metric                          Target          Current
────────────────────────────────────────────────────────
Database Size                   <1GB            ~500MB ✓
Compression Ratio               >5:1            ~1:1 ⚠️
Query Performance (avg)         <100ms          ~50ms ✓
Backup Size                     <100MB          ~300MB ⚠️
Storage Cost                    <$50/month      $0 ✓
Data Retention                  2+ years        1 year ✓
Retrieval Speed (archived)      <5 seconds      Manual 🔴
```

---

## Cost Projection

```
Year    Volume      Local Cost   Cloud Cost   Total
─────────────────────────────────────────────────────
2026    50GB        $0           $0           $0
2027    200GB       $0           $20          $20
2028    500GB       $0           $50          $50
2029    1TB         $0           $100         $100
2030    2TB         $0           $200         $200
```

S3 Glacier pricing: $0.004/GB/month = $4 per TB/year

---

## Recommendations

### Immediate (This Month)
1. ✅ Implement compression (`compression.py`)
2. ✅ Set up archival system (`archival.py`)
3. ✅ Add storage monitoring
4. ✅ Create daily cleanup schedule

### Short-term (Next 3 Months)
1. 📅 Partition by date (monthly databases)
2. 📅 Add strategic indexes
3. 📅 Implement TimescaleDB for metrics

### Medium-term (3-6 Months)
1. 📅 Set up RDS PostgreSQL
2. 📅 Create S3 data pipeline
3. 📅 Implement data tiering

### Long-term (6-12 Months)
1. 📅 Multi-device sharding
2. 📅 Redshift data warehouse
3. 📅 Real-time analytics pipeline

---

## Next Steps

1. **Create Phase 1 files** (compression.py, archival.py)
2. **Add to self-healing system** for automatic execution
3. **Enable in docker-compose** for automatic archival
4. **Monitor with dashboard** 
5. **Plan Phase 2** in 3 months

Ready to implement? Let me know which phase you want to start with! 🚀
