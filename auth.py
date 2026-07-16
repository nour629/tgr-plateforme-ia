"""
auth.py — Systeme d'authentification TGR
Roles : Admin, Agent, Auditeur
Stockage : SQLite
"""
import sqlite3, hashlib, os, streamlit as st
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "users.db")

# ── INIT DB ───────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'Agent',
            nom      TEXT,
            created  TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            username   TEXT,
            login_time TEXT,
            ip         TEXT
        )
    """)
    # Utilisateurs par defaut
    defaults = [
        ("admin",    "admin123",    "Admin",    "Administrateur TGR"),
        ("agent1",   "agent123",    "Agent",    "Agent Benali"),
        ("agent2",   "agent123",    "Agent",    "Agent Karimi"),
        ("auditeur", "audit123",    "Auditeur", "Auditeur Zhar"),
    ]
    for username, password, role, nom in defaults:
        try:
            c.execute("INSERT INTO users (username, password, role, nom, created) VALUES (?,?,?,?,?)",
                     (username, hash_password(password), role, nom, datetime.now().strftime("%Y-%m-%d")))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

# ── HASH ─────────────────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── AUTH ──────────────────────────────────────────────────────────────────────
def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, role, nom FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "role": row[1], "nom": row[2]}
    return None

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, role, nom, created FROM users ORDER BY role, username")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(username, password, role, nom):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role, nom, created) VALUES (?,?,?,?,?)",
                  (username, hash_password(password), role, nom, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

def change_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?",
              (hash_password(new_password), username))
    conn.commit()
    conn.close()

# ── SESSION ──────────────────────────────────────────────────────────────────
def login(user_info):
    st.session_state["authenticated"] = True
    st.session_state["username"]      = user_info["username"]
    st.session_state["role"]          = user_info["role"]
    st.session_state["nom"]           = user_info["nom"]
    st.session_state["login_time"]    = datetime.now().strftime("%H:%M")

def logout():
    for key in ["authenticated","username","role","nom","login_time"]:
        st.session_state.pop(key, None)

def is_authenticated():
    return st.session_state.get("authenticated", False)

def current_user():
    return {
        "username":   st.session_state.get("username", ""),
        "role":       st.session_state.get("role", ""),
        "nom":        st.session_state.get("nom", ""),
        "login_time": st.session_state.get("login_time", ""),
    }

def require_auth():
    """A appeler en haut de chaque page protegee."""
    init_db()
    if not is_authenticated():
        show_login_page()
        st.stop()

def require_role(allowed_roles):
    """Verifie que l-utilisateur a le bon role."""
    user = current_user()
    if user["role"] not in allowed_roles:
        st.error("Acces refuse — role insuffisant.")
        st.stop()

# ── PAGE DE LOGIN ─────────────────────────────────────────────────────────────
def show_login_page():
    from styles import GLOBAL_CSS, get_logo_html

    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <style>
    .stApp { background: #0B2E4E !important; }
    .main .block-container { padding: 0 !important; max-width: 100% !important; }
    section.main > div { padding-top: 0 !important; }
    [data-testid="stSidebarNavItems"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .stTextInput input {
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        font-size: 13px !important;
    }
    .stFormSubmitButton button {
        background: #0B2E4E !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        height: 40px !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

    LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "TGR_LOGO.jpg")
    logo_html = get_logo_html(LOGO_PATH)

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logo
        st.markdown(
            "<div style='text-align:center;margin-bottom:24px;'>"
            + logo_html.replace("width:85px", "width:130px") +
            "<div style='color:white;font-size:18px;font-weight:600;margin-top:14px;'>"
            "Tresorerie Generale du Royaume</div>"
            "<div style='color:rgba(255,255,255,0.5);font-size:11px;margin-top:4px;'>"
            "Plateforme Intelligente de Gestion Documentaire</div>"
            "<div style='height:2px;background:linear-gradient(90deg,transparent,#E8601C,transparent);"
            "margin:18px 0;'></div>"
            "</div>",
            unsafe_allow_html=True
        )

        # Form card
        st.markdown(
            "<div style='background:white;border-radius:12px;padding:28px 24px;"
            "box-shadow:0 20px 60px rgba(0,0,0,0.3);'>"
            "<div style='font-size:15px;font-weight:600;color:#0B2E4E;margin-bottom:4px;'>"
            "Connexion</div>"
            "<div style='font-size:10.5px;color:#94A3B8;margin-bottom:20px;'>"
            "Acces reserve au personnel TGR</div>"
            "</div>",
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            username = st.text_input("Identifiant", placeholder="Ex: agent1")
            password = st.text_input("Mot de passe", type="password", placeholder="Mot de passe")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    user = verify_user(username, password)
                    if user:
                        login(user)
                        try:
                            from audit import log
                            log("Systeme", "Connexion", user["username"] + " (" + user["role"] + ")", user["username"])
                        except: pass
                        st.rerun()
                    else:
                        st.error("Identifiant ou mot de passe incorrect.")

        st.markdown(
            "<div style='text-align:center;margin-top:10px;font-size:9.5px;"
            "color:rgba(255,255,255,0.3);'>"
            "Usage interne TGR uniquement </div>",
            unsafe_allow_html=True
        )