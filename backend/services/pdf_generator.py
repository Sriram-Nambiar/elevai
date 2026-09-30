import io
import os
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
    HRFlowable,
    Image as ReportLabImage,
)


class QuotePDFGenerator:
    """
    Publication-quality PDF Quotation & Engineering Spec Sheet generator for Elevai.
    Produces an explicitly unapproved planning draft with a site envelope,
    prototype fit-screen results, unknowns, and an itemized BOM.
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
        max_allowable_flooring_thickness_mm: Optional[int] = None,
        site_measurements: Optional[Dict[str, Any]] = None,
        scene_id: Optional[str] = None,
        reference_images: Optional[List[tuple[str, str]]] = None,
    ) -> bytes:
        """
        Generates an in-memory draft proposal with fit-screen results, assumptions,
        unknowns, and reviewer sign-off fields.
        """
        site_measurements = site_measurements or {}
        dims = cabin_dimensions_mm or site_measurements.get("cabin_dimensions_mm") or {}
        c_width = dims.get("width")
        c_depth = dims.get("depth")
        c_height = dims.get("height")
        max_allowable_flooring_thickness_mm = (
            max_allowable_flooring_thickness_mm
            if max_allowable_flooring_thickness_mm is not None
            else site_measurements.get("max_allowable_flooring_thickness_mm")
        )

        def mm_text(value):
            return f"{value:g} mm" if isinstance(value, (int, float)) else "Unknown"

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
                Paragraph("<b>DRAFT LIFT MODERNIZATION PROPOSAL</b>", self.title_style),
                Paragraph(f"<b>REF:</b> {quote_ref}<br/><b>DATE:</b> {now_str}", self.meta_style)
            ],
            [
                Paragraph("Catalog options and prototype dimensional screening · qualified review required", self.subtitle_style),
                Paragraph(f"<b>SCENE:</b> {scene_id or 'Not provided'}<br/><b>STATUS:</b> DRAFT", self.meta_style)
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
        story.append(Paragraph("SITE MEASUREMENTS (USER-PROVIDED; NOT PHOTO-CALIBRATED)", self.section_heading))

        envelope_data = [
            [
                Paragraph("<b>Clear Width</b>", self.cell_style_bold),
                Paragraph("<b>Clear Depth</b>", self.cell_style_bold),
                Paragraph("<b>Clear Height</b>", self.cell_style_bold),
                Paragraph("<b>Max Floor Sill Clearance</b>", self.cell_style_bold),
            ],
            [
                Paragraph(mm_text(c_width), self.cell_style),
                Paragraph(mm_text(c_depth), self.cell_style),
                Paragraph(mm_text(c_height), self.cell_style),
                Paragraph(mm_text(max_allowable_flooring_thickness_mm), self.cell_style),
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

        for caption, image_path in reference_images or []:
            if os.path.isfile(image_path):
                story.append(Paragraph(caption, self.section_heading))
                story.append(ReportLabImage(image_path, width=250, height=210, kind="proportional"))
                story.append(Spacer(1, 6))

        # ---------------------------------------------------------------------
        # 3. Prototype fit-screen status and adjustment warnings
        # ---------------------------------------------------------------------
        status = evaluation.get("overall_status", "REVIEW_REQUIRED")
        verdict_text = {
            "GEOMETRY_CHECKS_PASSED": "DIMENSIONAL SCREEN PASSED — PROFESSIONAL REVIEW STILL REQUIRED",
            "REJECTED": "FIT CHECK FAILED — DO NOT USE THIS CONFIGURATION",
        }.get(status, "REVIEW REQUIRED — IMPORTANT INFORMATION IS MISSING")
        if status == "GEOMETRY_CHECKS_PASSED":
            bg_color, text_color, border_color = self.c_appr_bg, self.c_appr_text, self.c_appr_border
        elif status == "REJECTED":
            bg_color, text_color, border_color = self.c_rej_bg, self.c_rej_text, self.c_rej_border
        else:
            bg_color, text_color, border_color = self.c_warn_bg, self.c_warn_text, colors.HexColor("#fcd34d")

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
            [[Paragraph(f"<b>PROTOTYPE FIT SCREEN:</b> {verdict_text}", verdict_style)]],
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
                    Paragraph(f"<b>Fit check issue:</b> {v}", ParagraphStyle(
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

        missing_information = evaluation.get("missing_information", [])
        story.append(Paragraph("UNKNOWN OR MISSING INFORMATION", self.section_heading))
        if missing_information:
            for missing in missing_information:
                story.append(Paragraph(f"• {missing}", self.cell_style))
        else:
            story.append(Paragraph("No required fit inputs were missing for this prototype screen.", self.cell_style))

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
            qty = item.get("quantity")
            unit_cost = item.get("unit_cost_inr")
            ext_cost = item.get("extended_cost_inr")

            def money_text(value):
                return f"Rs. {value:,.2f}" if isinstance(value, (int, float)) else "Pending fit"

            bom_table_data.append([
                Paragraph(f"<b>{sku}</b>", self.cell_style),
                Paragraph(name, self.cell_style),
                Paragraph(str(qty) if qty is not None else "—", self.cell_style_right),
                Paragraph(money_text(unit_cost), self.cell_style_right),
                Paragraph(money_text(ext_cost), self.cell_style_right),
            ])

        # Summary Total Row
        total_cost = evaluation.get("total_estimated_cost_inr")
        bom_table_data.append([
            Paragraph("<b>TOTAL ESTIMATED MODERNIZATION COST</b>", self.cell_style_bold),
            "",
            "",
            "",
            Paragraph(f"<b>{money_text(total_cost)}</b>", self.cell_style_right_bold)
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
        # 5. Assumptions and qualified reviewer gate
        # ---------------------------------------------------------------------
        story.append(Paragraph("ASSUMPTIONS AND SCOPE LIMITS", self.section_heading))
        assumptions = [
            "All dimensions are user-entered site measurements; the photograph and relative-depth model do not provide metric scale.",
            "Prices and product attributes are demonstration catalog values; verify current manufacturer specifications and availability.",
            "Estimate covers listed catalog materials only. Installation labor, taxes, freight, electrical changes, and statutory inspections are excluded.",
            "Surface renderings are procedural visual concepts and do not certify fit, finish, accessibility, or code compliance.",
            "A qualified lift professional must inspect the site and approve the selected products and work scope before customer issue.",
        ]
        for assumption in assumptions:
            story.append(Paragraph(f"• {assumption}", self.cell_style))

        story.append(Spacer(1, 10))
        approval_table = Table([
            [Paragraph("<b>QUALIFIED REVIEWER APPROVAL</b>", self.cell_style_bold)],
            [Paragraph("Reviewer name / role: _________________________________________________", self.cell_style)],
            [Paragraph("Decision:   [ ] Approve   [ ] Revise   [ ] Reject     Date: __________________", self.cell_style)],
            [Paragraph("This document remains a draft until reviewed and signed. Do not issue to a customer as an approved proposal.", self.cell_style)],
        ], colWidths=[522])
        approval_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_light),
            ("BOX", (0, 0), (-1, -1), 0.8, self.c_border_dark),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, self.c_border),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(approval_table)

        # Build document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # Backward compatibility alias
    generate_quote_pdf = generate_pdf
