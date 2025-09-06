#!/usr/bin/env python3
"""
HTTPS Domain Setup for DockerVirt VMs
Creates full domain names and configures HTTPS with TLS certificates
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Full domain configuration
DOMAINS_CONFIG = {
    "static-site": {
        "domain": "static-site.dockvirt.dev",
        "port": 80,
        "https_port": 443,
        "cert_type": "self_signed"
    },
    "flask-app": {
        "domain": "flask-app.dockvirt.dev", 
        "port": 5000,
        "https_port": 443,
        "cert_type": "self_signed"
    },
    "frontend": {
        "domain": "frontend.dockvirt.dev",
        "port": 80, 
        "https_port": 443,
        "cert_type": "self_signed"
    }
}

def run_cmd(cmd, cwd=None):
    """Execute command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"

def create_ca_certificate():
    """Create Certificate Authority for self-signed certificates"""
    ca_dir = Path.home() / ".dockvirt" / "certs" / "ca"
    ca_dir.mkdir(parents=True, exist_ok=True)
    
    ca_key = ca_dir / "ca-key.pem"
    ca_cert = ca_dir / "ca-cert.pem"
    
    if ca_cert.exists():
        print("✅ CA certificate already exists")
        return True
    
    print("🔐 Creating Certificate Authority...")
    
    # Generate CA private key
    success, stdout, stderr = run_cmd(f"openssl genrsa -out {ca_key} 4096")
    if not success:
        print(f"❌ Failed to generate CA key: {stderr}")
        return False
    
    # Generate CA certificate
    ca_subject = "/C=US/ST=California/L=San Francisco/O=DockerVirt Dev/OU=IT Department/CN=DockerVirt CA"
    success, stdout, stderr = run_cmd(
        f'openssl req -new -x509 -days 365 -key {ca_key} -out {ca_cert} -subj "{ca_subject}"'
    )
    if not success:
        print(f"❌ Failed to generate CA certificate: {stderr}")
        return False
    
    # Set proper permissions
    os.chmod(ca_key, 0o600)
    os.chmod(ca_cert, 0o644)
    
    print(f"✅ CA certificate created: {ca_cert}")
    return True

def create_domain_certificate(domain_name, domain_config):
    """Create SSL certificate for domain"""
    certs_dir = Path.home() / ".dockvirt" / "certs" / "domains"
    certs_dir.mkdir(parents=True, exist_ok=True)
    
    domain_key = certs_dir / f"{domain_name}-key.pem"
    domain_csr = certs_dir / f"{domain_name}-csr.pem" 
    domain_cert = certs_dir / f"{domain_name}-cert.pem"
    
    if domain_cert.exists():
        print(f"✅ Certificate for {domain_config['domain']} already exists")
        return True
    
    print(f"🔐 Creating certificate for {domain_config['domain']}...")
    
    # Generate domain private key
    success, stdout, stderr = run_cmd(f"openssl genrsa -out {domain_key} 2048")
    if not success:
        print(f"❌ Failed to generate key for {domain_name}: {stderr}")
        return False
    
    # Generate certificate signing request
    domain_subject = f"/C=US/ST=California/L=San Francisco/O=DockerVirt Dev/OU=IT Department/CN={domain_config['domain']}"
    success, stdout, stderr = run_cmd(
        f'openssl req -new -key {domain_key} -out {domain_csr} -subj "{domain_subject}"'
    )
    if not success:
        print(f"❌ Failed to generate CSR for {domain_name}: {stderr}")
        return False
    
    # Sign certificate with CA
    ca_dir = Path.home() / ".dockvirt" / "certs" / "ca"
    ca_key = ca_dir / "ca-key.pem"
    ca_cert = ca_dir / "ca-cert.pem"
    
    success, stdout, stderr = run_cmd(
        f"openssl x509 -req -in {domain_csr} -CA {ca_cert} -CAkey {ca_key} -CAcreateserial -out {domain_cert} -days 365"
    )
    if not success:
        print(f"❌ Failed to sign certificate for {domain_name}: {stderr}")
        return False
    
    # Set proper permissions
    os.chmod(domain_key, 0o600)
    os.chmod(domain_cert, 0o644)
    
    # Clean up CSR
    domain_csr.unlink(missing_ok=True)
    
    print(f"✅ Certificate created for {domain_config['domain']}: {domain_cert}")
    return True

