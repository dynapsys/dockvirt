# 🏭 Production Deployment - Enterprise Example

An example of a full production deployment with high availability, monitoring, and backup.

## 🎯 Goal

A demonstration of using dockvirt in a production environment for an e-commerce company serving 10k+ users daily.

## 🏗️ Production Architecture

```
                    🌐 Internet
                         │
                ┌────────┴────────┐
                │  Load Balancer  │
                │  lb.prod.com    │
                │  Ubuntu 22.04   │
                └────────┬────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────┴───────┐ ┌──────┴──────┐ ┌──────┴──────┐
│  Frontend 1   │ │ Frontend 2  │ │ Frontend 3  │
│ app1.prod.com │ │app2.prod.com│ │app3.prod.com│
│ React + Nginx │ │React + Nginx│ │React + Nginx│
│ Ubuntu 22.04  │ │ Ubuntu 22.04│ │ Ubuntu 22.04│
└───────┬───────┘ └──────┬──────┘ └──────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                ┌────────┼────────┐
                │                │
        ┌───────┴───────┐ ┌──────┴──────┐
        │   API Server  │ │ API Server  │
        │ api1.prod.com │ │api2.prod.com│
        │ Node.js + PM2 │ │Node.js + PM2│
        │  Fedora 38    │ │  Fedora 38  │
        └───────┬───────┘ └──────┬──────┘
                │                │
                └────────┼───────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
   ┌────────┴───────┐    │    ┌───────┴────────┐
   │   Database     │    │    │     Cache      │
   │ db.prod.com    │    │    │ cache.prod.com │
   │ PostgreSQL HA  │    │    │ Redis Cluster  │
   │ Ubuntu 22.04   │    │    │ Ubuntu 22.04   │
   └────────────────┘    │    └────────────────┘
                         │
                ┌────────┴────────┐
                │   Monitoring    │
                │ mon.prod.com    │
                │ Grafana+Prom+ELK│
                │ Ubuntu 22.04    │
                └─────────────────┘
```

## 🚀 Deployment Script

### production-deploy.sh

```bash
#!/bin/bash
# Production deployment script

set -e

echo "🚀 Starting production deployment..."

# Build production images first
docker build -t nginx-lb:prod ./load-balancer
docker build -t ecommerce-frontend:v2.1.0 ./frontend
docker build -t ecommerce-api:v2.1.0 ./api

# Load Balancer
dockvirt up \
  --name lb-prod \
  --domain lb.prod.com \
  --image nginx:latest \
  --port 80 \
  --mem 1024 \
  --os ubuntu22.04

# Frontend Cluster (3 instances)  
dockvirt up \
  --name frontend-1 \
  --domain app1.prod.com \
  --image ecommerce-frontend:v2.1.0 \
  --port 3000 \
  --mem 2048 \
  --os ubuntu22.04

dockvirt up \
  --name frontend-2 \
  --domain app2.prod.com \
  --image ecommerce-frontend:v2.1.0 \
  --port 3000 \
  --mem 2048 \
  --os ubuntu22.04

dockvirt up \
  --name frontend-3 \
  --domain app3.prod.com \
  --image ecommerce-frontend:v2.1.0 \
  --port 3000 \
  --mem 2048 \
  --os ubuntu22.04

# API Cluster (2 instances)
dockvirt up \
  --name api-1 \
  --domain api1.prod.com \
  --image ecommerce-api:v2.1.0 \
  --port 8080 \
  --mem 4096 \
  --cpus 4 \
  --os fedora38

dockvirt up \
  --name api-2 \
  --domain api2.prod.com \
  --image ecommerce-api:v2.1.0 \
  --port 8080 \
  --mem 4096 \
  --cpus 4 \
  --os fedora38

# Database (Primary-Secondary)
dockvirt up \
  --name db-primary \
  --domain db.prod.com \
  --image postgres-ha:13 \
  --port 5432 \
  --mem 16384 \
  --disk 500 \
  --cpus 8 \
  --os ubuntu22.04

# Redis Cache Cluster
dockvirt up \
  --name cache-cluster \
  --domain cache.prod.com \
  --image redis-cluster:7 \
  --port 6379 \
  --mem 8192 \
  --os ubuntu22.04

# Monitoring Stack
dockvirt up \
  --name monitoring \
  --domain mon.prod.com \
  --image monitoring-stack:latest \
  --port 3000,9090,5601 \
  --mem 8192 \
  --disk 200 \
  --os ubuntu22.04

echo "✅ Production deployment completed!"
echo "🌐 Access your application at: https://lb.prod.com"
echo "📊 Monitoring: https://mon.prod.com"
```

Tip: Use the dockvirt CLI from the local repository virtualenv when testing locally to ensure the latest code is used:

```bash
# From repository root
. .venv-3.13/bin/activate
dockvirt --help
# Or call the binary explicitly from the venv
.venv-3.13/bin/dockvirt --help
```

## 📊 Monitoring & Alerting

### Grafana Dashboards

1. **Business Metrics**
   - Orders per minute
   - Revenue tracking  
   - User registrations
   - Cart abandonment rate

2. **Application Performance**
   - API response times
   - Frontend load times
   - Database query performance
   - Cache hit rates

3. **Infrastructure Health**
   - VM CPU/Memory usage
   - Disk I/O and space
   - Network traffic
   - VM availability

### Alerting Rules

