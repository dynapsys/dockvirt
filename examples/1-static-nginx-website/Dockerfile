# Użyj oficjalnego obrazu Nginx
FROM nginx:alpine

# Skopiuj plik konfiguracyjny Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Skopiuj zawartość strony statycznej
COPY index.html /usr/share/nginx/html/index.html
