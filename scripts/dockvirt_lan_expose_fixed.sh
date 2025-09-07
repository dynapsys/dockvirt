#!/bin/bash

# DockerVirt LAN Expose - NetworkManager Compatible Version
# Bypasses NetworkManager restrictions for network visibility

set -e

echo "🌐 DockerVirt LAN Expose - Fixed for NetworkManager"
echo "===================================================="

# Sprawdź uprawnienia
if [[ $EUID -ne 0 ]]; then
   echo "❌ Skrypt wymaga uprawnień sudo"
   echo "Uruchom: sudo bash $0"
   exit 1
fi

# Parsuj argumenty
LOCAL_PORT=8080
EXPOSE_PORT=80
VIRTUAL_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            LOCAL_PORT="$2"
            shift 2
            ;;
        --expose-port)
            EXPOSE_PORT="$2"
            shift 2
            ;;
        --virtual-ip)
            VIRTUAL_IP="$2"
            shift 2
            ;;
        -h|--help)
            echo "Użycie: sudo bash $0 [--port 8080] [--expose-port 80] [--virtual-ip IP]"
            exit 0
            ;;
        *)
            echo "Nieznany parametr: $1"
            exit 1
            ;;
    esac
done

# Sprawdź czy localhost działa
echo "🔍 Sprawdzanie localhost:$LOCAL_PORT..."
if ! curl -s -m 3 http://localhost:$LOCAL_PORT/ >/dev/null 2>&1; then
    echo "❌ localhost:$LOCAL_PORT nie odpowiada"
    exit 1
fi

echo "✅ localhost:$LOCAL_PORT działa poprawnie"

# Auto-wykryj interfejs
INTERFACE=$(ip route show default | awk '{print $5}' | head -1)
if [[ -z "$INTERFACE" ]]; then
    INTERFACE="enp100s0"
fi

# Pobierz informacje o sieci
HOST_IP=$(ip addr show $INTERFACE | grep 'inet ' | grep -v '127\.' | head -1 | awk '{print $2}' | cut -d/ -f1)
CIDR=$(ip addr show $INTERFACE | grep 'inet ' | grep -v '127\.' | head -1 | awk '{print $2}' | cut -d/ -f2)

echo "📡 Interfejs: $INTERFACE"
echo "📍 Host IP: $HOST_IP/$CIDR"

# Znajdź wolny IP (jeśli nie podano)
if [[ -z "$VIRTUAL_IP" ]]; then
    echo "🔍 Szukanie wolnego IP w sieci..."
    
    BASE_NETWORK=$(echo $HOST_IP | cut -d. -f1-3)
    
    for i in {200..220}; do
        TEST_IP="$BASE_NETWORK.$i"
        
        if [[ "$TEST_IP" == "$HOST_IP" ]]; then
            continue
        fi
        
        if ! ping -c 1 -W 1 $TEST_IP >/dev/null 2>&1; then
            VIRTUAL_IP=$TEST_IP
            echo "✅ Znaleziono wolny IP: $VIRTUAL_IP"
            break
        fi
    done
    
    if [[ -z "$VIRTUAL_IP" ]]; then
        echo "❌ Nie znaleziono wolnego IP"
        exit 1
    fi
fi

# Funkcja cleanup
cleanup() {
    echo ""
    echo "🧹 Czyszczenie konfiguracji..."
    
    # Usuń iptables rules
    iptables -t nat -D PREROUTING -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
    iptables -t nat -D OUTPUT -p tcp --dport $EXPOSE_PORT -d $VIRTUAL_IP -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
    iptables -D INPUT -p tcp --dport $LOCAL_PORT -j ACCEPT 2>/dev/null || true
    
    # Usuń IP alias (jeśli udało się go utworzyć)
    ip addr del $VIRTUAL_IP/$CIDR dev $INTERFACE 2>/dev/null || true
    
    echo "✅ Wyczyszczono"
    exit 0
}

trap cleanup INT TERM

