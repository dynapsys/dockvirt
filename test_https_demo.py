#!/usr/bin/env python3
"""
Demo HTTPS Server z DockerVirt SSL Certificates
Demonstracja działania certyfikatów HTTPS
"""
import http.server
import ssl
import socketserver
from pathlib import Path
import sys

def create_https_server(domain="flask-app.dockvirt.dev", port=8443):
    """Utworz HTTPS server z certyfikatami DockerVirt"""
    
    cert_dir = Path.home() / ".dockvirt" / "certs" / "domains"
    cert_file = cert_dir / "flask-app-cert.pem"
    key_file = cert_dir / "flask-app-key.pem"
    
    if not cert_file.exists() or not key_file.exists():
        print(f"❌ Brak certyfikatów SSL:")
        print(f"   Cert: {cert_file}")
        print(f"   Key: {key_file}")
        return False
    
    print(f"🔐 Uruchamianie HTTPS serwera demo...")
    print(f"   Domena: {domain}")
    print(f"   Port: {port}")
    print(f"   Cert: {cert_file}")
    print(f"   Key: {key_file}")
    
    # Utwórz prostą stronę HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>DockerVirt HTTPS Demo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .success {{ color: green; }}
        .domain {{ color: blue; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🔐 DockerVirt HTTPS Demo</h1>
    <p class="success">✅ HTTPS działa poprawnie!</p>
    <p>Domena: <span class="domain">{domain}</span></p>
    <p>Port: <span class="domain">{port}</span></p>
    <p>Certyfikat: Self-signed via DockerVirt CA</p>
    
    <h2>Test Połączenia</h2>
    <p>Aby przetestować w przeglądarce:</p>
    <ol>
        <li>Otwórz: <a href="https://{domain}:{port}/">https://{domain}:{port}/</a></li>
        <li>Zaakceptuj certyfikat (self-signed)</li>
        <li>Zobacz tę stronę z HTTPS</li>
    </ol>
    
    <h2>Import CA Certificate</h2>
    <p>Dla pełnego zaufania, zaimportuj CA:</p>
    <p><code>~/.dockvirt/certs/ca/ca-cert.pem</code></p>
</body>
</html>"""
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())
    
    try:
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            # Konfiguracja SSL
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)
            
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            
            print(f"🚀 Server uruchomiony na https://{domain}:{port}/")
            print(f"💡 Dodaj do /etc/hosts: 127.0.0.1 {domain}")
            print(f"🌐 Test w przeglądarce: https://{domain}:{port}/")
            print(f"⏹️  Zatrzymaj: Ctrl+C")
            
            httpd.serve_forever()
            
    except Exception as e:
        print(f"❌ Błąd serwera HTTPS: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_https_server()
