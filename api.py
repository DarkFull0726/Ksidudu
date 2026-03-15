from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, subprocess, json, random, string, hashlib, time
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='.')
CORS(app)

# ═══════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════
DAYS_VALID   = 3
SSH_KEY      = os.path.expanduser("~/.ssh/id_bot")
USERS_DB     = "created_users.json"
WEB_SESSIONS = "web_sessions.json"  # sesiones web (IP → créditos)

WEB_CREDITS_DEFAULT = 3
WEB_REGEN_HOURS     = 10
WEB_MAX_CREDITS     = 3

VPS = {
    "brazil": {
        "IP": "216.238.105.165", "PORT": 22,
        "DOMAIN": "br.darkfullhn.xyz", "NS": "ns.darkfullhn.xyz",
        "LOCAL": False, "BYPASS_PAM": True,
        "FLAG": "🇧🇷", "NAME": "Brazil"
    },
    "mexico": {
        "IP": "64.177.80.171", "PORT": 22,
        "DOMAIN": "mxvlt.darkfullhn.xyz", "NS": "nsmxvlt.darkfullhn.xyz",
        "LOCAL": True, "BYPASS_PAM": False,
        "FLAG": "🇲🇽", "NAME": "México"
    },
    "chile": {
        "IP": "64.176.20.206", "PORT": 22,
        "DOMAIN": "cl.darkfullhn.xyz", "NS": "nscl.darkfullhn.xyz",
        "LOCAL": False, "BYPASS_PAM": True,
        "FLAG": "🇨🇱", "NAME": "Chile"
    },
    "dallas": {
        "IP": "149.28.241.124", "PORT": 22,
        "DOMAIN": "us.darkfullhn.xyz", "NS": "nsus.darkfullhn.xyz",
        "LOCAL": False, "BYPASS_PAM": True,
        "FLAG": "🇺🇸", "NAME": "Dallas"
    }
}

# ═══════════════════════════════════════
#  SESSIONS (créditos por IP)
# ═══════════════════════════════════════

def load_sessions():
    if not os.path.exists(WEB_SESSIONS):
        return {}
    with open(WEB_SESSIONS) as f:
        return json.load(f)

def save_sessions(data):
    with open(WEB_SESSIONS, "w") as f:
        json.dump(data, f, indent=2)

