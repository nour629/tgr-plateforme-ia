"""
dossiers_db.py — Base de donnees SQLite pour l'historique des dossiers clients
"""
import sqlite3, json, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dossiers.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS dossiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        type_client TEXT NOT NULL,
        agent TEXT, date_creation TEXT, date_maj TEXT,
        statut TEXT, score REAL,
        champs_json TEXT, documents_json TEXT, anomalies_json TEXT,
        nb_verifications INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS historique (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        agent TEXT, date_verif TEXT, statut TEXT, score REAL,
        anomalies_json TEXT, commentaire TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_client ON dossiers(client_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_type ON dossiers(type_client)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_statut ON dossiers(statut)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hist ON historique(client_id)")
    conn.commit()
    conn.close()

def save_dossier(dossier: dict, resultat: dict, agent: str = "Agent.TGR"):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_id   = dossier.get("client_id", "")
    type_client = dossier.get("type_client", "")
    champs      = json.dumps(dossier.get("champs", {}), ensure_ascii=False)
    documents   = json.dumps(dossier.get("documents_fournis", []), ensure_ascii=False)
    anomalies   = json.dumps(resultat.get("anomalies", []), ensure_ascii=False)
    statut      = resultat.get("statut", "")
    score       = resultat.get("score_conformite", 0)
    c.execute("SELECT id, nb_verifications FROM dossiers WHERE client_id=?", (client_id,))
    existing = c.fetchone()
    if existing:
        c.execute("""UPDATE dossiers SET statut=?, score=?, anomalies_json=?,
            date_maj=?, agent=?, nb_verifications=?, champs_json=?, documents_json=?
            WHERE client_id=?""",
            (statut, score, anomalies, now, agent, existing[1]+1, champs, documents, client_id))
    else:
        c.execute("""INSERT INTO dossiers
            (client_id, type_client, agent, date_creation, date_maj,
             statut, score, champs_json, documents_json, anomalies_json, nb_verifications)
            VALUES (?,?,?,?,?,?,?,?,?,?,1)""",
            (client_id, type_client, agent, now, now, statut, score, champs, documents, anomalies))
    c.execute("""INSERT INTO historique
        (client_id, agent, date_verif, statut, score, anomalies_json, commentaire)
        VALUES (?,?,?,?,?,?,?)""",
        (client_id, agent, now, statut, score, anomalies, ""))
    conn.commit()
    conn.close()

def save_lot(dossiers: list, resultats: list, agent: str = "Agent.TGR"):
    for d, r in zip(dossiers, resultats):
        save_dossier(d, r, agent)

def search_dossiers(client_id=None, type_client=None, statut=None,
                    date_from=None, score_min=None, limit=100) -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q, p = "SELECT * FROM dossiers WHERE 1=1", []
    if client_id:   q += " AND client_id LIKE ?";   p.append("%" + client_id + "%")
    if type_client: q += " AND type_client=?";       p.append(type_client)
    if statut:      q += " AND statut=?";            p.append(statut)
    if date_from:   q += " AND date_creation >= ?";  p.append(date_from)
    if score_min:   q += " AND score >= ?";          p.append(score_min)
    q += " ORDER BY date_maj DESC LIMIT ?"
    p.append(limit)
    c.execute(q, p)
    rows = c.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

def get_dossier(client_id: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM dossiers WHERE client_id=?", (client_id,))
    row = c.fetchone()
    conn.close()
    return row_to_dict(row) if row else {}

def get_historique(client_id: str) -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM historique WHERE client_id=? ORDER BY date_verif DESC", (client_id,))
    rows = c.fetchall()
    conn.close()
    return [hist_to_dict(r) for r in rows]

def get_stats() -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM dossiers"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM dossiers WHERE statut='conforme'"); conf = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM dossiers WHERE statut='partiellement_conforme'"); part = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM dossiers WHERE statut='non_conforme'"); nconf = c.fetchone()[0]
    c.execute("SELECT AVG(score) FROM dossiers"); avg = c.fetchone()[0] or 0
    c.execute("SELECT type_client, COUNT(*) FROM dossiers GROUP BY type_client"); par_type = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM historique"); total_verifs = c.fetchone()[0]
    conn.close()
    return {
        "total": total, "conformes": conf, "partiels": part,
        "non_conformes": nconf, "avg_score": round(avg, 3),
        "par_type": par_type, "total_verifs": total_verifs,
        "taux_conformite": round(conf/total, 3) if total > 0 else 0,
    }

def update_commentaire(client_id: str, commentaire: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE historique SET commentaire=?
        WHERE client_id=? AND id=(SELECT MAX(id) FROM historique WHERE client_id=?)""",
        (commentaire, client_id, client_id))
    conn.commit()
    conn.close()

def delete_dossier(client_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM dossiers WHERE client_id=?", (client_id,))
    c.execute("DELETE FROM historique WHERE client_id=?", (client_id,))
    conn.commit()
    conn.close()

def row_to_dict(row) -> dict:
    if not row: return {}
    return {"id":row[0],"client_id":row[1],"type_client":row[2],"agent":row[3],
            "date_creation":row[4],"date_maj":row[5],"statut":row[6],"score":row[7],
            "champs":json.loads(row[8] or "{}"), "documents":json.loads(row[9] or "[]"),
            "anomalies":json.loads(row[10] or "[]"), "nb_verifications":row[11]}

def hist_to_dict(row) -> dict:
    if not row: return {}
    return {"id":row[0],"client_id":row[1],"agent":row[2],"date_verif":row[3],
            "statut":row[4],"score":row[5],"anomalies":json.loads(row[6] or "[]"),
            "commentaire":row[7]}