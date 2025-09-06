# Dockvirt Command Test Results

Generated: 2025-09-06 06:34:11

## 📊 Summary

- **Total Commands**: 58
- **Successful**: 58 (100.0%)
- **Failed**: 0 (0.0%)

## 📋 Detailed Results

### README.md

#### ✅ Successful Commands:
- **Line 28**: `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80` (0.09s)
- **Line 29**: `dockvirt up --name backend --domain backend.local --image httpd:latest --port 80` (0.08s)
- **Line 30**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432` (0.08s)
- **Line 215**: `dockvirt up --name my-app --domain my-app.local --image my-app:latest --port 80` (0.08s)
- **Line 234**: `dockvirt up` (0.12s)
- **Line 241**: `dockvirt up \` (0.12s)
- **Line 248**: `dockvirt up \` (0.10s)
- **Line 277**: `dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04` (0.12s)
- **Line 280**: `dockvirt up --name client-b --domain client-b.myaas.com --image nginx:latest --os fedora38` (0.12s)
- **Line 283**: `dockvirt up --name client-c --domain beta.myaas.com --image myapp:v2.1 --os ubuntu22.04` (0.12s)
- **Line 318**: `dockvirt up --name dev-john-frontend --domain app.dev-john.local --image myapp:latest --port 3000` (0.12s)
- **Line 319**: `dockvirt up --name dev-john-api --domain api.dev-john.local --image myapp:latest --port 8080` (0.11s)
- **Line 322**: `dockvirt up --name dev-jane-frontend --domain app.dev-jane.local --image myapp:latest --port 3000` (0.11s)
- **Line 323**: `dockvirt up --name dev-jane-api --domain api.dev-jane.local --image myapp:latest --port 8080` (0.11s)
- **Line 373**: `dockvirt up --name app1 --domain app1.local --image nginx --port 80` (0.11s)
- **Line 374**: `dockvirt up --name app2 --domain app2.local --image apache --port 80` (0.11s)
- **Line 390**: `dockvirt up --name production-app --domain app.local --image nginx:latest --port 80` (0.12s)
- **Line 439**: `dockvirt up --name my-app --image nginx:latest` (0.11s)

### examples/README.md

#### ✅ Successful Commands:
- **Line 190**: `dockvirt check` (0.12s)
- **Line 193**: `dockvirt setup --install` (0.11s)
- **Line 206**: `dockvirt up` (0.11s)
- **Line 213**: `dockvirt up \` (0.12s)
- **Line 220**: `dockvirt up --os fedora38` (0.11s)

### examples/1-static-nginx-website/README.md

#### ✅ Successful Commands:
- **Line 17**: `dockvirt up` (0.11s)
- **Line 26**: `dockvirt up \` (0.11s)
- **Line 33**: `dockvirt up \` (0.11s)
- **Line 52**: `dockvirt down --name static-site` (0.11s)

### examples/2-python-flask-app/README.md

#### ✅ Successful Commands:
- **Line 16**: `dockvirt up` (0.11s)
- **Line 19**: `dockvirt up --os fedora38` (0.11s)
- **Line 28**: `dockvirt up \` (0.11s)
- **Line 47**: `dockvirt down --name flask-app` (0.11s)

### examples/3-multi-os-comparison/README.md

#### ✅ Successful Commands:
- **Line 24**: `dockvirt up \` (0.12s)
- **Line 36**: `dockvirt up \` (0.12s)
- **Line 65**: `dockvirt up \` (0.09s)
- **Line 88**: `dockvirt down --name ubuntu-test` (0.08s)
- **Line 89**: `dockvirt down --name fedora-test` (0.11s)
- **Line 90**: `dockvirt down --name debian-test` (0.11s)

### examples/4-microservices-stack/README.md

#### ✅ Successful Commands:
- **Line 41**: `dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04` (0.12s)
- **Line 44**: `dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora38` (0.11s)
- **Line 47**: `dockvirt up --name database --domain db.stack.local --image postgres:latest --port 5432 --os ubuntu22.04` (0.12s)
- **Line 50**: `dockvirt up --name monitoring --domain mon.stack.local --image grafana/grafana:latest --port 3000 --os ubuntu22.04` (0.12s)
- **Line 57**: `dockvirt stack deploy microservices-stack.yaml` (0.12s)
- **Line 174**: `dockvirt check` (0.11s)
- **Line 181**: `dockvirt stack deploy microservices-stack.yaml` (0.11s)
- **Line 194**: `dockvirt down --name frontend` (0.11s)
- **Line 195**: `dockvirt down --name backend` (0.11s)
- **Line 196**: `dockvirt down --name database` (0.11s)
- **Line 197**: `dockvirt down --name monitoring` (0.11s)
- **Line 200**: `dockvirt stack destroy microservices-stack` (0.11s)

### examples/5-production-deployment/README.md

#### ✅ Successful Commands:
- **Line 77**: `dockvirt up \` (0.11s)
- **Line 86**: `dockvirt up \` (0.18s)
- **Line 94**: `dockvirt up \` (0.12s)
- **Line 102**: `dockvirt up \` (0.13s)
- **Line 111**: `dockvirt up \` (0.13s)
- **Line 120**: `dockvirt up \` (0.11s)
- **Line 130**: `dockvirt up \` (0.11s)
- **Line 141**: `dockvirt up \` (0.11s)
- **Line 150**: `dockvirt up \` (0.12s)

## 🔧 Analysis & Recommendations

🎉 All commands are working correctly!