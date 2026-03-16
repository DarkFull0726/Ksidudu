#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  Setup V2Ray + SSL Automático — by DarkZFull
#  Uso: bash setup_v2ray.sh <dominio> <email>
#  Ejemplo: bash setup_v2ray.sh mia.darkfullhn.xyz admin@gmail.com
# ═══════════════════════════════════════════════════════════

DOMAIN=$1
EMAIL=$2
PORT_WS=8080
PATH_WS="/v2ray"
V2RAY_CFG="/usr/local/etc/v2ray/config.json"

# ── Colores ──
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  V2Ray + SSL Setup — by DarkZFull"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Verificar argumentos ──
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Uso: bash setup_v2ray.sh <dominio> <email>"
    echo "Ejemplo: bash setup_v2ray.sh mia.darkfullhn.xyz admin@gmail.com"
    exit 1
fi

info "Dominio: $DOMAIN"
info "Email:   $EMAIL"
echo ""

# ── 1. Instalar dependencias ──
info "Instalando dependencias..."
apt update -y > /dev/null 2>&1
apt install -y curl nginx certbot python3-certbot-nginx python3 > /dev/null 2>&1
ok "Dependencias instaladas"

# ── 2. Instalar V2Ray ──
info "Instalando V2Ray..."
bash <(curl -s https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) > /dev/null 2>&1
systemctl enable v2ray > /dev/null 2>&1
ok "V2Ray instalado"

# ── 3. Configurar V2Ray ──
info "Configurando V2Ray en puerto $PORT_WS WebSocket..."
cat > $V2RAY_CFG << EOF
{
  "log": {
    "access": "/var/log/v2ray/access.log",
    "error": "/var/log/v2ray/error.log",
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": $PORT_WS,
      "protocol": "vmess",
      "settings": { "clients": [] },
      "streamSettings": {
        "network": "ws",
        "wsSettings": { "path": "$PATH_WS" }
      }
    }
  ],
  "outbounds": [
    { "protocol": "freedom", "settings": {} }
  ]
}
EOF
systemctl start v2ray > /dev/null 2>&1
ok "V2Ray configurado"

# ── 4. Liberar puerto 80 temporalmente ──
info "Liberando puerto 80 para certificado SSL..."

# Detener nginx si está corriendo
systemctl stop nginx > /dev/null 2>&1

# Matar cualquier otro proceso en el 80
PIDS=$(lsof -ti :80 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    info "Matando procesos en puerto 80: $PIDS"
    kill -9 $PIDS 2>/dev/null
    sleep 2
fi

# Guardar qué servicios estaban activos para restaurar después
WAS_NGINX=0
systemctl is-active --quiet nginx && WAS_NGINX=1

ok "Puerto 80 liberado"

# ── 5. Obtener certificado SSL ──
info "Obteniendo certificado SSL para $DOMAIN..."
certbot certonly --standalone \
    -d $DOMAIN \
    --non-interactive \
    --agree-tos \
    -m $EMAIL

if [ $? -ne 0 ]; then
    err "Error obteniendo certificado. Verifica que $DOMAIN apunte a esta IP y el puerto 80 esté abierto en el firewall."
fi
ok "Certificado SSL obtenido"

# ── 6. Configurar Nginx con SSL ──
info "Configurando Nginx con SSL..."

# Remover configuración vieja si existe
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/v2ray
rm -f /etc/nginx/sites-available/v2ray

cat > /etc/nginx/sites-available/v2ray << EOF
server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location $PATH_WS {
        proxy_pass http://127.0.0.1:$PORT_WS;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 300s;
    }

    location / {
        return 200 'SSHFREE by DarkZFull';
        add_header Content-Type text/plain;
    }
}
EOF

ln -sf /etc/nginx/sites-available/v2ray /etc/nginx/sites-enabled/
nginx -t > /dev/null 2>&1 && systemctl start nginx > /dev/null 2>&1
ok "Nginx configurado con SSL"

# ── 7. Restaurar procesos que estaban en puerto 80 ──
# (Nginx ya ocupa el 443, el 80 queda libre)
info "Puerto 80 queda libre para otros servicios"

# ── 8. Crear usuario de prueba y generar VMess ──
info "Creando usuario de prueba..."

VMESS_LINK=$(python3 - << PYEOF
import json, uuid, base64

with open('$V2RAY_CFG') as f:
    config = json.load(f)

user_id = str(uuid.uuid4())
config['inbounds'][0]['settings']['clients'].append({
    "id": user_id, "alterId": 0, "email": "test@sshfree"
})

with open('$V2RAY_CFG', 'w') as f:
    json.dump(config, f, indent=2)

vmess = {
    "v":"2","ps":"$DOMAIN-SSHFREE",
    "add":"$DOMAIN","port":"443",
    "id":user_id,"aid":"0",
    "net":"ws","type":"none",
    "host":"$DOMAIN",
    "path":"$PATH_WS","tls":"tls"
}
print("vmess://" + base64.b64encode(json.dumps(vmess).encode()).decode())
PYEOF
)

systemctl restart v2ray > /dev/null 2>&1

# ── 9. Resultado final ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}  ✅ INSTALACIÓN COMPLETADA${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Dominio:    $DOMAIN"
echo "  Puerto:     443 (TLS)"
echo "  WebSocket:  $PATH_WS"
echo "  V2Ray:      Puerto $PORT_WS (interno)"
echo "  Cert:       /etc/letsencrypt/live/$DOMAIN/"
echo ""
echo "  VMESS de prueba:"
echo "  $VMESS_LINK"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Creado por @DarkZFull"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
