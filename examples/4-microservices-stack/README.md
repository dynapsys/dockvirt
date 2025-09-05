# 🌐 Mikrousługi Stack - Zaawansowany przykład

Ten przykład demonstruje użycie dockvirt do uruchomienia kompleksowego stosu mikrousług z wieloma VM.

## 🏗️ Architektura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend VM   │    │   Backend VM    │    │  Database VM    │
│                 │    │                 │    │                 │
│ React App       │◄──►│ Node.js API     │◄──►│ Redis + Postgres│
│ app.stack.local │    │ api.stack.local │    │ db.stack.local  │
│                 │    │                 │    │                 │
│ Ubuntu 22.04    │    │ Fedora 36       │    │ Ubuntu 22.04    │
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

## 🚀 Szybkie uruchomienie

### Opcja 1: Pojedyncze komendy

```bash
# Frontend
dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04

# Backend API  
dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora36

# Database
dockvirt up --name database --domain db.stack.local --image microstack-db:latest --port 5432 --os ubuntu22.04

# Monitoring
dockvirt up --name monitoring --domain mon.stack.local --image microstack-monitoring:latest --port 3000 --os ubuntu22.04
```

### Opcja 2: Stack deployment (planowane)

```bash
# Wdroż cały stack jedną komendą
dockvirt stack deploy microservices-stack.yaml
```

## 📦 Budowanie obrazów

```bash
# Build wszystkich komponentów
make build-all

# Lub pojedynczo
docker build -t microstack-frontend:latest ./frontend/
docker build -t microstack-api:latest ./backend/
docker build -t microstack-db:latest ./database/
docker build -t microstack-monitoring:latest ./monitoring/
```

## 🔧 Konfiguracja

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
os=fedora36
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

## 🌍 Dostęp do aplikacji

Po uruchomieniu, dodaj do `/etc/hosts`:

```
<IP_FRONTEND>    app.stack.local
<IP_BACKEND>     api.stack.local  
<IP_DATABASE>    db.stack.local
<IP_MONITORING>  mon.stack.local
```

Następnie otwórz:
- **Aplikacja:** http://app.stack.local
- **API Docs:** http://api.stack.local/docs
- **Monitoring:** http://mon.stack.local

## 📊 Monitorowanie

Grafana dashboards dostępne pod http://mon.stack.local:
- **Application Metrics** - wydajność frontendu i backendu
- **Infrastructure** - metryki VM (CPU, RAM, disk)
- **Database Performance** - PostgreSQL i Redis stats
- **Network Traffic** - komunikacja między serwisami

## 🧪 Testowanie

```bash
# Test całego stosu
curl http://api.stack.local/health
curl http://app.stack.local/api/status

# Load testing
ab -n 1000 -c 10 http://api.stack.local/api/users

# Monitoring test
curl http://mon.stack.local/api/health
```

## 🔄 Automatyzacja CI/CD

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

## 🗑️ Czyszczenie

```bash
# Usuń wszystkie VM ze stosu
dockvirt down --name frontend
dockvirt down --name backend  
dockvirt down --name database
dockvirt down --name monitoring

# Lub jedną komendą (planowane)
dockvirt stack destroy microservices-stack
```

## 💡 Wskazówki produkcyjne

1. **Persistent Storage**: Użyj większych dysków dla bazy danych
2. **Backup**: Regularnie rób kopie zapasowe VM
3. **SSL**: Caddy automatycznie obsługuje Let's Encrypt
4. **Scaling**: Dodaj load balancer VM dla większego ruchu
5. **Security**: Używaj różnych sieci dla różnych warstw

## 🚨 Troubleshooting

**Problem:** Serwisy nie mogą się komunikować  
**Rozwiązanie:** Sprawdź czy wszystkie VM są w tej samej sieci libvirt

**Problem:** Brak dostępu z zewnątrz  
**Rozwiązanie:** Sprawdź /etc/hosts i upewnij się że VM mają przydzielone IP

**Problem:** Wysoka latencja  
**Rozwiązanie:** Zwiększ RAM dla VM lub użyj SSD storage
