# Dockvirt Command Test Results

Generated: 2025-09-06 08:25:05

## 📊 Summary

- **Total Commands**: 60
- **Successful**: 60 (100.0%)
- **Failed**: 0 (0.0%)

## 📋 Detailed Results

### README.md

#### ✅ Successful Commands:
- **Line 28**: `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80` (0.09s)
- **Line 29**: `dockvirt up --name backend --domain backend.local --image httpd:latest --port 80` (0.16s)
- **Line 30**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432` (0.15s)
- **Line 138**: `dockvirt check  # Check system dependencies` (0.15s)
- **Line 139**: `dockvirt --help # Show available commands` (0.14s)
- **Line 310**: `dockvirt up --name my-app --domain my-app.local --image my-app:latest --port 80` (0.15s)
- **Line 332**: `dockvirt up` (0.16s)
- **Line 339**: `dockvirt up \` (0.14s)
- **Line 346**: `dockvirt up \` (0.11s)
- **Line 375**: `dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04` (0.15s)
- **Line 378**: `dockvirt up --name client-b --domain client-b.myaas.com --image nginx:latest --os fedora38` (0.16s)
- **Line 381**: `dockvirt up --name client-c --domain beta.myaas.com --image myapp:v2.1 --os ubuntu22.04` (0.15s)
- **Line 416**: `dockvirt up --name dev-john-frontend --domain app.dev-john.local --image myapp:latest --port 3000` (0.14s)
- **Line 417**: `dockvirt up --name dev-john-api --domain api.dev-john.local --image myapp:latest --port 8080` (0.15s)
- **Line 420**: `dockvirt up --name dev-jane-frontend --domain app.dev-jane.local --image myapp:latest --port 3000` (0.15s)
- **Line 421**: `dockvirt up --name dev-jane-api --domain api.dev-jane.local --image myapp:latest --port 8080` (0.15s)
- **Line 471**: `dockvirt up --name app1 --domain app1.local --image nginx --port 80` (0.16s)
- **Line 472**: `dockvirt up --name app2 --domain app2.local --image apache --port 80` (0.12s)
- **Line 533**: `dockvirt up --name production-app --domain app.local --image nginx:latest --port 80` (0.19s)
- **Line 582**: `dockvirt up --name my-app --image nginx:latest` (0.18s)

### examples/README.md

#### ✅ Successful Commands:
- **Line 190**: `dockvirt check` (0.21s)
- **Line 193**: `dockvirt setup --install` (0.18s)
- **Line 206**: `dockvirt up` (0.18s)
- **Line 213**: `dockvirt up \` (0.20s)
- **Line 220**: `dockvirt up --os fedora38` (0.18s)

### examples/1-static-nginx-website/README.md

#### ✅ Successful Commands:
- **Line 18**: `dockvirt up` (0.17s)
- **Line 24**: `dockvirt up \` (0.22s)
- **Line 31**: `dockvirt up \` (0.17s)
- **Line 50**: `dockvirt down --name static-site` (0.19s)

### examples/2-python-flask-app/README.md

#### ✅ Successful Commands:
- **Line 17**: `dockvirt up` (0.20s)
- **Line 20**: `dockvirt up --os fedora38` (0.18s)
- **Line 26**: `dockvirt up \` (0.13s)
- **Line 45**: `dockvirt down --name flask-app` (0.15s)

### examples/3-multi-os-comparison/README.md

#### ✅ Successful Commands:
- **Line 21**: `dockvirt up \` (0.20s)
- **Line 36**: `dockvirt up \` (0.17s)
- **Line 65**: `dockvirt up \` (0.18s)
- **Line 88**: `dockvirt down --name ubuntu-test` (0.17s)
- **Line 89**: `dockvirt down --name fedora-test` (0.15s)
- **Line 90**: `dockvirt down --name debian-test` (0.20s)

### examples/4-microservices-stack/README.md

#### ✅ Successful Commands:
- **Line 41**: `dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04` (0.18s)
- **Line 44**: `dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora38` (0.20s)
- **Line 47**: `dockvirt up --name database --domain db.stack.local --image postgres:latest --port 5432 --os ubuntu22.04` (0.18s)
- **Line 50**: `dockvirt up --name monitoring --domain mon.stack.local --image grafana/grafana:latest --port 3000 --os ubuntu22.04` (0.18s)
- **Line 57**: `dockvirt stack deploy microservices-stack.yaml` (0.20s)
- **Line 174**: `dockvirt check` (0.19s)
- **Line 181**: `dockvirt stack deploy microservices-stack.yaml` (0.15s)
- **Line 194**: `dockvirt down --name frontend` (0.18s)
- **Line 195**: `dockvirt down --name backend` (0.19s)
- **Line 196**: `dockvirt down --name database` (0.18s)
- **Line 197**: `dockvirt down --name monitoring` (0.17s)
- **Line 200**: `dockvirt stack destroy microservices-stack` (0.17s)

### examples/5-production-deployment/README.md

#### ✅ Successful Commands:
- **Line 77**: `dockvirt up \` (0.18s)
- **Line 86**: `dockvirt up \` (0.18s)
- **Line 94**: `dockvirt up \` (0.19s)
- **Line 102**: `dockvirt up \` (0.12s)
- **Line 111**: `dockvirt up \` (0.17s)
- **Line 120**: `dockvirt up \` (0.17s)
- **Line 130**: `dockvirt up \` (0.19s)
- **Line 141**: `dockvirt up \` (0.17s)
- **Line 150**: `dockvirt up \` (0.16s)

## 🔧 Analysis & Recommendations

🎉 All commands are working correctly!