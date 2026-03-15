import telebot
import os
import subprocess
import json
import random
import string
import pexpect
import re
import time
import threading
import logging
from datetime import datetime, timedelta
from telebot import types

# ═════════════════════ LOGGING ═════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ═════════════════════ CONFIG ═════════════════════
TOKEN      = "7998209606:AAGNwiDAH5cOhWftedzZosjq7GLElvJRtws"
ADMIN_ID   = 6290827127
DAYS_VALID = 3
SSH_KEY    = os.path.expanduser("~/.ssh/id_bot")

DEFAULT_CREDITS = 3
MAX_CREDITS     = 3
REGEN_HOURS     = 10

# Límite máximo de usuarios por VPS (0 = sin límite)
VPS_LIMITS = {
    "brazil": 50,
    "mexico": 50,
    "chile":  50,
    "dallas": 50,
}

# ═════════════════════ IDIOMAS ═════════════════════
LANG = {
    "es": {
        "welcome":        "👋 *BIENVENIDO A SSHFREE*\n   Creado por @DarkZFull",
        "welcome_admin":  "👑 *SUPER ADMIN*\n   Creado por @DarkZFull",
        "welcome_subadm": "🔑 *ADMIN*\n   Creado por @DarkZFull",
        "choose_vps":     "🌐 Elige VPS para crear usuario SSH:\n📅 Validez: *{days} días*",
        "credits_lbl":    "💳 Créditos: *{cr}/{max}*  {bar}",
        "credits_inf":    "♾️ Créditos: *Ilimitados*",
        "next_credit":    "⏱ Próximo crédito en: *{t}*",
        "no_credits":     "❌ No tienes créditos disponibles.\n\n⏱ Próximo crédito en: *{t}*\n\n💡 Si tienes un cupón escríbelo en el chat.\n📩 O contacta al administrador.",
        "no_credits_title":"💳 *SIN CRÉDITOS*\n   Creado por @DarkZFull",
        "banned":         "🚫 *ACCESO DENEGADO*\n\nTienes prohibido acceder a este bot.\n\n📋 *Motivo:*\n_{reason}_",
        "ask_user":       "✍️ Escribe el *nombre de usuario SSH* para VPS *{vps}*:",
        "ask_pass":       "🔐 Escribe la *contraseña*:",
        "creating":       "⏳ Creando usuario, espera...",
        "created_ok":     "✅ CUENTA CREADA CON ÉXITO",
        "error_conn":     "❌ ERROR DE CONEXIÓN",
        "vps_full":       "❌ VPS *{vps}* al límite ({max} usuarios). Elige otra.",
        "coupon_ok":      "✅ +{cr} créditos añadidos\n💳 Créditos actuales: *{now}*\n\nUsa /start para crear tu cuenta SSH.",
        "coupon_ok_title":"🎟️ *CUPÓN CANJEADO*\n   Creado por @DarkZFull",
        "coupon_bad":     "❌ Cupón inválido.",
        "coupon_used":    "❌ Este cupón ya fue canjeado.",
        "renew_choose":   "🔄 *RENOVAR CUENTA*\n\nSelecciona la cuenta SSH a renovar (cuesta 1 crédito):",
        "renew_none":     "❌ No tienes cuentas SSH activas para renovar.",
        "renew_ok":       "✅ *Cuenta renovada*\n\n👤 `{user}`\n📅 Nueva expiración: *{exp}*\n💳 Créditos restantes: *{cr}*",
        "renew_no_cr":    "❌ No tienes créditos para renovar.",
        "expiry_warn":    "⚠️ *AVISO DE EXPIRACIÓN*\n\nTu cuenta SSH expira en menos de 12 horas:\n\n👤 `{user}`\n🌐 VPS: {vps}\n⏰ Expira: {exp}\n\nRenueva con el botón en /start antes de que expire.",
        "btn_brazil":     "🇧🇷 Brazil",
        "btn_mexico":     "🇲🇽 México",
        "btn_chile":      "🇨🇱 Chile",
        "btn_dallas":     "🇺🇸 Dallas",
        "btn_myusers":    "📋 Mis Usuarios Activos",
        "btn_credits":    "💳 Mis Créditos",
        "btn_renew":      "🔄 Renovar Cuenta",
        "btn_admin":      "⚙️ Panel Admin",
        "btn_back":       "🔙 Volver",
        "my_users_title": "📋 *TUS USUARIOS SSH ACTIVOS*",
        "my_users_none":  "❌ No tienes usuarios SSH activos.",
        "credits_title":  "💳 *TUS CRÉDITOS*",
        "credits_info":   "Disponibles: *{cr}/{max}*  {bar}\n⏱ Próximo crédito en: *{t}*\n\n💡 Cada cuenta SSH consume *1 crédito*\n🎟️ Escribe tu cupón directamente en el chat",
        "credits_inf2":   "♾️ Créditos: *Ilimitados*",
    },
    "en": {
        "welcome":        "👋 *WELCOME TO SSHFREE*\n   Created by @DarkZFull",
        "welcome_admin":  "👑 *SUPER ADMIN*\n   Created by @DarkZFull",
        "welcome_subadm": "🔑 *ADMIN*\n   Created by @DarkZFull",
        "choose_vps":     "🌐 Choose VPS to create SSH account:\n📅 Valid for: *{days} days*",
        "credits_lbl":    "💳 Credits: *{cr}/{max}*  {bar}",
        "credits_inf":    "♾️ Credits: *Unlimited*",
        "next_credit":    "⏱ Next credit in: *{t}*",
        "no_credits":     "❌ You have no credits available.\n\n⏱ Next credit in: *{t}*\n\n💡 If you have a coupon, type it in the chat.\n📩 Contact the administrator.",
        "no_credits_title":"💳 *NO CREDITS*\n   Created by @DarkZFull",
        "banned":         "🚫 *ACCESS DENIED*\n\nYou are banned from this bot.\n\n📋 *Reason:*\n_{reason}_",
        "ask_user":       "✍️ Enter the *SSH username* for VPS *{vps}*:",
        "ask_pass":       "🔐 Enter the *password*:",
        "creating":       "⏳ Creating user, please wait...",
        "created_ok":     "✅ ACCOUNT CREATED SUCCESSFULLY",
        "error_conn":     "❌ CONNECTION ERROR",
        "vps_full":       "❌ VPS *{vps}* is full ({max} users). Choose another.",
        "coupon_ok":      "✅ +{cr} credits added\n💳 Current credits: *{now}*\n\nUse /start to create your SSH account.",
        "coupon_ok_title":"🎟️ *COUPON REDEEMED*\n   Created by @DarkZFull",
        "coupon_bad":     "❌ Invalid coupon.",
        "coupon_used":    "❌ This coupon has already been used.",
        "renew_choose":   "🔄 *RENEW ACCOUNT*\n\nSelect the SSH account to renew (costs 1 credit):",
        "renew_none":     "❌ You have no active SSH accounts to renew.",
        "renew_ok":       "✅ *Account renewed*\n\n👤 `{user}`\n📅 New expiration: *{exp}*\n💳 Remaining credits: *{cr}*",
        "renew_no_cr":    "❌ You don't have credits to renew.",
        "expiry_warn":    "⚠️ *EXPIRATION WARNING*\n\nYour SSH account expires in less than 12 hours:\n\n👤 `{user}`\n🌐 VPS: {vps}\n⏰ Expires: {exp}\n\nRenew it with the button in /start before it expires.",
        "btn_brazil":     "🇧🇷 Brazil",
        "btn_mexico":     "🇲🇽 México",
        "btn_chile":      "🇨🇱 Chile",
        "btn_dallas":     "🇺🇸 Dallas",
        "btn_myusers":    "📋 My Active Users",
        "btn_credits":    "💳 My Credits",
        "btn_renew":      "🔄 Renew Account",
        "btn_admin":      "⚙️ Admin Panel",
        "btn_back":       "🔙 Back",
        "my_users_title": "📋 *YOUR ACTIVE SSH USERS*",
        "my_users_none":  "❌ You have no active SSH users.",
        "credits_title":  "💳 *YOUR CREDITS*",
        "credits_info":   "Available: *{cr}/{max}*  {bar}\n⏱ Next credit in: *{t}*\n\n💡 Each SSH account costs *1 credit*\n🎟️ Type your coupon directly in the chat",
        "credits_inf2":   "♾️ Credits: *Unlimited*",
    }
}

