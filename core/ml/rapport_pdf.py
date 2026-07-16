"""
rapport_pdf.py — Generateur de rapports PDF de conformite TGR
Utilise reportlab pour creer un rapport professionnel avec logo, resultats et signature
"""

import os
import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak
)
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable

# ── COULEURS TGR ──────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#0B2E4E")
ORANGE  = colors.HexColor("#E8601C")
GREEN   = colors.HexColor("#2D6A10")
RED     = colors.HexColor("#B91C1C")
AMBER   = colors.HexColor("#92400E")
GRAY    = colors.HexColor("#64748B")
LGRAY   = colors.HexColor("#F1F5F9")
WHITE   = colors.white
BLACK   = colors.black

# ── STYLES ────────────────────────────────────────────────────────────────────
def get_styles():
    styles = getSampleStyleSheet()
    custom = {
        "title": ParagraphStyle("title", fontSize=16, fontName="Helvetica-Bold",
                                textColor=NAVY, alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, fontName="Helvetica",
                                   textColor=GRAY, alignment=TA_CENTER, spaceAfter=2),
        "section": ParagraphStyle("section", fontSize=11, fontName="Helvetica-Bold",
                                  textColor=NAVY, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", fontSize=9, fontName="Helvetica",
                               textColor=BLACK, spaceAfter=4, leading=14),
        "small": ParagraphStyle("small", fontSize=8, fontName="Helvetica",
                                textColor=GRAY, spaceAfter=2),
        "label": ParagraphStyle("label", fontSize=8, fontName="Helvetica-Bold",
                                textColor=GRAY),
        "value": ParagraphStyle("value", fontSize=9, fontName="Helvetica",
                                textColor=BLACK),
        "badge_ok":   ParagraphStyle("badge_ok",   fontSize=8, fontName="Helvetica-Bold",
                                     textColor=GREEN,  alignment=TA_CENTER),
        "badge_warn": ParagraphStyle("badge_warn", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=AMBER,  alignment=TA_CENTER),
        "badge_err":  ParagraphStyle("badge_err",  fontSize=8, fontName="Helvetica-Bold",
                                     textColor=RED,    alignment=TA_CENTER),
        "footer": ParagraphStyle("footer", fontSize=7, fontName="Helvetica",
                                 textColor=GRAY, alignment=TA_CENTER),
    }
    return custom

# ── HEADER / FOOTER DE PAGE ───────────────────────────────────────────────────
class HeaderFooter(canvas.Canvas):
    """Canvas personnalise avec header et footer TGR."""
    _agent    = ""
    _date_str = ""

    def showPage(self):
        self._draw_header_footer()
        canvas.Canvas.showPage(self)

    def save(self):
        canvas.Canvas.save(self)

    def _draw_header_footer(self):
        w, h = A4
        # Header
        self.setStrokeColor(ORANGE)
        self.setLineWidth(2)
        self.line(1.5*cm, h - 1.2*cm, w - 1.5*cm, h - 1.2*cm)
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(NAVY)
        self.drawString(1.5*cm, h - 0.9*cm, "TRESORERIE GENERALE DU ROYAUME")
        self.setFont("Helvetica", 7)
        self.setFillColor(GRAY)
        self.drawRightString(w - 1.5*cm, h - 0.9*cm, "Rapport de Conformite — Usage interne")
        # Footer
        self.setStrokeColor(LGRAY)
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.5*cm, w - 1.5*cm, 1.5*cm)
        self.setFont("Helvetica", 7)
        self.setFillColor(GRAY)
        self.drawString(1.5*cm, 1.1*cm, "Genere le " + self._date_str + " | Agent: " + self._agent)
        self.drawCentredString(w/2, 1.1*cm, "CONFIDENTIEL — Usage interne TGR")
        self.drawRightString(w - 1.5*cm, 1.1*cm, "Page " + str(self._pageNumber))

