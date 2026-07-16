"""
indexer.py — Pipeline d'indexation vers ChromaDB
PDF → OCR → Chunks → Embeddings → ChromaDB
Supporte : arabe, francais, documents bilingues
"""

import os
import re
import json
import requests
from pathlib import Path
from pdf2image import convert_from_path
import easyocr
import tempfile
from vector_store import add_chunks, detect_language, detect_doc_type, reset_collection, get_stats

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(SCRIPT_DIR, "..", "..", "data", "regulations")
OLLAMA_URL   = "http://localhost:11434"
EMBED_MODEL  = "nomic-embed-text"
CHUNK_SIZE   = 800
CHUNK_OVERLAP = 150

# ── OCR ───────────────────────────────────────────────────────────────────────
def ocr_pdf(pdf_path: str) -> list[dict]:
    """Convertit PDF en texte par page via EasyOCR bilingue."""
    pages_text = []

    images = convert_from_path(pdf_path, dpi=200)
    reader_fr = easyocr.Reader(["fr", "en"], gpu=False)
    reader_ar = easyocr.Reader(["ar", "en"], gpu=False)

    for i, img in enumerate(images):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name

        # Double passe
        results_fr = reader_fr.readtext(tmp_path)
        results_ar = reader_ar.readtext(tmp_path)

        texts_fr = [r[1] for r in results_fr if r[2] > 0.3]
        texts_ar = [r[1] for r in results_ar if r[2] > 0.3]

        # Combiner et dedupliquer
        combined = list(dict.fromkeys(texts_fr + texts_ar))
        full_text = " ".join(combined)
        full_text = clean_text(full_text)

        os.remove(tmp_path)

        if len(full_text.strip()) > 20:
            pages_text.append({
                "page": i + 1,
                "text": full_text,
                "langue": detect_language(full_text)
            })
        print(f"[OCR] Page {i+1}/{len(images)} — {len(full_text)} chars — {detect_language(full_text)}")

    return pages_text

def clean_text(text: str) -> str:
    text = re.sub(r"Scanned by CamScanner", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF.,;:!?()\-/]", " ", text)
    return text.strip()

# ── CHUNKING ──────────────────────────────────────────────────────────────────
def chunk_text(text: str, page: int, source_file: str,
               chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Decoupe le texte en chunks avec overlap."""
    chunks = []
    start  = 0
    idx    = 0

    while start < len(text):
        end   = start + chunk_size
        chunk = text[start:end]

        # Couper sur un mot complet
        if end < len(text):
            last_space = chunk.rfind(" ")
            if last_space > chunk_size * 0.7:
                chunk = chunk[:last_space]
                end   = start + last_space

        if len(chunk.strip()) > 50:
            chunks.append({
                "text":          chunk.strip(),
                "source_file":   source_file,
                "page_number":   page,
                "langue":        detect_language(chunk),
                "type_document": detect_doc_type(chunk, source_file),
                "chunk_index":   idx,
            })
            idx += 1

        start = end - overlap

    return chunks

# ── EMBEDDINGS ────────────────────────────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    """Calcule l'embedding via Ollama nomic-embed-text."""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    response.raise_for_status()
    return response.json()["embedding"]

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Calcule les embeddings en batch."""
    embeddings = []
    for i, text in enumerate(texts):
        emb = get_embedding(text)
        embeddings.append(emb)
        if (i + 1) % 5 == 0:
            print(f"[Embed] {i+1}/{len(texts)} embeddings calcules")
    return embeddings

# ── PIPELINE COMPLET ──────────────────────────────────────────────────────────
def index_pdf(pdf_path: str, date_document: str = "", reset: bool = False):
    """
    Pipeline complet : PDF → OCR → Chunks → Embeddings → ChromaDB

    pdf_path      : chemin vers le PDF
    date_document : date du document (YYYY-MM-DD), auto-detecte sinon
    reset         : True = vider la collection avant indexation
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Fichier introuvable : {pdf_path}")

    source_file = Path(pdf_path).name
    print(f"\n[Indexer] Debut indexation : {source_file}")

    if reset:
        reset_collection()

    # 1. OCR
    print("[Indexer] Etape 1/4 — OCR...")
    pages = ocr_pdf(pdf_path)
    print(f"[Indexer] {len(pages)} pages extraites")

    # 2. Chunking
    print("[Indexer] Etape 2/4 — Chunking...")
    all_chunks = []
    for page_data in pages:
        chunks = chunk_text(
            page_data["text"],
            page_data["page"],
            source_file
        )
        # Ajouter la date
        for c in chunks:
            c["date_document"] = date_document or ""
        all_chunks.extend(chunks)
    print(f"[Indexer] {len(all_chunks)} chunks crees")

    # 3. Embeddings
    print("[Indexer] Etape 3/4 — Calcul des embeddings...")
    texts = [c["text"] for c in all_chunks]
    embeddings = get_embeddings_batch(texts)

    # 4. Stockage ChromaDB
    print("[Indexer] Etape 4/4 — Stockage ChromaDB...")
    add_chunks(all_chunks, embeddings)

    stats = get_stats()
    print(f"\n[Indexer] Termine ! Stats ChromaDB :")
    print(f"  Total chunks : {stats['total_chunks']}")
    print(f"  Sources      : {stats['sources']}")
    print(f"  Types        : {stats['types']}")
    print(f"  Langues      : {stats['langues']}")

    return {"chunks": len(all_chunks), "pages": len(pages), "source": source_file}

def index_all_pdfs(data_dir: str = DATA_DIR):
    """Indexe tous les PDFs dans le dossier regulations."""
    pdfs = list(Path(data_dir).glob("*.pdf"))
    if not pdfs:
        print(f"[Indexer] Aucun PDF trouve dans {data_dir}")
        return

    print(f"[Indexer] {len(pdfs)} PDF(s) a indexer")
    reset_collection()

    for pdf in pdfs:
        try:
            index_pdf(str(pdf))
        except Exception as e:
            print(f"[Indexer] Erreur sur {pdf.name} : {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        index_pdf(sys.argv[1])
    else:
        index_all_pdfs()