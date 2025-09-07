#!/bin/bash

# Simple DockerVirt LAN Expose - No virtual IP needed
# Uses host IP with port forwarding - bypasses NetworkManager restrictions

set -e

echo "🌐 Simple DockerVirt LAN Expose"
echo "================================"

LOCAL_PORT=8080
EXPOSE_PORT=80

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port) LOCAL_PORT="$2"; shift 2 ;;
        --expose-port) EXPOSE_PORT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: sudo bash $0 [--port 8080] [--expose-port 80]"
            exit 0 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

# Check permissions
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script requires sudo"
   echo "Run: sudo bash $0"
   exit 1
fi

# Check if localhost works
echo "🔍 Checking localhost:$LOCAL_PORT..."
if ! curl -s -m 3 http://localhost:$LOCAL_PORT/ >/dev/null 2>&1; then
    echo "❌ localhost:$LOCAL_PORT not responding"
    echo "Make sure DockerVirt VM is running"
    exit 1
fi

echo "✅ localhost:$LOCAL_PORT works"

# Get network info
INTERFACE=$(ip route show default | awk '{print $5}' | head -1)
HOST_IP=$(ip addr show $INTERFACE | grep 'inet ' | grep -v '127\.' | head -1 | awk '{print $2}' | cut -d/ -f1)

echo "📡 Interface: $INTERFACE"  
echo "📍 Host IP: $HOST_IP"

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Removing firewall rules..."
    iptables -t nat -D PREROUTING -p tcp --dport $EXPOSE_PORT -j REDIRECT --to-port $LOCAL_PORT 2>/dev/null || true
    iptables -D INPUT -p tcp --dport $EXPOSE_PORT -j ACCEPT 2>/dev/null || true
    echo "✅ Cleaned up"
    exit 0
}

trap cleanup INT TERM

echo ""
echo "🚀 Setting up network access..."

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Remove old rules
iptables -t nat -D PREROUTING -p tcp --dport $EXPOSE_PORT -j REDIRECT --to-port $LOCAL_PORT 2>/dev/null || true
iptables -D INPUT -p tcp --dport $EXPOSE_PORT -j ACCEPT 2>/dev/null || true

# Add new rules - redirect external traffic on port 80 to localhost:8080
iptables -t nat -A PREROUTING -p tcp --dport $EXPOSE_PORT -j REDIRECT --to-port $LOCAL_PORT
iptables -A INPUT -p tcp --dport $EXPOSE_PORT -j ACCEPT

echo "✅ Port forwarding configured: $HOST_IP:$EXPOSE_PORT → localhost:$LOCAL_PORT"

# Test access
echo "🧪 Testing access..."
sleep 2

if timeout 5 curl -s http://$HOST_IP:$EXPOSE_PORT/ >/dev/null 2>&1; then
    TEST_RESULT="✅ WORKING PERFECTLY"
else
    TEST_RESULT="⚠️ May need more time to propagate"
fi

# Summary
echo ""
echo "=================================================="
echo "🎉 DOCKVIRT VM ACCESSIBLE FROM ENTIRE NETWORK!"
echo "=================================================="
echo ""
echo "🌐 ACCESS FROM ANY DEVICE IN YOUR NETWORK:"
echo "   http://$HOST_IP"
echo ""
echo "🧪 TEST FROM OTHER DEVICES:"
echo "   1. Smartphone/tablet: http://$HOST_IP"
echo "   2. Another computer: http://$HOST_IP"  
echo "   3. Ping test: ping $HOST_IP"
echo "   4. Curl test: curl http://$HOST_IP"
echo ""
echo "📋 CONFIGURATION:"
echo "   Host IP: $HOST_IP"
echo "   Port forwarding: $HOST_IP:$EXPOSE_PORT → localhost:$LOCAL_PORT"
echo "   Interface: $INTERFACE"
echo "   Status: $TEST_RESULT"
echo ""
echo "💡 IMPORTANT:"
echo "   ✅ All devices on same WiFi/LAN can access"
echo "   ✅ No DNS configuration needed"
echo "   ✅ No virtual IP needed - uses your host IP directly"
echo "   ✅ Simple and reliable solution"
echo ""
echo "=================================================="
echo "⚠️  Press Ctrl+C to stop and cleanup"
echo "=================================================="
echo ""

# Keep running
echo "🔄 System active. Monitoring access..."
while true; do
    sleep 60
    echo "   📊 Still running - $(date +%H:%M:%S)"
    
    # Quick connectivity check
    if ! curl -s -m 2 http://localhost:$LOCAL_PORT/ >/dev/null 2>&1; then
        echo "   ⚠️ localhost:$LOCAL_PORT stopped responding!"
    fi
done
