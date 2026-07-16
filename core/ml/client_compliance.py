"""
client_compliance.py
Vérifie la conformité d'un dossier client selon les règles du référentiel
TGR (note de service 91/04/TGR + règles OLYMPIC).

Règles extraites du document fourni :
- Personne physique : CIN obligatoire, format XX99999999 sans espaces
- Personne morale (société) : RC + code analytique, IF, représentant légal
- Association : statuts, PV AG, CIN des signataires
- Établissement public : texte de création, décision de nomination
- Coopérative : code ODCO requis en plus du dossier association
"""

import re
from datetime import datetime


# ─── RÈGLES PAR TYPE DE CLIENT (extraites du document TGR) ────────────────
REGLES_PAR_TYPE = {
    "personne_physique": {
        "champs_obligatoires": ["nom", "prenom", "cin", "adresse", "ville"],
        "documents_requis": ["copie_cin", "demande_ouverture", "specimen_signature"],
        "format_cin": r"^[A-Z]{1,2}\d{6,8}$",   # format XX99999999 sans espaces
    },
    "personne_physique_fonctionnaire": {
        "champs_obligatoires": ["nom", "prenom", "cin", "adresse", "ville", "employeur", "ppr"],
        "documents_requis": ["copie_cin", "demande_ouverture", "specimen_signature", "domiciliation_salaire"],
        "format_cin": r"^[A-Z]{1,2}\d{6,8}$",
    },
    "societe": {
        "champs_obligatoires": ["raison_sociale", "forme_juridique", "rc", "code_analytique", "adresse_siege"],
        "documents_requis": ["statuts", "extrait_rc", "cin_representant", "pv_designation_signataires"],
        "format_rc": r"^\d{1,3}/\d{2,6}$",   # format type tribunal/numéro
    },
    "association": {
        "champs_obligatoires": ["nom_association", "adresse_siege", "date_creation", "nom_president"],
        "documents_requis": ["statuts", "pv_ag_constitutive", "pv_derniere_ag", "certificat_depot", "liste_bureau", "cin_signataires"],
        "regle_speciale": "date_certificat_depot_posterieure_a_pv_ag",
    },
    "cooperative": {
        "champs_obligatoires": ["nom_cooperative", "adresse_siege", "date_creation", "code_odco"],
        "documents_requis": ["statuts", "pv_ag_constitutive", "pv_derniere_ag", "decision_agrement", "liste_bureau"],
    },
    "etablissement_public": {
        "champs_obligatoires": ["denomination", "adresse", "responsable"],
        "documents_requis": ["texte_creation", "texte_organisation_financiere", "decision_nomination_responsable", "lettre_accreditation",
                              "cin_signataires"],
    },
    "regie": {
        "champs_obligatoires": ["nom_regie", "code_regie", "cin_regisseur"],
        "documents_requis": ["demande_ouverture", "autorisation_ministere", "arrete_creation", "arrete_nomination_regisseur", "cin_regisseur"],
    },
}

# Catégorie de compte selon le type (extrait du document : régies/établissements
# publics non subventionnés → comptes avec intérêts ; subventionnés → sans intérêts)
CATEGORIE_COMPTE_DEFAUT = {
    "personne_physique": "avec_interets",
    "societe": "avec_interets",
    "association": "avec_interets",
    "cooperative": "avec_interets",
    "etablissement_public_subventionne": "sans_interets",
    "etablissement_public_non_subventionne": "avec_interets",
    "regie": "sans_interets",
}


# ─── VALIDATION DU FORMAT CIN ──────────────────────────────────────────────
def valider_format_cin(cin: str) -> tuple[bool, str]:
    """
    Format attendu (règle TGR/OLYMPIC) : XX99999999, sans espaces ni caractères spéciaux.
    """
    if not cin:
        return False, "CIN manquante"

    cin_clean = cin.strip()

    if " " in cin_clean or any(c in cin_clean for c in ".-/,"):
        return False, f"CIN '{cin}' contient des espaces ou caractères spéciaux interdits"

    if not re.match(r"^[A-Za-z]{1,2}\d{5,9}$", cin_clean):
        return False, f"CIN '{cin}' ne respecte pas le format XX99999999 attendu"

    return True, "Format CIN valide"


