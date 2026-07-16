"""
audit.py — Module central de journalisation des actions
Utilisé par toutes les pages pour logger les actions réelles des utilisateurs.
"""

import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_LOG = os.path.join(ROOT, "..", "audit_log.json")


def load_logs() -> list:
    if not os.path.exists(AUDIT_LOG):
        return []
    try:
        with open(AUDIT_LOG, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_logs(logs: list):
    with open(AUDIT_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def log(module: str, action: str, detail: str = "", user: str = "Agent.TGR"):
    """
    Enregistre une action dans la piste d'audit.
    
    Paramètres :
    - module  : "OCR" | "Anomalie" | "Assistant" | "Systeme"
    - action  : description courte de l'action
    - detail  : information complémentaire (nom fichier, question, etc.)
    - user    : identifiant de l'utilisateur (à connecter à l'auth plus tard)
    """
    logs = load_logs()
    logs.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "module": module,
        "action": action,
        "detail": detail
    })
    # Garder seulement les 500 dernières entrées
    save_logs(logs[:500])