def get_lang(uid):
    """Retorna 'en' o 'es' según el idioma del usuario (guardado en caché)."""
    data = load_credits()
    return data.get(str(uid), {}).get("lang", "es")

def set_lang(uid, lang):
    data = _ensure_user(uid)
    data[str(uid)]["lang"] = lang
    save_credits(data)

def t(uid, key, **kwargs):
    """Traduce una clave al idioma del usuario."""
    lang = get_lang(uid)
    text = LANG.get(lang, LANG["es"]).get(key, LANG["es"].get(key, key))
    return text.format(**kwargs) if kwargs else text

# ═════════════════════ VPS INFO ═════════════════════
VPS = {
    "brazil": {
        "IP": "216.238.105.165", "PORT": 22,
        "DOMAIN": "br.darkfullhn.xyz", "NS": "ns.darkfullhn.xyz",
        "PUBKEY": "9dbbfb7374360504a22e71b8ffda2c9c3c8ee62283d171fef9d881bd6b51b605",
        "LOCAL": False, "HAS_V2RAY": False, "BYPASS_PAM": True
    },
    "mexico": {
        "IP": "64.177.80.171", "PORT": 22,
        "DOMAIN": "mxvlt.darkfullhn.xyz", "NS": "nsmxvlt.darkfullhn.xyz",
        "PUBKEY": "9dbbfb7374360504a22e71b8ffda2c9c3c8ee62283d171fef9d881bd6b51b605",
        "LOCAL": True, "HAS_V2RAY": False, "BYPASS_PAM": False,
        "PORTS": " ∘ SSH: 22             ∘ System-DNS: 53\n ∘ WEB-NGinx: 80         ∘ SSL: 443\n ∘ SOCKS/PYTHON3: 5000   ∘ BadVPN: 7200\n ∘ BadVPN: 7300          ∘ SOCKS/PYTHON3: 8080\n ∘ UDP-Custom: 36712"
    },
    "chile": {
        "IP": "64.176.20.206", "PORT": 22,
        "DOMAIN": "cl.darkfullhn.xyz", "NS": "nscl.darkfullhn.xyz",
        "PUBKEY": "", "LOCAL": False, "HAS_V2RAY": False, "BYPASS_PAM": True
    },
    "dallas": {
        "IP": "149.28.241.124", "PORT": 22,
        "DOMAIN": "us.darkfullhn.xyz", "NS": "nsus.darkfullhn.xyz",
        "PUBKEY": "", "LOCAL": False, "HAS_V2RAY": False, "BYPASS_PAM": True
    },
    "miami": {
        "IP": "207.246.72.79", "PORT": 22,
        "DOMAIN": "mia.darkfullhn.xyz", "NS": "nsmia.darkfullhn.xyz",
        "PUBKEY": "", "LOCAL": False, "HAS_V2RAY": False, "BYPASS_PAM": True,
        "PORTS": " ∘ SSH: 22             ∘ System-DNS: 53\n ∘ SSL: 443             ∘ UDP-Custom: 36712"
    }
}

# ═════════════════════ ARCHIVOS ═════════════════════
USERS_DB   = "created_users.json"
CREDITS_DB = "credits.json"
ADMINS_DB  = "admins.json"
COUPONS_DB = "coupons.json"
BANNED_DB  = "banned.json"

bot    = telebot.TeleBot(TOKEN, parse_mode="Markdown")
states = {}

# ══════════════════════════════════════════════════════
#  BANNED
# ══════════════════════════════════════════════════════

def load_banned():
    if not os.path.exists(BANNED_DB):
        return {}
    with open(BANNED_DB) as f:
        return json.load(f)

def save_banned(data):
    with open(BANNED_DB, "w") as f:
        json.dump(data, f, indent=2)

def is_banned(uid):
    return str(uid) in load_banned()

def get_ban_reason(uid):
    return load_banned().get(str(uid), {}).get("reason", "Sin motivo / No reason")

def ban_user(uid, reason):
    data = load_banned()
    data[str(uid)] = {"reason": reason, "banned_at": datetime.now().isoformat()}
    save_banned(data)
    # Eliminar todos los usuarios SSH del baneado
    _delete_users_of(uid)

def unban_user(uid):
    data = load_banned()
    data.pop(str(uid), None)
    save_banned(data)

