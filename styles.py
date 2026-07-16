import base64, os

GLOBAL_CSS = """
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
.pr { background: #FFF0EB; color: #E8601C; }
.dot5 { width: 5px; height: 5px; border-radius: 50%; display: inline-block; margin-right: 3px; }
.dg { background: #2D6A10; } .dn { background: #0B2E4E; } .do { background: #E8601C; }
.page-content { padding: 14px 20px; }
.card { background: white; border-radius: 8px; border: 1px solid #E2E8F0; padding: 12px 14px; margin-bottom: 10px; }
.chdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #F1F5F9; }
.ctitle { font-size: 11.5px; font-weight: 500; color: #0B2E4E; }
.cact   { font-size: 9.5px; color: #E8601C; cursor: pointer; }
.sec-hdr { font-size: 11.5px; font-weight: 600; color: #0B2E4E; padding: 10px 0 8px; border-bottom: 2px solid #E2E8F0; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
.sec-hdr::before { content: ''; width: 3px; height: 14px; background: #E8601C; border-radius: 2px; display: inline-block; }
.kpi { background: white; border-radius: 8px; border: 1px solid #E2E8F0; padding: 12px 14px; }
.kpi-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.kpi-lbl  { font-size: 9.5px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-ico  { width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; }
.kpi-val  { font-size: 22px; font-weight: 500; line-height: 1; margin-bottom: 5px; }
.kpi-foot { display: flex; align-items: center; justify-content: space-between; }
.kpi-sub  { font-size: 9.5px; color: #94A3B8; }
.st-row { display: flex; align-items: center; gap: 7px; padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 10.5px; }
.st-row:last-child { border-bottom: none; }
.sdot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.sg { background: #2D6A10; } .so { background: #E8601C; }
.sname { flex: 1; color: #334155; }
.sval  { font-size: 9.5px; color: #94A3B8; }
.sbdg  { padding: 1px 6px; border-radius: 20px; font-size: 8.5px; font-weight: 500; }
.trow { display: flex; align-items: center; padding: 7px 10px; border-bottom: 1px solid #F1F5F9; font-size: 10.5px; }
.trow:last-child { border-bottom: none; }
.trow:hover { background: #F8FAFC; }
.thdr { display: flex; align-items: center; padding: 6px 10px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; font-size: 9px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; border-radius: 6px 6px 0 0; }
.badge { padding: 2px 7px; border-radius: 20px; font-size: 8.5px; font-weight: 600; }
.badge-green  { background: #EDF5E4; color: #2D6A10; }
.badge-orange { background: #FFF0EB; color: #E8601C; }
.badge-red    { background: #FEF2F2; color: #B91C1C; }
.badge-blue   { background: #EBF2FA; color: #0B2E4E; }
.badge-gray   { background: #F1F5F9; color: #64748B; }
.stButton > button { background: #0B2E4E !important; color: white !important; border: none !important; border-radius: 6px !important; font-size: 12px !important; font-weight: 500 !important; }
.stButton > button:hover { background: #12426E !important; }
.stTabs [data-baseweb="tab-list"] { background: white; border-bottom: 2px solid #E2E8F0; gap: 0; padding: 0; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; color: #64748B; font-size: 12px; font-weight: 500; padding: 8px 16px; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.stTabs [aria-selected="true"] { color: #0B2E4E !important; font-weight: 600 !important; border-bottom: 2px solid #E8601C !important; }
.stTextInput input, .stSelectbox > div > div, .stTextArea textarea { border: 1px solid #E2E8F0 !important; border-radius: 6px !important; font-size: 12px !important; }
</style>
"""

def get_logo_html(logo_path):
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return '<img src="data:image/jpeg;base64,' + b64 + '" style="width:85px;background:white;border-radius:5px;padding:3px;margin-bottom:0.6rem;">'
    except:
        return ""

