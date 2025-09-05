# Dockvirt Commands Test Report
==================================================

## Summary
- **Total Commands Tested**: 190
- **Successful**: 0
- **Failed**: 190
- **Success Rate**: 0.0%

## ❌ Failed Commands

### README.md

**Line 28**: `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 29**: `dockvirt up --name backend --domain backend.local --image httpd:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 30**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 73**: `pip install dockvirt`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 78**: `git clone https://github.com/dynapsys/dockvirt.git`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 79**: `cd dockvirt`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 107**: `pip install dockvirt`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 215**: `dockvirt up --name my-app --domain my-app.local --image my-app:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 225**: `cat > .dockvirt << EOF`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 234**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 241**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 248**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 277**: `dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 280**: `dockvirt up --name client-b --domain client-b.myaas.com --image nginx:latest --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 283**: `dockvirt up --name client-c --domain beta.myaas.com --image myapp:v2.1 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 318**: `dockvirt up --name dev-john-frontend --domain app.dev-john.local --image myapp:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 319**: `dockvirt up --name dev-john-api --domain api.dev-john.local --image myapp:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 322**: `dockvirt up --name dev-jane-frontend --domain app.dev-jane.local --image myapp:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 323**: `dockvirt up --name dev-jane-api --domain api.dev-jane.local --image myapp:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 373**: `dockvirt up --name app1 --domain app1.local --image nginx --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 374**: `dockvirt up --name app2 --domain app2.local --image apache --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 390**: `dockvirt up --name production-app --domain app.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 439**: `dockvirt up --name my-app --image nginx:latest`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

### examples/README.md

**Line 190**: `dockvirt check`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 193**: `dockvirt setup --install`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 206**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 213**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 220**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 238**: `dockvirt check`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 239**: `dockvirt setup --install`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 256**: `dockvirt down --name <name>`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 257**: `dockvirt ip --name <name>`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

### examples/1-static-nginx-website/README.md

**Line 17**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 26**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 33**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 52**: `dockvirt down --name static-site`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 57**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

### examples/2-python-flask-app/README.md

**Line 16**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 19**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 28**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 47**: `dockvirt down --name flask-app`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 60**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

### examples/3-multi-os-comparison/README.md

**Line 24**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 36**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 65**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 79**: `time dockvirt up --name perf-ubuntu --domain ubuntu.local --image nginx:latest --port 80`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 82**: `time dockvirt up --name perf-fedora --domain fedora.local --image nginx:latest --port 80 --os fedora38`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 88**: `dockvirt down --name ubuntu-test`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 89**: `dockvirt down --name fedora-test`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 90**: `dockvirt down --name debian-test`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 97**: `ls -la ~/.dockvirt/images/`
- **Error**: Invalid command format
- **Duration**: 0.00s

### examples/4-microservices-stack/README.md

**Line 41**: `dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 44**: `dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 47**: `dockvirt up --name database --domain db.stack.local --image postgres:latest --port 5432 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 50**: `dockvirt up --name monitoring --domain mon.stack.local --image grafana/grafana:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 57**: `dockvirt stack deploy microservices-stack.yaml`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 194**: `dockvirt down --name frontend`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 195**: `dockvirt down --name backend`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 196**: `dockvirt down --name database`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 197**: `dockvirt down --name monitoring`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 200**: `dockvirt stack destroy microservices-stack`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

### examples/5-production-deployment/README.md

**Line 77**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 86**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 94**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 102**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 111**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 120**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 130**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 141**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 150**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

### CONTRIBUTING.md

**Line 15**: `git clone https://github.com/TWOJA_NAZWA_UŻYTKOWNIKA/dockvirt.git`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 16**: `cd dockvirt`
- **Error**: Invalid command format
- **Duration**: 0.00s

### todo.md

**Line 108**: `dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 109**: `dockvirt up --name backend --domain backend.local --image backend-app:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 110**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 113**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 123**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 124**: `dockvirt up --name static-site --domain static-site.local --image my-static-website:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 130**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 131**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 132**: `dockvirt up --name flask-app --domain flask-app.local --image my-flask-app:latest --port 5000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 138**: `dockvirt up --name ubuntu-test --domain ubuntu-test.local --image multi-os-demo:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 139**: `dockvirt up --name fedora-test --domain fedora-test.local --image multi-os-demo:latest --port 80 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 221**: `dockvirt --help`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 222**: `dockvirt up --help`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 23**: `dockvirt --help`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 243**: `dockvirt/vm_manager.py`
- **Error**: Invalid command format
- **Duration**: 0.00s

### command_test_results.md