def _delete_users_of(uid):
    """Elimina todos los usuarios SSH creados por uid."""
    users  = load_users_db()
    active = []
    for u in users:
        if u.get("creator_id") == uid:
            try:
                vi = VPS[u["vps"]]
                if vi["LOCAL"]:
                    delete_user_local(u["username"])
                else:
                    delete_user_remote(vi["IP"], vi.get("PORT", 22), u["username"])
                logger.info(f"Eliminado SSH {u['username']} de usuario baneado {uid}")
            except Exception as e:
                logger.error(f"Error eliminando {u['username']}: {e}")
        else:
            active.append(u)
    save_users_db(active)

# ══════════════════════════════════════════════════════
#  ADMINS
# ══════════════════════════════════════════════════════

def load_admins():
    if not os.path.exists(ADMINS_DB):
        return {}
    with open(ADMINS_DB) as f:
        return json.load(f)

def save_admins(data):
    with open(ADMINS_DB, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(uid):
    return uid == ADMIN_ID or str(uid) in load_admins()

def is_super_admin(uid):
    return uid == ADMIN_ID

def admin_unlimited(uid):
    if uid == ADMIN_ID:
        return True
    return load_admins().get(str(uid), {}).get("credits", 0) == -1

# ══════════════════════════════════════════════════════
#  CRÉDITOS
# ══════════════════════════════════════════════════════

def load_credits():
    if not os.path.exists(CREDITS_DB):
        return {}
    with open(CREDITS_DB) as f:
        return json.load(f)

def save_credits(data):
    with open(CREDITS_DB, "w") as f:
        json.dump(data, f, indent=2)

def _ensure_user(uid):
    data = load_credits()
    key  = str(uid)
    if key not in data:
        data[key] = {"credits": DEFAULT_CREDITS, "last_regen": datetime.now().isoformat(), "lang": "es"}
        save_credits(data)
    return data

def _apply_regen(uid):
    if admin_unlimited(uid):
        return
    data  = _ensure_user(uid)
    key   = str(uid)
    entry = data[key]
    last  = datetime.fromisoformat(entry.get("last_regen", datetime.now().isoformat()))
    earned = int((datetime.now() - last).total_seconds() / 3600 // REGEN_HOURS)
    max_cr = load_admins().get(key, {}).get("credits", 0) if is_admin(uid) else MAX_CREDITS
    if earned > 0:
        entry["credits"]    = min(entry["credits"] + earned, max_cr)
        entry["last_regen"] = (last + timedelta(hours=earned * REGEN_HOURS)).isoformat()
        data[key] = entry
        save_credits(data)

def get_credits(uid):
    if admin_unlimited(uid):
        return 999
    _apply_regen(uid)
    data = _ensure_user(uid)
    return data[str(uid)]["credits"]

def spend_credit(uid):
    if admin_unlimited(uid):
        return True
    _apply_regen(uid)
    data = _ensure_user(uid)
    key  = str(uid)
    if data[key]["credits"] <= 0:
        return False
    data[key]["credits"] -= 1
    save_credits(data)
    admins = load_admins()
    if key in admins and admins[key]["credits"] != -1:
        admins[key]["credits"] = max(0, admins[key]["credits"] - 1)
        save_admins(admins)
    return True

def add_credits_to_user(uid, amount):
    if uid == ADMIN_ID:
        return
    _apply_regen(uid)
    data = _ensure_user(uid)
    key  = str(uid)
    if is_admin(uid):
        admins = load_admins()
        if key in admins and admins[key]["credits"] != -1:
            admins[key]["credits"] += amount
            save_admins(admins)
            data[key]["credits"] += amount
    else:
        data[key]["credits"] = min(data[key]["credits"] + amount, MAX_CREDITS)
    save_credits(data)

def time_to_next_credit(uid):
    _apply_regen(uid)
    data = _ensure_user(uid)
    last = datetime.fromisoformat(data[str(uid)]["last_regen"])
    rem  = (last + timedelta(hours=REGEN_HOURS)) - datetime.now()
    if rem.total_seconds() <= 0:
        return "0h 0m"
    return f"{int(rem.total_seconds()//3600)}h {int((rem.total_seconds()%3600)//60)}m"

def credits_bar(cr):
    n = min(cr, MAX_CREDITS)
    return "🟢" * n + "⚫" * (MAX_CREDITS - n)

# ══════════════════════════════════════════════════════
#  VPS LÍMITE
# ══════════════════════════════════════════════════════

def vps_user_count(vps_key):
    return sum(1 for u in load_users_db() if u.get("vps") == vps_key)

def vps_is_full(vps_key):
    limit = VPS_LIMITS.get(vps_key, 0)
    if limit == 0:
        return False
    return vps_user_count(vps_key) >= limit

# ══════════════════════════════════════════════════════
#  CUPONES
# ══════════════════════════════════════════════════════

def load_coupons():
    if not os.path.exists(COUPONS_DB):
        return {}
    with open(COUPONS_DB) as f:
        return json.load(f)

def save_coupons(data):
    with open(COUPONS_DB, "w") as f:
        json.dump(data, f, indent=2)

def generate_coupon(credits):
    code = "key-ltmssh:" + ''.join(random.choices(string.digits, k=8))
    data = load_coupons()
    data[code] = {"credits": credits, "used": False, "used_by": None,
                  "created_at": datetime.now().isoformat()}
    save_coupons(data)
    return code

def redeem_coupon(uid, code):
    data = load_coupons()
    if code not in data:
        return False, t(uid, "coupon_bad")
    if data[code]["used"]:
        return False, t(uid, "coupon_used")
    data[code]["used"]    = True
    data[code]["used_by"] = uid
    save_coupons(data)
    add_credits_to_user(uid, data[code]["credits"])
    return True, data[code]["credits"]

# ══════════════════════════════════════════════════════
#  USERS SSH DB
# ══════════════════════════════════════════════════════

def load_users_db():
    if not os.path.exists(USERS_DB):
        return []
    with open(USERS_DB) as f:
        return json.load(f)

def save_users_db(users):
    with open(USERS_DB, "w") as f:
        json.dump(users, f, indent=2)

def add_created_user(creator_id, username, vps_key, expiration):
    users = load_users_db()
    users.append({
        "creator_id": creator_id, "username": username,
        "vps": vps_key, "expiration": expiration,
        "created_at": datetime.now().isoformat()
    })
    save_users_db(users)

def renew_user_expiration(username):
    """Extiende la expiración de un usuario SSH en DAYS_VALID días desde ahora."""
    users = load_users_db()
    new_exp = (datetime.now() + timedelta(days=DAYS_VALID)).isoformat()
    new_exp_date = (datetime.now() + timedelta(days=DAYS_VALID)).strftime("%Y-%m-%d")
    for u in users:
        if u["username"] == username:
            u["expiration"] = new_exp
            # Actualizar fecha en el servidor
            vps_info = VPS[u["vps"]]
            if vps_info["LOCAL"]:
                os.system(f"chage -E {new_exp_date} {username} 2>/dev/null")
            else:
                ssh_run(vps_info["IP"], vps_info.get("PORT", 22),
                        f"chage -E {new_exp_date} {username} 2>/dev/null")
            break
    save_users_db(users)
    return new_exp

# ══════════════════════════════════════════════════════
#  EXPIRATION
# ══════════════════════════════════════════════════════

def expiration_date():
    return (datetime.now() + timedelta(days=DAYS_VALID)).strftime("%Y-%m-%d")

def expiration_datetime():
    return datetime.now() + timedelta(days=DAYS_VALID)

def expiration_pretty():
    return (datetime.now() + timedelta(days=DAYS_VALID)).strftime("%d/%m/%Y")

# ══════════════════════════════════════════════════════
#  SSH CORE
# ══════════════════════════════════════════════════════

def ssh_run(ip, port, cmd, timeout=30):
    if not os.path.exists(SSH_KEY):
        return False, f"*Llave SSH no encontrada* en `{SSH_KEY}`"
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
        stderr = r.stderr.strip()
        if "Permission denied" in stderr or "publickey" in stderr:
            err = f"*Acceso denegado* en `{ip}`\n`ssh-copy-id -i ~/.ssh/id_bot.pub root@{ip}`"
        elif "Connection refused" in stderr:
            err = f"*Conexión rechazada* por `{ip}:{port}`"
        elif "No route" in stderr or "unreachable" in stderr:
            err = f"*Sin ruta* al servidor `{ip}`"
        elif "timed out" in stderr.lower() or "Connection closed" in stderr:
            err = f"*Timeout/Conexión cerrada* `{ip}:{port}`"
        else:
            err = f"*Error SSH* `{ip}:{port}`:\n`{stderr or 'Sin detalle'}`"
        return False, err
    except subprocess.TimeoutExpired:
        return False, f"*Timeout* al conectar `{ip}:{port}`"
    except Exception as e:
        return False, f"*Error:* `{e}`"

def create_ssh(user, password):
    exp = expiration_date()
    os.system(f"id {user} >/dev/null 2>&1 && userdel -f {user} 2>/dev/null")
    os.system(f"useradd -M -s /bin/false -e {exp} {user} 2>/dev/null")
    os.system(f"echo '{user}:{password}' | chpasswd")
    os.system(f"chage -E {exp} -M 99999 {user}")
    os.system(f"usermod -f 0 {user}")

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
                return False, "No se pudo generar hash."
        cmd = (f"id {user} >/dev/null 2>&1 && userdel -f {user} 2>/dev/null; "
               f"useradd -M -s /bin/false -e {exp} -p '{pw_hash}' {user} 2>/dev/null && "
               f"chage -E {exp} -M 99999 {user} && usermod -f 0 {user}")
    else:
        cmd = (f"id {user} >/dev/null 2>&1 && userdel -f {user} 2>/dev/null; "
               f"useradd -M -s /bin/false -e {exp} {user} 2>/dev/null && "
               f"echo '{user}:{password}' | chpasswd && "
               f"chage -E {exp} -M 99999 {user} && usermod -f 0 {user}")
    return ssh_run(ip, port, cmd)

def delete_user_local(user):
    os.system(f"pkill -u {user} 2>/dev/null; userdel -f {user} 2>/dev/null")

def delete_user_remote(ip, port, user):
    ssh_run(ip, port, f"pkill -u {user} 2>/dev/null; userdel -f {user} 2>/dev/null")

# ══════════════════════════════════════════════════════
#  AUTO DELETE + NOTIFICACIÓN 12H
# ══════════════════════════════════════════════════════

notified_12h = set()  # usernames ya notificados

def check_expired_users():
    while True:
        try:
            users  = load_users_db()
            now    = datetime.now()
            active = []
            for u in users:
                exp = datetime.fromisoformat(u["expiration"])
                # Notificar 12h antes
                hours_left = (exp - now).total_seconds() / 3600
                if 0 < hours_left <= 12 and u["username"] not in notified_12h:
                    try:
                        creator_id = u.get("creator_id")
                        if creator_id:
                            exp_str = exp.strftime("%d/%m/%Y %H:%M")
                            bot.send_message(creator_id,
                                t(creator_id, "expiry_warn",
                                  user=u["username"],
                                  vps=u["vps"].upper(),
                                  exp=exp_str))
                            notified_12h.add(u["username"])
                    except Exception as e:
                        logger.error(f"Error notificando expiración: {e}")

                if now >= exp:
                    try:
                        vi = VPS[u["vps"]]
                        if vi["LOCAL"]:
                            delete_user_local(u["username"])
                        else:
                            delete_user_remote(vi["IP"], vi.get("PORT", 22), u["username"])
                        notified_12h.discard(u["username"])
                    except Exception as e:
                        logger.error(f"Error eliminando usuario expirado {u['username']}: {e}")
                else:
                    active.append(u)
            save_users_db(active)
        except Exception as e:
            logger.error(f"Auto-delete error: {e}")
        time.sleep(1800)  # cada 30 minutos

def start_auto_delete():
    threading.Thread(target=check_expired_users, daemon=True).start()

# ══════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════

def ban_check(m):
    uid = m.from_user.id if hasattr(m, 'from_user') else m
    if is_banned(uid):
        reason = get_ban_reason(uid)
        try:
            bot.send_message(
                m.chat.id if hasattr(m, 'chat') else uid,
                t(uid, "banned", reason=reason))
        except:
            pass
        return True
    return False

def main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(t(uid, "btn_brazil"), callback_data="vps_brazil"),
        types.InlineKeyboardButton(t(uid, "btn_mexico"), callback_data="vps_mexico"),
        types.InlineKeyboardButton(t(uid, "btn_chile"),  callback_data="vps_chile"),
        types.InlineKeyboardButton(t(uid, "btn_dallas"), callback_data="vps_dallas"),
    )
    kb.add(types.InlineKeyboardButton(t(uid, "btn_myusers"), callback_data="mis_usuarios"))
    kb.add(
        types.InlineKeyboardButton(t(uid, "btn_credits"), callback_data="mis_creditos"),
        types.InlineKeyboardButton(t(uid, "btn_renew"),   callback_data="renew_list"),
    )
    if get_lang(uid) == "es":
        kb.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"))
    else:
        kb.add(types.InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))
    if is_super_admin(uid):
        kb.add(types.InlineKeyboardButton(t(uid, "btn_admin"), callback_data="panel_admin"))
    return kb

