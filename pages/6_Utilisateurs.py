"""
6_Utilisateurs.py — Gestion des utilisateurs (Admin uniquement)
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header, kpi_card
from auth import require_auth, require_role, get_all_users, add_user, delete_user, change_password, current_user
from audit import log

st.set_page_config(page_title="Utilisateurs — TGR", page_icon="👥", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

require_auth()
require_role(["Admin"])

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
render_sidebar(logo_html)
render_topbar("Gestion des Utilisateurs", "Utilisateurs", "<span class='pill pn'>Admin uniquement</span>")

users = get_all_users()
roles = {"Admin": 0, "Agent": 0, "Auditeur": 0}
for u in users:
    if u[2] in roles: roles[u[2]] += 1

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(kpi_card("#0B2E4E","#EBF2FA","👥","Total utilisateurs",str(len(users)),"Comptes actifs"), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("#E8601C","#FFF0EB","🔑","Admins",str(roles["Admin"]),"Acces complet"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("#2D6A10","#EDF5E4","👤","Agents",str(roles["Agent"]),"Acces standard"), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("#185FA5","#EBF2FA","👁","Auditeurs",str(roles["Auditeur"]),"Lecture seule"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["👥  Liste des utilisateurs", "➕  Ajouter un utilisateur", "🔑  Changer mot de passe"])

ROLE_COLORS = {
    "Admin":    ("badge-red",    "🔑"),
    "Agent":    ("badge-green",  "👤"),
    "Auditeur": ("badge-blue",   "👁"),
}

with tab1:
    st.markdown(section_header("Comptes utilisateurs"), unsafe_allow_html=True)
    st.markdown(
        "<div class='thdr'>"
        "<span style='min-width:50px;'>ID</span>"
        "<span style='min-width:140px;'>Identifiant</span>"
        "<span style='min-width:160px;'>Nom</span>"
        "<span style='min-width:110px;'>Role</span>"
        "<span style='min-width:110px;'>Cree le</span>"
        "<span style='min-width:80px;text-align:right;'>Action</span>"
        "</div>",
        unsafe_allow_html=True
    )
    for u in users:
        uid, username, role, nom, created = u
        bclass, icon = ROLE_COLORS.get(role, ("badge-gray", "👤"))
        st.markdown(
            "<div class='trow'>"
            "<span style='min-width:50px;color:#94A3B8;font-size:10px;'>#" + str(uid) + "</span>"
            "<span style='min-width:140px;font-weight:600;color:#0B2E4E;font-size:10.5px;'>" + username + "</span>"
            "<span style='min-width:160px;color:#475569;font-size:10.5px;'>" + (nom or "-") + "</span>"
            "<span style='min-width:110px;'><span class='badge " + bclass + "'>" + icon + " " + role + "</span></span>"
            "<span style='min-width:110px;color:#94A3B8;font-size:10px;'>" + (created or "-") + "</span>"
            "<span style='min-width:80px;text-align:right;'></span>"
            "</div>",
            unsafe_allow_html=True
        )
        if username != current_user()["username"] and username != "admin":
            col_del, _ = st.columns([1, 8])
            with col_del:
                if st.button("Supprimer", key="del_" + username):
                    delete_user(username)
                    log("Systeme", "Utilisateur supprime", username, current_user()["username"])
                    st.success("Utilisateur " + username + " supprime.")
                    st.rerun()

with tab2:
    st.markdown(section_header("Ajouter un compte"), unsafe_allow_html=True)
    with st.form("add_user_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            new_username = st.text_input("Identifiant", placeholder="Ex: agent3")
            new_password = st.text_input("Mot de passe", type="password", placeholder="Min. 6 caracteres")
        with col_b:
            new_nom  = st.text_input("Nom complet", placeholder="Ex: Agent Alaoui")
            new_role = st.selectbox("Role", ["Agent", "Auditeur", "Admin"])

        st.markdown(
            "<div style='background:#EBF2FA;border:1px solid #BFDBFE;border-radius:6px;padding:8px 12px;font-size:10px;color:#1E40AF;margin:8px 0;'>"
            "Admin : acces complet + gestion utilisateurs<br>"
            "Agent : OCR, anomalies, assistant<br>"
            "Auditeur : lecture seule (dashboard + audit)"
            "</div>",
            unsafe_allow_html=True
        )
        if st.form_submit_button("Creer le compte", use_container_width=False):
            if not new_username or not new_password or not new_nom:
                st.error("Tous les champs sont obligatoires.")
            elif len(new_password) < 6:
                st.error("Le mot de passe doit contenir au moins 6 caracteres.")
            else:
                if add_user(new_username, new_password, new_role, new_nom):
                    log("Systeme", "Utilisateur cree", new_username + " (" + new_role + ")", current_user()["username"])
                    st.success("Compte " + new_username + " cree avec le role " + new_role + ".")
                    st.rerun()
                else:
                    st.error("Identifiant deja utilise. Choisissez-en un autre.")

with tab3:
    st.markdown(section_header("Changer un mot de passe"), unsafe_allow_html=True)
    with st.form("change_pwd_form"):
        target_user = st.selectbox("Utilisateur", [u[1] for u in users])
        new_pwd     = st.text_input("Nouveau mot de passe", type="password")
        confirm_pwd = st.text_input("Confirmer le mot de passe", type="password")
        if st.form_submit_button("Modifier le mot de passe"):
            if not new_pwd or not confirm_pwd:
                st.error("Remplissez les deux champs.")
            elif new_pwd != confirm_pwd:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(new_pwd) < 6:
                st.error("Minimum 6 caracteres.")
            else:
                change_password(target_user, new_pwd)
                log("Systeme", "Mot de passe modifie", target_user, current_user()["username"])
                st.success("Mot de passe de " + target_user + " modifie.")

st.markdown("</div>", unsafe_allow_html=True)