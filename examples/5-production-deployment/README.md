# 🏭 Production Deployment - Enterprise Example

Przykład pełnego wdrożenia produkcyjnego z wysoką dostępnością, monitoringiem i backup.

## 🎯 Cel

Demonstracja użycia dockvirt w środowisku produkcyjnym dla firmy e-commerce obsługującej 10k+ użytkowników dziennie.

## 🏗️ Architektura Production

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
        │  Fedora 36    │ │  Fedora 36  │
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

# Load Balancer
dockvirt up \\\n  --name lb-prod \\\n  --domain lb.prod.com \\\n  --image nginx-lb:prod \\\n  --port 80,443 \\\n  --mem 4096 \\\n  --os ubuntu22.04

# Frontend Cluster (3 instances)  
dockvirt up \\\n  --name frontend-1 \\\n  --domain app1.prod.com \\\n  --image ecommerce-frontend:v2.1.0 \\\n  --port 3000 \\\n  --mem 2048 \\\n  --os ubuntu22.04

dockvirt up \\\n  --name frontend-2 \\\n  --domain app2.prod.com \\\n  --image ecommerce-frontend:v2.1.0 \\\n  --port 3000 \\\n  --mem 2048 \\\n  --os ubuntu22.04

dockvirt up \\\n  --name frontend-3 \\\n  --domain app3.prod.com \\\n  --image ecommerce-frontend:v2.1.0 \\\n  --port 3000 \\\n  --mem 2048 \\\n  --os ubuntu22.04

# API Cluster (2 instances)\ndockvirt up \\\n  --name api-1 \\\n  --domain api1.prod.com \\\n  --image ecommerce-api:v2.1.0 \\\n  --port 8080 \\\n  --mem 8192 \\\n  --cpus 4 \\\n  --os fedora36

dockvirt up \\\n  --name api-2 \\\n  --domain api2.prod.com \\\n  --image ecommerce-api:v2.1.0 \\\n  --port 8080 \\\n  --mem 8192 \\\n  --cpus 4 \\\n  --os fedora36

# Database (Primary-Secondary)\ndockvirt up \\\n  --name db-primary \\\n  --domain db.prod.com \\\n  --image postgres-ha:13 \\\n  --port 5432 \\\n  --mem 16384 \\\n  --disk 500 \\\n  --cpus 8 \\\n  --os ubuntu22.04

# Redis Cache Cluster\ndockvirt up \\\n  --name cache-cluster \\\n  --domain cache.prod.com \\\n  --image redis-cluster:7 \\\n  --port 6379 \\\n  --mem 8192 \\\n  --os ubuntu22.04

# Monitoring Stack\ndockvirt up \\\n  --name monitoring \\\n  --domain mon.prod.com \\\n  --image monitoring-stack:latest \\\n  --port 3000,9090,5601 \\\n  --mem 8192 \\\n  --disk 200 \\\n  --os ubuntu22.04

echo \"✅ Production deployment completed!\"\necho \"🌐 Access your application at: https://lb.prod.com\"\necho \"📊 Monitoring: https://mon.prod.com\"\n```

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

```bash\n# Wysokowydajne VM dla bazy danych\ndockvirt up \\\n  --name db-optimized \\\n  --domain db.prod.com \\\n  --image postgres-tuned:13 \\\n  --mem 32768 \\\n  --cpus 16 \\\n  --disk 1000 \\\n  --disk-type ssd \\\n  --cpu-model host-passthrough \\\n  --os ubuntu22.04\n```\n\n### Cache Configuration\n\n```redis\n# Redis optimization\nmaxmemory 6gb\nmaxmemory-policy allkeys-lru\nsave 900 1\nsave 300 10\nsave 60 10000\n```

## 📈 Scaling Strategy

### Horizontal Scaling

```bash\n# Dodaj nowy frontend node\ndockvirt up \\\n  --name frontend-4 \\\n  --domain app4.prod.com \\\n  --image ecommerce-frontend:v2.1.0 \\\n  --port 3000 \\\n  --mem 2048 \\\n  --os ubuntu22.04\n\n# Zaktualizuj load balancer\ndockvirt exec lb-prod -- update-upstream app4.prod.com\n```

### Auto-scaling (Planned Feature)

```yaml\n# autoscale.yml\nrules:\n  - metric: cpu_usage\n    threshold: 80\n    action: scale_up\n    max_instances: 10\n    \n  - metric: request_rate\n    threshold: 1000\n    action: scale_up\n    cooldown: 300s\n```

## 🚨 Disaster Recovery

### Failover Procedure

```bash\n#!/bin/bash\n# failover.sh\n\necho \"🚨 Starting failover procedure...\"\n\n# Promote secondary database\ndockvirt exec db-secondary -- promote-to-primary\n\n# Update API configuration\ndockvirt exec api-1 -- update-db-config db-secondary.prod.com\ndockvirt exec api-2 -- update-db-config db-secondary.prod.com\n\n# Health check\ncurl -f https://lb.prod.com/health || exit 1\n\necho \"✅ Failover completed successfully\"\n```

## 📋 Production Checklist

### Pre-deployment\n- [ ] Load test completed (10k concurrent users)\n- [ ] Security scan passed\n- [ ] Database migrations tested\n- [ ] Backup strategy verified\n- [ ] Monitoring dashboards configured\n- [ ] SSL certificates valid\n- [ ] DNS records updated\n\n### Post-deployment\n- [ ] Health checks passing\n- [ ] Monitoring alerts configured  \n- [ ] Performance metrics baseline\n- [ ] Backup job scheduled\n- [ ] Team notifications sent\n- [ ] Documentation updated\n\n## 💰 Cost Optimization\n\n### Resource Planning\n\n| Component | VM Count | vCPU | RAM | Storage | Monthly Cost* |\n|-----------|----------|------|-----|---------|---------------|\n| Load Balancer | 1 | 2 | 4GB | 50GB | $45 |\n| Frontend | 3 | 2 | 2GB | 20GB | $90 |\n| API | 2 | 4 | 8GB | 50GB | $160 |\n| Database | 1 | 8 | 32GB | 1TB | $320 |\n| Cache | 1 | 4 | 8GB | 100GB | $95 |\n| Monitoring | 1 | 4 | 8GB | 200GB | $105 |\n| **Total** | **9** | **30** | **70GB** | **1.49TB** | **$815** |\n\n*Estimated costs for cloud VM equivalent\n\n### Cost Saving Tips\n\n1. **Scheduled scaling** - Reduce VM size during low traffic\n2. **Spot instances** - Use for non-critical workloads  \n3. **Storage optimization** - Use different storage tiers\n4. **Reserved capacity** - Long-term commitments for discounts