def get_client_id(request):
    """Identificador único por IP + user-agent hash."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '')
    raw = f"{ip}:{ua}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def get_or_create_session(cid):
    sessions = load_sessions()
    if cid not in sessions:
        sessions[cid] = {
            "credits": WEB_CREDITS_DEFAULT,
            "last_regen": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        save_sessions(sessions)
    return sessions[cid]

def apply_regen(cid):
    sessions = load_sessions()
    if cid not in sessions:
        get_or_create_session(cid)
        sessions = load_sessions()
    s = sessions[cid]
    last   = datetime.fromisoformat(s["last_regen"])
    earned = int((datetime.now() - last).total_seconds() / 3600 // WEB_REGEN_HOURS)
    if earned > 0:
        s["credits"]    = min(s["credits"] + earned, WEB_MAX_CREDITS)
        s["last_regen"] = (last + timedelta(hours=earned * WEB_REGEN_HOURS)).isoformat()
        sessions[cid]   = s
        save_sessions(sessions)
    return sessions[cid]

def spend_credit(cid):
    sessions = load_sessions()
    apply_regen(cid)
    sessions = load_sessions()
    if sessions[cid]["credits"] <= 0:
        return False
    sessions[cid]["credits"] -= 1
    save_sessions(sessions)
    return True

def time_to_next(cid):
    sessions = load_sessions()
    if cid not in sessions:
        return "0h 0m"
    last = datetime.fromisoformat(sessions[cid]["last_regen"])
    rem  = (last + timedelta(hours=WEB_REGEN_HOURS)) - datetime.now()
    if rem.total_seconds() <= 0:
        return "0h 0m"
    return f"{int(rem.total_seconds()//3600)}h {int((rem.total_seconds()%3600)//60)}m"

# ═══════════════════════════════════════
#  SSH
# ═══════════════════════════════════════

def expiration_date():
    return (datetime.now() + timedelta(days=DAYS_VALID)).strftime("%Y-%m-%d")

def expiration_pretty():
    return (datetime.now() + timedelta(days=DAYS_VALID)).strftime("%d/%m/%Y")

def ssh_run(ip, port, cmd, timeout=30):
    try:
        r = subprocess.run([
            "ssh", "-i", SSH_KEY, "-p", str(port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "PasswordAuthentication=no",
            f"root@{ip}", cmd
        ], capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            return True, r.stdout.strip()
        return False, r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def create_ssh_local(user, password):
    exp = expiration_date()
    os.system(f"id {user} >/dev/null 2>&1 && userdel -f {user} 2>/dev/null")
    os.system(f"useradd -M -s /bin/false -e {exp} {user} 2>/dev/null")
    os.system(f"echo '{user}:{password}' | chpasswd")
    os.system(f"chage -E {exp} -M 99999 {user}")
    os.system(f"usermod -f 0 {user}")
    return True, None

def create_ssh_remote(ip, port, user, password, bypass_pam=False):
    exp = expiration_date()
    if bypass_pam:
        try:
            h = subprocess.run(["openssl", "passwd", "-6", password], capture_output=True, text=True)
            pw_hash = h.stdout.strip() if h.returncode == 0 else None
        except:
            pw_hash = None
        if not pw_hash:
            try:
                import crypt
                pw_hash = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))
            except:
                return False, "No se pudo generar hash de contraseña"
        cmd = (f"id {user} >/dev/null 2>&1 && userdel -f {user} 2>/dev/null; "
               f"useradd -M -s /bin/false -e {exp} -p '{pw_hash}' {user} 2>/dev/null && "
               f"chage -E {exp} -M 99999 {user} && usermod -f 0 {user}")
    else:
        cmd = (f"id {user} >/dev/null 2>&1 && userdel -f {user} 2>/dev/null; "
               f"useradd -M -s /bin/false -e {exp} {user} 2>/dev/null && "
               f"echo '{user}:{password}' | chpasswd && "
               f"chage -E {exp} -M 99999 {user} && usermod -f 0 {user}")
    return ssh_run(ip, port, cmd)

def save_created_user(creator, username, vps_key):
    users = []
    if os.path.exists(USERS_DB):
        with open(USERS_DB) as f:
            users = json.load(f)
    users.append({
        "creator_id": f"web:{creator}",
        "username": username,
        "vps": vps_key,
        "expiration": (datetime.now() + timedelta(days=DAYS_VALID)).isoformat(),
        "created_at": datetime.now().isoformat()
    })
    with open(USERS_DB, "w") as f:
        json.dump(users, f, indent=2)

# ═══════════════════════════════════════
#  RUTAS API
# ═══════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/status')
def api_status():
    """Retorna créditos y estado del usuario."""
    cid     = get_client_id(request)
    session = apply_regen(cid)
    nxt     = time_to_next(cid)
    return jsonify({
        "credits":       session["credits"],
        "max_credits":   WEB_MAX_CREDITS,
        "next_credit":   nxt,
        "regen_hours":   WEB_REGEN_HOURS,
        "days_valid":    DAYS_VALID
    })

@app.route('/api/servers')
def api_servers():
    """Retorna info de los servidores."""
    result = {}
    for key, vps in VPS.items():
        result[key] = {
            "name":   vps["NAME"],
            "flag":   vps["FLAG"],
            "domain": vps["DOMAIN"],
            "ip":     vps["IP"]
        }
    return jsonify(result)

@app.route('/api/create', methods=['POST'])
def api_create():
    """Crea una cuenta SSH."""
    cid  = get_client_id(request)
    data = request.get_json()

    vps_key  = data.get("vps", "").lower()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    # Validaciones
    if vps_key not in VPS:
        return jsonify({"ok": False, "error": "VPS inválida"}), 400

    if not username or len(username) < 3 or len(username) > 20:
        return jsonify({"ok": False, "error": "Usuario debe tener entre 3 y 20 caracteres"}), 400

    if not username.isalnum():
        return jsonify({"ok": False, "error": "Solo letras y números en el usuario"}), 400

    if not password or len(password) < 4:
        return jsonify({"ok": False, "error": "La contraseña debe tener al menos 4 caracteres"}), 400

    # Verificar créditos
    session = apply_regen(cid)
    if session["credits"] <= 0:
        nxt = time_to_next(cid)
        return jsonify({
            "ok": False,
            "error": f"Sin créditos. Próximo crédito en: {nxt}",
            "no_credits": True
        }), 429

    ssh_user = f"ltmsshfree-{username}"
    vps_info = VPS[vps_key]
    port     = vps_info.get("PORT", 22)

    # Crear usuario
    if vps_info["LOCAL"]:
        ok, err = create_ssh_local(ssh_user, password)
    else:
        ok, err = create_ssh_remote(
            vps_info["IP"], port, ssh_user, password,
            bypass_pam=vps_info.get("BYPASS_PAM", False))

    if not ok:
        return jsonify({"ok": False, "error": f"Error en servidor: {err}"}), 500

    # Descontar crédito
    spend_credit(cid)
    save_created_user(cid, ssh_user, vps_key)

    session_after = apply_regen(cid)
    ip     = vps_info["IP"]
    domain = vps_info["DOMAIN"]
    exp    = expiration_pretty()

    return jsonify({
        "ok": True,
        "username":   ssh_user,
        "password":   password,
        "vps":        vps_key,
        "vps_name":   vps_info["NAME"],
        "flag":       vps_info["FLAG"],
        "ip":         ip,
        "domain":     domain,
        "ns":         vps_info["NS"],
        "expiration": exp,
        "days":       DAYS_VALID,
        "credits_left": session_after["credits"],
        "connections": {
            "udp":    f"{ip}:1-65535@{ssh_user}:{password}",
            "ssl":    f"{ip}:443@{ssh_user}:{password}",
            "ssh80":  f"{ip}:80@{ssh_user}:{password}",
            "domain": f"{domain}:80@{ssh_user}:{password}"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

# ═══════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════
ADMIN_PASSWORD = "DarkIuudjii"
ADMIN_TOKENS   = {}  # token → expiry

def gen_token():
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    ADMIN_TOKENS[token] = datetime.now() + timedelta(hours=8)
    return token

def valid_token(token):
    if not token or token not in ADMIN_TOKENS:
        return False
    if datetime.now() > ADMIN_TOKENS[token]:
        del ADMIN_TOKENS[token]
        return False
    return True

@app.route("/admin")
def admin_page():
    return send_from_directory(".", "admin.html")

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if data.get("password") == ADMIN_PASSWORD:
        token = gen_token()
        return jsonify({"ok": True, "token": token})
    return jsonify({"ok": False, "error": "Contraseña incorrecta"}), 401

@app.route("/api/admin/stats")
def admin_stats():
    if not valid_token(request.headers.get("X-Token")):
        return jsonify({"error": "No autorizado"}), 401
    users   = []
    if os.path.exists(USERS_DB):
        with open(USERS_DB) as f: users = json.load(f)
    banned  = {}
    if os.path.exists("banned.json"):
        with open("banned.json") as f: banned = json.load(f)
    coupons = {}
    if os.path.exists("coupons.json"):
        with open("coupons.json") as f: coupons = json.load(f)
    sessions = load_sessions()
    by_vps = {}
    for u in users:
        v = u.get("vps","?")
        by_vps[v] = by_vps.get(v, 0) + 1
    return jsonify({
        "total_users":   len(users),
        "total_banned":  len(banned),
        "total_coupons": len(coupons),
        "total_sessions": len(sessions),
        "by_vps": by_vps,
        "users":  users,
        "banned": [{"id": k, **v} for k,v in banned.items()],
        "coupons": [{"code": k, **v} for k,v in coupons.items()]
    })

@app.route("/api/admin/genkey", methods=["POST"])
def admin_genkey():
    if not valid_token(request.headers.get("X-Token")):
        return jsonify({"error": "No autorizado"}), 401
    data    = request.get_json()
    credits = int(data.get("credits", 1))
    code    = "key-ltmssh:" + ''.join(random.choices(string.digits, k=8))
    coupons = {}
    if os.path.exists("coupons.json"):
        with open("coupons.json") as f: coupons = json.load(f)
    coupons[code] = {"credits": credits, "used": False, "used_by": None, "created_at": datetime.now().isoformat()}
    with open("coupons.json","w") as f: json.dump(coupons, f, indent=2)
    return jsonify({"ok": True, "code": code, "credits": credits})

@app.route("/api/admin/delete_user", methods=["POST"])
def admin_delete_user():
    if not valid_token(request.headers.get("X-Token")):
        return jsonify({"error": "No autorizado"}), 401
    data     = request.get_json()
    username = data.get("username")
    users    = []
    if os.path.exists(USERS_DB):
        with open(USERS_DB) as f: users = json.load(f)
    target = next((u for u in users if u["username"] == username), None)
    if not target:
        return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404
    vps_info = VPS.get(target["vps"], {})
    if vps_info.get("LOCAL"):
        os.system(f"pkill -u {username} 2>/dev/null; userdel -f {username} 2>/dev/null")
    else:
        ip   = vps_info.get("IP","")
        port = vps_info.get("PORT", 22)
        subprocess.run(["ssh","-i",SSH_KEY,"-p",str(port),"-o","StrictHostKeyChecking=no",
            "-o","BatchMode=yes",f"root@{ip}",
            f"pkill -u {username} 2>/dev/null; userdel -f {username} 2>/dev/null"],
            capture_output=True, timeout=15)
    users = [u for u in users if u["username"] != username]
    with open(USERS_DB,"w") as f: json.dump(users, f, indent=2)
    return jsonify({"ok": True})

@app.route("/api/admin/add_credits", methods=["POST"])
def admin_add_credits():
    if not valid_token(request.headers.get("X-Token")):
        return jsonify({"error": "No autorizado"}), 401
    data   = request.get_json()
    cid    = data.get("session_id")
    amount = int(data.get("credits", 1))
    sessions = load_sessions()
    if cid not in sessions:
        return jsonify({"ok": False, "error": "Sesion no encontrada"}), 404
    sessions[cid]["credits"] = min(sessions[cid]["credits"] + amount, WEB_MAX_CREDITS)
    save_sessions(sessions)
    return jsonify({"ok": True, "credits": sessions[cid]["credits"]})
