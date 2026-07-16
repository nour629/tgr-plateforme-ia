"""
pipeline_ocr.py
Pipeline OCR adapté aux documents TGR :
- Fiche d'ouverture de compte (Mod. FP1/PP)
- Procuration (FP46)
- Documents financiers généraux (factures, mandats, bons de commande)

Mode 1 (prioritaire) : Gemini Vision API — lecture directe du manuscrit
Mode 2 (fallback)    : EasyOCR + extraction spatiale + correction manuelle
"""

import easyocr
import cv2
import numpy as np
import re
import json
import base64
import requests
from datetime import datetime
from pathlib import Path
from pdf2image import convert_from_path
import os
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "..", "config.json")
SEUIL_VALIDATION = 0.85



# ─── CONFIG ──────────────────────────────────────────────────────────────────
def load_config() -> dict:
    defaults = {"mode": "ollama", "gemini_api_key": ""}
    if not os.path.exists(CONFIG_PATH): return defaults
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f: return {**defaults, **json.load(f)}
    except: return defaults


# ─── 1. PRÉTRAITEMENT IMAGE ───────────────────────────────────────────────────
def preprocess(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    return binary


# ─── 2. DÉTECTION TYPE DE DOCUMENT ───────────────────────────────────────────
def detect_document_type(text: str) -> str:
    """Détecte le type de document à partir du texte OCR brut."""
    text_lower = text.lower()
    if "procuration" in text_lower:
        return "procuration"
    if "compte n°" in text_lower or "fp1" in text_lower or "fp 1" in text_lower or "ouverture" in text_lower:
        return "fiche_ouverture_compte"
    if any(k in text_lower for k in ["facture", "invoice", "fournisseur"]):
        return "facture"
    if any(k in text_lower for k in ["bon de commande", "b.c", "bc-"]):
        return "bon_commande"
    if any(k in text_lower for k in ["mandat", "ordonnateur"]):
        return "mandat_paiement"
    return "document_general"


# ─── 3. EXTRACTION PAR TYPE ───────────────────────────────────────────────────
def extract_fiche_ouverture(text: str, ocr_results: list) -> dict:
    """
    Extrait les champs d'une fiche d'ouverture de compte TGR (FP1/PP).
    Utilise les coordonnées spatiales (bbox) pour trouver les valeurs
    à droite ou en dessous de chaque label — adapté aux formulaires manuscrits.
    """

    def bbox_center(bbox):
        """Retourne le centre (x, y) d'une bbox EasyOCR."""
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return (sum(xs)/len(xs), sum(ys)/len(ys))

    def find_value_near_label(label_pattern: str, direction: str = "right", tolerance_y: int = 30) -> tuple[str, float]:
        """
        Trouve la valeur la plus proche d'un label dans le texte OCR.
        direction='right' : cherche à droite du label (même ligne)
        direction='below' : cherche en dessous du label
        """
        label_bbox = None
        label_conf = 0.5

        # Trouver le label
        for r in ocr_results:
            if re.search(label_pattern, r["text"], re.IGNORECASE):
                label_bbox = r["bbox"]
                label_conf = r["confidence"]
                break

        if not label_bbox:
            return None, 0.0

        lx, ly = bbox_center(label_bbox)
        l_right = max(p[0] for p in label_bbox)  # bord droit du label
        l_bottom = max(p[1] for p in label_bbox)  # bord bas du label

        candidates = []
        for r in ocr_results:
            # Ignorer les labels connus
            if re.search(label_pattern, r["text"], re.IGNORECASE):
                continue
            if re.search(r'\b(nom|pr[eé]nom|cin|naissance|nationalit|domicile|ville|t[eé]l|profession|matricule|administration|ouverture|versement|chronologique|analytique|enseigne)\b', r["text"], re.IGNORECASE):
                continue

            cx, cy = bbox_center(r["bbox"])

            if direction == "right":
                # À droite du label, même ligne (tolérance verticale)
                if cx > l_right and abs(cy - ly) < tolerance_y:
                    dist = cx - l_right
                    candidates.append((dist, r["text"], r["confidence"]))
            elif direction == "below":
                # En dessous du label
                if cy > l_bottom and abs(cx - lx) < 150:
                    dist = cy - l_bottom
                    candidates.append((dist, r["text"], r["confidence"]))

        if not candidates:
            return None, label_conf * 0.5

        # Prendre le plus proche
        candidates.sort(key=lambda x: x[0])
        best_text = candidates[0][1].strip()
        best_conf = candidates[0][2]

        return best_text, round(best_conf, 2)

    champs = {}

    # Numéro de compte
    val, conf = find_value_near_label(r'compte\s*n[°o]?', direction="right", tolerance_y=40)
    if not val:
        m = re.search(r'(?:compte\s*n[°o]?\s*[:\.]?\s*)([0-9]{5,12})', text, re.IGNORECASE)
        val = m.group(1) if m else None
        conf = 0.7
    champs["numero_compte"] = {"valeur": val, "confiance": conf}

    # Nom
    val, conf = find_value_near_label(r'^\s*nom\s*[:\.]?\s*$|nom\s*:', direction="right", tolerance_y=25)
    champs["nom"] = {"valeur": val.upper() if val else None, "confiance": conf}

    # Prénom
    val, conf = find_value_near_label(r'pr[eé]nom\s*[:\.]?', direction="right", tolerance_y=25)
    champs["prenom"] = {"valeur": val.title() if val else None, "confiance": conf}

    # CIN
    val, conf = find_value_near_label(r'c\.?i\.?n\.?\s*(?:le|n°|:)?', direction="right", tolerance_y=30)
    if val:
        # Nettoyer : garder seulement les chars alphanumériques
        val = re.sub(r'[^A-Za-z0-9]', '', val).upper()
    champs["cin"] = {"valeur": val if val else None, "confiance": conf}

    # Date de naissance
    val, conf = find_value_near_label(r'naissance', direction="right", tolerance_y=25)
    if not val:
        m = re.search(r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', text)
        val = m.group(1) if m else None
        conf = 0.7
    champs["date_naissance"] = {"valeur": val, "confiance": conf}

    # Nationalité
    val, conf = find_value_near_label(r'nationalit[eé]', direction="right", tolerance_y=25)
    champs["nationalite"] = {"valeur": val.title() if val else None, "confiance": conf}

    # Domicile
    val, conf = find_value_near_label(r'domicile', direction="right", tolerance_y=30)
    champs["domicile"] = {"valeur": val, "confiance": conf}

    # Ville
    val, conf = find_value_near_label(r'\bville\b', direction="right", tolerance_y=25)
    champs["ville"] = {"valeur": val.title() if val else None, "confiance": conf}

    # Téléphone
    val, conf = find_value_near_label(r't[eé]l[eé]?(?:phone)?', direction="right", tolerance_y=25)
    if val:
        val = re.sub(r'[^0-9]', '', val)
    champs["telephone"] = {"valeur": val if val and len(val) >= 8 else None, "confiance": conf}

    # Profession
    val, conf = find_value_near_label(r'profession', direction="right", tolerance_y=25)
    champs["profession"] = {"valeur": val.title() if val else None, "confiance": conf}

    # Date d'ouverture
    val, conf = find_value_near_label(r'ouverture', direction="right", tolerance_y=30)
    if not val or not re.search(r'\d', str(val)):
        # Chercher toutes les dates et prendre celle après "ouverture"
        dates = re.findall(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', text)
        val = dates[-1] if dates else None
        conf = 0.65
    champs["date_ouverture"] = {"valeur": val, "confiance": conf}

    return champs


def extract_procuration(text: str, ocr_results: list) -> dict:
    """Extrait les champs d'une procuration TGR (FP46)."""

    def find_conf(pattern):
        for r in ocr_results:
            if re.search(pattern, r["text"], re.IGNORECASE):
                return r["confidence"]
        return 0.5

    champs = {}

    m = re.search(r'mr\/mme\s*[:\.]?\s*(.{5,40}?)(?:\n|demeurant)', text, re.IGNORECASE)
    champs["mandant"] = {"valeur": m.group(1).strip() if m else None, "confiance": round(find_conf(r'mr|mme'), 2)}

    m = re.search(r'compte\s*(?:de\s*d[eé]p[oô]t)?\s*n[°o]?\s*([0-9]{4,12})', text, re.IGNORECASE)
    champs["numero_compte"] = {"valeur": m.group(1).strip() if m else None, "confiance": round(find_conf(r'compte'), 2)}

    m = re.search(r'(?:monsieur|madame|m\.?)\s+([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s\-]{2,30})\s+dont', text, re.IGNORECASE)
    champs["mandataire"] = {"valeur": m.group(1).strip() if m else None, "confiance": round(find_conf(r'mandataire'), 2)}

    m = re.search(r'(?:kenitra|rabat|casablanca|fes|marrakech|agadir)\s*,?\s*le\s+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', text, re.IGNORECASE)
    champs["date_procuration"] = {"valeur": m.group(1).strip() if m else None, "confiance": round(find_conf(r'le\s+\d'), 2)}

    m = re.search(r'agence\s+(?:bancaire\s+)?([A-ZÀ-ÿa-z\s]{3,20})', text, re.IGNORECASE)
    champs["agence"] = {"valeur": m.group(1).strip().title() if m else None, "confiance": round(find_conf(r'agence'), 2)}

    return champs


def extract_document_financier(text: str, ocr_results: list) -> dict:
    """Extrait les champs d'un document financier (facture, bon commande, mandat)."""

    def find_conf(pattern):
        for r in ocr_results:
            if re.search(pattern, r["text"], re.IGNORECASE):
                return r["confidence"]
        return 0.5

    champs = {}

    m = re.search(r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b', text)
    champs["date"] = {"valeur": m.group(0) if m else None, "confiance": round(find_conf(r'\d{1,2}[\/\-]'), 2)}

    m = re.search(r'\b(\d{1,3}(?:[\s\.]\d{3})*(?:[,\.]\d{2})?)\s*(?:MAD|DH|درهم)?\b', text)
    champs["montant"] = {"valeur": m.group(0).strip() if m else None, "confiance": round(find_conf(r'\d+[\s,\.]\d+'), 2)}

    m = re.search(r'(?:fournisseur|société|sarl|sa\b)[:\s]+([A-ZÀ-ÿa-z\s\-\.&]{3,40})', text, re.IGNORECASE)
    champs["fournisseur"] = {"valeur": m.group(1).strip().title() if m else None, "confiance": round(find_conf(r'fournisseur|société'), 2)}

    m = re.search(r'\b(?:N°?|Ref|BC|MR|FAC)[\s\-]*(\d{2,}[\-\/]?\d*)', text, re.IGNORECASE)
    champs["reference"] = {"valeur": m.group(0).strip() if m else None, "confiance": round(find_conf(r'N°|Ref|BC'), 2)}

    return champs


# ─── 4. DÉTECTION SIGNATURE / TAMPON ─────────────────────────────────────────
def detect_signature_tampon(image_path: str) -> dict:
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    zone = img[int(h * 0.55):, :]
    _, thresh = cv2.threshold(zone, 180, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    zones_denses = [c for c in contours if cv2.contourArea(c) > 400]
    signature = len(zones_denses) >= 1
    tampon    = len(zones_denses) >= 3
    conf = min(0.5 + len(zones_denses) * 0.08, 0.95)
    return {
        "signature": {"valeur": signature, "confiance": round(conf, 2)},
        "tampon":    {"valeur": tampon,    "confiance": round(max(conf - 0.05, 0.4), 2)},
    }


# ─── 5. OCR DOUBLE PASSE ─────────────────────────────────────────────────────
def run_ocr(image_path: str) -> list[dict]:
    processed_path = image_path.replace(".jpg", "_proc.png").replace(".png", "_proc.png").replace(".jpeg", "_proc.png")
    processed = preprocess(image_path)
    cv2.imwrite(processed_path, processed)

    reader_ar = easyocr.Reader(['ar', 'en'], gpu=False)
    result_ar = reader_ar.readtext(processed_path)

    reader_fr = easyocr.Reader(['fr', 'en'], gpu=False)
    result_fr = reader_fr.readtext(processed_path)

    all_results, seen = [], set()
    for (bbox, text, conf) in result_ar + result_fr:
        text_clean = text.strip()
        if len(text_clean) < 2: continue
        key = text_clean.lower()[:15]
        if key not in seen:
            seen.add(key)
            all_results.append({"text": text_clean, "confidence": round(conf, 3), "bbox": bbox})

    try: os.remove(processed_path)
    except: pass

    return sorted(all_results, key=lambda x: -x["confidence"])


# ─── 6. PIPELINE COMPLET ─────────────────────────────────────────────────────
def run_pipeline(image_path: str) -> dict:
    """
    Point d'entrée principal. Accepte JPG, PNG, ou PDF (1 page).
    Retourne le JSON structuré complet.
    """
    # Si PDF → convertir la première page en image
    actual_path = image_path
    temp_files = []

    if image_path.lower().endswith(".pdf"):
        images = convert_from_path(image_path, dpi=200)
        temp_dir = tempfile.mkdtemp()
        pages_results = []

        for i, img in enumerate(images):
            tmp = os.path.join(temp_dir, f"page_{i+1}.png")
            img.save(tmp)
            temp_files.append(tmp)

            page_result = _process_single_image(tmp, f"page_{i+1}")
            pages_results.append(page_result)

        # Fusionner les résultats de toutes les pages
        result = _merge_pages(pages_results, image_path)
    else:
        result = _process_single_image(image_path, Path(image_path).stem)

    for f in temp_files:
        try: os.remove(f)
        except: pass

    return result


# ─── EXTRACTION VIA GEMINI VISION ────────────────────────────────────────────
def extract_with_gemini_vision(image_path: str, doc_type: str, api_key: str) -> dict:
    """Gemini 2.5 Flash Vision — extraction des champs depuis image."""
    import base64, json, re, requests as req2
    from pathlib import Path

    if doc_type == "fiche_ouverture_compte":
        prompt = 'Analyze this TGR Morocco bank account form. Return ONLY valid JSON no markdown: {"numero_compte":null,"nom":null,"prenom":null,"cin":null,"date_naissance":null,"nationalite":null,"domicile":null,"ville":null,"telephone":null,"profession":null,"date_ouverture":null}'
    elif doc_type == "procuration":
        prompt = 'Analyze this TGR proxy document. Return ONLY valid JSON no markdown: {"mandant":null,"numero_compte":null,"mandataire":null,"date_procuration":null,"agence":null}'
    else:
        prompt = 'Analyze this financial document. Return ONLY valid JSON no markdown: {"date":null,"montant":null,"fournisseur":null,"reference":null,"objet":null}'

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    ext  = Path(image_path).suffix.lower()
    mime = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png"}.get(ext, "image/png")

    url  = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" + api_key
    body = {"contents": [{"parts": [
        {"inline_data": {"mime_type": mime, "data": image_data}},
        {"text": prompt}
    ]}]}

    resp = req2.post(url, json=body, timeout=120)
    resp.raise_for_status()

    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    raw = re.sub(r"^```json|^```|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    extracted = json.loads(raw)

    return {
        k: {"valeur": v if v and str(v).strip() not in ("null","None","") else None,
            "confiance": 0.92 if v else 0.0}
        for k, v in extracted.items()
    }

def _process_single_image(image_path: str, doc_id: str) -> dict:
    # Détection du type via EasyOCR rapide (une seule passe légère)
    reader_fr = easyocr.Reader(['fr', 'en'], gpu=False)
    result_quick = reader_fr.readtext(image_path)
    quick_text = " ".join([r[1] for r in result_quick])
    doc_type = detect_document_type(quick_text)

    config = load_config()
    used_vision = False

    mode = config.get("mode", "ollama")
    gemini_key = config.get("gemini_api_key", "") if mode == "gemini" else ""
    print(f"[DEBUG] mode={mode}, gemini_key={gemini_key[:10] if gemini_key else 'EMPTY'}")
    champs = None
    if gemini_key and mode == "gemini":
        print("[DEBUG] Trying Gemini Vision...")
        try:
            champs = extract_with_gemini_vision(image_path, doc_type, gemini_key)
            used_vision = True
            print("[DEBUG] Gemini Vision SUCCESS")
        except Exception as e:
            print(f"[Vision] Gemini error: {e} — fallback to EasyOCR")
            champs = None
    else:
        print("[DEBUG] No Gemini key found — using EasyOCR")

    # ── MODE 2 : EasyOCR + extraction spatiale (fallback) ─────────────────
    gemini_was_used = used_vision  # Remember if Gemini was used
    if not champs:
        ocr_results = run_ocr(image_path)
        full_text   = " ".join([r["text"] for r in ocr_results])

        if doc_type == "fiche_ouverture_compte":
            champs = extract_fiche_ouverture(full_text, ocr_results)
        elif doc_type == "procuration":
            champs = extract_procuration(full_text, ocr_results)
        else:
            champs = extract_document_financier(full_text, ocr_results)

    # ── Signature / Tampon (toujours via OpenCV) ──────────────────────────
    sig_tampon = detect_signature_tampon(image_path)
    champs.update(sig_tampon)

    champs_a_valider = [
        n for n, d in champs.items()
        if isinstance(d.get("valeur"), str) and d["confiance"] < SEUIL_VALIDATION
    ]
    statut = "valide" if not champs_a_valider else (
        "partiel" if len(champs_a_valider) < len(champs)/2 else "a_verifier"
    )

    return {
        "document_id": doc_id,
        "type_document": doc_type,
        "methode_extraction": "gemini_vision" if gemini_was_used else "easyocr",
        "champs": champs,
        "statut_validation": statut,
        "champs_a_valider": champs_a_valider,
        "nb_blocs_ocr": len(result_quick),
    }


def _merge_pages(pages: list[dict], original_path: str) -> dict:
    """Fusionne les résultats de plusieurs pages d'un PDF."""
    merged_champs = {}
    for page in pages:
        for nom, data in page["champs"].items():
            if nom not in merged_champs or (data["valeur"] and not merged_champs[nom]["valeur"]):
                merged_champs[nom] = data

    champs_a_valider = [
        n for n, d in merged_champs.items()
        if isinstance(d.get("valeur"), str) and d["confiance"] < SEUIL_VALIDATION
    ]
    statut = "valide" if not champs_a_valider else ("partiel" if len(champs_a_valider) < len(merged_champs)/2 else "a_verifier")

    # Une page suffit à avoir utilisé Gemini Vision pour que le document
    # dans son ensemble soit considéré comme extrait via Gemini Vision.
    methode_extraction = "gemini_vision" if any(
        p.get("methode_extraction") == "gemini_vision" for p in pages
    ) else "easyocr"

    return {
        "document_id": Path(original_path).stem,
        "type_document": pages[0]["type_document"] if pages else "inconnu",
        "methode_extraction": methode_extraction,
        "nb_pages": len(pages),
        "champs": merged_champs,
        "statut_validation": statut,
        "champs_a_valider": champs_a_valider,
        "nb_blocs_ocr": sum(p["nb_blocs_ocr"] for p in pages),
    }


# ─── AFFICHAGE CONSOLE ────────────────────────────────────────────────────────
def print_result(output: dict):
    print("\n" + "═"*55)
    print(f"  TYPE : {output['type_document'].replace('_',' ').upper()}")
    print(f"  DOC  : {output['document_id']}")
    print("═"*55)
    for nom, data in output["champs"].items():
        val  = data.get("valeur")
        conf = data.get("confiance", 0)
        icon = "✅" if conf >= 0.90 else ("🟡" if conf >= 0.75 else "🔴")
        display = ("✔ Oui" if val else "✘ Non") if isinstance(val, bool) else (str(val) if val else "—")
        print(f"  {icon}  {nom:<22} {display:<30} ({conf:.0%})")
    print("─"*55)
    print(f"  Statut : {output['statut_validation'].upper()}")
    if output["champs_a_valider"]:
        print(f"  À valider : {', '.join(output['champs_a_valider'])}")
    print("═"*55+"\n")


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "OCR1.pdf"
    print(f"\n[OCR] Traitement de : {path}")
    result = run_pipeline(path)
    print_result(result)
    out = f"output_{result['document_id']}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[✓] JSON sauvegardé : {out}\n")