def admin_panel_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Añadir Admin",    callback_data="adm_addadmin"),
        types.InlineKeyboardButton("🗑️ Eliminar Admin", callback_data="adm_deladmin"),
    )
    kb.add(
        types.InlineKeyboardButton("👥 Ver Admins",      callback_data="adm_listadmins"),
        types.InlineKeyboardButton("💳 Dar Créditos",    callback_data="adm_addcredits"),
    )
    kb.add(
        types.InlineKeyboardButton("🎟️ Generar Cupón",  callback_data="adm_genkey"),
        types.InlineKeyboardButton("📋 Ver Cupones",     callback_data="adm_listkeys"),
    )
    kb.add(
        types.InlineKeyboardButton("🚫 Banear Usuario",  callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Desbanear",        callback_data="adm_unban"),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Ver Baneados",    callback_data="adm_listbanned"),
        types.InlineKeyboardButton("🖥️ Usuarios SSH",   callback_data="adm_listusers"),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Límites VPS",     callback_data="adm_vpslimits"),
    )
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="back_start"))
    return kb

def build_start_msg(uid):
    cr = get_credits(uid)
    if uid == ADMIN_ID:
        header  = t(uid, "welcome_admin")
        cr_line = t(uid, "credits_inf")
    elif is_admin(uid):
        header  = t(uid, "welcome_subadm")
        cr_line = t(uid, "credits_inf") if cr == 999 else t(uid, "credits_lbl", cr=cr, max=MAX_CREDITS, bar=credits_bar(cr))
    else:
        header  = t(uid, "welcome")
        cr_line = t(uid, "credits_lbl", cr=cr, max=MAX_CREDITS, bar=credits_bar(cr))

    return (f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{cr_line}\n\n"
            f"{t(uid, 'choose_vps', days=DAYS_VALID)}")

