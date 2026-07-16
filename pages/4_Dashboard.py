import streamlit as st
import pandas as pd
import json, os, sys, random
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "ml"))
from styles import GLOBAL_CSS, get_logo_html, render_sidebar, render_topbar, section_header, kpi_card
from auth import require_auth, current_user

st.set_page_config(page_title="Dashboard — TGR", page_icon="📊", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Plotly theme TGR
NAVY   = "#0B2E4E"
ORANGE = "#E8601C"
GREEN  = "#2D6A10"
RED    = "#B91C1C"
BLUE   = "#185FA5"
AMBER  = "#92400E"
COLORS = [NAVY, ORANGE, GREEN, BLUE, RED, AMBER, "#64748B"]

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "TGR_LOGO.jpg")
logo_html = get_logo_html(LOGO_PATH)
render_sidebar(logo_html)
require_auth()

ROOT      = os.path.join(os.path.dirname(__file__), "..")
AUDIT_LOG = os.path.join(ROOT, "..", "audit_log.json")
DB_PATH   = os.path.join(ROOT, "..", "dossiers.db")

def load_logs():
    if not os.path.exists(AUDIT_LOG): return []
    try:
        with open(AUDIT_LOG, encoding="utf-8") as f: return json.load(f)
    except: return []

def save_logs(logs):
    with open(AUDIT_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def demo_logs():
    users   = ["Agent.Benali","Agent.Karimi","Auditeur.Zhar","Admin.TGR"]
    actions = {
        "OCR":      ["Upload document","Extraction lancee","Correction champ"],
        "Anomalie": ["Dossier client verifie","Anomalie flaggee"],
        "Assistant":["Question posee","Source consultee"],
        "Systeme":  ["Connexion","Deconnexion","Config mise a jour"],
    }
    logs, base = [], datetime.now() - timedelta(days=7)
    for i in range(50):
        mod = random.choice(list(actions.keys()))
        logs.append({
            "timestamp": (base + timedelta(hours=i*3)).strftime("%Y-%m-%d %H:%M:%S"),
            "user": random.choice(users),
            "module": mod,
            "action": random.choice(actions[mod]),
            "detail": ""
        })
    return sorted(logs, key=lambda x: x["timestamp"], reverse=True)

def load_dossiers_stats():
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "ml"))
        from core.ml.dossiers_db import get_stats
        return get_stats()
    except: return {}

logs = load_logs()
if not logs:
    logs = demo_logs()
    save_logs(logs)

df = pd.DataFrame(logs)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"]  = df["timestamp"].dt.date
df["heure"] = df["timestamp"].dt.hour
df["jour"]  = df["timestamp"].dt.day_name()

today = datetime.now().strftime("%Y-%m-%d")
docs  = sum(1 for l in logs if l.get("module")=="OCR" and "Upload" in l.get("action",""))
anom  = sum(1 for l in logs if l.get("module")=="Anomalie" and "flagg" in l.get("action",""))
ques  = sum(1 for l in logs if l.get("module")=="Assistant" and "Question" in l.get("action",""))
doss_stats = load_dossiers_stats()

