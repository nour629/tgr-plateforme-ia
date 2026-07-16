"""
notifications.py — Systeme de notifications email via Resend
Envoie des alertes automatiques pour :
- Dossier non conforme detecte
- Document uploade en OCR
- Question posee a l-assistant
"""

import os
import json
from datetime import datetime

# Config
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH  = os.path.join(SCRIPT_DIR, "..", "config.json")

def load_config() -> dict:
    defaults = {
        "resend_api_key": "",
        "email_from":     "TGR Platform <noreply@tgr.ma>",
        "email_to":       "",
        "notifications_enabled": False,
        "notify_anomalie": True,
        "notify_ocr":      True,
        "notify_assistant": False,
    }
    if not os.path.exists(CONFIG_PATH): return defaults
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return {**defaults, **json.load(f)}
    except: return defaults

# ── TEMPLATES EMAIL ───────────────────────────────────────────────────────────
def template_anomalie(client_id: str, type_client: str, score: float,
                      anomalies: list, agent: str) -> tuple[str, str]:
    """Retourne (subject, html) pour une notification d-anomalie."""
    subject = "[TGR] Anomalie detectee — " + client_id

    anomalies_html = "".join([
        "<li style='margin:4px 0;color:#92400E;'>" + a + "</li>"
        for a in anomalies
    ])

    score_color = "#2D6A10" if score >= 0.9 else ("#E8601C" if score >= 0.7 else "#B91C1C")
    statut_txt  = "Conforme" if score >= 0.9 else ("Partiel" if score >= 0.7 else "Non conforme")

    html = """
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#0B2E4E;padding:20px 24px;border-radius:8px 8px 0 0;">
        <div style="color:white;font-size:18px;font-weight:600;">
          Tresorerie Generale du Royaume
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:12px;margin-top:2px;">
          Plateforme IA — Notification automatique
        </div>
      </div>
      <div style="background:#FFF7ED;border-left:4px solid #E8601C;padding:16px 24px;">
        <div style="font-size:14px;font-weight:600;color:#92400E;">
          ⚠️ Anomalie detectee dans un dossier client
        </div>
      </div>
      <div style="background:white;padding:24px;border:1px solid #E2E8F0;">
        <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
          <tr>
            <td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;
                       font-size:12px;width:140px;">ID Client</td>
            <td style="padding:8px;font-size:13px;color:#0B2E4E;font-weight:600;">""" + client_id + """</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">
              Type</td>
            <td style="padding:8px;font-size:13px;color:#475569;">""" + type_client.replace("_"," ").title() + """</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">
              Score</td>
            <td style="padding:8px;font-size:13px;font-weight:600;color:""" + score_color + """;">
              """ + "{:.0%}".format(score) + " — " + statut_txt + """</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">
              Agent</td>
            <td style="padding:8px;font-size:13px;color:#475569;">""" + agent + """</td>
          </tr>
          <tr>
            <td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">
              Date</td>
            <td style="padding:8px;font-size:13px;color:#475569;">""" + datetime.now().strftime("%d/%m/%Y a %H:%M") + """</td>
          </tr>
        </table>
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;padding:14px;">
          <div style="font-weight:600;color:#B91C1C;font-size:13px;margin-bottom:8px;">
            Anomalies detectees :
          </div>
          <ul style="margin:0;padding-left:20px;">""" + anomalies_html + """</ul>
        </div>
        <div style="margin-top:16px;padding:12px;background:#EBF2FA;border-radius:6px;
                    font-size:12px;color:#1E40AF;">
          Action requise : Veuillez verifier et corriger ce dossier dans la plateforme TGR.
        </div>
      </div>
      <div style="background:#F8FAFC;padding:12px 24px;border-radius:0 0 8px 8px;
                  font-size:11px;color:#94A3B8;text-align:center;">
        Plateforme IA TGR — Message automatique — Ne pas repondre
      </div>
    </div>
    """
    return subject, html

