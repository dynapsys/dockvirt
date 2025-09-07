#!/usr/bin/env python3
"""
DockerVirt LAN Exposure - Test HTTP Server

Purpose:
- Serve a simple HTML page on a local port (default 8080)
- Used to validate LAN exposure (iptables DNAT: Host:80 -> 127.0.0.1:8080)
- Designed to be run via systemd for persistence

Usage:
  python3 scripts/test_server.py --port 8080 --host 127.0.0.1

"""

import argparse
import http.server
import socketserver
from datetime import datetime
import sys


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Friendlier logging to stdout for systemd journal
        sys.stdout.write("%s - - [%s] %s\n" % (
            self.client_address[0],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            format % args,
        ))

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>DockerVirt LAN Test - Static Website</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; background: #0f172a; color: #e2e8f0; }}
    .card {{ background: #111827; padding: 24px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 900px; margin: 0 auto; }}
    h1 {{ margin-top: 0; }}
    .ok {{ background: #065f46; padding: 12px 16px; border-radius: 8px; display: inline-block; }}
    .info {{ background: #1f2937; padding: 12px 16px; border-radius: 8px; }}
    code {{ background: #0b1220; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>🌐 DockerVirt LAN Network Exposure Test</h1>

    <p class="ok">✅ SUCCESS: Network Exposure Working!</p>

    <div class="info">
      <h3>Access Information</h3>
      <ul>
        <li><strong>Original Service:</strong> 127.0.0.1:{{PORT}}</li>
        <li><strong>LAN Access:</strong> Your host IP on port 80</li>
        <li><strong>Method:</strong> iptables DNAT (PREROUTING)</li>
        <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
      </ul>
    </div>

    <p>Try opening from another device in LAN: <code>http://&lt;HOST_IP&gt;</code></p>
  </div>
</body>
</html>
"""
            # Replace placeholder without introducing templating engine
            html_content = html_content.replace("{{PORT}}", str(self.server.server_address[1]))
            self.wfile.write(html_content.encode("utf-8"))
        else:
            super().do_GET()


def main():
    parser = argparse.ArgumentParser(description="DockerVirt LAN test HTTP server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()

    print("🚀 Starting DockerVirt LAN Test Server")
    print(f"📍 Serving on: http://{args.host}:{args.port}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)

    with socketserver.TCPServer((args.host, args.port), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