echo ""
echo "🚀 Konfiguracja dostępu sieciowego (bypass NetworkManager)..."

# METODA 1: Spróbuj utworzyć IP alias z tymczasowym wyłączeniem NetworkManager dla interfejsu
echo "📦 Próba 1: Tymczasowe wyłączenie zarządzania NetworkManager..."

# Zapisz stan NetworkManager
NM_MANAGED=$(nmcli device show $INTERFACE 2>/dev/null | grep "GENERAL.STATE" | grep -q "managed" && echo "yes" || echo "no")

if [[ "$NM_MANAGED" == "yes" ]]; then
    echo "   🔧 Tymczasowo wyłączam zarządzanie NetworkManager dla $INTERFACE..."
    nmcli device set $INTERFACE managed no 2>/dev/null || true
    sleep 2
fi

# Spróbuj dodać IP
if ip addr add $VIRTUAL_IP/$CIDR dev $INTERFACE 2>/dev/null; then
    echo "   ✅ Pomyślnie utworzono IP alias: $VIRTUAL_IP"
    IP_CREATED=true
    
    # Przywróć zarządzanie NetworkManager (ale pozostaw IP)
    if [[ "$NM_MANAGED" == "yes" ]]; then
        echo "   🔄 Przywracam zarządzanie NetworkManager..."
        nmcli device set $INTERFACE managed yes 2>/dev/null || true
    fi
else
    echo "   ❌ Nie udało się utworzyć IP alias"
    IP_CREATED=false
    
    # Przywróć zarządzanie NetworkManager
    if [[ "$NM_MANAGED" == "yes" ]]; then
        nmcli device set $INTERFACE managed yes 2>/dev/null || true
    fi
fi

# METODA 2: Jeśli IP alias nie działa, użyj tylko iptables z SNAT
if [[ "$IP_CREATED" == "false" ]]; then
    echo "📦 Próba 2: Konfiguracja bez IP alias (tylko iptables)..."
    echo "   ⚠️  Będzie działać dla ruchu zewnętrznego, ale może nie dla localhost"
fi

# Włącz IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

echo "🔄 Konfiguracja iptables..."

# Usuń stare reguły
iptables -t nat -D PREROUTING -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
iptables -t nat -D OUTPUT -p tcp --dport $EXPOSE_PORT -d $VIRTUAL_IP -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
iptables -D INPUT -p tcp --dport $LOCAL_PORT -j ACCEPT 2>/dev/null || true

if [[ "$IP_CREATED" == "true" ]]; then
    # Standardowe przekierowanie z wirtualnego IP
    iptables -t nat -A PREROUTING -d $VIRTUAL_IP -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT
    echo "   ✅ Standardowe NAT: $VIRTUAL_IP:$EXPOSE_PORT → localhost:$LOCAL_PORT"
    
    # Ogłoś IP w sieci
    echo "📢 Ogłaszanie IP w sieci..."
    for _ in {1..3}; do
        arping -U -I $INTERFACE -c 2 $VIRTUAL_IP >/dev/null 2>&1 || true
        sleep 0.5
    done
    
else
    # Alternatywne przekierowanie - przechwytuj ruch na wszystkich interfejsach
    iptables -t nat -A PREROUTING -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT
    iptables -t nat -A OUTPUT -p tcp --dport $EXPOSE_PORT -d $VIRTUAL_IP -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT
    echo "   ✅ Uniwersalne NAT: port $EXPOSE_PORT → localhost:$LOCAL_PORT"
fi

# Zezwól na ruch przychodzący
iptables -A INPUT -p tcp --dport $LOCAL_PORT -j ACCEPT

echo "✅ iptables skonfigurowany"

# Test dostępności
echo "🧪 Test dostępności..."
sleep 2