# ══════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def cmd_start(m):
    try:
        if ban_check(m): return
        uid = m.from_user.id
        _ensure_user(uid)
        cr  = get_credits(uid)

        if cr <= 0 and not admin_unlimited(uid):
            nxt = time_to_next_credit(uid)
            bot.send_message(m.chat.id,
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{t(uid, 'no_credits_title')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{t(uid, 'no_credits', t=nxt)}")
            return

        bot.send_message(m.chat.id, build_start_msg(uid), reply_markup=main_keyboard(uid))
    except Exception as e:
        logger.error(f"Error /start uid={m.from_user.id}: {e}", exc_info=True)
        try:
            bot.send_message(m.chat.id, "⚠️ Error inesperado. Intenta con /start")
        except:
            pass

# ══════════════════════════════════════════════════════
#  CAMBIO DE IDIOMA
# ══════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data in ("lang_es", "lang_en"))
def cb_lang(c):
    uid  = c.from_user.id
    lang = c.data.split("_")[1]
    set_lang(uid, lang)
    bot.answer_callback_query(c.id, "🇪🇸 Español" if lang == "es" else "🇺🇸 English")
    try:
        bot.edit_message_text(build_start_msg(uid),
            c.message.chat.id, c.message.message_id,
            reply_markup=main_keyboard(uid))
    except:
        bot.send_message(c.message.chat.id, build_start_msg(uid), reply_markup=main_keyboard(uid))

# ══════════════════════════════════════════════════════
#  PANEL ADMIN
# ══════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "panel_admin")
def cb_panel_admin(c):
    if not is_super_admin(c.from_user.id): return
    bot.edit_message_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ *PANEL DE ADMINISTRACIÓN*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Selecciona una acción:",
        c.message.chat.id, c.message.message_id,
        reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "back_start")
def cb_back_start(c):
    uid = c.from_user.id
    try:
        bot.edit_message_text(build_start_msg(uid),
            c.message.chat.id, c.message.message_id,
            reply_markup=main_keyboard(uid))
    except:
        pass

# ─── AÑADIR ADMIN ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_addadmin")
def cb_addadmin(c):
    if not is_super_admin(c.from_user.id): return
    states[c.from_user.id] = ("adm_addadmin_id",)
    bot.send_message(c.message.chat.id,
        "➕ *AÑADIR ADMIN*\n\nEscribe el *ID de Telegram* del nuevo admin:")

# ─── ELIMINAR ADMIN ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_deladmin")
def cb_deladmin_list(c):
    if not is_super_admin(c.from_user.id): return
    admins = load_admins()
    if not admins:
        bot.answer_callback_query(c.id, "No hay admins registrados.", show_alert=True); return
    kb = types.InlineKeyboardMarkup()
    for uid_str, info in admins.items():
        cr = "∞" if info["credits"] == -1 else str(info["credits"])
        kb.add(types.InlineKeyboardButton(f"🗑️ ID {uid_str}  |  💳 {cr}",
               callback_data=f"confirm_deladmin_{uid_str}"))
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    bot.edit_message_text("🗑️ *ELIMINAR ADMIN*\n\nSelecciona el admin a eliminar:",
        c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_deladmin_"))
def cb_confirm_deladmin(c):
    if not is_super_admin(c.from_user.id): return
    target = c.data.replace("confirm_deladmin_", "")
    admins = load_admins()
    admins.pop(target, None)
    save_admins(admins)
    bot.answer_callback_query(c.id, f"✅ Admin {target} eliminado.")
    cb_deladmin_list(c)

# ─── VER ADMINS ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_listadmins")
def cb_list_admins(c):
    if not is_super_admin(c.from_user.id): return
    admins = load_admins()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    if not admins:
        bot.edit_message_text("📋 No hay admins registrados.",
            c.message.chat.id, c.message.message_id, reply_markup=kb); return
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━", "👥 *ADMINS REGISTRADOS*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for uid_str, info in admins.items():
        pool = "Ilimitados" if info["credits"] == -1 else str(info["credits"])
        cur  = get_credits(int(uid_str))
        lines.append(f"👤 ID: `{uid_str}`")
        lines.append(f"   💳 Pool: *{pool}*  |  Actuales: *{'∞' if cur==999 else cur}*\n")
    bot.edit_message_text("\n".join(lines),
        c.message.chat.id, c.message.message_id, reply_markup=kb)

# ─── DAR CRÉDITOS ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_addcredits")
def cb_addcredits(c):
    if not is_super_admin(c.from_user.id): return
    states[c.from_user.id] = ("adm_addcredits_id",)
    bot.send_message(c.message.chat.id, "💳 *DAR CRÉDITOS*\n\nEscribe el *ID del usuario*:")

# ─── GENERAR CUPÓN ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_genkey")
def cb_genkey(c):
    if not is_super_admin(c.from_user.id): return
    states[c.from_user.id] = ("adm_genkey_credits",)
    bot.send_message(c.message.chat.id, "🎟️ *GENERAR CUPÓN*\n\n¿Cuántos créditos tendrá?\nEscribe el número:")

# ─── VER CUPONES ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_listkeys")
def cb_list_keys(c):
    if not is_super_admin(c.from_user.id): return
    coupons = load_coupons()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    if not coupons:
        bot.edit_message_text("📋 No hay cupones.", c.message.chat.id, c.message.message_id, reply_markup=kb); return
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━", "🎟️ *CUPONES GENERADOS*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for code, info in coupons.items():
        estado = f"✅ Canjeado por `{info['used_by']}`" if info["used"] else "🟢 Disponible"
        lines.append(f"🔑 `{code}`\n   💳 {info['credits']} créditos  —  {estado}\n")
    bot.edit_message_text("\n".join(lines), c.message.chat.id, c.message.message_id, reply_markup=kb)

# ─── BANEAR ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_ban")
def cb_ban(c):
    if not is_super_admin(c.from_user.id): return
    states[c.from_user.id] = ("adm_ban_id",)
    bot.send_message(c.message.chat.id, "🚫 *BANEAR USUARIO*\n\nEscribe el *ID de Telegram* del usuario:")

# ─── DESBANEAR ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_unban")
def cb_unban_list(c):
    if not is_super_admin(c.from_user.id): return
    banned = load_banned()
    if not banned:
        bot.answer_callback_query(c.id, "No hay usuarios baneados.", show_alert=True); return
    kb = types.InlineKeyboardMarkup()
    for uid_str, info in banned.items():
        short = info["reason"][:20] + "..." if len(info["reason"]) > 20 else info["reason"]
        kb.add(types.InlineKeyboardButton(f"✅ {uid_str}  —  {short}",
               callback_data=f"confirm_unban_{uid_str}"))
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    bot.edit_message_text("✅ *DESBANEAR*\n\nSelecciona el usuario:",
        c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_unban_"))
def cb_confirm_unban(c):
    if not is_super_admin(c.from_user.id): return
    target = c.data.replace("confirm_unban_", "")
    unban_user(int(target))
    bot.answer_callback_query(c.id, f"✅ Usuario {target} desbaneado.")
    cb_unban_list(c)

# ─── VER BANEADOS ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_listbanned")
def cb_list_banned(c):
    if not is_super_admin(c.from_user.id): return
    banned = load_banned()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    if not banned:
        bot.edit_message_text("📋 No hay baneados.", c.message.chat.id, c.message.message_id, reply_markup=kb); return
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━", "🚫 *USUARIOS BANEADOS*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for uid_str, info in banned.items():
        dt = datetime.fromisoformat(info["banned_at"]).strftime("%d/%m/%Y")
        lines.append(f"👤 `{uid_str}`  📅 {dt}\n   📋 _{info['reason']}_\n")
    bot.edit_message_text("\n".join(lines), c.message.chat.id, c.message.message_id, reply_markup=kb)

# ─── VER USUARIOS SSH ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_listusers")
def cb_list_users(c):
    if not is_super_admin(c.from_user.id): return
    users = load_users_db()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    if not users:
        bot.edit_message_text("📋 No hay usuarios SSH.", c.message.chat.id, c.message.message_id, reply_markup=kb); return
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━", "🖥️ *USUARIOS SSH ACTIVOS*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for u in users:
        exp = datetime.fromisoformat(u["expiration"]).strftime("%d/%m/%Y")
        lines.append(f"👤 `{u['username']}`  🌐 {u['vps'].upper()}  ⏰ {exp}\n   🆔 `{u.get('creator_id','?')}`\n")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n_...lista truncada_"
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)

# ─── VER/EDITAR LÍMITES VPS ───
@bot.callback_query_handler(func=lambda c: c.data == "adm_vpslimits")
def cb_vpslimits(c):
    if not is_super_admin(c.from_user.id): return
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━", "📊 *LÍMITES POR VPS*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for vps_key in VPS:
        count = vps_user_count(vps_key)
        limit = VPS_LIMITS.get(vps_key, 0)
        lbl   = "Sin límite" if limit == 0 else str(limit)
        lines.append(f"🌐 *{vps_key.upper()}*: {count}/{lbl} usuarios")
    lines.append("\n_Para cambiar un límite edita `VPS_LIMITS` en el código._")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Volver", callback_data="panel_admin"))
    bot.edit_message_text("\n".join(lines), c.message.chat.id, c.message.message_id, reply_markup=kb)

# ══════════════════════════════════════════════════════
#  CALLBACKS GENERALES
# ══════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "mis_usuarios")
def cb_mis_usuarios(c):
    if ban_check(c.message): return
    uid  = c.from_user.id
    mine = [u for u in load_users_db() if u.get("creator_id") == uid]
    kb   = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, "btn_back"), callback_data="back_start"))
    if not mine:
        bot.edit_message_text(t(uid, "my_users_none"),
            c.message.chat.id, c.message.message_id, reply_markup=kb); return
    lines = [f"━━━━━━━━━━━━━━━━━━━━━━━━━\n{t(uid, 'my_users_title')}\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for u in mine:
        exp = datetime.fromisoformat(u["expiration"]).strftime("%d/%m/%Y %H:%M")
        lines.append(f"👤 `{u['username']}`\n   🌐 {u['vps'].upper()}  |  ⏰ {exp}\n")
    bot.edit_message_text("\n".join(lines), c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "mis_creditos")
def cb_mis_creditos(c):
    if ban_check(c.message): return
    uid = c.from_user.id
    cr  = get_credits(uid)
    kb  = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, "btn_back"), callback_data="back_start"))
    if cr == 999:
        text = f"━━━━━━━━━━━━━━━━━━━━━━━━━\n{t(uid,'credits_title')}\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,'credits_inf2')}"
    else:
        nxt  = time_to_next_credit(uid)
        bar  = credits_bar(cr)
        text = f"━━━━━━━━━━━━━━━━━━━━━━━━━\n{t(uid,'credits_title')}\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,'credits_info',cr=cr,max=MAX_CREDITS,bar=bar,t=nxt)}"
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)

