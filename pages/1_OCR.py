import streamlit as st
import json, sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "ocr"))
from auth import require_auth, current_user
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header
from audit import log
try:
    from core.notifications import notify_ocr
except: notify_ocr = lambda *a, **k: False

st.set_page_config(page_title="OCR — TGR", page_icon="📄", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
require_auth()
render_sidebar(logo_html)
render_topbar("Extraction OCR", "OCR", "<span class='pill pn'>Module 1</span>")

FIELD_LABELS = {
    "numero_compte":"Numero de compte","nom":"Nom","prenom":"Prenom","cin":"CIN",
    "date_naissance":"Date de naissance","nationalite":"Nationalite","domicile":"Domicile",
    "ville":"Ville","telephone":"Telephone","profession":"Profession","date_ouverture":"Date d-ouverture",
    "mandant":"Mandant","mandataire":"Mandataire","date_procuration":"Date procuration","agence":"Agence",
    "date":"Date","montant":"Montant","fournisseur":"Fournisseur","reference":"Reference","objet":"Objet",
    "signature":"Signature presente","tampon":"Tampon present",
}
TYPE_LABELS = {
    "fiche_ouverture_compte":"Fiche d-ouverture de compte",
    "procuration":"Procuration","facture":"Facture",
    "bon_commande":"Bon de commande","mandat_paiement":"Mandat de paiement",
    "document_general":"Document general",
}

def conf_badge(conf):
    if conf >= 0.90: return "<span class='badge badge-green'>OK " + "{:.0%}".format(conf) + "</span>"
    if conf >= 0.75: return "<span class='badge badge-orange'>~ " + "{:.0%}".format(conf) + "</span>"
    return "<span class='badge badge-red'>! " + "{:.0%}".format(conf) + "</span>"

if "ocr_result"  not in st.session_state: st.session_state.ocr_result = None
if "corrections" not in st.session_state: st.session_state.corrections = {}
if "validated"   not in st.session_state: st.session_state.validated = False

col_up, col_info = st.columns([3, 1])
with col_up:
    st.markdown(section_header("Telechargement du document"), unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Glissez-deposez votre document ou cliquez pour parcourir", type=["jpg","jpeg","png","pdf"])
    if uploaded_file and st.button("Lancer l-extraction OCR"):
        st.session_state.validated = False
        st.session_state.corrections = {}
        log("OCR", "Upload document", uploaded_file.name)
        suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        with st.spinner("Traitement OCR en cours..."):
            try:
                from core.ocr.pipeline_ocr import run_pipeline
                result = run_pipeline(tmp_path)
                st.session_state.ocr_result = result
                log("OCR", "Extraction lancee", uploaded_file.name + " — " + result.get("type_document","") + " — " + str(result.get("nb_blocs_ocr","")) + " blocs")
                notify_ocr(uploaded_file.name, result.get("type_document",""), result.get("nb_blocs_ocr",0), current_user().get("username","Agent"))
                st.success("Extraction terminee — " + str(result["nb_blocs_ocr"]) + " blocs detectes")
            except Exception as e:
                st.error("Erreur : " + str(e))
            finally:
                try: os.remove(tmp_path)
                except: pass

with col_info:
    st.markdown(section_header("Types supportes"), unsafe_allow_html=True)
    st.markdown(
        "<div class='card'>"
        "<div style='font-size:10.5px;color:#334155;line-height:2.2;'>"
        "📋 Fiche ouverture compte<br>"
        "📜 Procuration (FP46)<br>"
        "🧾 Factures fournisseurs<br>"
        "📦 Bons de commande<br>"
        "💳 Mandats de paiement"
        "</div></div>",
        unsafe_allow_html=True
    )

if st.session_state.ocr_result:
    result = st.session_state.ocr_result
    st.markdown(section_header("Resultats de l-extraction"), unsafe_allow_html=True)

    type_label = TYPE_LABELS.get(result.get("type_document",""), result.get("type_document",""))
    methode = result.get("methode_extraction","easyocr")
    methode_bdg = "<span class='badge badge-green'>Gemini Vision</span>" if methode == "gemini_vision" else "<span class='badge badge-blue'>EasyOCR</span>"

    st.markdown(
        "<div style='display:flex;align-items:center;gap:1rem;padding:8px 12px;background:white;"
        "border:1px solid #E2E8F0;border-radius:6px;margin-bottom:12px;font-size:10.5px;'>"
        "<span style='color:#64748B;'>Type detecte :</span>"
        "<span style='font-weight:600;color:#0B2E4E;'>" + type_label + "</span>"
        "<span style='margin-left:auto;'>" + methode_bdg + "</span></div>",
        unsafe_allow_html=True
    )

    col_res, col_img = st.columns([3, 2])
    with col_res:
        st.markdown(
            "<div class='thdr'>"
            "<span style='flex:1;'>Champ</span>"
            "<span style='flex:2;'>Valeur extraite</span>"
            "<span style='width:80px;text-align:right;'>Confiance</span>"
            "</div>",
            unsafe_allow_html=True
        )
        rows = ""
        for nom, data in result["champs"].items():
            valeur = data["valeur"]
            conf   = data["confiance"]
            label  = FIELD_LABELS.get(nom, nom.replace("_"," ").title())
            display = ("Oui" if valeur else "Non") if isinstance(valeur, bool) else (str(valeur) if valeur else "non detecte")
            rows += (
                "<div class='trow'>"
                "<span style='flex:1;font-weight:500;color:#334155;font-size:10px;'>" + label + "</span>"
                "<span style='flex:2;color:#0B2E4E;font-size:10.5px;'>" + display + "</span>"
                "<span style='width:80px;text-align:right;'>" + conf_badge(conf) + "</span>"
                "</div>"
            )
        st.markdown("<div class='card' style='padding:0;'>" + rows + "</div>", unsafe_allow_html=True)

        statut = result["statut_validation"]
        if statut == "valide":
            st.markdown("<div style='margin-top:10px;padding:8px 12px;background:#EDF5E4;border:1px solid #BBF7D0;border-radius:6px;font-size:10.5px;font-weight:600;color:#2D6A10;'>Document valide automatiquement</div>", unsafe_allow_html=True)
        elif statut == "partiel":
            st.markdown("<div style='margin-top:10px;padding:8px 12px;background:#FFF7ED;border:1px solid #FED7AA;border-radius:6px;font-size:10.5px;font-weight:600;color:#C2410C;'>Certains champs necessitent une verification</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-top:10px;padding:8px 12px;background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;font-size:10.5px;font-weight:600;color:#B91C1C;'>Document a verifier manuellement</div>", unsafe_allow_html=True)

        if result.get("champs_a_valider") and not st.session_state.validated:
            st.markdown("<br>", unsafe_allow_html=True)
            for nom in result["champs_a_valider"]:
                label = FIELD_LABELS.get(nom, nom)
                val = result["champs"][nom].get("valeur","") or ""
                corrected = st.text_input("Corriger " + label, value=str(val), key="c_" + nom)
                if corrected: st.session_state.corrections[nom] = corrected
            if st.button("Valider les corrections"):
                for n, v in st.session_state.corrections.items():
                    result["champs"][n]["valeur"] = v
                    result["champs"][n]["confiance"] = 1.0
                result["champs_a_valider"] = []
                result["statut_validation"] = "valide"
                st.session_state.ocr_result = result
                st.session_state.validated = True
                log("OCR", "Correction champ", str(len(st.session_state.corrections)) + " champ(s) corrige(s)")
                st.rerun()
        if st.session_state.validated:
            st.success("Corrections enregistrees.")

    with col_img:
        if uploaded_file and uploaded_file.type != "application/pdf":
            st.image(uploaded_file, use_container_width=True)
        st.markdown(
            "<div class='card' style='margin-top:10px;font-size:10px;color:#64748B;line-height:2;'>"
            "<div style='font-weight:600;color:#0B2E4E;margin-bottom:4px;'>Informations</div>"
            + result["document_id"] + "<br>"
            + result.get("type_document","").replace("_"," ") + "<br>"
            + str(result["nb_blocs_ocr"]) + " blocs OCR"
            + "</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("Exporter JSON", json.dumps(result, ensure_ascii=False, indent=2),
                       "ocr_" + result["document_id"] + ".json", "application/json")

st.markdown("</div>", unsafe_allow_html=True)