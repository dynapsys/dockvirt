# 🌐 Microservices Stack - Advanced Example

This example demonstrates using dockvirt to run a complex microservices stack with multiple VMs.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend VM   │    │   Backend VM    │    │  Database VM    │
│                 │    │                 │    │                 │
│ React App       │◄──►│ Node.js API     │◄──►│ Redis + Postgres│
│ app.stack.local │    │ api.stack.local │    │ db.stack.local  │
│                 │    │                 │    │                 │
│ Ubuntu 22.04    │    │ Fedora 38       │    │ Ubuntu 22.04    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Monitoring VM  │
                    │                 │
                    │ Grafana + Prom  │
                    │ mon.stack.local │
                    │                 │
                    │ Ubuntu 22.04    │
                    └─────────────────┘
```

## 🚀 Quick Start

### Option 1: Single Commands

```bash
# Build Docker images first
docker build -t microstack-frontend:latest ./frontend
docker build -t microstack-api:latest ./api  
docker build -t microstack-db:latest ./database
docker build -t microstack-monitoring:latest ./monitoring

# Developer tip: ensure you use the local repo CLI from the venv if another dockvirt is on PATH
# ../../.venv-3.13/bin/dockvirt --help
# Or activate the venv:
# source ../../.venv-3.13/bin/activate

# Frontend
dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04

# Backend API  
dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora38

# Database
dockvirt up --name database --domain db.stack.local --image postgres:latest --port 5432 --os ubuntu22.04

# Monitoring
dockvirt up --name monitoring --domain mon.stack.local --image grafana/grafana:latest --port 3000 --os ubuntu22.04
```

### Option 2: Stack Deployment (Planned)

```bash
# Deploy the entire stack with one command
dockvirt stack deploy microservices-stack.yaml
```

## 📦 Building Images

```bash
# Build all components
make build-all

# Or individually
docker build -t microstack-frontend:latest ./frontend/
docker build -t microstack-api:latest ./backend/
docker build -t microstack-db:latest ./database/
docker build -t microstack-monitoring:latest ./monitoring/
```

## 🔧 Configuration

### Frontend (.dockvirt-frontend)
```
name=frontend
domain=app.stack.local
image=microstack-frontend:latest
port=3000
os=ubuntu22.04
mem=2048
```

### Backend (.dockvirt-backend)
```
name=backend
domain=api.stack.local
image=microstack-api:latest
port=8080
os=fedora38
mem=4096
```

### Database (.dockvirt-database)
```
name=database
domain=db.stack.local
image=microstack-db:latest
port=5432
os=ubuntu22.04
mem=4096
disk=50
```

### Monitoring (.dockvirt-monitoring)
```
name=monitoring
domain=mon.stack.local
image=microstack-monitoring:latest
port=3000
os=ubuntu22.04
mem=2048
```

## 🌍 Accessing the Application

After startup, add the following to `/etc/hosts`:

```
<IP_FRONTEND>    app.stack.local
<IP_BACKEND>     api.stack.local  
<IP_DATABASE>    db.stack.local
<IP_MONITORING>  mon.stack.local
```

Then open:
- **Application:** http://app.stack.local
- **API Docs:** http://api.stack.local/docs
- **Monitoring:** http://mon.stack.local

Tip: If a reverse proxy (Caddy) is used inside the VM, IP-based HTTP checks may require a Host header. For quick checks by IP:

```bash
curl -H 'Host: app.stack.local' http://<ip_frontend>/
curl -H 'Host: api.stack.local' http://<ip_backend>/
curl -H 'Host: mon.stack.local' http://<ip_monitoring>/
```

## 📊 Monitoring

Grafana dashboards are available at http://mon.stack.local:
- **Application Metrics** - frontend and backend performance
- **Infrastructure** - VM metrics (CPU, RAM, disk)
- **Database Performance** - PostgreSQL and Redis stats
- **Network Traffic** - communication between services

## 🧪 Testing

```bash
# Test the entire stack
curl http://api.stack.local/health
curl http://app.stack.local/api/status

# Load testing
ab -n 1000 -c 10 http://api.stack.local/api/users

# Monitoring test
curl http://mon.stack.local/api/health
```

## 🔄 CI/CD Automation

### GitHub Actions Example

```yaml
name: Deploy Microservices Stack

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup DockerVirt
        run: |
          pip install dockvirt
          dockvirt check
          
      - name: Build Images
        run: make build-all
        
      - name: Deploy Stack
        run: |
          dockvirt stack deploy microservices-stack.yaml
          
      - name: Health Check
        run: |
          sleep 60  # Wait for VMs to boot
          curl -f http://api.stack.local/health
          curl -f http://app.stack.local/
```

## 🗑️ Cleanup

```bash
# Remove all VMs from the stack
dockvirt down --name frontend
dockvirt down --name backend  
dockvirt down --name database
dockvirt down --name monitoring

# Or with a single command (planned)
dockvirt stack destroy microservices-stack
```

## 💡 Production Tips

1. **Persistent Storage**: Use larger disks for the database
2. **Backup**: Regularly back up the VMs
3. **SSL**: Caddy automatically handles Let's Encrypt
4. **Scaling**: Add a load balancer VM for higher traffic
5. **Security**: Use different networks for different layers

## 🚨 Troubleshooting

**Problem:** Services cannot communicate  
**Solution:** Check if all VMs are on the same libvirt network

**Problem:** No external access  
**Solution:** Check /etc/hosts and make sure the VMs have been assigned IPs

> Note: Do not run `dockvirt` or `make` with `sudo`. The tools request sudo only when needed and act on your real HOME.

**Problem:** High latency  
**Solution:** Increase the VM's RAM or use SSD storage