# ─── RENOVAR CUENTA ───
@bot.callback_query_handler(func=lambda c: c.data == "renew_list")
def cb_renew_list(c):
    if ban_check(c.message): return
    uid  = c.from_user.id
    cr   = get_credits(uid)
    mine = [u for u in load_users_db() if u.get("creator_id") == uid]
    kb   = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, "btn_back"), callback_data="back_start"))
    if not mine:
        bot.edit_message_text(t(uid, "renew_none"),
            c.message.chat.id, c.message.message_id, reply_markup=kb); return
    if cr <= 0 and not admin_unlimited(uid):
        bot.edit_message_text(t(uid, "renew_no_cr"),
            c.message.chat.id, c.message.message_id, reply_markup=kb); return
    kb2 = types.InlineKeyboardMarkup()
    for u in mine:
        exp = datetime.fromisoformat(u["expiration"]).strftime("%d/%m")
        kb2.add(types.InlineKeyboardButton(
            f"🔄 {u['username']}  ({u['vps'].upper()})  ⏰{exp}",
            callback_data=f"renew_{u['username']}"))
    kb2.add(types.InlineKeyboardButton(t(uid, "btn_back"), callback_data="back_start"))
    bot.edit_message_text(t(uid, "renew_choose"),
        c.message.chat.id, c.message.message_id, reply_markup=kb2)

