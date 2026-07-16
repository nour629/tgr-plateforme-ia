import streamlit as st
import json, os, sys, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import require_auth, current_user
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header, strow
from audit import log

st.set_page_config(page_title="Parametres — TGR", page_icon="⚙️", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
require_auth()
render_sidebar(logo_html)
render_topbar("Parametres de Configuration", "Parametres", "<span class='pill pn'>Administration</span>")

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONFIG_PATH = os.path.join(ROOT, "..", "config.json")

def load_config():
    defaults = {"mode":"ollama","claude_api_key":"","ollama_model":"mistral"}
    if not os.path.exists(CONFIG_PATH): return defaults
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f: return {**defaults, **json.load(f)}
    except: return defaults

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(config, f, ensure_ascii=False, indent=2)

config = load_config()
mode_actuel = config.get("mode","ollama")

st.markdown(section_header("Mode de generation — Assistant Reglementaire"), unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    is_active = mode_actuel == "ollama"
    border = "2px solid #E8601C" if is_active else "1px solid #E2E8F0"
    bg = "#FFF7ED" if is_active else "white"
    active_html = "<span class='badge badge-green'>Mode actif</span>" if is_active else ""
    st.markdown(
        "<div class='card' style='border:" + border + ";background:" + bg + ";'>"
        "<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;'>"
        "<div style='font-weight:600;color:#0B2E4E;font-size:12px;'>Mode Local — Ollama</div>" + active_html + "</div>"
        "<div style='font-size:10.5px;color:#475569;line-height:2;'>"
        "✅ Donnees 100% confidentielles<br>"
        "✅ Aucun cout d-utilisation<br>"
        "✅ Fonctionne sans internet<br>"
        "⚠️ Reponses plus lentes (1-2 min)<br>"
        "⚠️ Necessite Ollama installe"
        "</div></div>",
        unsafe_allow_html=True
    )

with col2:
    is_active = mode_actuel == "gemini"
    border = "2px solid #E8601C" if is_active else "1px solid #E2E8F0"
    bg = "#FFF7ED" if is_active else "white"
    active_html = "<span class='badge badge-green'>Mode actif</span>" if is_active else ""
    st.markdown(
        "<div class='card' style='border:" + border + ";background:" + bg + ";'>"
        "<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;'>"
        "<div style='font-weight:600;color:#0B2E4E;font-size:12px;'>Mode API — Gemini 2.5 Flash</div>" + active_html + "</div>"
        "<div style='font-size:10.5px;color:#475569;line-height:2;'>"
        "✅ Reponses rapides (quelques secondes)<br>"
        "✅ Gemini Vision pour OCR manuscrit<br>"
        "✅ Gratuit — Google AI Studio<br>"
        "⚠️ Necessite une cle API<br>"
        "⚠️ Les donnees transitent par internet"
        "</div></div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
nouveau_mode = st.radio(
    "Selectionner le mode actif",
    options=["ollama","gemini"],
    format_func=lambda x: {"ollama":"Mode Local (Ollama)","gemini":"Mode API (Gemini Flash)"}.get(x,x),
    index=1 if mode_actuel=="gemini" else 0,
    horizontal=True
)

if nouveau_mode == "ollama":
    st.markdown(section_header("Configuration Ollama"), unsafe_allow_html=True)
    col_a, col_b = st.columns([1,2])
    with col_a:
        ollama_model = st.selectbox("Modele", ["mistral","llama3","phi3","gemma"],
                                    index=["mistral","llama3","phi3","gemma"].index(config.get("ollama_model","mistral")))
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Tester la connexion Ollama"):
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=3)
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models",[])]
                    st.success("Ollama actif — modeles : " + (", ".join(models) if models else "aucun"))
                else:
                    st.error("Ollama ne repond pas.")
            except:
                st.error("Ollama inaccessible. Lancez ollama serve.")
    api_key = ""
else:
    ollama_model = config.get("ollama_model","mistral")
    api_key = ""

if nouveau_mode == "gemini":
    st.markdown(section_header("Configuration Gemini Flash"), unsafe_allow_html=True)
    col_g1, col_g2 = st.columns([2,1])
    with col_g1:
        _gem_default = config.get("gemini_api_key","")
        gemini_key = st.text_input("Cle API Google Gemini",
            value=_gem_default,
            type="password", placeholder="AIza...")
    with col_g2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Tester Gemini Flash"):
            with st.spinner("Test..."):
                try:
                    import requests as _rg
                    _url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" + gemini_key
                    _resp = _rg.post(_url, json={"contents":[{"parts":[{"text":"Say hello"}]}]}, timeout=15)
                    if _resp.status_code == 200:
                        _ans = _resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("Gemini Flash actif : " + _ans.strip())
                    else:
                        st.error("Erreur " + str(_resp.status_code) + " : " + _resp.text[:200])
                except Exception as e:
                    st.error("Erreur : " + str(e))
    st.markdown(
        "<div style='background:#EDF5E4;border:1px solid #BBF7D0;border-radius:6px;"
        "padding:8px 12px;font-size:10px;color:#2D6A10;margin-top:6px;'>"
        "Cle API gratuite sur <strong>aistudio.google.com</strong> — 15 req/min gratuits."
        "</div>", unsafe_allow_html=True
    )
else:
    try:
        import json as _jg
        with open(CONFIG_PATH, encoding="utf-8") as _fg: _cg = _jg.load(_fg)
        gemini_key = _cg.get("gemini_api_key","")
    except: gemini_key = ""

st.markdown("<br>", unsafe_allow_html=True)
col_save, _ = st.columns([1,4])
with col_save:
    if st.button("Sauvegarder la configuration"):
        # Reload existing config and update
        import json as _js
        _existing = {}
        try:
            with open(CONFIG_PATH, encoding="utf-8") as _fc: _existing = _js.load(_fc)
        except: pass
        _gk = gemini_key if "gemini_key" in dir() else _existing.get("gemini_api_key","")
        _existing.update({"mode": nouveau_mode, "ollama_model": ollama_model, "gemini_api_key": _gk})
        with open(CONFIG_PATH, "w", encoding="utf-8") as _fc: _js.dump(_existing, _fc, ensure_ascii=False, indent=2)
        log("Systeme","Configuration mise a jour","Mode : " + nouveau_mode)
        mode_label = {"ollama": "Ollama local", "gemini": "Gemini Flash"}.get(nouveau_mode, nouveau_mode)
        st.success("Configuration sauvegardee — Mode : " + mode_label)
        st.rerun()

st.markdown(section_header("Statut actuel"), unsafe_allow_html=True)
ok_bdg = "<span class='sbdg' style='background:#EDF5E4;color:#2D6A10;'>Actif</span>"
ko_bdg = "<span class='sbdg' style='background:#FFF0EB;color:#E8601C;'>Inactif</span>"

def check_ollama():
    try:
        return requests.get("http://localhost:11434/api/tags",timeout=2).status_code==200
    except: return False

ollama_ok = check_ollama()
claude_ok = bool(api_key)

st.markdown(
    "<div class='card'>"
    + strow("sg" if ollama_ok else "so", "Ollama — Mistral 7B", ok_bdg if ollama_ok else ko_bdg)
    + strow("sg", "Mode actif", "<span class='sval'>" + mode_actuel.upper() + "</span>")
    + strow("sg", "Modele", "<span class='sval'>" + ("claude-sonnet-4-6" if mode_actuel=="claude" else config.get("ollama_model","mistral")) + "</span>")
    + "</div>",
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

# ── SECTION NOTIFICATIONS ─────────────────────────────────────────────────────
st.markdown(section_header("Notifications Email — Resend"), unsafe_allow_html=True)

import json as _json

def load_full_config():
    defaults = {
        "mode": "ollama", "claude_api_key": "", "ollama_model": "mistral",
        "resend_api_key": "", "email_from": "TGR Platform <noreply@resend.dev>",
        "email_to": "", "notifications_enabled": False,
        "notify_anomalie": True, "notify_ocr": True, "notify_assistant": False,
    }
    if not os.path.exists(CONFIG_PATH): return defaults
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f: return {**defaults, **_json.load(f)}
    except: return defaults

full_config = load_full_config()

col_notif1, col_notif2 = st.columns(2)
with col_notif1:
    notif_enabled = st.toggle("Activer les notifications email",
                               value=full_config.get("notifications_enabled", False))
    resend_key    = st.text_input("Cle API Resend", value=full_config.get("resend_api_key",""),
                                   type="password", placeholder="re_xxxxxxxxxxxx")
    email_to      = st.text_input("Email destinataire", value=full_config.get("email_to",""),
                                   placeholder="responsable@tgr.ma")
    email_from    = st.text_input("Email expediteur", value=full_config.get("email_from","TGR Platform <noreply@resend.dev>"))

with col_notif2:
    st.markdown("<div class='card' style='margin-top:28px;'>", unsafe_allow_html=True)
    st.markdown("<div class='chdr'><div class='ctitle'>Declencheurs</div></div>", unsafe_allow_html=True)
    n_anomalie  = st.checkbox("Dossier non conforme detecte",  value=full_config.get("notify_anomalie", True))
    n_ocr       = st.checkbox("Document uploade en OCR",       value=full_config.get("notify_ocr", True))
    n_assistant = st.checkbox("Question posee a l-assistant",  value=full_config.get("notify_assistant", False))

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Tester l-envoi email", use_container_width=True):
        if not resend_key:
            st.error("Entrez d-abord votre cle API Resend.")
        elif not email_to:
            st.error("Entrez l-email destinataire.")
        else:
            with st.spinner("Envoi en cours..."):
                try:
                    import resend
                    resend.api_key = resend_key
                    resend.Emails.send({
                        "from":    email_from,
                        "to":      [email_to],
                        "subject": "[TGR] Test de notification",
                        "html":    "<h2>Test reussi</h2><p>Les notifications TGR fonctionnent correctement.</p>"
                    })
                    st.success("Email envoye avec succes a " + email_to)
                except Exception as e:
                    st.error("Erreur : " + str(e))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div style='background:#EBF2FA;border:1px solid #BFDBFE;border-radius:6px;padding:8px 12px;"
    "font-size:10px;color:#1E40AF;margin:8px 0;'>"
    "Obtenez votre cle API gratuite sur <strong>resend.com</strong> → "
    "API Keys → Create API Key. Jusqu-a 3000 emails/mois gratuits."
    "</div>",
    unsafe_allow_html=True
)

col_save2, _ = st.columns([1, 4])
with col_save2:
    if st.button("💾  Sauvegarder notifications"):
        new_cfg = load_full_config()
        new_cfg.update({
            "notifications_enabled": notif_enabled,
            "resend_api_key":  resend_key,
            "email_to":        email_to,
            "email_from":      email_from,
            "notify_anomalie": n_anomalie,
            "notify_ocr":      n_ocr,
            "notify_assistant":n_assistant,
            "gemini_api_key":  gemini_key,
        })
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            _json.dump(new_cfg, f, ensure_ascii=False, indent=2)
        log("Systeme", "Config notifications mise a jour", "Resend", current_user().get("username",""))
        st.success("Configuration notifications sauvegardee.")

# ── COMPOSER UN EMAIL ─────────────────────────────────────────────────────────
st.markdown(section_header("Composer un Email"), unsafe_allow_html=True)

with st.form("compose_email_form"):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        compose_to      = st.text_input("Destinataire", placeholder="encadrant@tgr.ma")
        compose_subject = st.text_input("Objet", placeholder="[TGR] Rapport de stage — Point d-avancement")
    with col_e2:
        compose_from = st.text_input("De", value=full_config.get("email_from","TGR Platform <noreply@resend.dev>"))
        compose_cc   = st.text_input("CC (optionnel)", placeholder="responsable@tgr.ma")

    compose_body = st.text_area(
        "Message",
        height=200,
        placeholder="Bonjour,\n\nJe me permets de vous informer...\n\nCordialement,"
    )

    col_send, col_preview = st.columns([1, 3])
    with col_send:
        send_clicked = st.form_submit_button("📧  Envoyer l-email", use_container_width=True)

    if send_clicked:
        if not compose_to:
            st.error("Veuillez entrer un destinataire.")
        elif not compose_subject:
            st.error("Veuillez entrer un objet.")
        elif not compose_body:
            st.error("Veuillez ecrire un message.")
        else:
            cfg = load_full_config()
            if not cfg.get("resend_api_key",""):
                st.error("Cle API Resend non configuree. Remplissez la section ci-dessus.")
            else:
                with st.spinner("Envoi en cours..."):
                    try:
                        import resend
                        resend.api_key = cfg["resend_api_key"]
                        body_html = (
                            "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>"
                            "<div style='background:#0B2E4E;padding:16px 20px;border-radius:8px 8px 0 0;'>"
                            "<div style='color:white;font-size:16px;font-weight:600;'>Tresorerie Generale du Royaume</div>"
                            "<div style='color:rgba(255,255,255,0.5);font-size:11px;'>Plateforme IA TGR</div>"
                            "</div>"
                            "<div style='background:white;padding:24px;border:1px solid #E2E8F0;'>"
                            "<div style='font-size:13px;color:#1E293B;line-height:1.8;white-space:pre-wrap;'>"
                            + compose_body.replace("<", "&lt;").replace(">", "&gt;") +
                            "</div></div>"
                            "<div style='background:#F8FAFC;padding:10px 20px;border-radius:0 0 8px 8px;"
                            "font-size:10px;color:#94A3B8;text-align:center;'>"
                            "Envoye via Plateforme IA TGR — " + current_user().get("username","") +
                            "</div></div>"
                        )
                        payload = {
                            "from":    compose_from,
                            "to":      [compose_to],
                            "subject": compose_subject,
                            "html":    body_html,
                        }
                        if compose_cc:
                            payload["cc"] = [compose_cc]

                        resend.Emails.send(payload)
                        log("Systeme", "Email envoye", compose_subject, current_user().get("username",""))
                        st.success("Email envoye avec succes a " + compose_to)
                    except Exception as e:
                        st.error("Erreur envoi : " + str(e))