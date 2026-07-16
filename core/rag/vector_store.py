"""
vector_store.py — Base vectorielle ChromaDB
Remplace FAISS + chunks.json + metadata.json
Supporte filtrage par : source, date, type, langue, page
Supporte recherche bilingue arabe/francais
"""

import os
import json
import chromadb
from chromadb.config import Settings
from datetime import datetime

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "tgr_documents"

# ── CLIENT CHROMADB ───────────────────────────────────────────────────────────
def get_client():
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )

def get_collection():
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

# ── DETECTION LANGUE ──────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    ratio = arabic_chars / max(len(text), 1)
    if ratio > 0.3:   return "ar"
    if ratio > 0.05:  return "ar_fr"
    return "fr"

# ── DETECTION TYPE DOCUMENT ───────────────────────────────────────────────────
def detect_doc_type(text: str, filename: str = "") -> str:
    text_lower = (text + filename).lower()
    if any(k in text_lower for k in ["procuration", "fp46", "mandataire"]):
        return "procuration"
    if any(k in text_lower for k in ["ouverture", "fp1", "compte n", "fiche"]):
        return "fiche_ouverture"
    if any(k in text_lower for k in ["circulaire", "note de service", "instruction"]):
        return "circulaire"
    if any(k in text_lower for k in ["referentiel", "olympic", "client"]):
        return "referentiel"
    if any(k in text_lower for k in ["facture", "fournisseur"]):
        return "facture"
    return "document_general"

# ── AJOUT DE CHUNKS ───────────────────────────────────────────────────────────
def add_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """
    Ajoute des chunks dans ChromaDB avec leurs metadonnees.

    chunks: liste de dicts avec keys:
        - text, source_file, page_number
        - date_document (optionnel), type_document (optionnel)
    embeddings: vecteurs correspondants
    """
    collection = get_collection()

    ids, docs, metas, embeds = [], [], [], []

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        text      = chunk.get("text", "")
        source    = chunk.get("source_file", "inconnu")
        page      = chunk.get("page_number", 0)
        date_doc  = chunk.get("date_document", "")
        type_doc  = chunk.get("type_document", "") or detect_doc_type(text, source)
        langue    = chunk.get("langue", "") or detect_language(text)

        chunk_id = source.replace(".pdf","").replace(" ","_") + "_p" + str(page) + "_c" + str(i)

        ids.append(chunk_id)
        docs.append(text)
        embeds.append(emb)
        metas.append({
            "source_file":    source,
            "page_number":    int(page),
            "type_document":  type_doc,
            "langue":         langue,
            "date_document":  date_doc or datetime.now().strftime("%Y-%m-%d"),
            "char_count":     len(text),
            "indexed_at":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    if ids:
        collection.upsert(ids=ids, documents=docs, embeddings=embeds, metadatas=metas)
        print(f"[ChromaDB] {len(ids)} chunks indexés dans '{COLLECTION_NAME}'")

# ── RECHERCHE AVEC FILTRES ────────────────────────────────────────────────────
def search(
    query: str,
    query_embedding: list[float],
    k: int = 4,
    filter_source: str = None,
    filter_type: str = None,
    filter_langue: str = None,
    filter_date_from: str = None,
) -> list[dict]:
    """
    Recherche semantique avec filtres optionnels.

    Retourne une liste de dicts avec :
        text, source_file, page_number, type_document, langue,
        date_document, distance, pertinence
    """
    collection = get_collection()

    # Construction du filtre ChromaDB
    where = {}
    conditions = []

    if filter_source:
        conditions.append({"source_file": {"$eq": filter_source}})
    if filter_type:
        conditions.append({"type_document": {"$eq": filter_type}})
    if filter_langue:
        conditions.append({"langue": {"$in": [filter_langue, "ar_fr"]}})
    if filter_date_from:
        conditions.append({"date_document": {"$gte": filter_date_from}})

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    # Requete ChromaDB
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(k, collection.count()) if collection.count() > 0 else k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where:
        kwargs["where"] = where

    try:
        results = collection.query(**kwargs)
    except Exception as e:
        print(f"[ChromaDB] Erreur recherche : {e}")
        return []

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        pertinence = round(max(0, 1 - dist), 3)
        output.append({
            "text":          doc,
            "source_file":   meta.get("source_file",""),
            "page_number":   meta.get("page_number", 0),
            "type_document": meta.get("type_document",""),
            "langue":        meta.get("langue",""),
            "date_document": meta.get("date_document",""),
            "distance":      round(dist, 4),
            "pertinence":    pertinence,
        })

    # Trier par pertinence decroissante
    return sorted(output, key=lambda x: -x["pertinence"])

# ── STATS DE LA COLLECTION ────────────────────────────────────────────────────
def get_stats() -> dict:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return {"total_chunks": 0, "sources": [], "types": [], "langues": []}

    # Recuperer tous les metadatas
    all_meta = collection.get(include=["metadatas"])["metadatas"]

    sources = list(set(m.get("source_file","") for m in all_meta))
    types   = list(set(m.get("type_document","") for m in all_meta))
    langues = list(set(m.get("langue","") for m in all_meta))

    return {
        "total_chunks": count,
        "sources":      sources,
        "types":        types,
        "langues":      langues,
        "nb_sources":   len(sources),
    }

# ── SUPPRIMER UN DOCUMENT ─────────────────────────────────────────────────────
def delete_source(source_file: str):
    collection = get_collection()
    collection.delete(where={"source_file": {"$eq": source_file}})
    print(f"[ChromaDB] Source supprimée : {source_file}")

# ── LISTER LES SOURCES ────────────────────────────────────────────────────────
def list_sources() -> list[str]:
    stats = get_stats()
    return stats.get("sources", [])

# ── RESET COLLECTION ─────────────────────────────────────────────────────────
def reset_collection():
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[ChromaDB] Collection '{COLLECTION_NAME}' supprimee.")
    except: pass
    get_collection()
    print(f"[ChromaDB] Collection '{COLLECTION_NAME}' recreee.")