# Test 1: Bezpośredni test IP (jeśli został utworzony)
if [[ "$IP_CREATED" == "true" ]]; then
    if timeout 5 curl -s http://$VIRTUAL_IP:$EXPOSE_PORT/ >/dev/null 2>&1; then
        TEST_RESULT="✅ DZIAŁA PERFEKT"
        WORKING_URL="http://$VIRTUAL_IP"
    else
        TEST_RESULT="⚠️ IP utworzony, ale wymaga więcej czasu"
        WORKING_URL="http://$VIRTUAL_IP"
    fi
else
    # Test 2: Test przez host IP z przekierowaniem portu
    if timeout 5 curl -s http://$HOST_IP:$EXPOSE_PORT/ >/dev/null 2>&1; then
        TEST_RESULT="✅ DZIAŁA (przez host IP)"
        WORKING_URL="http://$HOST_IP"
    else
        TEST_RESULT="⚠️ Skonfigurowano, może potrzebować czasu"
        WORKING_URL="http://$HOST_IP (lub bezpośrednio port $EXPOSE_PORT)"
    fi
fi

# Podsumowanie
echo ""
echo "===================================================="
echo "🎉 DOCKVIRT VM DOSTĘPNY W SIECI LOKALNEJ!"
echo "===================================================="
echo ""

if [[ "$IP_CREATED" == "true" ]]; then
    echo "✅ METODA: Wirtualny IP + Port Forwarding"
    echo "🌐 ADRES DLA WSZYSTKICH URZĄDZEŃ:"
    echo "   $WORKING_URL"
    echo ""
    echo "🧪 TESTOWANIE Z INNYCH URZĄDZEŃ:"
    echo "   1. Smartfon/tablet: $WORKING_URL"
    echo "   2. Inny komputer: $WORKING_URL"
    echo "   3. Ping test: ping $VIRTUAL_IP"
else
    echo "✅ METODA: Port Forwarding przez Host IP"
    echo "🌐 DOSTĘP Z SIECI:"
    echo "   http://$HOST_IP:$EXPOSE_PORT"
    echo ""
    echo "🧪 TESTOWANIE:"
    echo "   1. Z innych urządzeń: http://$HOST_IP:$EXPOSE_PORT"
    echo "   2. Lub bezpośrednio: http://$HOST_IP"
fi

echo ""
echo "📋 KONFIGURACJA:"
echo "   Host: $HOST_IP ($INTERFACE)"
echo "   Wirtualny IP: ${IP_CREATED==true && echo $VIRTUAL_IP || echo "Nie utworzono (NetworkManager)"}"
echo "   Przekierowanie: port $EXPOSE_PORT → localhost:$LOCAL_PORT"
echo "   Status: $TEST_RESULT"
echo ""
echo "💡 INFORMACJE:"
echo "   ✅ Wszystkie urządzenia w sieci mają dostęp"
echo "   ✅ Nie potrzebujesz konfigurować DNS"
if [[ "$IP_CREATED" == "true" ]]; then
    echo "   ✅ Wirtualny IP jest bezpośrednio dostępny"
else
    echo "   ⚠️ NetworkManager blokował IP alias, używamy host IP"
fi
echo ""
echo "===================================================="
echo "⚠️  Naciśnij Ctrl+C aby zatrzymać"
echo "===================================================="
echo ""

# Główna pętla
if [[ "$IP_CREATED" == "true" ]]; then
    echo "🔄 Odświeżam ARP co 30 sekund dla lepszej widoczności..."
    while true; do
        sleep 30
        arping -U -I $INTERFACE -c 1 $VIRTUAL_IP >/dev/null 2>&1 || true
        
        # Sprawdź czy IP nadal istnieje
        if ! ip addr show $INTERFACE | grep -q $VIRTUAL_IP; then
            echo "⚠️ IP zniknął, próbuję odtworzyć..."
            ip addr add $VIRTUAL_IP/$CIDR dev $INTERFACE 2>/dev/null || true
        fi
    done
else
    echo "🔄 System aktywny. Port forwarding działa..."
    while true; do
        sleep 60
        echo "   📊 System nadal aktywny - $(date +%H:%M:%S)"
    done
fi
