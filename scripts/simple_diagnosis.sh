#!/bin/bash

# Simple DockerVirt LAN Diagnosis - No external dependencies
# Tests content and connectivity for network exposure

echo "🔍 DockerVirt LAN Diagnosis - Content & Connectivity Test"
echo "=========================================================="

HOST_IP="192.168.188.226"

echo "🕐 Test started: $(date +%H:%M:%S)"
echo ""

# 1. Test localhost:8080 (original service)
echo "1️⃣ TESTING LOCALHOST:8080 (Original Service)"
echo "---------------------------------------------"

if curl -s --connect-timeout 5 http://localhost:8080/ >/dev/null 2>&1; then
    echo "✅ Connection: SUCCESS"
    
    # Get content details
    CONTENT=$(curl -s --connect-timeout 5 http://localhost:8080/ 2>/dev/null)
    SIZE=${#CONTENT}
    LINES=$(echo "$CONTENT" | wc -l)
    
    echo "📄 Content size: $SIZE bytes, $LINES lines"
    
    # Show first few lines
    echo "📋 Content preview:"
    echo "$CONTENT" | head -5 | while read line; do
        echo "   $line"
    done
    
    # Check if it's HTML
    if echo "$CONTENT" | grep -qi "<!DOCTYPE\|<html\|<body"; then
        echo "📝 Content type: HTML document"
        TITLE=$(echo "$CONTENT" | grep -i "<title>" | sed 's/<[^>]*>//g' | xargs)
        if [[ -n "$TITLE" ]]; then
            echo "📋 Page title: $TITLE"
        fi
    else
        echo "📝 Content type: Plain text or other"
    fi
    
    LOCALHOST_WORKING=true
else
    echo "❌ Connection: FAILED"
    echo "📄 localhost:8080 not responding"
    LOCALHOST_WORKING=false
fi

echo ""

# 2. Test host IP port 80 (network exposure)
echo "2️⃣ TESTING HOST IP PORT 80 (Network Exposure)"
echo "-----------------------------------------------"

if curl -s --connect-timeout 5 http://$HOST_IP:80/ >/dev/null 2>&1; then
    echo "✅ Connection: SUCCESS"
    
    # Get content details
    CONTENT_80=$(curl -s --connect-timeout 5 http://$HOST_IP:80/ 2>/dev/null)
    SIZE_80=${#CONTENT_80}
    LINES_80=$(echo "$CONTENT_80" | wc -l)
    
    echo "📄 Content size: $SIZE_80 bytes, $LINES_80 lines"
    
    # Show first few lines
    echo "📋 Content preview:"
    echo "$CONTENT_80" | head -5 | while read line; do
        echo "   $line"
    done
    
    # Check if it's HTML
    if echo "$CONTENT_80" | grep -qi "<!DOCTYPE\|<html\|<body"; then
        echo "📝 Content type: HTML document"
        TITLE_80=$(echo "$CONTENT_80" | grep -i "<title>" | sed 's/<[^>]*>//g' | xargs)
        if [[ -n "$TITLE_80" ]]; then
            echo "📋 Page title: $TITLE_80"
        fi
    else
        echo "📝 Content type: Plain text or other"
    fi
    
    HOST_PORT_WORKING=true
else
    echo "❌ Connection: FAILED"
    echo "📄 $HOST_IP:80 not responding"
    HOST_PORT_WORKING=false
fi

echo ""

# 3. Content comparison
echo "3️⃣ CONTENT COMPARISON"
echo "----------------------"

if [[ "$LOCALHOST_WORKING" == "true" && "$HOST_PORT_WORKING" == "true" ]]; then
    if [[ "$CONTENT" == "$CONTENT_80" ]]; then
        echo "✅ Content IDENTICAL - Port forwarding working correctly"
        echo "📋 Both services return exactly the same content"
    else
        echo "⚠️ Content DIFFERENT - Potential issue"
        echo "📋 localhost:8080 size: $SIZE bytes"
        echo "📋 $HOST_IP:80 size: $SIZE_80 bytes"
        
        # Show differences
        echo "🔍 Content differences:"
        diff <(echo "$CONTENT") <(echo "$CONTENT_80") | head -10
    fi
elif [[ "$LOCALHOST_WORKING" == "true" ]]; then
    echo "⚠️ Only localhost:8080 working - Network exposure not active"
elif [[ "$HOST_PORT_WORKING" == "true" ]]; then
    echo "⚠️ Only $HOST_IP:80 working - Unusual configuration"
else
    echo "❌ Neither service responding - System issue"
fi

echo ""

# 4. Network diagnostics
echo "4️⃣ NETWORK DIAGNOSTICS"
echo "-----------------------"

# Check if ports are listening
echo "🚪 Port status check:"
if netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    echo "   ✅ Port 8080: Listening"
else
    echo "   ❌ Port 8080: Not listening"
fi

if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    echo "   ✅ Port 80: Listening" 
else
    echo "   ❌ Port 80: Not listening"
fi

# Check iptables rules
echo ""
echo "🔧 Active iptables rules:"
RULES=$(sudo iptables -t nat -L PREROUTING -n 2>/dev/null | grep -E "DNAT|REDIRECT")
if [[ -n "$RULES" ]]; then
    echo "$RULES" | while read rule; do
        echo "   $rule"
    done
else
    echo "   ❌ No DNAT/REDIRECT rules found"
fi

# Check VM status
echo ""
echo "🖥️ VM Status:"
if sudo virsh list --state-running 2>/dev/null | grep -q "static-site"; then
    echo "   ✅ VM 'static-site' running"
    
    # Get VM IP
    VM_DHCP=$(sudo virsh net-dhcp-leases default 2>/dev/null | grep static-site)
    if [[ -n "$VM_DHCP" ]]; then
        VM_IP=$(echo "$VM_DHCP" | grep -oE '192\.168\.122\.[0-9]+')
        echo "   📍 VM IP: $VM_IP"
        
        # Test VM direct access
        if curl -s --connect-timeout 3 http://$VM_IP:80/ >/dev/null 2>&1; then
            echo "   ✅ VM port 80: Responding"
        else
            echo "   ❌ VM port 80: Not responding"
        fi
    fi
else
    echo "   ❌ VM 'static-site' not running"
fi

echo ""

# 5. Summary and recommendations
echo "=========================================================="
echo "📊 DIAGNOSIS SUMMARY"
echo "=========================================================="
echo ""

if [[ "$LOCALHOST_WORKING" == "true" && "$HOST_PORT_WORKING" == "true" ]]; then
    echo "🎉 SUCCESS: Network exposure is working!"
    echo ""
    echo "✅ Services status:"
    echo "   • localhost:8080 ✅ Working ($SIZE bytes)"
    echo "   • $HOST_IP:80 ✅ Working ($SIZE_80 bytes)"
    echo "   • Content matching ✅ $([ "$CONTENT" = "$CONTENT_80" ] && echo "Identical" || echo "Different")"
    echo ""
    echo "🌐 Network access:"
    echo "   • From this computer: http://$HOST_IP"
    echo "   • From other devices: http://$HOST_IP"
    echo "   • Smartphone/tablet: http://$HOST_IP"
    echo ""
    echo "💡 The solution is working correctly!"

elif [[ "$LOCALHOST_WORKING" == "true" ]]; then
    echo "⚠️ PARTIAL: localhost works, network exposure needs fixing"
    echo ""
    echo "✅ localhost:8080 working ($SIZE bytes)"
    echo "❌ $HOST_IP:80 not accessible"
    echo ""
    echo "🔧 Try fixing with:"
    echo "   sudo bash scripts/dockvirt_lan_simple.sh --port 8080"

else
    echo "❌ PROBLEM: Services not responding"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "   1. Check VM: sudo virsh list --all"
    echo "   2. Restart VM: cd examples/1-static-nginx-website && dockvirt up"
    echo "   3. Check port forwarding: sudo iptables -t nat -L"
fi

echo ""
echo "🕐 Test completed: $(date +%H:%M:%S)"
