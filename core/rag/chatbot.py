"""
chatbot.py — Pipeline RAG avec ChromaDB
Recherche semantique filtrable + generation Ollama/Claude
"""

import os
import json
import requests
from vector_store import search, get_stats, list_sources

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "..", "config.json")
OLLAMA_URL  = "http://localhost:11434/api/generate"
CLAUDE_URL   = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL  = "claude-sonnet-4-6"
GEMINI_MODEL  = "gemini-2.5-flash-latest"
EMBED_MODEL  = "nomic-embed-text"

SYSTEM_PROMPT = """Tu es un assistant reglementaire pour la Tresorerie Generale du Royaume du Maroc.
Reponds UNIQUEMENT a partir des extraits de documents fournis.
Ne melange jamais les categories de clients (association, societe, cooperative, personne physique).
Ignore les mentions 'Scanned by CamScanner'.
Si l'information n'est pas dans les extraits, dis-le clairement.
Reponds en francais, de facon concise et structuree."""

# ── CONFIG ────────────────────────────────────────────────────────────────────
def load_config() -> dict:
    defaults = {"mode": "ollama", "claude_api_key": "", "ollama_model": "mistral"}
    if not os.path.exists(CONFIG_PATH): return defaults
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f: return {**defaults, **json.load(f)}
    except: return defaults

# ── EMBEDDING DE LA QUESTION ──────────────────────────────────────────────────
def embed_query(text: str) -> list[float]:
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    response.raise_for_status()
    return response.json()["embedding"]

# ── CONSTRUCTION DU PROMPT ────────────────────────────────────────────────────
def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join([
        "[Extrait " + str(i+1) + " — " + c["source_file"] +
        ", page " + str(c["page_number"]) +
        ", type: " + c["type_document"] +
        ", langue: " + c["langue"] + "]\n" + c["text"]
        for i, c in enumerate(chunks)
    ])
    return (
        SYSTEM_PROMPT + "\n\n"
        "EXTRAITS DE DOCUMENTS :\n" + context + "\n\n"
        "QUESTION :\n" + question + "\n\n"
        "REPONSE (en francais, basee uniquement sur les extraits) :"
    )

# ── GENERATION OLLAMA ─────────────────────────────────────────────────────────
def generate_ollama(prompt: str, model: str = "mistral") -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": 0.3, "num_predict": 500}},
        timeout=300
    )
    response.raise_for_status()
    return response.json()["response"].strip()

# ── GENERATION CLAUDE ─────────────────────────────────────────────────────────
def generate_claude(prompt: str, api_key: str) -> str:
    if not api_key:
        raise ValueError("Cle API Claude manquante.")
    response = requests.post(
        CLAUDE_URL,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": CLAUDE_MODEL, "max_tokens": 1024,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"].strip()

# ── GENERATION GEMINI FLASH ──────────────────────────────────────────────────
def generate_gemini(prompt: str, api_key: str) -> str:
    if not api_key:
        raise ValueError("Gemini API key missing.")
    import requests as req
    # Use REST API directly with correct endpoint
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" + api_key
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = req.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        # Try gemini-2.5-flash as fallback
        url2 = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" + api_key
        resp = req.post(url2, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────
def ask(
    question: str,
    k: int = 4,
    filter_source: str = None,
    filter_type: str = None,
    filter_langue: str = None,
    filter_date_from: str = None,
) -> dict:
    """
    Pipeline RAG complet avec filtres optionnels.

    Parametres de filtre :
        filter_source    : nom du fichier source (ex: "referentiel_client.pdf")
        filter_type      : type de doc (circulaire, referentiel, fiche_ouverture...)
        filter_langue    : "fr" | "ar" | "ar_fr"
        filter_date_from : date minimale YYYY-MM-DD
    """
    config = load_config()
    mode   = config.get("mode", "ollama")

    # 1. Embedding de la question
    try:
        query_emb = embed_query(question)
    except Exception as e:
        return {
            "question": question, "reponse": "Erreur embedding : " + str(e),
            "sources": [], "trouve": False, "mode": mode
        }

    # 2. Recherche ChromaDB avec filtres
    chunks = search(
        query=question,
        query_embedding=query_emb,
        k=k,
        filter_source=filter_source,
        filter_type=filter_type,
        filter_langue=filter_langue,
        filter_date_from=filter_date_from,
    )

    # Seuil de pertinence
    chunks_pertinents = [c for c in chunks if c["pertinence"] >= 0.3]

    if not chunks_pertinents:
        return {
            "question": question,
            "reponse": "Je ne trouve pas d'information pertinente sur ce sujet dans les documents indexes.",
            "sources": [], "trouve": False, "mode": mode
        }

    # 3. Generation
    prompt = build_prompt(question, chunks_pertinents)

    try:
        if mode == "gemini":
            reponse = generate_gemini(prompt, config.get("gemini_api_key",""))
        else:
            reponse = generate_ollama(prompt, config.get("ollama_model","mistral"))
    except Exception as e:
        reponse = "Erreur de generation : " + str(e)

    # 4. Sources dedupliquees
    vues, sources = set(), []
    for c in chunks_pertinents:
        key = (c["source_file"], c["page_number"])
        if key not in vues:
            vues.add(key)
            sources.append({
                "fichier":       c["source_file"],
                "page":          c["page_number"],
                "type":          c["type_document"],
                "langue":        c["langue"],
                "date":          c["date_document"],
                "extrait":       c["text"][:200] + ("..." if len(c["text"]) > 200 else ""),
                "pertinence":    c["pertinence"],
            })

    return {
        "question":  question,
        "reponse":   reponse,
        "sources":   sources,
        "trouve":    True,
        "mode":      mode,
        "nb_chunks": len(chunks_pertinents),
    }

if __name__ == "__main__":
    stats = get_stats()
    print("ChromaDB stats:", stats)
    q = input("Question : ").strip()
    if q:
        r = ask(q)
        print("\nReponse:", r["reponse"])
        for s in r["sources"]:
            print(f"  Source: {s['fichier']} p.{s['page']} ({s['pertinence']:.0%}) [{s['langue']}]")