render_topbar("Tableau de Bord et Audit", "Dashboard",
              "<span class='pill pn'>Module 4</span>")

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(kpi_card("#0B2E4E","#EBF2FA","📄","Documents traites",str(docs),"Module OCR"), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("#E8601C","#FFF0EB","⚠️","Anomalies detectees",str(anom),"Dossiers clients"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("#185FA5","#EBF2FA","💬","Questions posees",str(ques),"Assistant RAG"), unsafe_allow_html=True)
with c4:
    taux = doss_stats.get("taux_conformite", 0)
    st.markdown(kpi_card("#2D6A10","#EDF5E4","📈","Taux conformite","{:.0%}".format(taux) if taux else "—","Base SQLite"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── ROW 1 : Activite par module + Evolution ───────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown(section_header("Activite par module"), unsafe_allow_html=True)
    module_counts = df["module"].value_counts().reset_index()
    module_counts.columns = ["Module","Actions"]
    fig1 = go.Figure(go.Bar(
        x=module_counts["Module"],
        y=module_counts["Actions"],
        marker_color=[NAVY, ORANGE, GREEN, BLUE][:len(module_counts)],
        text=module_counts["Actions"],
        textposition="outside",
        textfont=dict(size=11, color=NAVY),
    ))
    fig1.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#475569")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with col2:
    st.markdown(section_header("Evolution journaliere"), unsafe_allow_html=True)
    daily = df.groupby("date").size().reset_index(name="Actions")
    fig2 = go.Figure(go.Scatter(
        x=daily["date"],
        y=daily["Actions"],
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.5),
        marker=dict(color=ORANGE, size=7, line=dict(color="white", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(232,96,28,0.08)",
    ))
    fig2.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#475569")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── ROW 2 : Repartition horaire + Conformite ─────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown(section_header("Activite par heure de la journee"), unsafe_allow_html=True)
    hourly = df.groupby("heure").size().reset_index(name="Actions")
    all_hours = pd.DataFrame({"heure": range(24)})
    hourly = all_hours.merge(hourly, on="heure", how="left").fillna(0)
    fig3 = go.Figure(go.Bar(
        x=hourly["heure"],
        y=hourly["Actions"],
        marker_color=[NAVY if h >= 8 and h <= 17 else "#CBD5E1" for h in hourly["heure"]],
    ))
    fig3.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        xaxis=dict(showgrid=False, tickvals=list(range(0,24,2)),
                   ticktext=[str(h)+"h" for h in range(0,24,2)],
                   tickfont=dict(size=10, color="#475569")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with col4:
    st.markdown(section_header("Repartition par utilisateur"), unsafe_allow_html=True)
    user_counts = df["user"].value_counts().reset_index()
    user_counts.columns = ["Utilisateur","Actions"]
    fig4 = go.Figure(go.Pie(
        labels=user_counts["Utilisateur"],
        values=user_counts["Actions"],
        hole=0.45,
        marker=dict(colors=COLORS[:len(user_counts)]),
        textfont=dict(size=10),
        textposition="outside",
    ))
    fig4.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        showlegend=True,
        legend=dict(font=dict(size=10), x=1, y=0.5),
    )
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

# ── ROW 3 : Conformite dossiers (si SQLite) ───────────────────────────────────
if doss_stats.get("total", 0) > 0:
    st.markdown(section_header("Analyse de Conformite — Base SQLite"), unsafe_allow_html=True)
    col5, col6 = st.columns(2)

    with col5:
        # Donut conformite
        labels = ["Conformes","A corriger","Non conformes"]
        values = [doss_stats.get("conformes",0), doss_stats.get("partiels",0), doss_stats.get("non_conformes",0)]
        fig5 = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.5,
            marker=dict(colors=[GREEN, ORANGE, RED]),
            textfont=dict(size=11),
        ))
        fig5.add_annotation(
            text="<b>" + "{:.0%}".format(doss_stats.get("taux_conformite",0)) + "</b><br><span style='font-size:10px;'>Conformes</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color=NAVY)
        )
        fig5.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=10, b=10, l=10, r=10),
            height=220, showlegend=True,
            legend=dict(font=dict(size=10)),
        )
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    with col6:
        # Bar par type de client
        par_type = doss_stats.get("par_type", {})
        if par_type:
            df_type = pd.DataFrame(list(par_type.items()), columns=["Type","Nombre"])
            df_type["Type"] = df_type["Type"].str.replace("_"," ").str.title()
            fig6 = go.Figure(go.Bar(
                x=df_type["Nombre"], y=df_type["Type"],
                orientation="h",
                marker_color=NAVY,
                text=df_type["Nombre"],
                textposition="outside",
            ))
            fig6.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(t=10, b=10, l=10, r=10),
                height=220,
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                yaxis=dict(showgrid=False, tickfont=dict(size=10)),
                showlegend=False,
            )
            st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

# ── PISTE D-AUDIT ─────────────────────────────────────────────────────────────
st.markdown(section_header("Piste d-Audit"), unsafe_allow_html=True)

f1,f2,f3 = st.columns([1,1,2])
with f1: mod_f = st.selectbox("Module",["Tous","OCR","Anomalie","Assistant","Systeme"])
with f2: usr_f = st.selectbox("Utilisateur",["Tous"]+sorted(df["user"].unique().tolist()))
with f3:
    st.markdown("<br>", unsafe_allow_html=True)
    search = st.text_input("", placeholder="Rechercher une action...")

filtered = logs.copy()
if mod_f != "Tous": filtered = [l for l in filtered if l["module"]==mod_f]
if usr_f != "Tous": filtered = [l for l in filtered if l["user"]==usr_f]
if search: filtered = [l for l in filtered if search.lower() in l["action"].lower()]

mod_badge = {"OCR":"badge-blue","Anomalie":"badge-orange","Assistant":"badge-green","Systeme":"badge-gray"}

st.markdown(
    "<div class='thdr'>"
    "<span style='min-width:70px;'>Heure</span>"
    "<span style='min-width:140px;'>Utilisateur</span>"
    "<span style='flex:1;'>Action</span>"
    "<span style='min-width:110px;text-align:right;'>Module</span>"
    "</div>",
    unsafe_allow_html=True
)

rows_html = ""
for e in filtered[:50]:
    t = e["timestamp"][11:16]
    bclass = mod_badge.get(e["module"],"badge-gray")
    rows_html += (
        "<div class='trow'>"
        "<span style='min-width:70px;color:#94A3B8;font-size:10px;'>" + t + "</span>"
        "<span style='min-width:140px;font-weight:500;color:#0B2E4E;font-size:10.5px;'>" + e["user"] + "</span>"
        "<span style='flex:1;color:#475569;font-size:10.5px;'>" + e["action"] + "</span>"
        "<span style='min-width:110px;text-align:right;'><span class='badge " + bclass + "'>" + e["module"] + "</span></span>"
        "</div>"
    )
st.markdown("<div class='card' style='padding:0;'>" + rows_html + "</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
csv = pd.DataFrame(filtered).to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇  Exporter CSV", csv, "audit_" + datetime.now().strftime("%Y%m%d") + ".csv", "text/csv")

st.markdown("</div>", unsafe_allow_html=True)