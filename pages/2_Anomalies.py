import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "ml"))
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header, kpi_card
from auth import require_auth, current_user
from audit import log
from core.ml.client_compliance import verifier_lot_clients, REGLES_PAR_TYPE
from core.ml.rapport_pdf import generate_rapport_pdf
try:
    from core.notifications import notify_anomalie
except: notify_anomalie = lambda *a, **k: False
from core.ml.dossiers_db import save_lot, search_dossiers, get_dossier, get_historique, get_stats, update_commentaire, delete_dossier, init_db

st.set_page_config(page_title="Anomalies — TGR", page_icon="⚠️", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
render_sidebar(logo_html)
require_auth()

init_db()
user = current_user()

render_topbar("Detection d-Anomalies — Dossiers Clients", "Anomalies",
              "<span class='pill pn'>Module 2</span>")

DOSSIERS = [
    {"client_id":"CLI-00123","type_client":"personne_physique",
     "champs":{"nom":"Benhammi","prenom":"Youssef","cin":"BE 123456","adresse":"Rue Hassan II","ville":"Rabat"},
     "documents_fournis":["copie_cin","demande_ouverture"]},
    {"client_id":"CLI-00456","type_client":"societe",
     "champs":{"raison_sociale":"ATLAS BTP SARL","forme_juridique":"SARL","rc":"12/4582","code_analytique":"4582","adresse_siege":"Zone Industrielle, Casablanca"},
     "documents_fournis":["statuts","extrait_rc","cin_representant","pv_designation_signataires"]},
    {"client_id":"CLI-00789","type_client":"association",
     "champs":{"nom_association":"Association Al Amal","adresse_siege":"Av. Mohammed V, Fes","date_creation":"2018-03-12","nom_president":"Karim Alaoui","date_certificat_depot":"2018-01-10","date_derniere_ag":"2024-06-15"},
     "documents_fournis":["statuts","pv_ag_constitutive","liste_bureau"]},
    {"client_id":"CLI-01011","type_client":"cooperative",
     "champs":{"nom_cooperative":"Cooperative Agricole Souss","adresse_siege":"Agadir","date_creation":"2020-05-02"},
     "documents_fournis":["statuts","pv_ag_constitutive"]},
    {"client_id":"CLI-01234","type_client":"etablissement_public",
     "champs":{"denomination":"Ecole Superieure de Technologie","adresse":"Av. Allal El Fassi, Rabat","responsable":"Dr. Mohammed Alami"},
     "documents_fournis":["texte_creation","decision_nomination_responsable"]},
]

tab1, tab2, tab3 = st.tabs(["⚠️  Verification Conformite", "📋  Historique Dossiers", "🔍  Recherche & Statistiques"])

# ── TAB 1 : VERIFICATION ──────────────────────────────────────────────────────
with tab1:
    resultats = verifier_lot_clients(DOSSIERS)
    n_ok  = sum(1 for r in resultats if r["statut"]=="conforme")
    n_pt  = sum(1 for r in resultats if r["statut"]=="partiellement_conforme")
    n_ko  = sum(1 for r in resultats if r["statut"]=="non_conforme")

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi_card("#0B2E4E","#EBF2FA","📁","Dossiers analyses",str(len(resultats)),"Total"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("#2D6A10","#EDF5E4","✅","Conformes",str(n_ok),"Sans anomalie"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("#E8601C","#FFF0EB","🟡","A corriger",str(n_pt),"Partiels"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("#B91C1C","#FEF2F2","❌","Non conformes",str(n_ko),"Bloquants"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sauvegarder dans SQLite
    col_save, col_pdf, _ = st.columns([1, 1, 3])
    with col_save:
        if st.button("💾  Sauvegarder dans la base"):
            save_lot(DOSSIERS, resultats, user.get("username","Agent.TGR"))
            log("Anomalie", "Dossiers sauvegardes", str(len(DOSSIERS)) + " dossiers", user.get("username",""))
            for d, r in zip(DOSSIERS, resultats):
                if r.get("statut") == "non_conforme":
                    notify_anomalie(d["client_id"], d["type_client"], r["score_conformite"], r.get("anomalies",[]), user.get("username","Agent"))
            st.success(str(len(DOSSIERS)) + " dossiers sauvegardes dans la base SQLite.")
    with col_pdf:
        LOGO_PATH_PDF = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
        try:
            pdf_bytes = generate_rapport_pdf(
                DOSSIERS, resultats,
                agent=user.get("username","Agent.TGR"),
                logo_path=LOGO_PATH_PDF
            )
            st.download_button(
                "📄  Exporter PDF",
                data=pdf_bytes,
                file_name="rapport_conformite_" + __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M") + ".pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error("Erreur PDF : " + str(e))

    st.markdown(section_header("Resultats par dossier"), unsafe_allow_html=True)
    st.markdown(
        "<div class='thdr'>"
        "<span style='min-width:120px;'>ID Client</span>"
        "<span style='min-width:160px;'>Type</span>"
        "<span style='flex:1;'>Anomalies</span>"
        "<span style='min-width:80px;text-align:center;'>Score</span>"
        "<span style='min-width:110px;text-align:right;'>Statut</span>"
        "</div>", unsafe_allow_html=True
    )

    for r in resultats:
        statut = r["statut"]
        if statut == "conforme":
            bdg, bg = "<span class='badge badge-green'>Conforme</span>", "#F0FDF4"
        elif statut == "partiellement_conforme":
            bdg, bg = "<span class='badge badge-orange'>Partiel</span>", "#FFFBEB"
        else:
            bdg, bg = "<span class='badge badge-red'>Non conforme</span>", "#FEF2F2"

        score = r["score_conformite"]
        sc    = "#2D6A10" if score>=0.9 else ("#E8601C" if score>=0.7 else "#B91C1C")
        anom  = "".join(["<div style='font-size:9.5px;color:#92400E;margin-top:2px;'>⚠ " + a + "</div>" for a in r.get("anomalies",[])])
        if not anom: anom = "<div style='font-size:9.5px;color:#2D6A10;'>Aucune anomalie</div>"

        st.markdown(
            "<div class='trow' style='background:" + bg + ";border:1px solid #E2E8F0;border-top:none;align-items:flex-start;'>"
            "<span style='min-width:120px;font-weight:600;color:#0B2E4E;font-size:10.5px;'>" + r["client_id"] + "</span>"
            "<span style='min-width:160px;color:#475569;font-size:10px;'>" + r.get("type_client","").replace("_"," ").title() + "</span>"
            "<div style='flex:1;'>" + anom + "</div>"
            "<span style='min-width:80px;text-align:center;font-weight:600;color:" + sc + ";'>" + "{:.0%}".format(score) + "</span>"
            "<span style='min-width:110px;text-align:right;'>" + bdg + "</span>"
            "</div>", unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Detail des anomalies"), unsafe_allow_html=True)
    for r in resultats:
        if r["statut"] == "conforme": continue
        with st.expander(r["client_id"] + " — " + r.get("type_client","").replace("_"," ").title()):
            if r.get("champs_manquants"):
                st.markdown("**Champs manquants :**")
                for c in r["champs_manquants"]: st.markdown("- `" + c + "`")
            if r.get("documents_manquants"):
                st.markdown("**Documents manquants :**")
                for d in r["documents_manquants"]: st.markdown("- `" + d + "`")

    with st.expander("📋 Referentiel de conformite TGR"):
        for tc, reg in REGLES_PAR_TYPE.items():
            ca, cb = st.columns(2)
            with ca: st.markdown("**" + tc.replace("_"," ").title() + "** — " + ", ".join(["`"+c+"`" for c in reg["champs_obligatoires"]]))
            with cb: st.markdown(", ".join(["`"+d+"`" for d in reg["documents_requis"]]))
            st.markdown("---")

# ── TAB 2 : HISTORIQUE ────────────────────────────────────────────────────────
with tab2:
    st.markdown(section_header("Historique des dossiers"), unsafe_allow_html=True)

    # Recherche rapide
    col_s, col_t, col_st = st.columns(3)
    with col_s: search_id = st.text_input("Rechercher par ID", placeholder="CLI-00123")
    with col_t: filter_type = st.selectbox("Type client", ["Tous","personne_physique","societe","association","cooperative","etablissement_public"])
    with col_st: filter_statut = st.selectbox("Statut", ["Tous","conforme","partiellement_conforme","non_conforme"])

    dossiers_db = search_dossiers(
        client_id=search_id if search_id else None,
        type_client=filter_type if filter_type != "Tous" else None,
        statut=filter_statut if filter_statut != "Tous" else None,
    )

    if not dossiers_db:
        st.info("Aucun dossier en base. Cliquez sur 'Sauvegarder dans la base' dans l-onglet Verification.")
    else:
        st.markdown(str(len(dossiers_db)) + " dossier(s) trouve(s)", unsafe_allow_html=True)
        st.markdown(
            "<div class='thdr'>"
            "<span style='min-width:120px;'>ID Client</span>"
            "<span style='min-width:150px;'>Type</span>"
            "<span style='min-width:130px;'>Agent</span>"
            "<span style='min-width:100px;'>Score</span>"
            "<span style='min-width:100px;'>Verifications</span>"
            "<span style='min-width:130px;'>Derniere MAJ</span>"
            "<span style='min-width:110px;text-align:right;'>Statut</span>"
            "</div>", unsafe_allow_html=True
        )

        for d in dossiers_db:
            statut = d.get("statut","")
            if statut == "conforme":     bdg = "<span class='badge badge-green'>Conforme</span>"
            elif statut == "partiellement_conforme": bdg = "<span class='badge badge-orange'>Partiel</span>"
            else:                        bdg = "<span class='badge badge-red'>Non conforme</span>"
            score = d.get("score", 0)
            sc = "#2D6A10" if score>=0.9 else ("#E8601C" if score>=0.7 else "#B91C1C")
            date_maj = d.get("date_maj","")[:16] if d.get("date_maj") else "-"
            nb_verif = d.get("nb_verifications", 1)

            st.markdown(
                "<div class='trow'>"
                "<span style='min-width:120px;font-weight:600;color:#0B2E4E;font-size:10.5px;'>" + d["client_id"] + "</span>"
                "<span style='min-width:150px;color:#475569;font-size:10px;'>" + d.get("type_client","").replace("_"," ").title() + "</span>"
                "<span style='min-width:130px;color:#475569;font-size:10px;'>" + (d.get("agent") or "-") + "</span>"
                "<span style='min-width:100px;font-weight:600;color:" + sc + ";'>" + "{:.0%}".format(score) + "</span>"
                "<span style='min-width:100px;color:#475569;font-size:10px;'>" + str(nb_verif) + " fois</span>"
                "<span style='min-width:130px;color:#94A3B8;font-size:9.5px;'>" + date_maj + "</span>"
                "<span style='min-width:110px;text-align:right;'>" + bdg + "</span>"
                "</div>", unsafe_allow_html=True
            )

            # Historique detail
            with st.expander("Historique de " + d["client_id"]):
                hist = get_historique(d["client_id"])
                if hist:
                    for h in hist:
                        sc2 = "#2D6A10" if h["score"]>=0.9 else ("#E8601C" if h["score"]>=0.7 else "#B91C1C")
                        st.markdown(
                            "<div style='display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid #F1F5F9;font-size:10px;'>"
                            "<span style='color:#94A3B8;min-width:130px;'>" + (h["date_verif"] or "")[:16] + "</span>"
                            "<span style='color:#0B2E4E;font-weight:500;min-width:110px;'>" + (h["agent"] or "-") + "</span>"
                            "<span style='font-weight:600;color:" + sc2 + ";min-width:60px;'>" + "{:.0%}".format(h["score"]) + "</span>"
                            "<span style='color:#475569;flex:1;'>" + (", ".join(h["anomalies"][:2]) if h["anomalies"] else "Conforme") + "</span>"
                            "</div>", unsafe_allow_html=True
                        )

                    # Commentaire
                    commentaire = st.text_input("Ajouter un commentaire", key="comm_" + d["client_id"])
                    if st.button("Enregistrer", key="save_comm_" + d["client_id"]):
                        update_commentaire(d["client_id"], commentaire)
                        st.success("Commentaire enregistre.")

# ── TAB 3 : STATS ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown(section_header("Statistiques de la base"), unsafe_allow_html=True)
    stats = get_stats()

    if stats["total"] == 0:
        st.info("Aucun dossier en base. Sauvegardez d-abord des dossiers.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(kpi_card("#0B2E4E","#EBF2FA","📁","Total dossiers",str(stats["total"]),"Base SQLite"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("#2D6A10","#EDF5E4","📈","Taux conformite","{:.0%}".format(stats["taux_conformite"]),"Global"), unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("#E8601C","#FFF0EB","🔄","Verifications",str(stats["total_verifs"]),"Total historique"), unsafe_allow_html=True)
        with c4: st.markdown(kpi_card("#185FA5","#EBF2FA","⭐","Score moyen","{:.0%}".format(stats["avg_score"]),"Moyenne"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown(section_header("Repartition par statut"), unsafe_allow_html=True)
            import pandas as pd
            df_statut = pd.DataFrame({
                "Statut": ["Conformes","A corriger","Non conformes"],
                "Nombre": [stats["conformes"], stats["partiels"], stats["non_conformes"]]
            })
            st.bar_chart(df_statut.set_index("Statut"), color="#0B2E4E", height=220)

        with col_g2:
            st.markdown(section_header("Repartition par type de client"), unsafe_allow_html=True)
            if stats["par_type"]:
                df_type = pd.DataFrame(list(stats["par_type"].items()), columns=["Type","Nombre"])
                st.bar_chart(df_type.set_index("Type"), color="#E8601C", height=220)

st.markdown("</div>", unsafe_allow_html=True)