@bot.callback_query_handler(func=lambda c: c.data.startswith("renew_") and not c.data.startswith("renew_list"))
def cb_renew_confirm(c):
    if ban_check(c.message): return
    uid      = c.from_user.id
    username = c.data.replace("renew_", "")
    cr       = get_credits(uid)

    if cr <= 0 and not admin_unlimited(uid):
        bot.answer_callback_query(c.id, t(uid, "renew_no_cr"), show_alert=True); return

    spend_credit(uid)
    new_exp = renew_user_expiration(username)
    exp_pretty = datetime.fromisoformat(new_exp).strftime("%d/%m/%Y")
    cr_after   = get_credits(uid)
    cr_lbl     = "∞" if cr_after == 999 else str(cr_after)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, "btn_back"), callback_data="back_start"))
    bot.edit_message_text(
        t(uid, "renew_ok", user=username, exp=exp_pretty, cr=cr_lbl),
        c.message.chat.id, c.message.message_id, reply_markup=kb)

# ─── ELEGIR VPS ───
@bot.callback_query_handler(func=lambda c: c.data.startswith("vps_"))
def cb_choose_vps(c):
    if ban_check(c.message): return
    uid     = c.from_user.id
    cr      = get_credits(uid)
    vps_key = c.data.split("_")[1]

    if cr <= 0 and not admin_unlimited(uid):
        nxt = time_to_next_credit(uid)
        bot.answer_callback_query(c.id, f"💳 {t(uid,'next_credit',t=nxt)}", show_alert=True); return

    if vps_is_full(vps_key) and not is_super_admin(uid):
        bot.answer_callback_query(c.id,
            t(uid, "vps_full", vps=vps_key.upper(), max=VPS_LIMITS[vps_key]),
            show_alert=True); return

    states[uid] = ("vps_user", vps_key)
    bot.send_message(c.message.chat.id, t(uid, "ask_user", vps=vps_key.upper()))

