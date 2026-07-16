import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "rag"))
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header
from auth import require_auth, current_user
from audit import log
try:
    from core.notifications import notify_assistant
except: notify_assistant = lambda *a, **k: False

st.set_page_config(page_title="Assistant — TGR", page_icon="💬", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
render_sidebar(logo_html)
require_auth()

if "chat_history" not in st.session_state: st.session_state.chat_history = []

# Verifier ChromaDB
def check_ready():
    try:
        from core.rag.vector_store import get_stats, get_collection
        col = get_collection()
        idx_ok = col.count() > 0
        stats  = get_stats() if idx_ok else {}
    except: idx_ok, stats = False, {}
    try:
        import requests
        ollama = requests.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except: ollama = False
    return idx_ok, ollama, stats

idx_ok, ollama_ok, stats = check_ready()
n_q = len(st.session_state.chat_history)

idx_bdg  = "<span class='pill pg'>Base documentaire</span>" if idx_ok   else "<span class='pill pr'>Index vide</span>"
llm_bdg  = "<span class='pill pg'>IA active</span>"        if ollama_ok else "<span class='pill pr'>IA inactive</span>"
render_topbar("Assistant Reglementaire", "Assistant", idx_bdg + " " + llm_bdg)

# Stats ChromaDB
if idx_ok:
    nb_chunks = stats.get("total_chunks", 0)
    nb_sources = stats.get("nb_sources", 0)
    sources_list = stats.get("sources", [])
    types_list   = stats.get("types", [])
    langues_list = stats.get("langues", [])
else:
    nb_chunks = nb_sources = 0
    sources_list = types_list = langues_list = []

col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
with col_stats1:
    st.markdown("<div class='kpi' style='border-top:3px solid #0B2E4E;'><div class='kpi-head'><div class='kpi-lbl'>Chunks indexes</div><div class='kpi-ico' style='background:#EBF2FA;color:#0B2E4E;'>🧩</div></div><div class='kpi-val' style='color:#0B2E4E;'>" + str(nb_chunks) + "</div><div class='kpi-sub'>Base ChromaDB</div></div>", unsafe_allow_html=True)
with col_stats2:
    st.markdown("<div class='kpi' style='border-top:3px solid #E8601C;'><div class='kpi-head'><div class='kpi-lbl'>Documents sources</div><div class='kpi-ico' style='background:#FFF0EB;color:#E8601C;'>📄</div></div><div class='kpi-val' style='color:#E8601C;'>" + str(nb_sources) + "</div><div class='kpi-sub'>PDFs indexes</div></div>", unsafe_allow_html=True)
with col_stats3:
    langues_str = " + ".join(langues_list) if langues_list else "—"
    st.markdown("<div class='kpi' style='border-top:3px solid #2D6A10;'><div class='kpi-head'><div class='kpi-lbl'>Langues</div><div class='kpi-ico' style='background:#EDF5E4;color:#2D6A10;'>🌐</div></div><div class='kpi-val' style='font-size:14px;color:#2D6A10;'>" + langues_str + "</div><div class='kpi-sub'>Arabe + Francais</div></div>", unsafe_allow_html=True)
with col_stats4:
    st.markdown("<div class='kpi' style='border-top:3px solid #185FA5;'><div class='kpi-head'><div class='kpi-lbl'>Questions posees</div><div class='kpi-ico' style='background:#EBF2FA;color:#185FA5;'>💬</div></div><div class='kpi-val' style='color:#185FA5;'>" + str(n_q) + "</div><div class='kpi-sub'>Cette session</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Filtres + Questions en 2 colonnes
col_main, col_filters = st.columns([3, 1])

with col_filters:
    st.markdown(section_header("Filtres de recherche"), unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    filter_source = st.selectbox(
        "Document source",
        ["Tous"] + sources_list,
        help="Filtrer par document specifique"
    )
    filter_type = st.selectbox(
        "Type de document",
        ["Tous", "circulaire", "referentiel", "fiche_ouverture", "procuration", "document_general"],
        help="Filtrer par type"
    )
    filter_langue = st.selectbox(
        "Langue",
        ["Toutes", "fr", "ar", "ar_fr"],
        help="Filtrer par langue du document"
    )
    filter_date = st.date_input(
        "Documents depuis",
        value=None,
        help="Filtrer par date minimale"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Bouton reindexer (Admin seulement)
    user = current_user()
    if user.get("role") == "Admin":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='chdr'><div class='ctitle'>Administration</div></div>", unsafe_allow_html=True)
        uploaded_pdf = st.file_uploader("Ajouter un document", type=["pdf"])
        if uploaded_pdf and st.button("Indexer ce document"):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_pdf.getbuffer())
                tmp_path = tmp.name
            with st.spinner("Indexation en cours..."):
                try:
                    from core.rag.indexer import index_pdf
                    result = index_pdf(tmp_path)
                    log("Assistant", "Document indexe", uploaded_pdf.name, user["username"])
                    st.success(str(result["chunks"]) + " chunks indexes.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur : " + str(e))
                finally:
                    try: os.remove(tmp_path)
                    except: pass
        st.markdown("</div>", unsafe_allow_html=True)

with col_main:
    # Questions frequentes
    EXEMPLES = [
        ("📋", "Quels documents pour ouvrir un compte d-une association ?"),
        ("🪪",  "Quel est le format de la CIN dans OLYMPIC ?"),
        ("🤝", "Quelles pieces requises pour une cooperative ?"),
        ("🏛️", "Quels comptes ouvrir sans autorisation prealable ?"),
    ]
    st.markdown(section_header("Questions frequentes"), unsafe_allow_html=True)
    clicked = None
    cols = st.columns(4)
    for col, (icon, q) in zip(cols, EXEMPLES):
        with col:
            st.markdown(
                "<div class='card' style='padding:10px 12px;border-left:3px solid #E8601C;'>"
                "<div style='font-size:1.1rem;margin-bottom:4px;'>" + icon + "</div>"
                "<div style='font-size:10px;font-weight:500;color:#0B2E4E;line-height:1.4;'>" + q + "</div>"
                "</div>", unsafe_allow_html=True
            )
            if st.button(q, key="q_" + q[:20], use_container_width=True):
                clicked = q

    # Conversation
    st.markdown(section_header("Conversation"), unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown(
            "<div class='card' style='text-align:center;padding:2rem 1rem;color:#94A3B8;'>"
            "<div style='font-size:2rem;margin-bottom:8px;'>💬</div>"
            "<div style='font-size:11px;'>Posez votre premiere question ou choisissez un exemple.</div>"
            "</div>", unsafe_allow_html=True
        )
    else:
        chat_html = "<div class='card' style='padding:12px;'>"
        for entry in st.session_state.chat_history:
            filters_used = entry.get("filters_used","")
            chat_html += (
                "<div style='display:flex;justify-content:flex-end;margin:6px 0;'>"
                "<div style='background:#0B2E4E;color:white;border-radius:8px 8px 2px 8px;padding:8px 12px;max-width:70%;font-size:11px;line-height:1.5;'>"
                + entry["question"] + "</div></div>"
                "<div style='display:flex;gap:8px;margin:6px 0;'>"
                "<div style='width:28px;height:28px;background:#E8601C;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:600;flex-shrink:0;'>IA</div>"
                "<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px 8px 8px 2px;padding:8px 12px;max-width:78%;font-size:11px;line-height:1.6;color:#1E293B;'>"
                + entry["reponse"] + "</div></div>"
            )
            if filters_used:
                chat_html += "<div style='font-size:9px;color:#94A3B8;margin:2px 0 6px 36px;'>" + filters_used + "</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        for entry in st.session_state.chat_history:
            if entry.get("sources"):
                with st.expander(str(len(entry["sources"])) + " source(s) — " + entry["question"][:40] + "..."):
                    for s in entry["sources"]:
                        lang_badge = "<span class='badge badge-blue'>AR</span>" if s["langue"]=="ar" else "<span class='badge badge-green'>FR</span>" if s["langue"]=="fr" else "<span class='badge badge-orange'>AR+FR</span>"
                        st.markdown(
                            "<div style='border-left:3px solid #E8601C;padding:6px 10px;margin:3px 0;background:#FFF7ED;border-radius:0 6px 6px 0;'>"
                            "<div style='font-weight:600;color:#0B2E4E;font-size:10px;display:flex;align-items:center;gap:6px;'>"
                            + s["fichier"] + " — page " + str(s["page"]) + " · " + "{:.0%}".format(s["pertinence"]) + " " + lang_badge + "</div>"
                            "<div style='font-size:9.5px;color:#64748B;font-style:italic;margin-top:2px;'>" + s["extrait"] + "</div>"
                            "</div>", unsafe_allow_html=True
                        )

    # Input
    question_input = st.chat_input("Posez votre question sur la reglementation TGR...")
    question = clicked or question_input

    if question:
        if not idx_ok:
            st.error("La base documentaire est vide. Un Admin doit indexer des documents.")
        elif not ollama_ok:
            st.error("Le systeme IA n-est pas actif. Lancez Ollama.")
        else:
            # Construire les filtres
            f_source  = None if filter_source  == "Tous"   else filter_source
            f_type    = None if filter_type    == "Tous"   else filter_type
            f_langue  = None if filter_langue  == "Toutes" else filter_langue
            f_date    = str(filter_date) if filter_date else None

            filters_label = []
            if f_source:  filters_label.append("Source: " + f_source)
            if f_type:    filters_label.append("Type: " + f_type)
            if f_langue:  filters_label.append("Langue: " + f_langue)
            if f_date:    filters_label.append("Depuis: " + f_date)
            filters_str = " | ".join(filters_label) if filters_label else ""

            with st.spinner("Recherche dans la base documentaire..."):
                try:
                    from core.rag.chatbot import ask
                    result = ask(
                        question,
                        filter_source=f_source,
                        filter_type=f_type,
                        filter_langue=f_langue,
                        filter_date_from=f_date,
                    )
                    log("Assistant", "Question posee", question[:100], current_user().get("username",""))
                    try:
                        notify_assistant(question, current_user().get("username","Agent"))
                    except: pass
                    st.session_state.chat_history.append({
                        "question":     question,
                        "reponse":      result["reponse"],
                        "sources":      result["sources"],
                        "filters_used": filters_str,
                    })
                    st.rerun()
                except Exception as e:
                    st.error("Erreur : " + str(e))

    if st.session_state.chat_history:
        col_c, _ = st.columns([1, 5])
        with col_c:
            if st.button("Effacer la conversation"):
                st.session_state.chat_history = []
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)