**Line 14**: `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 18**: `dockvirt up --name backend --domain backend.local --image httpd:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 22**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 42**: `dockvirt up --name my-app --domain my-app.local --image my-app:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 50**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 54**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 58**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 62**: `dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 66**: `dockvirt up --name client-b --domain client-b.myaas.com --image nginx:latest --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 70**: `dockvirt up --name client-c --domain beta.myaas.com --image myapp:v2.1 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 74**: `dockvirt up --name dev-john-frontend --domain app.dev-john.local --image myapp:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 78**: `dockvirt up --name dev-john-api --domain api.dev-john.local --image myapp:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 82**: `dockvirt up --name dev-jane-frontend --domain app.dev-jane.local --image myapp:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 86**: `dockvirt up --name dev-jane-api --domain api.dev-jane.local --image myapp:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 90**: `dockvirt up --name app1 --domain app1.local --image nginx --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 94**: `dockvirt up --name app2 --domain app2.local --image apache --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 98**: `dockvirt up --name production-app --domain app.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 102**: `dockvirt up --name my-app --image nginx:latest`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 108**: `dockvirt check`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 112**: `dockvirt setup --install`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 116**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 120**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 124**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 128**: `dockvirt check`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 132**: `dockvirt setup --install`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 136**: `dockvirt down --name <name>`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 140**: `dockvirt ip --name <name>`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 146**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 150**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 154**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 158**: `dockvirt down --name static-site`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 162**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 168**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 172**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 176**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 180**: `dockvirt down --name flask-app`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 184**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 190**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 194**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 198**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 210**: `dockvirt down --name ubuntu-test`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 214**: `dockvirt down --name fedora-test`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 218**: `dockvirt down --name debian-test`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 228**: `dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 232**: `dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 236**: `dockvirt up --name database --domain db.stack.local --image postgres:latest --port 5432 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 240**: `dockvirt up --name monitoring --domain mon.stack.local --image grafana/grafana:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 244**: `dockvirt stack deploy microservices-stack.yaml`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 248**: `dockvirt down --name frontend`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 252**: `dockvirt down --name backend`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 256**: `dockvirt down --name database`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 260**: `dockvirt down --name monitoring`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 264**: `dockvirt stack destroy microservices-stack`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 270**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 274**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 278**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 282**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 286**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 290**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 294**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 298**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 302**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 318**: `dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 322**: `dockvirt up --name backend --domain backend.local --image backend-app:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 326**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 330**: `dockvirt up \`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 334**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 338**: `dockvirt up --name static-site --domain static-site.local --image my-static-website:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 342**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 346**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 350**: `dockvirt up --name flask-app --domain flask-app.local --image my-flask-app:latest --port 5000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 354**: `dockvirt up --name ubuntu-test --domain ubuntu-test.local --image multi-os-demo:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 358**: `dockvirt up --name fedora-test --domain fedora-test.local --image multi-os-demo:latest --port 80 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 362**: `dockvirt --help`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 366**: `dockvirt up --help`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 370**: `dockvirt --help`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 374**: `dockvirt/vm_manager.py`
- **Error**: Invalid command format
- **Duration**: 0.00s

**Line 380**: `dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 384**: `dockvirt up --name backend --domain backend.local --image backend-app:latest --port 8080`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 388**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 392**: `dockvirt up --name my-app --domain my-app.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 396**: `dockvirt up --name fedora-app --domain fedora-app.local --image httpd:latest --port 80 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 400**: `dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 404**: `dockvirt up --name client-b --domain client-b.myaas.com --image myapp:v1.9 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 408**: `dockvirt stack deploy dev-john`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 412**: `dockvirt generate-image --type deb-package --output my-app.deb`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 416**: `dockvirt generate-image --type raspberry-pi --size 8GB --output rpi-dockvirt.img`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 420**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 424**: `dockvirt up --name static-site --domain static-site.local --image my-static-website:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 428**: `dockvirt up --name static-site-fedora --domain static-site-fedora.local --image my-static-website:latest --port 80 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 432**: `dockvirt up`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 436**: `dockvirt up --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 440**: `dockvirt up --name flask-app --domain flask-app.local --image my-flask-app:latest --port 5000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 444**: `dockvirt up --name ubuntu-test --domain ubuntu-test.local --image multi-os-demo:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 448**: `dockvirt up --name fedora-test --domain fedora-test.local --image multi-os-demo:latest --port 80 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 452**: `dockvirt up --name debian-test --domain debian-test.local --image nginx:latest --port 80 --os debian11`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 464**: `dockvirt up --name frontend --domain app.stack.local --image microstack-frontend:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 468**: `dockvirt up --name backend --domain api.stack.local --image microstack-api:latest --port 8080 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 472**: `dockvirt up --name database --domain db.stack.local --image microstack-db:latest --port 5432 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 476**: `dockvirt up --name monitoring --domain mon.stack.local --image microstack-monitoring:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 480**: `dockvirt up --name lb-prod --domain lb.prod.com --image nginx-lb:prod --port 80 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 484**: `dockvirt up --name frontend-1 --domain app1.prod.com --image ecommerce-frontend:v2.1.0 --port 3000 --mem 2048 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 488**: `dockvirt up --name api-1 --domain api1.prod.com --image ecommerce-api:v2.1.0 --port 8080 --mem 4096 --cpus 4 --os fedora38`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 492**: `dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 496**: `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 500**: `dockvirt up --name my-app --domain my-app.local --image my-app:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 504**: `dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 508**: `dockvirt up --name frontend --domain frontend.local --image my-frontend:latest --port 3000 --os ubuntu22.04`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 512**: `dockvirt stack deploy`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 516**: `dockvirt generate-image`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 520**: `dockvirt stack deploy`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 524**: `dockvirt generate-image`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 532**: `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 533**: `dockvirt up --name backend --domain backend.local --image httpd:latest --port 80`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

**Line 534**: `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
- **Error**: Exception: 'NoneType' object has no attribute 'invoke'
- **Duration**: 0.00s

## 🔧 Recommendations

### Commands to Fix:
- **Exception**: 190 commands
  - `dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80`
  - `dockvirt up --name backend --domain backend.local --image httpd:latest --port 80`
  - `dockvirt up --name db --domain db.local --image postgres:latest --port 5432`
  - ... and 187 more

- **Invalid command format**: 12 commands
  - `pip install dockvirt`
  - `git clone https://github.com/dynapsys/dockvirt.git`
  - `cd dockvirt`
  - ... and 9 more