def template_ocr(filename: str, doc_type: str, nb_blocs: int, agent: str) -> tuple[str, str]:
    subject = "[TGR] Nouveau document traite — " + filename
    html = """
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#0B2E4E;padding:20px 24px;border-radius:8px 8px 0 0;">
        <div style="color:white;font-size:18px;font-weight:600;">Tresorerie Generale du Royaume</div>
        <div style="color:rgba(255,255,255,0.6);font-size:12px;">Plateforme IA — Notification OCR</div>
      </div>
      <div style="background:#EBF2FA;border-left:4px solid #0B2E4E;padding:16px 24px;">
        <div style="font-size:14px;font-weight:600;color:#1E40AF;">📄 Document traite par OCR</div>
      </div>
      <div style="background:white;padding:24px;border:1px solid #E2E8F0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;width:140px;">Fichier</td>
              <td style="padding:8px;font-size:13px;color:#0B2E4E;font-weight:600;">""" + filename + """</td></tr>
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">Type detecte</td>
              <td style="padding:8px;font-size:13px;color:#475569;">""" + doc_type.replace("_"," ").title() + """</td></tr>
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">Blocs OCR</td>
              <td style="padding:8px;font-size:13px;color:#475569;">""" + str(nb_blocs) + """ blocs detectes</td></tr>
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">Agent</td>
              <td style="padding:8px;font-size:13px;color:#475569;">""" + agent + """</td></tr>
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">Date</td>
              <td style="padding:8px;font-size:13px;color:#475569;">""" + datetime.now().strftime("%d/%m/%Y a %H:%M") + """</td></tr>
        </table>
      </div>
      <div style="background:#F8FAFC;padding:12px 24px;border-radius:0 0 8px 8px;
                  font-size:11px;color:#94A3B8;text-align:center;">
        Plateforme IA TGR — Message automatique
      </div>
    </div>
    """
    return subject, html

def template_assistant(question: str, agent: str) -> tuple[str, str]:
    subject = "[TGR] Nouvelle question reglementaire"
    html = """
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#0B2E4E;padding:20px 24px;border-radius:8px 8px 0 0;">
        <div style="color:white;font-size:18px;font-weight:600;">Tresorerie Generale du Royaume</div>
        <div style="color:rgba(255,255,255,0.6);font-size:12px;">Plateforme IA — Assistant Reglementaire</div>
      </div>
      <div style="background:#EDF5E4;border-left:4px solid #2D6A10;padding:16px 24px;">
        <div style="font-size:14px;font-weight:600;color:#2D6A10;">💬 Nouvelle question posee</div>
      </div>
      <div style="background:white;padding:24px;border:1px solid #E2E8F0;">
        <div style="background:#F8FAFC;border-radius:6px;padding:14px;font-size:13px;
                    color:#0B2E4E;font-style:italic;margin-bottom:16px;">
          "\" + question + "\""
        </div>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;width:100px;">Agent</td>
              <td style="padding:8px;font-size:13px;color:#475569;">""" + agent + """</td></tr>
          <tr><td style="padding:8px;background:#F8FAFC;font-weight:600;color:#64748B;font-size:12px;">Date</td>
              <td style="padding:8px;font-size:13px;color:#475569;">""" + datetime.now().strftime("%d/%m/%Y a %H:%M") + """</td></tr>
        </table>
      </div>
      <div style="background:#F8FAFC;padding:12px 24px;border-radius:0 0 8px 8px;
                  font-size:11px;color:#94A3B8;text-align:center;">
        Plateforme IA TGR — Message automatique
      </div>
    </div>
    """.replace('"\\' + '" + question + "\\"', '"' + question + '"')
    return subject, html

# ── ENVOI EMAIL ───────────────────────────────────────────────────────────────
def send_email(subject: str, html: str) -> bool:
    """Envoie un email via Resend API."""
    config = load_config()

    if not config.get("notifications_enabled", False):
        return False
    if not config.get("resend_api_key", ""):
        return False
    if not config.get("email_to", ""):
        return False

    try:
        import resend
        resend.api_key = config["resend_api_key"]
        resend.Emails.send({
            "from":    config.get("email_from", "TGR Platform <noreply@resend.dev>"),
            "to":      [config["email_to"]],
            "subject": subject,
            "html":    html,
        })
        return True
    except Exception as e:
        print("[Notifications] Erreur envoi email : " + str(e))
        return False

# ── FONCTIONS PUBLIQUES ───────────────────────────────────────────────────────
def notify_anomalie(client_id: str, type_client: str, score: float,
                    anomalies: list, agent: str) -> bool:
    config = load_config()
    if not config.get("notify_anomalie", True): return False
    subject, html = template_anomalie(client_id, type_client, score, anomalies, agent)
    return send_email(subject, html)

def notify_ocr(filename: str, doc_type: str, nb_blocs: int, agent: str) -> bool:
    config = load_config()
    if not config.get("notify_ocr", True): return False
    subject, html = template_ocr(filename, doc_type, nb_blocs, agent)
    return send_email(subject, html)

def notify_assistant(question: str, agent: str) -> bool:
    config = load_config()
    if not config.get("notify_assistant", False): return False
    subject, html = template_assistant(question, agent)
    return send_email(subject, html)