# ══════════════════════════════════════════════════════
#  HANDLER DE TEXTO
# ══════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text is not None and not m.text.startswith("/"), content_types=["text"])
def handle_text(m):
    try:
        if ban_check(m): return
        uid  = m.from_user.id
        text = m.text.strip()

        # ── Cupón directo ──
        if text.startswith("key-ltmssh:"):
            ok, result = redeem_coupon(uid, text)
            if ok:
                cr_now = get_credits(uid)
                cr_lbl = "∞" if cr_now == 999 else str(cr_now)
                bot.send_message(m.chat.id,
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{t(uid, 'coupon_ok_title')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{t(uid, 'coupon_ok', cr=result, now=cr_lbl)}")
            else:
                bot.send_message(m.chat.id, result)
            return

        # ── Flujo de estados ──
        state = states.get(uid)
        if not state:
            return

        # ════ AÑADIR ADMIN — ID ════
        if state[0] == "adm_addadmin_id":
            if not text.isdigit():
                bot.send_message(m.chat.id, "⚠️ Escribe solo el ID numérico."); return
            states[uid] = ("adm_addadmin_credits", int(text))
            bot.send_message(m.chat.id,
                f"💳 ¿Cuántos créditos tendrá el admin `{text}`?\n\nEscribe un número o `ilimitado`:"); return

        # ════ AÑADIR ADMIN — créditos ════
        if state[0] == "adm_addadmin_credits":
            target  = state[1]
            cr_raw  = text.lower()
            credits = -1 if cr_raw in ("ilimitado", "inf", "-1") else (int(cr_raw) if cr_raw.isdigit() else None)
            if credits is None:
                bot.send_message(m.chat.id, "⚠️ Escribe un número o `ilimitado`."); return
            admins = load_admins()
            admins[str(target)] = {"credits": credits, "added_at": datetime.now().isoformat()}
            save_admins(admins)
            data = load_credits()
            data[str(target)] = {"credits": credits if credits != -1 else 999,
                                  "last_regen": datetime.now().isoformat(), "lang": "es"}
            save_credits(data)
            del states[uid]
            bot.send_message(m.chat.id,
                f"✅ *Admin añadido*\n\n👤 ID: `{target}`\n"
                f"💳 Créditos: *{'Ilimitados' if credits==-1 else credits}*",
                reply_markup=admin_panel_keyboard()); return

        # ════ DAR CRÉDITOS — ID ════
        if state[0] == "adm_addcredits_id":
            if not text.isdigit():
                bot.send_message(m.chat.id, "⚠️ Escribe solo el ID numérico."); return
            states[uid] = ("adm_addcredits_amount", int(text))
            bot.send_message(m.chat.id, f"💳 ¿Cuántos créditos darás al usuario `{text}`?"); return

        # ════ DAR CRÉDITOS — cantidad ════
        if state[0] == "adm_addcredits_amount":
            if not text.isdigit() or int(text) < 1:
                bot.send_message(m.chat.id, "⚠️ Escribe un número válido."); return
            target = state[1]
            amount = int(text)
            add_credits_to_user(target, amount)
            del states[uid]
            bot.send_message(m.chat.id,
                f"✅ *+{amount} créditos* → `{target}`\n💳 Ahora tiene: *{get_credits(target)}*",
                reply_markup=admin_panel_keyboard()); return

        # ════ GENERAR CUPÓN ════
        if state[0] == "adm_genkey_credits":
            if not text.isdigit() or int(text) < 1:
                bot.send_message(m.chat.id, "⚠️ Escribe un número válido."); return
            credits = int(text)
            code    = generate_coupon(credits)
            del states[uid]
            bot.send_message(m.chat.id,
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n🎟️ *CUPÓN GENERADO*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔑 Código:\n`{code}`\n\n💳 Créditos: *{credits}*\n"
                f"📌 Uso único — el usuario lo escribe directo en el chat",
                reply_markup=admin_panel_keyboard()); return

        # ════ BANEAR — ID ════
        if state[0] == "adm_ban_id":
            target_raw = text.lstrip("@")
            if not target_raw.isdigit():
                bot.send_message(m.chat.id, "⚠️ Escribe el *ID numérico* del usuario."); return
            states[uid] = ("adm_ban_reason", int(target_raw))
            bot.send_message(m.chat.id, f"📋 ¿Cuál es el *motivo del ban* para `{target_raw}`?"); return

        # ════ BANEAR — motivo ════
        if state[0] == "adm_ban_reason":
            target = state[1]
            reason = text
            ban_user(target, reason)   # también elimina sus SSH
            del states[uid]
            bot.send_message(m.chat.id,
                f"✅ *Usuario baneado y sus cuentas SSH eliminadas*\n\n"
                f"👤 ID: `{target}`\n📋 Motivo: _{reason}_",
                reply_markup=admin_panel_keyboard())
            try:
                bot.send_message(target,
                    t(target, "banned", reason=reason))
            except:
                pass
            return

        # ════ CREAR SSH — usuario ════
        if state[0] == "vps_user":
            states[uid] = ("vps_pass", state[1], text)
            bot.send_message(m.chat.id, t(uid, "ask_pass")); return

        # ════ CREAR SSH — contraseña ════
        if state[0] == "vps_pass":
            cr = get_credits(uid)
            if cr <= 0 and not admin_unlimited(uid):
                nxt = time_to_next_credit(uid)
                del states[uid]
                bot.send_message(m.chat.id,
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n{t(uid,'no_credits_title')}\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{t(uid,'no_credits',t=nxt)}"); return

            vps_key   = state[1]
            base_user = state[2]
            password  = text
            ssh_user  = f"ltmsshfree-{base_user}"

            # Verificar límite VPS
            if vps_is_full(vps_key) and not is_super_admin(uid):
                del states[uid]
                bot.send_message(m.chat.id,
                    t(uid, "vps_full", vps=vps_key.upper(), max=VPS_LIMITS[vps_key])); return

            wait     = bot.send_message(m.chat.id, t(uid, "creating"))
            vps_info = VPS[vps_key]
            port     = vps_info.get("PORT", 22)

            if vps_info["LOCAL"]:
                create_ssh(ssh_user, password)
            else:
                ok, err_msg = create_ssh_remote(
                    vps_info["IP"], port, ssh_user, password,
                    bypass_pam=vps_info.get("BYPASS_PAM", False))
                if not ok:
                    del states[uid]
                    bot.edit_message_text(
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"{t(uid,'error_conn')}\n"
                        f"   VPS: {vps_key.upper()} | `{vps_info['IP']}:{port}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{err_msg}",
                        m.chat.id, wait.message_id); return

            spend_credit(uid)
            exp_show = expiration_pretty()
            add_created_user(uid, ssh_user, vps_key, expiration_datetime().isoformat())
            del states[uid]

            ip       = vps_info["IP"]
            domain   = vps_info["DOMAIN"]
            cr_after = get_credits(uid)
            cr_lbl   = "∞" if cr_after == 999 else f"{cr_after}/{MAX_CREDITS}"

            footer = (
                f"   👑 Admin\n   💳 {cr_lbl}\n   Creado por @DarkZFull"
            ) if is_admin(uid) else (
                f"   💳 Créditos restantes: {cr_lbl}\n"
                f"   ⏰ Regen: +1 cada {REGEN_HOURS}h\n"
                f"   Creado por @DarkZFull"
            )

            msg = (
                f"```\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{t(uid,'created_ok')}\n"
                f"   Creado por @DarkZFull\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 CREDENCIALES:\n"
                f"Usuario: {ssh_user}\n"
                f"Password: {password}\n\n"
                f"📅 EXPIRACIÓN:\n"
                f"Fecha: {exp_show} ({DAYS_VALID} días)\n\n"
                f"🌐 SERVIDOR:\n"
                f"IP: {ip}\nHost: {domain}\n\n"
                f"🔌 PUERTOS ACTIVOS:\n"
                f"{vps_info.get('PORTS', ' ∘ SSH: 22             ∘ System-DNS: 53\n ∘ SSL: 443             ∘ UDP-Custom: 36712')}\n"
                f" ∘ SSL: 443            ∘ V2RAY: 8080\n"
                f" ∘ SlowDNS: 5300       ∘ UDP-Custom: 36712\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📱 CONFIGURACIONES DE CONEXIÓN\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔹 UDP HTTP Custom:\n{ip}:1-65535@{ssh_user}:{password}\n\n"
                f"🔹 SSL/TLS (SNI):\n{ip}:443@{ssh_user}:{password}\n\n"
                f"🔹 SSH Puerto 80 (IP):\n{ip}:80@{ssh_user}:{password}\n\n"
                f"🔹 SSH Puerto 80 (Dominio):\n{domain}:80@{ssh_user}:{password}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"NS: {vps_info['NS']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{footer}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"```"
            )
            bot.edit_message_text(msg, m.chat.id, wait.message_id)

    except Exception as e:
        logger.error(f"Error handle_text uid={m.from_user.id}: {e}", exc_info=True)
        try:
            bot.send_message(m.chat.id, "⚠️ Error inesperado. Intenta con /start")
        except:
            pass

# ══════════════════════════════════════════════════════
#  EXCEPTION HANDLER
# ══════════════════════════════════════════════════════

class BotExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        logger.error(f"Error en handler: {exception}", exc_info=True)
        return True

bot.exception_handler = BotExceptionHandler()

# ══════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🤖 BOT ACTIVO Y CORRIENDO")
    print("   Creado por @DarkZFull")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Bot iniciado correctamente")
    start_auto_delete()
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
