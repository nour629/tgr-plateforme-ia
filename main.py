import streamlit as st
import json, os, sys, base64
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))


# Auth
try:
    from auth import require_auth, init_db
    init_db()
    require_auth()
except ImportError:
    pass

st.set_page_config(page_title="TGR — Plateforme IA", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
section.main > div { padding-top: 0 !important; }
[data-testid="stAppViewBlockContainer"] { padding: 0 !important; }
[data-testid="stSidebarNavItems"],[data-testid="stSidebarNavSeparator"] { display: none !important; }
[data-testid="stSidebar"] { background: #0B2E4E !important; min-width: 220px !important; max-width: 220px !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.5) !important; font-family: 'Inter', sans-serif !important; }
.sb-top { padding: 14px 14px 12px; border-bottom: 1px solid rgba(255,255,255,0.07); }
.sb-brand { display: flex; align-items: center; gap: 9px; }
.sb-box { width: 30px; height: 30px; border-radius: 7px; background: #E8601C; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; color: white !important; flex-shrink: 0; }
.sb-name { font-size: 11px; font-weight: 500; color: white !important; line-height: 1.35; }
.sb-min  { font-size: 8.5px; color: rgba(255,255,255,0.3) !important; margin-top: 1px; }
.sb-line { height: 1px; background: rgba(232,96,28,0.35); margin-top: 12px; }
.sb-grp  { padding: 12px 14px 3px; font-size: 8.5px; color: rgba(255,255,255,0.25) !important; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500; }
.sb-foot { padding: 10px 14px; font-size: 9px; color: rgba(255,255,255,0.15) !important; line-height: 1.7; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 1rem; }
.topbar { background: white; height: 46px; border-bottom: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: space-between; padding: 0 22px; }
.tb-bc { font-size: 9px; color: #94A3B8; margin-bottom: 1px; }
.tb-t  { font-size: 13px; font-weight: 500; color: #0B2E4E; }
.pill  { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 20px; font-size: 9.5px; font-weight: 500; }
.pg { background: #EAF3DE; color: #2D6A10; }
.pn { background: #E6EFF8; color: #0B2E4E; }
.dot5 { width: 5px; height: 5px; border-radius: 50%; display: inline-block; margin-right: 3px; }
.dg { background: #2D6A10; } .dn { background: #0B2E4E; }
.page-content { padding: 14px 20px; }
.banner { background: #0B2E4E; border-radius: 10px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.b-tag { display: inline-block; background: rgba(232,96,28,0.2); border: 1px solid rgba(232,96,28,0.45); color: #F4A574; font-size: 8.5px; font-weight: 500; padding: 2px 8px; border-radius: 20px; margin-bottom: 6px; letter-spacing: 0.06em; text-transform: uppercase; }
.b-title { font-size: 14px; font-weight: 500; color: white; margin-bottom: 2px; }
.b-sub   { font-size: 10px; color: rgba(255,255,255,0.42); }
.b-stats { display: flex; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; overflow: hidden; }
.b-stat  { padding: 10px 18px; text-align: center; border-right: 1px solid rgba(255,255,255,0.08); }
.b-stat:last-child { border-right: none; }
.b-val   { font-size: 20px; font-weight: 500; color: white; line-height: 1; }
.b-lbl   { font-size: 8px; color: rgba(255,255,255,0.35); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi { background: white; border-radius: 8px; border: 1px solid #E2E8F0; padding: 12px 14px; }
.kpi-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.kpi-lbl  { font-size: 9.5px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-ico  { width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; }
.kpi-val  { font-size: 22px; font-weight: 500; line-height: 1; margin-bottom: 5px; }
.kpi-foot { display: flex; align-items: center; justify-content: space-between; }
.kpi-sub  { font-size: 9.5px; color: #94A3B8; }
.kpi-tr   { font-size: 9px; font-weight: 500; }
.tup  { color: #2D6A10; } .twarn { color: #E8601C; } .tneu { color: #94A3B8; }
.card { background: white; border-radius: 8px; border: 1px solid #E2E8F0; padding: 12px 14px; }
.chdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #F1F5F9; }
.ctitle { font-size: 11.5px; font-weight: 500; color: #0B2E4E; }
.cact   { font-size: 9.5px; color: #E8601C; cursor: pointer; }
.mod { display: flex; align-items: center; gap: 9px; padding: 7px 0; border-bottom: 1px solid #F8FAFC; }
.mod:last-child { border-bottom: none; }
.mic  { width: 28px; height: 28px; border-radius: 6px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 12px; }
.mn   { font-size: 11px; font-weight: 500; color: #0B2E4E; }
.md   { font-size: 9.5px; color: #94A3B8; margin-top: 1px; }
.mtag { margin-left: auto; font-size: 8.5px; font-weight: 500; padding: 2px 6px; border-radius: 20px; flex-shrink: 0; }
.act-row { display: flex; align-items: flex-start; gap: 9px; padding: 7px 0; border-bottom: 1px solid #F1F5F9; }
.act-row:last-child { border-bottom: none; }
.av { width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 500; }
.an { font-size: 10.5px; font-weight: 500; color: #334155; }
.as { font-size: 9.5px; color: #94A3B8; margin-top: 1px; }
.atime { font-size: 9px; color: #94A3B8; margin-left: auto; white-space: nowrap; }
.st-row { display: flex; align-items: center; gap: 7px; padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 10.5px; }
.st-row:last-child { border-bottom: none; }
.sdot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.sg { background: #2D6A10; } .so { background: #E8601C; }
.sname { flex: 1; color: #334155; }
.sval  { font-size: 9.5px; color: #94A3B8; }
.sbdg  { padding: 1px 6px; border-radius: 20px; font-size: 8.5px; font-weight: 500; }
.audit-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 10px; }
.audit-row:last-child { border-bottom: none; }
.a-user { font-weight: 500; color: #0B2E4E; min-width: 85px; font-size: 10px; }
.a-act  { flex: 1; color: #475569; }
.a-mod  { padding: 1px 6px; border-radius: 20px; font-size: 8px; font-weight: 500; }
.a-time { color: #94A3B8; font-size: 9px; white-space: nowrap; }
.doc-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 10.5px; }
.doc-row:last-child { border-bottom: none; }
.dic  { width: 24px; height: 24px; border-radius: 5px; background: #EBF2FA; display: flex; align-items: center; justify-content: center; font-size: 11px; color: #0B2E4E; flex-shrink: 0; }
.dname { flex: 1; color: #334155; }
.dtype { font-size: 9px; color: #94A3B8; }
</style>
""", unsafe_allow_html=True)

# Logo
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "TGR_LOGO.jpg")
def get_logo():
    try:
        with open(LOGO_PATH, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""
logo_b64 = get_logo()
logo_img = ('<img src="data:image/jpeg;base64,' + logo_b64 + '" style="width:90px;background:white;border-radius:5px;padding:3px;margin-bottom:0.6rem;">') if logo_b64 else ""

# Data
AUDIT_LOG = os.path.join(os.path.dirname(__file__), "..", "audit_log.json")
def load_logs():
    try:
        with open(AUDIT_LOG, encoding="utf-8") as f: return json.load(f)
    except: return []

logs = load_logs()
today = datetime.now().strftime("%Y-%m-%d")
docs_total = sum(1 for l in logs if l.get("module") == "OCR" and "Upload" in l.get("action", ""))
docs_today = sum(1 for l in logs if l.get("module") == "OCR" and "Upload" in l.get("action", "") and l.get("timestamp", "").startswith(today))
anom_total = sum(1 for l in logs if l.get("module") == "Anomalie")
ques_total = sum(1 for l in logs if l.get("module") == "Assistant" and "Question" in l.get("action", ""))
ques_today = sum(1 for l in logs if l.get("module") == "Assistant" and "Question" in l.get("action", "") and l.get("timestamp", "").startswith(today))
recent_logs = logs[:4] if logs else []

def check_ollama():
    try:
        import requests as req
        return req.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except: return False

def check_faiss():
    return os.path.exists(os.path.join(os.path.dirname(__file__), "..", "core", "rag", "faiss_index.bin"))

def check_claude():
    try:
        with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
            return bool(json.load(f).get("claude_api_key", ""))
    except: return False

ollama_ok = check_ollama()
faiss_ok  = check_faiss()
claude_ok = check_claude()

# Sidebar
with st.sidebar:
    st.markdown(
        "<div class='sb-top'>"
        + logo_img
        + "<div class='sb-brand'><div class='sb-box'>TGR</div>"
        + "<div><div class='sb-name'>Tresorerie Generale<br>du Royaume</div>"
        + "<div class='sb-min'>Ministere des Finances</div></div></div>"
        + "<div class='sb-line'></div></div>",
        unsafe_allow_html=True
    )
    st.markdown("<div class='sb-grp'>Modules</div>", unsafe_allow_html=True)
    st.page_link("main.py",               label="🏠  Accueil")
    st.page_link("pages/1_OCR.py",        label="📄  Extraction OCR")
    st.page_link("pages/2_Anomalies.py",  label="⚠️  Detection Anomalies")
    st.page_link("pages/3_Assistant.py",  label="💬  Assistant Reglementaire")
    st.page_link("pages/4_Dashboard.py",  label="📊  Tableau de Bord")
    st.markdown("<div class='sb-grp' style='margin-top:4px;'>Administration</div>", unsafe_allow_html=True)
    st.page_link("pages/5_Parametres.py", label="⚙️  Parametres")
    st.markdown("<div class='sb-foot'>Plateforme IA — Usage interne TGR<br></div>", unsafe_allow_html=True)

# Topbar
st.markdown(
    "<div class='topbar'>"
    "<div><div class='tb-bc'>TGR — Plateforme IA / Accueil</div>"
    "<div class='tb-t'>Tableau de Bord Principal</div></div>"
    "<div style='display:flex;gap:7px;'>"
    "<span class='pill pg'><span class='dot5 dg'></span>Systeme actif</span>"
    "<span class='pill pn'><span class='dot5 dn'></span>Mode local securise</span>"
    "</div></div>"
    "<div class='page-content'>",
    unsafe_allow_html=True
)

# Banner
st.markdown(
    "<div class='banner'>"
    "<div><div class='b-tag'>Maroc Digital 2030</div>"
    "<div class='b-title'>Plateforme Intelligente de Gestion Documentaire</div>"
    "<div class='b-sub'>Systeme integre d-extraction, de conformite et d-assistance reglementaire — TGR</div></div>"
    "<div class='b-stats'>"
    "<div class='b-stat'><div class='b-val'>4</div><div class='b-lbl'>Modules</div></div>"
    "<div class='b-stat'><div class='b-val'>7</div><div class='b-lbl'>Types clients</div></div>"
    "<div class='b-stat'><div class='b-val'>100%</div><div class='b-lbl'>Local securise</div></div>"
    "</div></div>",
    unsafe_allow_html=True
)

# KPIs — build HTML with string concatenation (no f-string apostrophe issues)
c1, c2, c3, c4 = st.columns(4)

with c1:
    trend_html = ("<span class='kpi-tr tup'>+ " + str(docs_today) + " aujourd-hui</span>") if docs_today > 0 else "<span class='kpi-tr tneu'>Aucun aujourd-hui</span>"
    val_html = str(docs_total) if docs_total else "—"
    st.markdown(
        "<div class='kpi' style='border-top:3px solid #0B2E4E;'>"
        "<div class='kpi-head'><div class='kpi-lbl'>Documents traites</div>"
        "<div class='kpi-ico' style='background:#EBF2FA;color:#0B2E4E;'>📄</div></div>"
        "<div class='kpi-val' style='color:#0B2E4E;'>" + val_html + "</div>"
        "<div class='kpi-foot'><span class='kpi-sub'>Module OCR</span>" + trend_html + "</div></div>",
        unsafe_allow_html=True
    )

with c2:
    val_html = str(anom_total) if anom_total else "—"
    st.markdown(
        "<div class='kpi' style='border-top:3px solid #E8601C;'>"
        "<div class='kpi-head'><div class='kpi-lbl'>Anomalies detectees</div>"
        "<div class='kpi-ico' style='background:#FFF0EB;color:#E8601C;'>⚠️</div></div>"
        "<div class='kpi-val' style='color:#E8601C;'>" + val_html + "</div>"
        "<div class='kpi-foot'><span class='kpi-sub'>Dossiers clients</span>"
        "<span class='kpi-tr twarn'>Non conformes</span></div></div>",
        unsafe_allow_html=True
    )

with c3:
    trend3_html = ("<span class='kpi-tr tup'>+ " + str(ques_today) + " aujourd-hui</span>") if ques_today > 0 else "<span class='kpi-tr tneu'>Aucune aujourd-hui</span>"
    val_html = str(ques_total) if ques_total else "—"
    st.markdown(
        "<div class='kpi' style='border-top:3px solid #185FA5;'>"
        "<div class='kpi-head'><div class='kpi-lbl'>Questions posees</div>"
        "<div class='kpi-ico' style='background:#EBF2FA;color:#185FA5;'>💬</div></div>"
        "<div class='kpi-val' style='color:#185FA5;'>" + val_html + "</div>"
        "<div class='kpi-foot'><span class='kpi-sub'>Assistant RAG</span>" + trend3_html + "</div></div>",
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        "<div class='kpi' style='border-top:3px solid #2D6A10;'>"
        "<div class='kpi-head'><div class='kpi-lbl'>Score conformite</div>"
        "<div class='kpi-ico' style='background:#EDF5E4;color:#2D6A10;'>🎯</div></div>"
        "<div class='kpi-val' style='color:#2D6A10;'>0.862</div>"
        "<div class='kpi-foot'><span class='kpi-sub'>PR-AUC</span>"
        "<span class='kpi-tr tup'>Bon niveau</span></div></div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Row 2 — Modules + Activity
col_mod, col_act = st.columns([3, 2])

with col_mod:
    st.markdown(
        "<div class='card'>"
        "<div class='chdr'><div class='ctitle'>Modules disponibles</div></div>"
        "<div class='mod'><div class='mic' style='background:#EBF2FA;color:#0B2E4E;'>📄</div>"
        "<div><div class='mn'>Extraction OCR</div><div class='md'>Lecture automatique des fiches et procurations TGR</div></div>"
        "<span class='mtag' style='background:#EBF2FA;color:#0B2E4E;'>M1</span></div>"
        "<div class='mod'><div class='mic' style='background:#FFF0EB;color:#E8601C;'>⚠️</div>"
        "<div><div class='mn'>Detection Anomalies</div><div class='md'>Verification conformite selon referentiel OLYMPIC</div></div>"
        "<span class='mtag' style='background:#FFF0EB;color:#E8601C;'>M2</span></div>"
        "<div class='mod'><div class='mic' style='background:#EDF5E4;color:#2D6A10;'>💬</div>"
        "<div><div class='mn'>Assistant Reglementaire</div><div class='md'>Interrogez les circulaires et instructions TGR</div></div>"
        "<span class='mtag' style='background:#EDF5E4;color:#2D6A10;'>M3</span></div>"
        "<div class='mod'><div class='mic' style='background:#EBF2FA;color:#185FA5;'>📊</div>"
        "<div><div class='mn'>Tableau de Bord et Audit</div><div class='md'>Supervision globale et piste d-audit complete</div></div>"
        "<span class='mtag' style='background:#EBF2FA;color:#185FA5;'>M4</span></div>"
        "</div>",
        unsafe_allow_html=True
    )

with col_act:
    mod_colors = {
        "OCR":      ("background:#EBF2FA;color:#0B2E4E;", "AB"),
        "Anomalie": ("background:#FFF0EB;color:#E8601C;", "KZ"),
        "Assistant":("background:#EDF5E4;color:#2D6A10;", "MZ"),
        "Systeme":  ("background:#EBF2FA;color:#185FA5;", "AT"),
    }
    rows_html = ""
    if recent_logs:
        for l in recent_logs[:4]:
            mod = l.get("module", "OCR")
            style, initials = mod_colors.get(mod, ("background:#EBF2FA;color:#0B2E4E;", "??"))
            time_str = l.get("timestamp", "")[-8:-3]
            action = l.get("action", "—")
            detail = l.get("detail", "") or l.get("user", "")
            rows_html += (
                "<div class='act-row'>"
                "<div class='av' style='" + style + "'>" + initials + "</div>"
                "<div><div class='an'>" + action + "</div>"
                "<div class='as'>" + detail + "</div></div>"
                "<div class='atime'>" + time_str + "</div></div>"
            )
    else:
        rows_html = "<div style='font-size:11px;color:#94A3B8;text-align:center;padding:1rem;'>Aucune activite recente</div>"

    st.markdown(
        "<div class='card'>"
        "<div class='chdr'><div class='ctitle'>Activite recente</div></div>"
        + rows_html + "</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Row 3 — Status + Audit + Docs
col_st, col_audit, col_doc = st.columns(3)

with col_st:
    ok_bdg   = "<span class='sbdg' style='background:#EDF5E4;color:#2D6A10;'>Actif</span>"
    ko_bdg   = "<span class='sbdg' style='background:#FFF0EB;color:#E8601C;'>Inactif</span>"
    miss_bdg = "<span class='sbdg' style='background:#FFF0EB;color:#E8601C;'>Manquante</span>"
    conf_bdg = "<span class='sbdg' style='background:#EDF5E4;color:#2D6A10;'>Configuree</span>"
    active_bdg = "<span class='sbdg' style='background:#EDF5E4;color:#2D6A10;'>Active</span>"

    def strow(dot, name, badge):
        return "<div class='st-row'><div class='sdot " + dot + "'></div><span class='sname'>" + name + "</span>" + badge + "</div>"

    st.markdown(
        "<div class='card'>"
        "<div class='chdr'><div class='ctitle'>Statut systeme</div></div>"
        + strow("sg" if ollama_ok else "so", "Ollama — Mistral 7B", ok_bdg if ollama_ok else ko_bdg)
        + strow("sg" if faiss_ok else "so", "Index FAISS", "<span class='sval'>24 chunks</span>" if faiss_ok else miss_bdg)
        + strow("sg", "EasyOCR", "<span class='sval'>Fr + Ar</span>")
        + strow("sg" if claude_ok else "so", "Claude Vision API", conf_bdg if claude_ok else miss_bdg)
        + strow("sg", "Piste audit", active_bdg)
        + "</div>",
        unsafe_allow_html=True
    )

with col_audit:
    mod_bdg_styles = {
        "OCR":      "background:#EBF2FA;color:#0B2E4E;",
        "Anomalie": "background:#FFF0EB;color:#E8601C;",
        "Assistant":"background:#EDF5E4;color:#2D6A10;",
        "Systeme":  "background:#EBF2FA;color:#185FA5;",
    }
    audit_html = ""
    if recent_logs:
        for l in recent_logs[:4]:
            mod = l.get("module", "OCR")
            bstyle = mod_bdg_styles.get(mod, "background:#EBF2FA;color:#0B2E4E;")
            time_str = l.get("timestamp", "")[-8:-3]
            user = l.get("user", "—")[:12]
            action = l.get("action", "—")
            audit_html += (
                "<div class='audit-row'>"
                "<span class='a-user'>" + user + "</span>"
                "<span class='a-act'>" + action + "</span>"
                "<span class='a-mod' style='" + bstyle + "'>" + mod + "</span>"
                "<span class='a-time'>" + time_str + "</span></div>"
            )
    else:
        audit_html = "<div style='font-size:11px;color:#94A3B8;text-align:center;padding:0.5rem;'>Aucune entree</div>"

    st.markdown(
        "<div class='card'>"
        "<div class='chdr'><div class='ctitle'>Piste audit</div><div class='cact'>Voir tout</div></div>"
        + audit_html + "</div>",
        unsafe_allow_html=True
    )

with col_doc:
    st.markdown(
        "<div class='card'>"
        "<div class='chdr'><div class='ctitle'>Documents supportes</div></div>"
        "<div class='doc-row'><div class='dic'>🪪</div><span class='dname'>Fiche ouverture compte</span><span class='dtype'>FP1/PP</span></div>"
        "<div class='doc-row'><div class='dic'>✍️</div><span class='dname'>Procuration bancaire</span><span class='dtype'>FP46</span></div>"
        "<div class='doc-row'><div class='dic'>🧾</div><span class='dname'>Factures fournisseurs</span><span class='dtype'>PDF/IMG</span></div>"
        "<div class='doc-row'><div class='dic'>📋</div><span class='dname'>Bons de commande</span><span class='dtype'>PDF/IMG</span></div>"
        "<div class='doc-row'><div class='dic'>📜</div><span class='dname'>Circulaires TGR</span><span class='dtype'>PDF</span></div>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)