def render_sidebar(logo_html, active_page=""):
    import streamlit as st
    try:
        from auth import current_user, logout, is_authenticated
        user = current_user() if is_authenticated() else {}
    except: user = {}

    with st.sidebar:
        st.markdown(
            "<div class='sb-top'>"
            + logo_html
            + "<div class='sb-brand'><div class='sb-box'>TGR</div>"
            + "<div><div class='sb-name'>Tresorerie Generale<br>du Royaume</div>"
            + "<div class='sb-min'>Ministere des Finances</div></div></div>"
            + "<div class='sb-line'></div></div>",
            unsafe_allow_html=True
        )

        # User info
        if user:
            role_colors = {"Admin":"#E8601C","Agent":"#2D6A10","Auditeur":"#185FA5"}
            role_color = role_colors.get(user.get("role",""), "#64748B")
            st.markdown(
                "<div style='padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.07);'>"
                "<div style='font-size:10px;color:rgba(255,255,255,0.4);margin-bottom:4px;'>Connecte en tant que</div>"
                "<div style='display:flex;align-items:center;gap:8px;'>"
                "<div style='width:26px;height:26px;border-radius:50%;background:" + role_color + ";display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;color:white;flex-shrink:0;'>"
                + user.get("username","?")[0].upper() + "</div>"
                "<div><div style='font-size:11px;font-weight:500;color:white;'>" + user.get("nom", user.get("username","")) + "</div>"
                "<div style='font-size:9px;color:" + role_color + ";'>" + user.get("role","") + "</div></div>"
                "</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("<div class='sb-grp'>Modules</div>", unsafe_allow_html=True)
        st.page_link("main.py",               label="🏠  Accueil")
        st.page_link("pages/1_OCR.py",        label="📄  Extraction OCR")
        st.page_link("pages/7_OCR_Lot.py",     label="📦  OCR par Lot")
        st.page_link("pages/2_Anomalies.py",  label="⚠️  Detection Anomalies")
        st.page_link("pages/3_Assistant.py",  label="💬  Assistant Reglementaire")
        st.page_link("pages/4_Dashboard.py",  label="📊  Tableau de Bord")
        st.markdown("<div class='sb-grp' style='margin-top:4px;'>Administration</div>", unsafe_allow_html=True)
        st.page_link("pages/5_Parametres.py", label="⚙️  Parametres")
        if user.get("role") == "Admin":
            st.page_link("pages/6_Utilisateurs.py", label="👥  Utilisateurs")

        # Logout button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪  Deconnexion", use_container_width=True, key="logout_btn"):
            try:
                from audit import log
                log("Systeme", "Deconnexion", user.get("username",""), user.get("username",""))
                logout()
            except: pass
            st.rerun()

        st.markdown("<div class='sb-foot'>Plateforme IA — Usage interne TGR<br>Stage Ingenieur 2025 / 2026</div>", unsafe_allow_html=True)

def render_topbar(title, breadcrumb, badges_html=""):
    import streamlit as st
    st.markdown(
        "<div class='topbar'>"
        "<div><div class='tb-bc'>TGR — Plateforme IA / " + breadcrumb + "</div>"
        "<div class='tb-t'>" + title + "</div></div>"
        "<div style='display:flex;gap:7px;'>" + badges_html + "</div>"
        "</div><div class='page-content'>",
        unsafe_allow_html=True
    )

def section_header(title):
    return "<div class='sec-hdr'>" + title + "</div>"

def strow(dot, name, badge):
    return "<div class='st-row'><div class='sdot " + dot + "'></div><span class='sname'>" + name + "</span>" + badge + "</div>"

def kpi_card(color, bg, icon, label, value, sub, trend=""):
    return (
        "<div class='kpi' style='border-top:3px solid " + color + ";'>"
        "<div class='kpi-head'><div class='kpi-lbl'>" + label + "</div>"
        "<div class='kpi-ico' style='background:" + bg + ";color:" + color + ";'>" + icon + "</div></div>"
        "<div class='kpi-val' style='color:" + color + ";'>" + value + "</div>"
        "<div class='kpi-foot'><span class='kpi-sub'>" + sub + "</span>" + trend + "</div></div>"
    )