# ── GENERATION DU RAPPORT ─────────────────────────────────────────────────────
def generate_rapport_pdf(
    dossiers: list,
    resultats: list,
    agent: str = "Agent.TGR",
    logo_path: str = None,
) -> bytes:
    """
    Genere un rapport PDF de conformite.
    Retourne le PDF en bytes (pour st.download_button).
    """
    buffer   = io.BytesIO()
    styles   = get_styles()
    now      = datetime.now()
    date_str = now.strftime("%d/%m/%Y a %H:%M")
    ref_num  = "RPT-" + now.strftime("%Y%m%d-%H%M%S")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2.5*cm,
        title="Rapport de Conformite TGR",
        author=agent,
    )

    story = []
    w = A4[0] - 3*cm  # largeur utile

    # ── PAGE DE GARDE ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))

    # Logo TGR
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=4*cm, height=3*cm)
            img.hAlign = "CENTER"
            story.append(img)
        except: pass

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("RAPPORT DE CONFORMITE", styles["title"]))
    story.append(Paragraph("Verification des Dossiers d-Ouverture de Comptes", styles["subtitle"]))
    story.append(Paragraph("Referentiel Client OLYMPIC — TGR", styles["subtitle"]))
    story.append(Spacer(1, 0.4*cm))

    # Ligne orange
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=8))

    # Infos du rapport
    info_data = [
        ["Reference",  ref_num,             "Date",    date_str],
        ["Agent",      agent,               "Dossiers", str(len(dossiers))],
        ["Conformes",  str(sum(1 for r in resultats if r["statut"]=="conforme")),
         "Non conformes", str(sum(1 for r in resultats if r["statut"]=="non_conforme"))],
    ]
    info_table = Table(info_data, colWidths=[2.5*cm, 5*cm, 2.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",    (2,0), (2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR",   (0,0), (0,-1), GRAY),
        ("TEXTCOLOR",   (2,0), (2,-1), GRAY),
        ("TEXTCOLOR",   (1,0), (1,-1), NAVY),
        ("TEXTCOLOR",   (3,0), (3,-1), NAVY),
        ("BACKGROUND",  (0,0), (-1,-1), LGRAY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [LGRAY, WHITE]),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.6*cm))

    # ── SYNTHESE ───────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Synthese de la verification", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LGRAY, spaceAfter=6))

    # Stats globales
    total  = len(resultats)
    n_ok   = sum(1 for r in resultats if r["statut"]=="conforme")
    n_pt   = sum(1 for r in resultats if r["statut"]=="partiellement_conforme")
    n_ko   = sum(1 for r in resultats if r["statut"]=="non_conforme")
    avg_sc = sum(r["score_conformite"] for r in resultats) / total if total > 0 else 0

    stats_data = [
        ["Indicateur", "Valeur", "Pourcentage"],
        ["Dossiers analyses",         str(total),   "100%"],
        ["Dossiers conformes",         str(n_ok),   "{:.0%}".format(n_ok/total) if total else "0%"],
        ["Dossiers partiellement conf.", str(n_pt),  "{:.0%}".format(n_pt/total) if total else "0%"],
        ["Dossiers non conformes",     str(n_ko),   "{:.0%}".format(n_ko/total) if total else "0%"],
        ["Score moyen de conformite",  "{:.1%}".format(avg_sc), ""],
    ]
    st_tbl = Table(stats_data, colWidths=[8*cm, 3*cm, 3*cm])
    st_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0), WHITE),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LGRAY]),
        ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        # Colorier la ligne non conformes
        ("TEXTCOLOR",    (0,4), (-1,4), RED),
        ("FONTNAME",     (0,4), (-1,4), "Helvetica-Bold"),
        ("TEXTCOLOR",    (0,2), (-1,2), GREEN),
    ]))
    story.append(st_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── DETAIL PAR DOSSIER ─────────────────────────────────────────────────────
    story.append(Paragraph("2. Detail par dossier", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LGRAY, spaceAfter=6))

    for i, (dossier, resultat) in enumerate(zip(dossiers, resultats)):
        client_id   = dossier.get("client_id", "")
        type_client = dossier.get("type_client","").replace("_"," ").title()
        statut      = resultat.get("statut","")
        score       = resultat.get("score_conformite", 0)
        anomalies   = resultat.get("anomalies", [])

        # Couleur selon statut
        if statut == "conforme":
            hdr_color, statut_txt, score_color = GREEN, "CONFORME", GREEN
        elif statut == "partiellement_conforme":
            hdr_color, statut_txt, score_color = ORANGE, "PARTIELLEMENT CONFORME", ORANGE
        else:
            hdr_color, statut_txt, score_color = RED, "NON CONFORME", RED

        # En-tete dossier
        hdr_data = [[
            Paragraph("<b>" + client_id + "</b> — " + type_client, ParagraphStyle("h", fontSize=9, fontName="Helvetica-Bold", textColor=WHITE)),
            Paragraph(statut_txt + " | " + "{:.0%}".format(score), ParagraphStyle("s", fontSize=9, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_RIGHT)),
        ]]
        hdr_tbl = Table(hdr_data, colWidths=[w*0.65, w*0.35])
        hdr_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,-1), hdr_color),
            ("TOPPADDING",  (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING",(0,0), (-1,-1), 8),
        ]))
        story.append(hdr_tbl)

        # Champs du dossier
        champs = dossier.get("champs", {})
        if champs:
            champ_rows = [["Champ", "Valeur"]]
            for k, v in list(champs.items())[:6]:
                champ_rows.append([k.replace("_"," ").title(), str(v) if v else "-"])
            ch_tbl = Table(champ_rows, colWidths=[4*cm, w - 4*cm])
            ch_tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#F8FAFC")),
                ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTNAME",     (0,1), (0,-1), "Helvetica-Bold"),
                ("TEXTCOLOR",    (0,0), (0,-1), GRAY),
                ("FONTSIZE",     (0,0), (-1,-1), 8),
                ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LGRAY]),
                ("TOPPADDING",   (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0), (-1,-1), 4),
                ("LEFTPADDING",  (0,0), (-1,-1), 6),
            ]))
            story.append(ch_tbl)

        # Anomalies
        if anomalies:
            story.append(Spacer(1, 0.1*cm))
            anom_data = [["Anomalies detectees"]]
            for a in anomalies:
                anom_data.append(["  " + a])
            an_tbl = Table(anom_data, colWidths=[w])
            an_tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#FEF2F2")),
                ("TEXTCOLOR",    (0,0), (-1,0), RED),
                ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
                ("TEXTCOLOR",    (0,1), (-1,-1), colors.HexColor("#92400E")),
                ("FONTSIZE",     (0,0), (-1,-1), 8),
                ("BACKGROUND",   (0,1), (-1,-1), colors.HexColor("#FFF7ED")),
                ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#FED7AA")),
                ("TOPPADDING",   (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0), (-1,-1), 4),
                ("LEFTPADDING",  (0,0), (-1,-1), 8),
            ]))
            story.append(an_tbl)
        else:
            ok_data = [["Aucune anomalie detectee — Dossier complet"]]
            ok_tbl  = Table(ok_data, colWidths=[w])
            ok_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
                ("TEXTCOLOR",   (0,0), (-1,-1), GREEN),
                ("FONTNAME",    (0,0), (-1,-1), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#BBF7D0")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING", (0,0), (-1,-1), 8),
            ]))
            story.append(ok_tbl)

        story.append(Spacer(1, 0.3*cm))

    # ── SIGNATURE ──────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3. Validation et Signature", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LGRAY, spaceAfter=10))

    sign_data = [
        ["Agent verificateur", "Visa du responsable"],
        ["\n\n\nNom : " + agent + "\nDate : " + date_str, "\n\n\nNom : ___________________\nDate : ___________________"],
        ["Signature : ___________________", "Signature / Cachet : ___________________"],
    ]
    sign_tbl = Table(sign_data, colWidths=[w/2, w/2])
    sign_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("ALIGN",       (0,0), (-1,0), "CENTER"),
        ("MINROWHEIGHT",(0,1), (-1,-1), 3*cm),
    ]))
    story.append(sign_tbl)

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ORANGE, spaceAfter=6))
    story.append(Paragraph(
        "Ce rapport a ete genere automatiquement par la Plateforme IA TGR. "
        "Reference : " + ref_num + " — " + date_str,
        styles["footer"]
    ))
    story.append(Paragraph(
        "CONFIDENTIEL — Document a usage interne exclusif de la Tresorerie Generale du Royaume",
        ParagraphStyle("conf", fontSize=7, fontName="Helvetica-Bold",
                       textColor=RED, alignment=TA_CENTER)
    ))

    # Build avec header/footer
    def make_canvas(filename, **kwargs):
        c = HeaderFooter(filename, **kwargs)
        c._agent    = agent
        c._date_str = date_str
        return c

    doc.build(story, canvasmaker=make_canvas)
    return buffer.getvalue()
