import streamlit as st
import json, sys, os, tempfile, time
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "ocr"))
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header, kpi_card
from auth import require_auth, current_user
from audit import log

st.set_page_config(page_title="OCR Lot — TGR", page_icon="📦", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
render_sidebar(logo_html)
require_auth()

user = current_user()
render_topbar("Extraction OCR par Lot", "OCR Lot",
              "<span class='pill pn'>Module 1 — Lot</span>")

FIELD_LABELS = {
    "numero_compte":"N° Compte","nom":"Nom","prenom":"Prenom","cin":"CIN",
    "date_naissance":"Date naissance","nationalite":"Nationalite",
    "domicile":"Domicile","ville":"Ville","telephone":"Tel",
    "profession":"Profession","date_ouverture":"Date ouverture",
    "mandant":"Mandant","mandataire":"Mandataire",
    "date_procuration":"Date procuration","agence":"Agence",
    "date":"Date","montant":"Montant","fournisseur":"Fournisseur",
    "reference":"Reference","signature":"Signature","tampon":"Tampon",
}

TYPE_LABELS = {
    "fiche_ouverture_compte": "Fiche ouverture",
    "procuration":            "Procuration",
    "facture":                "Facture",
    "bon_commande":           "Bon de commande",
    "mandat_paiement":        "Mandat paiement",
    "document_general":       "Document general",
}

if "lot_results"  not in st.session_state: st.session_state.lot_results  = []
if "lot_running"  not in st.session_state: st.session_state.lot_running  = False

# ── UPLOAD ────────────────────────────────────────────────────────────────────
st.markdown(section_header("Telechargement des documents"), unsafe_allow_html=True)

col_up, col_info = st.columns([3, 1])
with col_up:
    uploaded_files = st.file_uploader(
        "Selectionnez plusieurs documents (JPG, PNG, PDF)",
        type=["jpg","jpeg","png","pdf"],
        accept_multiple_files=True,
        help="Vous pouvez selectionner jusqu-a 20 documents a la fois"
    )

with col_info:
    st.markdown(
        "<div class='card'>"
        "<div class='chdr'><div class='ctitle'>Traitement en lot</div></div>"
        "<div style='font-size:10px;color:#475569;line-height:2;'>"
        "📄 Jusqu-a 20 fichiers<br>"
        "🔍 Detection auto du type<br>"
        "📊 Rapport global<br>"
        "⬇️ Export JSON lot<br>"
        "📧 Notification auto"
        "</div></div>",
        unsafe_allow_html=True
    )

if uploaded_files:
    st.markdown(
        "<div style='background:#EBF2FA;border:1px solid #BFDBFE;border-radius:6px;"
        "padding:8px 12px;font-size:10.5px;color:#1E40AF;margin:8px 0;'>"
        + str(len(uploaded_files)) + " fichier(s) selectionne(s) — "
        + ", ".join([f.name for f in uploaded_files[:3]])
        + ("..." if len(uploaded_files) > 3 else "")
        + "</div>",
        unsafe_allow_html=True
    )

    col_btn, col_clear, _ = st.columns([1, 1, 4])
    with col_btn:
        launch = st.button("▶  Lancer le traitement lot", use_container_width=True)
    with col_clear:
        if st.button("🗑  Effacer les resultats", use_container_width=True):
            st.session_state.lot_results = []
            st.rerun()

    if launch:
        st.session_state.lot_results = []
        log("OCR", "Traitement lot lance", str(len(uploaded_files)) + " fichiers", user.get("username",""))

        progress_bar = st.progress(0, text="Initialisation...")
        status_area  = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            progress = (i) / len(uploaded_files)
            progress_bar.progress(progress, text="Traitement " + str(i+1) + "/" + str(len(uploaded_files)) + " — " + uploaded_file.name)
            status_area.markdown(
                "<div style='font-size:10.5px;color:#475569;padding:6px 0;'>"
                "⏳ Traitement de <strong>" + uploaded_file.name + "</strong>...</div>",
                unsafe_allow_html=True
            )

            suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            start_time = time.time()
            try:
                from core.ocr.pipeline_ocr import run_pipeline
                result = run_pipeline(tmp_path)
                duration = round(time.time() - start_time, 1)
                result["filename"]  = uploaded_file.name
                result["duration"]  = duration
                result["error"]     = None
                result["file_size"] = round(uploaded_file.size / 1024, 1)
                st.session_state.lot_results.append(result)
            except Exception as e:
                st.session_state.lot_results.append({
                    "filename": uploaded_file.name,
                    "error":    str(e),
                    "type_document": "—",
                    "champs": {},
                    "statut_validation": "erreur",
                    "nb_blocs_ocr": 0,
                    "duration": round(time.time() - start_time, 1),
                })
            finally:
                try: os.remove(tmp_path)
                except: pass

        progress_bar.progress(1.0, text="Traitement termine !")
        status_area.empty()
        log("OCR", "Traitement lot termine", str(len(st.session_state.lot_results)) + " fichiers traites", user.get("username",""))
        st.rerun()

# ── RESULTATS ─────────────────────────────────────────────────────────────────
if st.session_state.lot_results:
    results = st.session_state.lot_results
    n_total  = len(results)
    n_ok     = sum(1 for r in results if r.get("statut_validation") == "valide")
    n_part   = sum(1 for r in results if r.get("statut_validation") == "partiel")
    n_err    = sum(1 for r in results if r.get("error") or r.get("statut_validation") == "erreur")
    avg_time = round(sum(r.get("duration",0) for r in results) / n_total, 1)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi_card("#0B2E4E","#EBF2FA","📦","Documents traites",str(n_total),"Total lot"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("#2D6A10","#EDF5E4","✅","Valides",str(n_ok),"Extraction reussie"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("#E8601C","#FFF0EB","🟡","Partiels",str(n_part),"A verifier"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("#185FA5","#EBF2FA","⏱","Temps moyen",str(avg_time)+"s","Par document"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Resultats par document"), unsafe_allow_html=True)

    # En-tete tableau
    st.markdown(
        "<div class='thdr'>"
        "<span style='min-width:200px;'>Fichier</span>"
        "<span style='min-width:150px;'>Type detecte</span>"
        "<span style='min-width:80px;'>Blocs OCR</span>"
        "<span style='min-width:80px;'>Duree</span>"
        "<span style='min-width:100px;'>Statut</span>"
        "<span style='flex:1;'></span>"
        "</div>",
        unsafe_allow_html=True
    )

    for r in results:
        statut = r.get("statut_validation","erreur")
        if statut == "valide":
            bdg = "<span class='badge badge-green'>Valide</span>"
        elif statut == "partiel":
            bdg = "<span class='badge badge-orange'>Partiel</span>"
        elif statut == "a_verifier":
            bdg = "<span class='badge badge-orange'>A verifier</span>"
        else:
            bdg = "<span class='badge badge-red'>Erreur</span>"

        type_label = TYPE_LABELS.get(r.get("type_document",""), r.get("type_document","—"))

        st.markdown(
            "<div class='trow'>"
            "<span style='min-width:200px;font-weight:500;color:#0B2E4E;font-size:10.5px;'>📄 " + r.get("filename","") + "</span>"
            "<span style='min-width:150px;color:#475569;font-size:10px;'>" + type_label + "</span>"
            "<span style='min-width:80px;color:#475569;font-size:10px;'>" + str(r.get("nb_blocs_ocr",0)) + "</span>"
            "<span style='min-width:80px;color:#475569;font-size:10px;'>" + str(r.get("duration",0)) + "s</span>"
            "<span style='min-width:100px;'>" + bdg + "</span>"
            "<span style='flex:1;'></span>"
            "</div>",
            unsafe_allow_html=True
        )

        # Detail expandable
        if not r.get("error") and r.get("champs"):
            with st.expander("Voir les champs extraits — " + r.get("filename","")):
                champs = r.get("champs",{})
                cols = st.columns(3)
                for j, (nom, data) in enumerate(champs.items()):
                    valeur = data.get("valeur")
                    conf   = data.get("confiance", 0)
                    label  = FIELD_LABELS.get(nom, nom.replace("_"," ").title())
                    display = ("Oui" if valeur else "Non") if isinstance(valeur, bool) else (str(valeur) if valeur else "—")
                    conf_color = "#2D6A10" if conf >= 0.9 else ("#E8601C" if conf >= 0.75 else "#B91C1C")
                    with cols[j % 3]:
                        st.markdown(
                            "<div style='padding:5px 8px;border:1px solid #E2E8F0;border-radius:5px;margin-bottom:5px;'>"
                            "<div style='font-size:9px;color:#64748B;'>" + label + "</div>"
                            "<div style='font-size:10.5px;font-weight:500;color:#0B2E4E;'>" + display + "</div>"
                            "<div style='font-size:8.5px;color:" + conf_color + ";'>" + "{:.0%}".format(conf) + "</div>"
                            "</div>",
                            unsafe_allow_html=True
                        )
        elif r.get("error"):
            with st.expander("Erreur — " + r.get("filename","")):
                st.error(r["error"])

    # ── EXPORT ────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Export des resultats"), unsafe_allow_html=True)

    col_j, col_c, _ = st.columns([1, 1, 3])

    with col_j:
        # Export JSON global
        export_data = {
            "date_traitement": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent":           user.get("username",""),
            "nb_documents":    n_total,
            "resultats":       results
        }
        st.download_button(
            "⬇  Exporter JSON lot",
            json.dumps(export_data, ensure_ascii=False, indent=2),
            "ocr_lot_" + datetime.now().strftime("%Y%m%d_%H%M") + ".json",
            "application/json",
            use_container_width=True
        )

    with col_c:
        # Export CSV resume
        import io
        csv_lines = ["Fichier,Type,Blocs OCR,Duree,Statut"]
        for r in results:
            csv_lines.append(",".join([
                r.get("filename",""),
                r.get("type_document",""),
                str(r.get("nb_blocs_ocr",0)),
                str(r.get("duration",0)) + "s",
                r.get("statut_validation","")
            ]))
        csv_content = "\n".join(csv_lines).encode("utf-8-sig")
        st.download_button(
            "⬇  Exporter CSV resume",
            csv_content,
            "ocr_lot_resume_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv",
            "text/csv",
            use_container_width=True
        )

st.markdown("</div>", unsafe_allow_html=True)