# ─── VALIDATION D'UN DOSSIER CLIENT ───────────────────────────────────────
def verifier_dossier_client(dossier: dict) -> dict:
    """
    Prend un dossier client (dict) et retourne un rapport de conformité.

    dossier attendu :
    {
        "client_id": "CLI-00123",
        "type_client": "personne_physique" | "societe" | "association" | ...,
        "champs": {"nom": "...", "cin": "...", ...},
        "documents_fournis": ["copie_cin", "demande_ouverture", ...]
    }
    """
    type_client = dossier.get("type_client")
    champs = dossier.get("champs", {})
    documents_fournis = set(dossier.get("documents_fournis", []))

    if type_client not in REGLES_PAR_TYPE:
        return {
            "client_id": dossier.get("client_id"),
            "statut": "type_inconnu",
            "anomalies": [f"Type de client '{type_client}' non reconnu dans le référentiel"],
            "score_conformite": 0.0,
        }

    regles = REGLES_PAR_TYPE[type_client]
    anomalies = []

    # 1. Vérifier les champs obligatoires
    champs_manquants = [
        c for c in regles["champs_obligatoires"]
        if not champs.get(c)
    ]
    if champs_manquants:
        anomalies.append(f"Champs obligatoires manquants : {', '.join(champs_manquants)}")

    # 2. Vérifier les documents requis
    documents_manquants = [
        d for d in regles["documents_requis"]
        if d not in documents_fournis
    ]
    if documents_manquants:
        anomalies.append(f"Documents justificatifs manquants : {', '.join(documents_manquants)}")

    # 3. Vérifier le format CIN si applicable
    if "format_cin" in regles or "cin" in champs:
        cin = champs.get("cin", "")
        if cin:
            valide, message = valider_format_cin(cin)
            if not valide:
                anomalies.append(message)

    # 4. Règle spéciale association (date certificat > date PV AG)
    if regles.get("regle_speciale") == "date_certificat_depot_posterieure_a_pv_ag":
        date_certif = champs.get("date_certificat_depot")
        date_pv_ag = champs.get("date_derniere_ag")
        if date_certif and date_pv_ag:
            try:
                d_certif = datetime.strptime(date_certif, "%Y-%m-%d")
                d_pv = datetime.strptime(date_pv_ag, "%Y-%m-%d")
                if d_certif <= d_pv:
                    anomalies.append(
                        "Le certificat de dépôt doit être postérieur au PV de la dernière AG "
                        f"(certificat: {date_certif}, PV AG: {date_pv_ag})"
                    )
            except ValueError:
                anomalies.append("Format de date invalide pour la vérification certificat/PV AG")

    # Calcul du score de conformité
    total_checks = len(regles["champs_obligatoires"]) + len(regles["documents_requis"])
    checks_ok = total_checks - len(champs_manquants) - len(documents_manquants)
    score_conformite = round(checks_ok / total_checks, 2) if total_checks > 0 else 1.0

    if not anomalies:
        statut = "conforme"
    elif score_conformite >= 0.7:
        statut = "partiellement_conforme"
    else:
        statut = "non_conforme"

    return {
        "client_id": dossier.get("client_id"),
        "type_client": type_client,
        "statut": statut,
        "score_conformite": score_conformite,
        "anomalies": anomalies,
        "champs_manquants": champs_manquants,
        "documents_manquants": documents_manquants,
    }


# ─── TRAITEMENT EN LOT ─────────────────────────────────────────────────────
def verifier_lot_clients(dossiers: list[dict]) -> list[dict]:
    """Vérifie une liste de dossiers clients et trie par score de conformité croissant."""
    resultats = [verifier_dossier_client(d) for d in dossiers]
    return sorted(resultats, key=lambda r: r["score_conformite"])


# ─── EXEMPLE / TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    dossiers_test = [
        {
            "client_id": "CLI-00123",
            "type_client": "personne_physique",
            "champs": {
                "nom": "Benhammi", "prenom": "Youssef",
                "cin": "BE 123456",  # ❌ contient un espace
                "adresse": "Rue Hassan II", "ville": "Rabat"
            },
            "documents_fournis": ["copie_cin", "demande_ouverture"]
            # ❌ specimen_signature manquant
        },
        {
            "client_id": "CLI-00456",
            "type_client": "societe",
            "champs": {
                "raison_sociale": "ATLAS BTP SARL",
                "forme_juridique": "SARL",
                "rc": "12/4582",
                "code_analytique": "4582",
                "adresse_siege": "Zone Industrielle, Casablanca"
            },
            "documents_fournis": ["statuts", "extrait_rc", "cin_representant", "pv_designation_signataires"]
            # ✅ dossier complet
        },
        {
            "client_id": "CLI-00789",
            "type_client": "association",
            "champs": {
                "nom_association": "Association Al Amal",
                "adresse_siege": "Av. Mohammed V, Fès",
                "date_creation": "2018-03-12",
                "nom_president": "Karim Alaoui",
                "date_certificat_depot": "2018-01-10",   # ❌ antérieure au PV AG
                "date_derniere_ag": "2024-06-15"
            },
            "documents_fournis": ["statuts", "pv_ag_constitutive", "liste_bureau"]
            # ❌ pv_derniere_ag, certificat_depot, cin_signataires manquants
        },
    ]

    print("═" * 60)
    print("  VÉRIFICATION DE CONFORMITÉ — DOSSIERS CLIENTS")
    print("═" * 60)

    resultats = verifier_lot_clients(dossiers_test)

    for r in resultats:
        icon = "✅" if r["statut"] == "conforme" else ("🟡" if r["statut"] == "partiellement_conforme" else "🔴")
        print(f"\n{icon} {r['client_id']}  ({r['type_client']})")
        print(f"   Statut : {r['statut'].upper()}  —  Score : {r['score_conformite']:.0%}")
        if r["anomalies"]:
            for a in r["anomalies"]:
                print(f"   ⚠️  {a}")