```yaml\n# prometheus-alerts.yml\ngroups:\n  - name: production-alerts\n    rules:\n      - alert: HighAPILatency\n        expr: avg(api_request_duration_seconds) > 2\n        for: 5m\n        annotations:\n          summary: \"API latency is too high\"\n          \n      - alert: DatabaseConnectionsHigh\n        expr: postgres_connections_active > 80\n        for: 2m\n        annotations:\n          summary: \"Database connections approaching limit\"\n          \n      - alert: VMMemoryUsageHigh\n        expr: vm_memory_usage_percent > 85\n        for: 5m\n        annotations:\n          summary: \"VM memory usage is high\"\n```

## 🔒 Security & Backup

### SSL Configuration

```yaml\n# Caddyfile dla Load Balancer\nlb.prod.com {\n    tls your-email@company.com\n    \n    # Round-robin load balancing\n    reverse_proxy app1.prod.com app2.prod.com app3.prod.com {\n        health_check /health\n        health_check_interval 30s\n    }\n    \n    # Security headers\n    header {\n        Strict-Transport-Security \"max-age=31536000;\"\n        X-Content-Type-Options \"nosniff\"\n        X-Frame-Options \"DENY\"\n        X-XSS-Protection \"1; mode=block\"\n    }\n}\n```

### Backup Strategy

```bash\n#!/bin/bash\n# backup-production.sh\n\n# Database backup\ndockvirt exec db-primary -- pg_dump ecommerce > \"/backup/db-$(date +%Y%m%d).sql\"\n\n# VM snapshots  \nvirsh snapshot-create-as frontend-1 \"daily-$(date +%Y%m%d)\"\nvirsh snapshot-create-as api-1 \"daily-$(date +%Y%m%d)\"\nvirsh snapshot-create-as db-primary \"daily-$(date +%Y%m%d)\"\n\n# Upload to S3\naws s3 sync /backup/ s3://company-backups/dockvirt/\n\necho \"✅ Backup completed\"\n```

## 🎯 Performance Tuning

### VM Optimization

```bash\n# High-performance VM for the database\ndockvirt up \\\n  --name db-optimized \\\n  --domain db.prod.com \\\n  --image postgres-tuned:13 \\\n  --mem 32768 \\\n  --cpus 16 \\\n  --disk 1000 \\\n  --disk-type ssd \\\n  --cpu-model host-passthrough \\\n  --os ubuntu22.04\n```\n\n### Cache Configuration\n\n```redis\n# Redis optimization\nmaxmemory 6gb\nmaxmemory-policy allkeys-lru\nsave 900 1\nsave 300 10\nsave 60 10000\n```

## 📈 Scaling Strategy

### Horizontal Scaling

```bash\n# Add a new frontend node\ndockvirt up \\\n  --name frontend-4 \\\n  --domain app4.prod.com \\\n  --image ecommerce-frontend:v2.1.0 \\\n  --port 3000 \\\n  --mem 2048 \\\n  --os ubuntu22.04\n\n# Update the load balancer\ndockvirt exec lb-prod -- update-upstream app4.prod.com\n```

### Auto-scaling (Planned Feature)

```yaml\n# autoscale.yml\nrules:\n  - metric: cpu_usage\n    threshold: 80\n    action: scale_up\n    max_instances: 10\n    \n  - metric: request_rate\n    threshold: 1000\n    action: scale_up\n    cooldown: 300s\n```

## 🚨 Disaster Recovery

### Failover Procedure

```bash
#!/bin/bash
# failover.sh

echo "🚨 Starting failover procedure..."

# Promote secondary database
dockvirt exec db-secondary -- promote-to-primary

# Update API configuration
dockvirt exec api-1 -- update-db-config db-secondary.prod.com
dockvirt exec api-2 -- update-db-config db-secondary.prod.com

# Health check
curl -f https://lb.prod.com/health || exit 1

echo "✅ Failover completed successfully"
```

## 📋 Production Checklist

### Pre-deployment
- [ ] Load test completed (10k concurrent users)
- [ ] Security scan passed
- [ ] Database migrations tested
- [ ] Backup strategy verified
- [ ] Monitoring dashboards configured
- [ ] SSL certificates valid
- [ ] DNS records updated

### Post-deployment
- [ ] Health checks passing
- [ ] Monitoring alerts configured  
- [ ] Performance metrics baseline
- [ ] Backup job scheduled
- [ ] Team notifications sent
- [ ] Documentation updated

## 💰 Cost Optimization

### Resource Planning

| Component | VM Count | vCPU | RAM | Storage | Monthly Cost* |
|-----------|----------|------|-----|---------|---------------|
| Load Balancer | 1 | 2 | 4GB | 50GB | $45 |
| Frontend | 3 | 2 | 2GB | 20GB | $90 |
| API | 2 | 4 | 8GB | 50GB | $160 |
| Database | 1 | 8 | 32GB | 1TB | $320 |
| Cache | 1 | 4 | 8GB | 100GB | $95 |
| Monitoring | 1 | 4 | 8GB | 200GB | $105 |
| **Total** | **9** | **30** | **70GB** | **1.49TB** | **$815** |

*Estimated costs for cloud VM equivalent

### Cost Saving Tips

1. **Scheduled scaling** - Reduce VM size during low traffic
2. **Spot instances** - Use for non-critical workloads  
3. **Storage optimization** - Use different storage tiers
4. **Reserved capacity** - Long-term commitments for discounts

## 🧪 Quick HTTP checks with Host header

When verifying services by IP (before DNS is set up), include the Host header (Caddy/Reverse proxy):

```bash
curl -H 'Host: lb.prod.com' http://<lb_ip>/
curl -H 'Host: app1.prod.com' http://<app1_ip>/
curl -H 'Host: api1.prod.com' http://<api1_ip>/
curl -H 'Host: mon.prod.com' http://<mon_ip>/
```

> Note: Do not run `dockvirt` or `make` with `sudo`. The tools request sudo only when needed and act on your real HOME.
