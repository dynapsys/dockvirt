#!/bin/bash
# Firefox Deweloperski - HTTPS bez ostrzeżeń o certyfikatach
# Używaj TYLKO do testowania lokalnych aplikacji VM

echo "=== Firefox Deweloperski - HTTPS bez ostrzeżeń ==="
echo "🔧 Uruchamianie Firefox z wyłączonymi ostrzeżeniami HTTPS"
echo "⚠️  UWAGA: Używaj TYLKO do testowania lokalnych VM!"
echo ""

# Tworzenie tymczasowego profilu Firefox dla deweloperki
TEMP_PROFILE="/tmp/firefox-dev-profile-$$"
mkdir -p "$TEMP_PROFILE"

# Konfiguracja Firefox user.js z wyłączonymi sprawdzeniami HTTPS
cat > "$TEMP_PROFILE/user.js" << 'EOF'
// Wyłączenie ostrzeżeń HTTPS dla deweloperki
user_pref("security.tls.insecure_fallback_hosts", "dockvirt.dev,*.dockvirt.dev,localhost,127.0.0.1");
user_pref("security.mixed_content.block_active_content", false);
user_pref("security.mixed_content.block_display_content", false);
user_pref("security.cert_pinning.enforcement_level", 0);
user_pref("security.tls.hello_downgrade_check", false);
user_pref("browser.xul.error_pages.expert_bad_cert", true);
user_pref("general.warnOnAboutConfig", false);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.sessionstore.warnOnQuit", false);
EOF

echo "🚀 Uruchamianie Firefox Deweloperski..."
echo "📱 URL: ${1:-https://static-site-https.dockvirt.dev/}"
echo ""

# Uruchomienie Firefox z tymczasowym profilem i bez sprawdzania certyfikatów
firefox \
    --profile "$TEMP_PROFILE" \
    --no-remote \
    --ignore-certificate-errors \
    --ignore-ssl-errors \
    --ignore-certificate-errors-spki-list \
    --disable-web-security \
    "${1:-https://static-site-https.dockvirt.dev/}" &

FIREFOX_PID=$!
echo "✅ Firefox Deweloperski uruchomiony (PID: $FIREFOX_PID)"
echo "🔧 Profil tymczasowy: $TEMP_PROFILE"
echo ""
echo "Po zakończeniu testowania, zamknij Firefox a profil zostanie usunięty."

# Funkcja czyszcząca po zakończeniu
cleanup() {
    echo ""
    echo "🧹 Czyszczenie profilu tymczasowego..."
    rm -rf "$TEMP_PROFILE" 2>/dev/null
    echo "✅ Profile tymczasowy usunięty"
}

# Rejestracja funkcji czyszczącej
trap cleanup EXIT

# Oczekiwanie na zakończenie Firefox
wait $FIREFOX_PID