def create_caddy_https_config():
    """Create Caddy configuration with HTTPS support"""
    caddy_config = {
        "admin": {
            "disabled": True
        },
        "apps": {
            "http": {
                "servers": {
                    "srv0": {
                        "listen": [":80", ":443"],
                        "routes": []
                    }
                }
            },
            "tls": {
                "certificates": {
                    "load_files": []
                }
            }
        }
    }
    
    certs_dir = Path.home() / ".dockvirt" / "certs" / "domains"
    
    for domain_name, domain_config in DOMAINS_CONFIG.items():
        domain_cert = certs_dir / f"{domain_name}-cert.pem"
        domain_key = certs_dir / f"{domain_name}-key.pem"
        
        # Add certificate loading
        caddy_config["apps"]["tls"]["certificates"]["load_files"].append({
            "certificate": str(domain_cert),
            "key": str(domain_key)
        })
        
        # Add HTTP route (redirect to HTTPS)
        caddy_config["apps"]["http"]["servers"]["srv0"]["routes"].append({
            "match": [{"host": [domain_config["domain"]]}],
            "handle": [{
                "handler": "static_response",
                "status_code": 301,
                "headers": {
                    "Location": [f"https://{domain_config['domain']}"]
                }
            }],
            "terminal": True
        })
        
        # Add HTTPS route
        caddy_config["apps"]["http"]["servers"]["srv0"]["routes"].append({
            "match": [{"host": [domain_config["domain"]], "protocol": "https"}],
            "handle": [{
                "handler": "reverse_proxy",
                "upstreams": [{"dial": f"localhost:{domain_config['port']}"}]
            }],
            "terminal": True
        })
    
    return caddy_config

def update_vm_with_https(vm_name, domain_config):
    """Update VM configuration to support HTTPS"""
    print(f"🔧 Updating {vm_name} VM for HTTPS...")
    
    # Create updated docker-compose template
    compose_template = f"""version: '3.8'
services:
  app:
    image: {vm_name}:latest
    restart: unless-stopped
    networks:
      - app-network
    
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile.json:/etc/caddy/caddy.json:ro
      - caddy_data:/data
      - caddy_config:/config
      - /home/ubuntu/.dockvirt/certs:/certs:ro
    networks:
      - app-network
    command: ["caddy", "run", "--config", "/etc/caddy/caddy.json"]

networks:
  app-network:
    driver: bridge

volumes:
  caddy_data:
  caddy_config:
"""
    
    # Create Caddyfile.json for this VM
    caddy_config = create_caddy_https_config()
    
    # Write templates to dockvirt templates directory
    templates_dir = Path("/home/tom/github/dynapsys/dockvirt/dockvirt/templates")
    
    with open(templates_dir / "docker-compose-https.yml.j2", "w") as f:
        f.write(compose_template)
    
    with open(templates_dir / "Caddyfile-https.json.j2", "w") as f:
        json.dump(caddy_config, f, indent=2)
    
    return True

def setup_hosts_file():
    """Add domain entries to /etc/hosts"""
    print("📝 Updating /etc/hosts with full domain names...")
    
    hosts_entries = []
    
    # Get current VM IPs
    success, stdout, stderr = run_cmd("virsh --connect qemu:///system net-dhcp-leases default")
    if not success:
        print("⚠️  Could not get VM IPs, skipping /etc/hosts update")
        return True
    
    for domain_name, domain_config in DOMAINS_CONFIG.items():
        # Find VM IP from DHCP leases
        for line in stdout.splitlines():
            if domain_name in line:
                parts = line.split()
                if len(parts) >= 5:
                    ip = parts[4].split('/')[0]
                    hosts_entries.append(f"{ip} {domain_config['domain']}")
                    break
    
    if hosts_entries:
        print("Adding to /etc/hosts:")
        for entry in hosts_entries:
            print(f"  {entry}")
        
        # Add entries to /etc/hosts
        hosts_content = "\n".join(hosts_entries) + "\n"
        success, stdout, stderr = run_cmd(f'echo "{hosts_content}" | sudo tee -a /etc/hosts')
        if success:
            print("✅ /etc/hosts updated")
        else:
            print(f"❌ Failed to update /etc/hosts: {stderr}")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up HTTPS domains for DockerVirt VMs")
    print("=" * 50)
    
    # 1. Create CA certificate
    if not create_ca_certificate():
        print("❌ Failed to create CA certificate")
        return False
    
    # 2. Create domain certificates
    for domain_name, domain_config in DOMAINS_CONFIG.items():
        if not create_domain_certificate(domain_name, domain_config):
            print(f"❌ Failed to create certificate for {domain_name}")
            return False
    
    # 3. Update VM configurations
    for domain_name, domain_config in DOMAINS_CONFIG.items():
        if not update_vm_with_https(domain_name, domain_config):
            print(f"❌ Failed to update {domain_name} VM configuration")
            return False
    
    # 4. Setup hosts file
    if not setup_hosts_file():
        print("❌ Failed to setup hosts file")
        return False
    
    print("=" * 50)
    print("✅ HTTPS setup completed!")
    print("\n📋 Next steps:")
    print("1. Recreate VMs with new HTTPS configuration:")
    for domain_name, domain_config in DOMAINS_CONFIG.items():
        print(f"   dockvirt down --name {domain_name}")
        print(f"   dockvirt up --name {domain_name} --domain {domain_config['domain']} --https")
    
    print("\n2. Access your VMs via HTTPS:")
    for domain_name, domain_config in DOMAINS_CONFIG.items():
        print(f"   https://{domain_config['domain']}/")
    
    print("\n3. Trust the CA certificate in your browser:")
    ca_cert = Path.home() / ".dockvirt" / "certs" / "ca" / "ca-cert.pem"
    print(f"   Import: {ca_cert}")
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
