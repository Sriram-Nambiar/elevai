import io
from datetime import datetime
from typing import Dict, List, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)


class QuotePDFGenerator:
    """
    Publication-quality PDF Quotation & Engineering Spec Sheet generator for Elevai.
    Conforms to EN 81-70 compliance reporting standards with custom styling,
    spatial envelope grid, verdict banners, and itemized BOM tables.
    """

    def __init__(self):
        # Color Palette
        self.c_primary = colors.HexColor("#0f172a")      # Slate 900
        self.c_subtitle = colors.HexColor("#64748b")     # Slate 500
        self.c_bg_light = colors.HexColor("#f8fafc")     # Slate 50
        self.c_border = colors.HexColor("#e2e8f0")       # Slate 200
        self.c_border_dark = colors.HexColor("#cbd5e1")  # Slate 300

        # Verdict Colors
        self.c_appr_bg = colors.HexColor("#dcfce7")      # Light Emerald
        self.c_appr_text = colors.HexColor("#166534")    # Dark Green
        self.c_appr_border = colors.HexColor("#86efac")

        self.c_rej_bg = colors.HexColor("#fee2e2")       # Light Crimson
        self.c_rej_text = colors.HexColor("#991b1b")     # Dark Red
        self.c_rej_border = colors.HexColor("#fca5a5")

        self.c_warn_bg = colors.HexColor("#fef3c7")      # Light Amber
        self.c_warn_text = colors.HexColor("#92400e")    # Dark Amber

        # Typography / Styles
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        self.title_style = ParagraphStyle(
            name="QuoteTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=self.c_primary,
            spaceAfter=3
        )

        self.subtitle_style = ParagraphStyle(
            name="QuoteSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=self.c_subtitle,
            spaceAfter=12
        )

        self.meta_style = ParagraphStyle(
            name="QuoteMeta",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=self.c_subtitle,
            alignment=2  # Right aligned
        )

        self.section_heading = ParagraphStyle(
            name="SectionHeading",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=self.c_primary,
            spaceBefore=8,
            spaceAfter=4
        )

        self.cell_style = ParagraphStyle(
            name="TableCell",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=self.c_primary
        )

        self.cell_style_bold = ParagraphStyle(
            name="TableCellBold",
            parent=self.cell_style,
            fontName="Helvetica-Bold"
        )

        self.cell_style_right = ParagraphStyle(
            name="TableCellRight",
            parent=self.cell_style,
            alignment=2
        )

        self.cell_style_right_bold = ParagraphStyle(
            name="TableCellRightBold",
            parent=self.cell_style_bold,
            alignment=2
        )

        self.cell_style_header = ParagraphStyle(
            name="TableHeaderCell",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white
        )

        self.cell_style_header_right = ParagraphStyle(
            name="TableHeaderCellRight",
            parent=self.cell_style_header,
            alignment=2
        )

    def generate_pdf(
        self,
        evaluation: Dict[str, Any],
        cabin_dimensions_mm: Optional[Dict[str, int]] = None,
        max_allowable_flooring_thickness_mm: int = 12
    ) -> bytes:
        """
        Generates in-memory PDF binary stream containing complete spatial envelope,
        EN 81-70 compliance verdict, warnings, and itemized BOM.
        """
        dims = cabin_dimensions_mm or {"width": 1200, "depth": 1400, "height": 2350}
        c_width = dims.get("width", 1200)
        c_depth = dims.get("depth", 1400)
        c_height = dims.get("height", 2350)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []
        now_str = datetime.now().strftime("%d %b %Y, %H:%M")
        quote_ref = f"ELV-{datetime.now().strftime('%Y%m%d')}-01"

        # ---------------------------------------------------------------------
        # 1. Header Block with Reference & Metadata
        # ---------------------------------------------------------------------
        header_table_data = [
            [
                Paragraph("<b>ELEVAI MODERNIZATION SPECIFICATION & QUOTE</b>", self.title_style),
                Paragraph(f"<b>QUOTE REF:</b> {quote_ref}<br/><b>DATE:</b> {now_str}", self.meta_style)
            ],
            [
                Paragraph("Standards Baseline: EN 81-70 Accessibility & Dimensional Compliance", self.subtitle_style),
                Paragraph("<b>ENGINE:</b> Deterministic Rules v1.0", self.meta_style)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[360, 162])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=self.c_primary, spaceBefore=4, spaceAfter=10))

        # ---------------------------------------------------------------------
        # 2. Site Spatial Envelope Table (2x4 Grid)
        # ---------------------------------------------------------------------
        story.append(Paragraph("SITE SPATIAL ENVELOPE (CALIBRATED CLEARANCES)", self.section_heading))

        envelope_data = [
            [
                Paragraph("<b>Clear Width</b>", self.cell_style_bold),
                Paragraph("<b>Clear Depth</b>", self.cell_style_bold),
                Paragraph("<b>Clear Height</b>", self.cell_style_bold),
                Paragraph("<b>Max Floor Sill Clearance</b>", self.cell_style_bold),
            ],
            [
                Paragraph(f"{c_width} mm", self.cell_style),
                Paragraph(f"{c_depth} mm", self.cell_style),
                Paragraph(f"{c_height} mm", self.cell_style),
                Paragraph(f"{max_allowable_flooring_thickness_mm} mm", self.cell_style),
            ]
        ]
        col_w = 522 / 4
        envelope_table = Table(envelope_data, colWidths=[col_w, col_w, col_w, col_w])
        envelope_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_light),
            ("BOX", (0, 0), (-1, -1), 1, self.c_border_dark),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(envelope_table)
        story.append(Spacer(1, 10))

        # ---------------------------------------------------------------------
        # 3. Compliance Verdict Banner & Adjustment Warnings
        # ---------------------------------------------------------------------
        is_compliant = evaluation.get("is_compliant", False)
        verdict_text = (
            "APPROVED (Compliant with EN 81-70 & Spatial Tolerances)"
            if is_compliant
            else "REJECTED (Dimensional Clearance / Code Breach Detected)"
        )
        bg_color = self.c_appr_bg if is_compliant else self.c_rej_bg
        text_color = self.c_appr_text if is_compliant else self.c_rej_text
        border_color = self.c_appr_border if is_compliant else self.c_rej_border

        verdict_style = ParagraphStyle(
            name="VerdictParagraph",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=text_color,
            alignment=1  # Centered
        )

        verdict_table = Table(
            [[Paragraph(f"<b>COMPLIANCE VERDICT:</b> {verdict_text}", verdict_style)]],
            colWidths=[522]
        )
        verdict_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(verdict_table)

        # Fatal Violations (if any)
        violations = evaluation.get("violations", [])
        if violations:
            story.append(Spacer(1, 6))
            violation_paragraphs = [
                Paragraph(f"<b>Fatal Breach:</b> {v}", ParagraphStyle(
                    name="ViolItem",
                    parent=self.styles["Normal"],
                    fontName="Helvetica",
                    fontSize=8,
                    leading=11,
                    textColor=self.c_rej_text
                ))
                for v in violations
            ]
            viol_table = Table([[vp] for vp in violation_paragraphs], colWidths=[522])
            viol_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecdd3")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(viol_table)

        # Warnings / Site Adjustments (if any)
        warnings = evaluation.get("warnings", [])
        if warnings:
            story.append(Spacer(1, 6))
            warning_paragraphs = [
                Paragraph(f"• <b>Site Adjustment Notice:</b> {w}", ParagraphStyle(
                    name="WarnItem",
                    parent=self.styles["Normal"],
                    fontName="Helvetica",
                    fontSize=8,
                    leading=11,
                    textColor=self.c_warn_text
                ))
                for w in warnings
            ]
            warn_table = Table([[wp] for wp in warning_paragraphs], colWidths=[522])
            warn_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_warn_bg),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(warn_table)

        story.append(Spacer(1, 10))

        # ---------------------------------------------------------------------
        # 4. Itemized Bill of Materials (BOM) Table
        # ---------------------------------------------------------------------
        story.append(Paragraph("ITEMIZED BILL OF MATERIALS (BOM)", self.section_heading))

        bom_items = evaluation.get("bill_of_materials", [])
        bom_table_data = [
            [
                Paragraph("SKU ID", self.cell_style_header),
                Paragraph("Component Description", self.cell_style_header),
                Paragraph("Qty", self.cell_style_header_right),
                Paragraph("Unit Cost (INR)", self.cell_style_header_right),
                Paragraph("Extended (INR)", self.cell_style_header_right),
            ]
        ]

        for item in bom_items:
            sku = item.get("sku_id", "-")
            name = item.get("name", sku)
            qty = item.get("quantity", 1)
            unit_cost = item.get("unit_cost_inr", 0.0)
            ext_cost = item.get("extended_cost_inr", qty * unit_cost)

            bom_table_data.append([
                Paragraph(f"<b>{sku}</b>", self.cell_style),
                Paragraph(name, self.cell_style),
                Paragraph(str(qty), self.cell_style_right),
                Paragraph(f"Rs. {unit_cost:,.2f}", self.cell_style_right),
                Paragraph(f"Rs. {ext_cost:,.2f}", self.cell_style_right),
            ])

        # Summary Total Row
        total_cost = evaluation.get("total_estimated_cost_inr", 0.0)
        bom_table_data.append([
            Paragraph("<b>TOTAL ESTIMATED MODERNIZATION COST</b>", self.cell_style_bold),
            "",
            "",
            "",
            Paragraph(f"<b>Rs. {total_cost:,.2f}</b>", self.cell_style_right_bold)
        ])

        bom_col_widths = [105, 205, 38, 87, 87]
        bom_table = Table(bom_table_data, colWidths=bom_col_widths, repeatRows=1)

        # Row shading
        t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), self.c_primary),
            ("BOX", (0, 0), (-1, -1), 1, self.c_border_dark),
            ("INNERGRID", (0, 0), (-1, -2), 0.5, self.c_border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            # Total summary row formatting
            ("SPAN", (0, -1), (3, -1)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, self.c_primary),
            ("TOPPADDING", (0, -1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ]

        # Alternate row background
        for i in range(1, len(bom_items) + 1):
            bg = colors.white if i % 2 != 0 else self.c_bg_light
            t_style.append(("BACKGROUND", (0, i), (-1, i), bg))

        bom_table.setStyle(TableStyle(t_style))
        story.append(bom_table)

        # ---------------------------------------------------------------------
        # 5. Footer / Commercial Terms
        # ---------------------------------------------------------------------
        story.append(Spacer(1, 14))
        footer_text = (
            "<b>Note:</b> Quotation is valid for 30 days from generation date. "
            "All dimensions are subject to physical site re-survey by authorized technicians prior to manufacture. "
            "Hardware adheres to standard EN 81-70 accessibility criteria."
        )
        story.append(Paragraph(footer_text, ParagraphStyle(
            name="QuoteFooter",
            parent=self.styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=self.c_subtitle
        )))

        # Build document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # Backward compatibility alias
    generate_quote_pdf = generate_pdf
