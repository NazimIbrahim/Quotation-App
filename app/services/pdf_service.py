"""
PDF Generation Service for AMA Ceramics Quotation Management System.
Generates high-resolution, printable minimalist corporate PDF quotations matching
exact specifications, all terms & conditions, single-line company name, and
transparent 1:1 logo branding aligned to the right.
"""
import os
from datetime import date, datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
    Image as RLImage,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.graphics.shapes import Drawing, Polygon
from PIL import Image as PILImage

from app.config import (
    COMPANY_CONFIG,
    BANK_DETAILS,
    STANDARD_TERMS_AND_CONDITIONS,
    SIGNATORIES,
    OUTPUT_PDF_DIR,
    ASSETS_DIR,
)
from app.database.models import Quotation, QuotationArea, QuotationItem, CompanySetting


def number_to_inr_words(amount: float) -> str:
    """Converts a float amount into Indian currency words."""
    try:
        val = int(round(amount))
        if val == 0:
            return "Zero Rupees Only"

        def convert_less_than_thousand(n):
            units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                     "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                     "Seventeen", "Eighteen", "Nineteen"]
            tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
            res = ""
            if n >= 100:
                res += units[n // 100] + " Hundred "
                n %= 100
            if n >= 20:
                res += tens[n // 10] + " "
                n %= 10
            if n > 0:
                res += units[n] + " "
            return res.strip()

        crores = val // 10000000
        val %= 10000000
        lakhs = val // 100000
        val %= 100000
        thousands = val // 1000
        val %= 1000
        hundreds = val

        parts = []
        if crores:
            parts.append(f"{convert_less_than_thousand(crores)} Crore")
        if lakhs:
            parts.append(f"{convert_less_than_thousand(lakhs)} Lakh")
        if thousands:
            parts.append(f"{convert_less_than_thousand(thousands)} Thousand")
        if hundreds:
            parts.append(convert_less_than_thousand(hundreds))

        return "INR " + " ".join(parts).strip() + " Rupees Only"
    except Exception:
        return f"INR {amount:,.2f}"


class CeramicPDFGenerator:
    """Minimalist Corporate PDF Generator for Quotations matching reference design."""
    PRIMARY_COLOR = colors.HexColor("#1565C0")    # Corporate Royal Blue
    SECONDARY_COLOR = colors.HexColor("#1976D2")  # Mid Royal Blue
    DARK_NAVY = colors.HexColor("#0D47A1")        # Deep Royal Navy
    LIGHT_BLUE = colors.HexColor("#42A5F5")       # Cyan / Sky Accent
    ACCENT_GOLD = colors.HexColor("#D97706")      # Warm Amber
    BG_LIGHT = colors.HexColor("#F8FAFC")         # Crisp light neutral
    ROW_BG_LIGHT = colors.HexColor("#F8FAFC")     # Alternating row background
    DIVIDER_COLOR = colors.HexColor("#CBD5E1")    # Crisp subtle borders
    DIVIDER_LIGHT = colors.HexColor("#F1F5F9")    # Light divider tone
    BORDER_COLOR = colors.HexColor("#CBD5E1")     # Border tone
    TEXT_MAIN = colors.HexColor("#0F172A")        # Dark slate primary text
    TEXT_BODY = colors.HexColor("#334155")        # Body dark text
    TEXT_MUTED = colors.HexColor("#64748B")       # Muted subtitle text

    # Strict uniform section gap for identical spacing between all sections
    SECTION_GAP = 18

    @classmethod
    def create_minimalist_logo_mark(cls) -> Drawing:
        """Creates a modern geometric blue chevron/tile logo mark fallback."""
        d = Drawing(30, 26)
        d.add(Polygon([2, 8, 14, 26, 20, 26, 8, 8], fillColor=cls.PRIMARY_COLOR, strokeColor=None))
        d.add(Polygon([10, 0, 22, 18, 28, 18, 16, 0], fillColor=cls.LIGHT_BLUE, strokeColor=None))
        return d

    @classmethod
    def draw_background_decorations(cls, canv, doc):
        """Draws corporate geometric corner polygons, top stripe, and bottom footer contact badges."""
        W, H = doc.pagesize
        canv.saveState()

        # 1. Top Edge Blue Strip
        canv.setFillColor(cls.PRIMARY_COLOR)
        canv.rect(0, H - 7, W, 7, stroke=0, fill=1)

        # 2. Top-Left Geometric Polygon Accents
        canv.setFillColor(cls.LIGHT_BLUE)
        p3 = canv.beginPath()
        p3.moveTo(0, H - 72)
        p3.lineTo(165, H)
        p3.lineTo(155, H)
        p3.lineTo(0, H - 67)
        p3.close()
        canv.drawPath(p3, stroke=0, fill=1)

        canv.setFillColor(cls.SECONDARY_COLOR)
        p2 = canv.beginPath()
        p2.moveTo(0, H - 67)
        p2.lineTo(155, H)
        p2.lineTo(115, H)
        p2.lineTo(0, H - 50)
        p2.close()
        canv.drawPath(p2, stroke=0, fill=1)

        canv.setFillColor(cls.DARK_NAVY)
        p1 = canv.beginPath()
        p1.moveTo(0, H)
        p1.lineTo(115, H)
        p1.lineTo(0, H - 50)
        p1.close()
        canv.drawPath(p1, stroke=0, fill=1)

        # 3. Bottom-Right Geometric Polygon Accents
        canv.setFillColor(cls.LIGHT_BLUE)
        pb3 = canv.beginPath()
        pb3.moveTo(W - 145, 0)
        pb3.lineTo(W, 64)
        pb3.lineTo(W, 59)
        pb3.lineTo(W - 135, 0)
        pb3.close()
        canv.drawPath(pb3, stroke=0, fill=1)

        canv.setFillColor(cls.SECONDARY_COLOR)
        pb2 = canv.beginPath()
        pb2.moveTo(W - 135, 0)
        pb2.lineTo(W, 59)
        pb2.lineTo(W, 42)
        pb2.lineTo(W - 95, 0)
        pb2.close()
        canv.drawPath(pb2, stroke=0, fill=1)

        canv.setFillColor(cls.DARK_NAVY)
        pb1 = canv.beginPath()
        pb1.moveTo(W, 0)
        pb1.lineTo(W - 95, 0)
        pb1.lineTo(W, 42)
        pb1.close()
        canv.drawPath(pb1, stroke=0, fill=1)

        # 4. Bottom Footer Contact Badges
        setting = CompanySetting.get_settings()
        footer_y = 18
        icon_sz = 14

        phone_val = setting.phone.split("/")[0].strip() if setting.phone else ""
        email_val = setting.email.split("|")[0].strip() if setting.email else ""
        loc_val = f"{setting.address_line2}, {setting.state}" if setting.address_line2 else f"{setting.city or 'Morbi'}, {setting.state}"

        contacts = [
            ("phone", phone_val),
            ("email", email_val),
            ("pin", loc_val),
        ]

        cur_x = 28
        max_allowed_x = W - 155

        for icon_type, text in contacts:
            if not text:
                continue

            text_w = canv.stringWidth(text, "Helvetica", 7.5)
            if cur_x + icon_sz + 5 + text_w > max_allowed_x:
                while text_w > (max_allowed_x - cur_x - icon_sz - 12) and len(text) > 5:
                    text = text[:-4] + "..."
                    text_w = canv.stringWidth(text, "Helvetica", 7.5)

            # Solid dark navy icon square
            canv.setFillColor(cls.DARK_NAVY)
            canv.rect(cur_x, footer_y - 2, icon_sz, icon_sz, fill=1, stroke=0)

            # Crisp white vector icon
            canv.setStrokeColor(colors.white)
            canv.setFillColor(colors.white)
            canv.setLineWidth(0.8)

            cx = cur_x + icon_sz / 2
            cy = footer_y - 2 + icon_sz / 2

            if icon_type == "phone":
                canv.arc(cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5, 45, 90)
                canv.circle(cx - 2, cy - 2, 1.2, fill=1, stroke=0)
                canv.circle(cx + 2, cy + 2, 1.2, fill=1, stroke=0)
                canv.line(cx - 2, cy - 2, cx + 2, cy + 2)
            elif icon_type == "email":
                ex = cx - 4
                ey = cy - 2.5
                canv.rect(ex, ey, 8, 5.5, fill=0, stroke=1)
                canv.line(ex, ey + 5.5, cx, cy)
                canv.line(cx, cy, ex + 8, ey + 5.5)
            elif icon_type == "pin":
                canv.circle(cx, cy + 1, 2, fill=0, stroke=1)
                pin_p = canv.beginPath()
                pin_p.moveTo(cx - 1.8, cy + 0.5)
                pin_p.lineTo(cx, cy - 3.5)
                pin_p.lineTo(cx + 1.8, cy + 0.5)
                canv.drawPath(pin_p, fill=0, stroke=1)

            canv.setFillColor(colors.HexColor("#334155"))
            canv.setFont("Helvetica", 7.5)
            text_x = cur_x + icon_sz + 5
            canv.drawString(text_x, footer_y + 2, text)

            cur_x = text_x + text_w + 18

        canv.restoreState()

    @classmethod
    def generate_quotation_pdf(cls, quote_id: int, output_filepath: str = None) -> str:
        """Generates official quotation PDF with single-line company name, 1:1 logo, and all terms."""
        quote = Quotation.get_by_id(quote_id)
        if not quote:
            raise ValueError(f"Quotation #{quote_id} not found.")

        if not output_filepath:
            safe_num = quote.quotation_number.replace("/", "_").replace("\\", "_")
            filename = f"Quotation_{safe_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_filepath = str(OUTPUT_PDF_DIR / filename)

        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=26,
            bottomMargin=42,
        )

        styles = getSampleStyleSheet()

        # Typography
        style_comp_name = ParagraphStyle(
            "CompanyName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=cls.TEXT_MAIN,
            alignment=0,  # Left-aligned relative to logo
        )
        style_comp_tag = ParagraphStyle(
            "CompanyTagline",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9.5,
            textColor=cls.TEXT_MUTED,
            alignment=0,
        )
        style_quote_h1 = ParagraphStyle(
            "QuoteTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=cls.TEXT_MAIN,
            alignment=2,
        )
        style_meta_k = ParagraphStyle(
            "MetaKey",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_MUTED,
            alignment=2,
        )
        style_meta_v = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_MAIN,
            alignment=2,
        )
        style_bill_label = ParagraphStyle(
            "BillLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=cls.TEXT_MUTED,
        )
        style_client_name = ParagraphStyle(
            "ClientName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=cls.TEXT_MAIN,
        )
        style_client_info = ParagraphStyle(
            "ClientInfo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_MUTED,
        )
        style_th = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.8,
            leading=8.5,
            textColor=colors.white,
            alignment=1,
        )
        style_td = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=cls.TEXT_MAIN,
        )
        style_td_center = ParagraphStyle(
            "TableCellCenter",
            parent=style_td,
            alignment=1,
        )
        style_td_right = ParagraphStyle(
            "TableCellRight",
            parent=style_td,
            alignment=2,
        )
        style_area_title = ParagraphStyle(
            "AreaTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=cls.PRIMARY_COLOR,
        )
        style_thank_you = ParagraphStyle(
            "ThankYou",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=cls.TEXT_MAIN,
        )
        style_sec_title = ParagraphStyle(
            "SectionTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_MAIN,
        )
        style_sec_body = ParagraphStyle(
            "SectionBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=10,
            textColor=cls.TEXT_MUTED,
        )
        style_term_item = ParagraphStyle(
            "TermItem",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8.5,
            textColor=cls.TEXT_MUTED,
        )
        style_summary_label = ParagraphStyle(
            "SummaryLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_MUTED,
            alignment=2,
        )
        style_summary_val = ParagraphStyle(
            "SummaryValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_MAIN,
            alignment=2,
        )
        style_total_label = ParagraphStyle(
            "TotalLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.white,
        )
        style_total_val = ParagraphStyle(
            "TotalVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12,
            textColor=colors.white,
            alignment=2,
        )
        style_sign_label = ParagraphStyle(
            "SignLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=cls.TEXT_MUTED,
            alignment=1,
        )

        story = []
        setting = CompanySetting.get_settings()

        # =============================================================
        # 1. TOP HEADER: Right-Handed Alignment with Increased Logo Scale
        # =============================================================
        logo_img_path = setting.logo_path if (setting.logo_path and os.path.isfile(setting.logo_path)) else str(ASSETS_DIR / "company_logo.png")
        # Increased scale of 1:1 logo to 150% (from 46pt to 69pt)
        logo_sz = 69

        logo_flowable = None
        if os.path.isfile(logo_img_path):
            try:
                logo_flowable = RLImage(logo_img_path, width=logo_sz, height=logo_sz)
            except Exception:
                logo_flowable = None

        if not logo_flowable:
            logo_flowable = cls.create_minimalist_logo_mark()
            logo_sz = 45

        comp_paras = [
            Paragraph(f"<b>{setting.company_name}</b>", style_comp_name),
            Paragraph(setting.tagline.upper() if setting.tagline else "", style_comp_tag),
        ]
        if setting.gstin:
            comp_paras.append(Paragraph(f"<font color='#94A3B8'>GSTIN:</font> {setting.gstin} | <font color='#94A3B8'>State:</font> {setting.state}", style_comp_tag))

        # Dynamically measure exact text width so it sits flush against right margin
        w_name = pdfmetrics.stringWidth(setting.company_name, "Helvetica-Bold", 14)
        w_tag = pdfmetrics.stringWidth(setting.tagline.upper() if setting.tagline else "", "Helvetica", 7)
        gst_text = f"GSTIN: {setting.gstin} | State: {setting.state}" if setting.gstin else ""
        w_gst = pdfmetrics.stringWidth(gst_text, "Helvetica", 7)

        text_col_w = max(w_name, w_tag, w_gst) + 6
        gap_w = 8
        logo_col_w = logo_sz + gap_w

        right_branding_inner = Table([[logo_flowable, comp_paras]], colWidths=[logo_col_w, text_col_w])
        right_branding_inner.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Sits flush against the right margin (547 pt available)
        total_branding_w = logo_col_w + text_col_w
        left_spacer_w = 547 - total_branding_w

        top_header_table = Table([["", right_branding_inner]], colWidths=[left_spacer_w, total_branding_w])
        top_header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(top_header_table)

        # UNIFORM SECTION GAP 1
        story.append(Spacer(1, cls.SECTION_GAP))

        # =============================================================
        # 2. BILL TO & QUOTATION TITLE ROW
        # =============================================================
        bill_to_items = [
            Paragraph("Bill To:", style_bill_label),
            Spacer(1, 2),
            Paragraph(quote.customer_name, style_client_name),
        ]
        if quote.project_name:
            bill_to_items.append(Paragraph(f"{quote.project_name}", style_client_info))
        bill_to_items.append(Paragraph(f"Phone: {quote.customer_phone}", style_client_info))
        if hasattr(quote.customer, "email") and quote.customer.email:
            bill_to_items.append(Paragraph(f"Email: {quote.customer.email}", style_client_info))
        bill_to_items.append(Paragraph(f"Address: {quote.delivery_address}", style_client_info))

        q_date_str = quote.quotation_date.strftime("%B %d, %Y") if isinstance(quote.quotation_date, (date, datetime)) else str(quote.quotation_date)

        meta_sub_data = [
            [Paragraph("Quotation Number:", style_meta_k), Paragraph(f"#{quote.quotation_number}", style_meta_v)],
            [Paragraph("Quotation Date:", style_meta_k), Paragraph(q_date_str, style_meta_v)],
            [Paragraph("Valid Till:", style_meta_k), Paragraph("15 Days from date", style_meta_v)],
            [Paragraph("Sales Executive:", style_meta_k), Paragraph(quote.sales_person_name, style_meta_v)],
        ]
        meta_sub_table = Table(meta_sub_data, colWidths=[110, 137])
        meta_sub_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        quote_meta_items = [
            Paragraph("QUOTATION", style_quote_h1),
            Spacer(1, 4),
            meta_sub_table
        ]

        meta_table = Table([[bill_to_items, quote_meta_items]], colWidths=[290, 257])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(meta_table)

        # UNIFORM SECTION GAP 2
        story.append(Spacer(1, cls.SECTION_GAP))

        # =============================================================
        # 3. PRODUCT ITEMS TABLE (10 Columns)
        # =============================================================
        col_widths = [22, 126, 46, 52, 45, 47, 49, 46, 50, 64]

        table_data = [
            [
                Paragraph("<b>NO.</b>", style_th),
                Paragraph("<b>PRODUCT DESCRIPTION</b>", style_th),
                Paragraph("<b>SIZE</b>", style_th),
                Paragraph("<b>BRAND</b>", style_th),
                Paragraph("<b>COV.<br/>(SQFT/BX)</b>", style_th),
                Paragraph("<b>QTY<br/>(SQFT)</b>", style_th),
                Paragraph("<b>RATE/SQFT<br/>(Rs.)</b>", style_th),
                Paragraph("<b>QTY<br/>(BOXES)</b>", style_th),
                Paragraph("<b>RATE/BOX<br/>(Rs.)</b>", style_th),
                Paragraph("<b>TOTAL<br/>(Rs.)</b>", style_th),
            ]
        ]

        table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY_COLOR),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, 0), 0.5, colors.white),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, cls.DIVIDER_LIGHT),
            ('TOPPADDING', (0, 0), (-1, 0), 5.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5.5),
            ('TOPPADDING', (0, 1), (-1, -1), 4.5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]

        current_row = 1
        areas = list(quote.areas.order_by(QuotationArea.display_order))

        for area in areas:
            area_title = f"✦ AREA: {area.area_name.upper()}"
            area_cell = Paragraph(f"<b>{area_title}</b>", style_area_title)
            table_data.append([area_cell, "", "", "", "", "", "", "", "", ""])

            table_styles.append(('SPAN', (0, current_row), (9, current_row)))
            table_styles.append(('BACKGROUND', (0, current_row), (9, current_row), colors.HexColor("#F8FAFC")))
            table_styles.append(('LINEBELOW', (0, current_row), (9, current_row), 0.5, cls.DIVIDER_COLOR))
            table_styles.append(('LINEABOVE', (0, current_row), (9, current_row), 0.5, cls.DIVIDER_COLOR))
            table_styles.append(('TOPPADDING', (0, current_row), (9, current_row), 3.5))
            table_styles.append(('BOTTOMPADDING', (0, current_row), (9, current_row), 3.5))
            current_row += 1

            items = list(area.items.order_by(QuotationItem.sl_no))
            for item in items:
                row_bg = colors.HexColor("#FAFAFA") if current_row % 2 == 1 else colors.white
                table_styles.append(('BACKGROUND', (0, current_row), (-1, current_row), row_bg))

                item_brand = getattr(item, "brand", "") or "-"
                cov_val = float(getattr(item, "coverage_area", 0.0) or 0.0)
                cov_str = f"{cov_val:.2f}" if cov_val > 0 else "-"

                qty_sqft_str = f"{item.quantity_sqft:,.2f}" if item.quantity_sqft > 0 else "-"
                rate_sqft_str = f"{item.rate_per_sqft:,.2f}" if item.rate_per_sqft > 0 else "-"
                qty_box_str = f"{item.quantity_boxes:,.1f}" if item.quantity_boxes > 0 else "-"
                rate_box_str = f"{item.rate_per_box:,.2f}" if item.rate_per_box > 0 else "-"
                total_str = f"{item.total_amount:,.2f}"

                t_mode = getattr(item, "tax_mode", "exclusive") or "exclusive"
                tax_tag = "(Incl. 18%)" if t_mode == "inclusive" else "(+18% GST)"

                table_data.append([
                    Paragraph(f"{item.sl_no:02d}", style_td_center),
                    Paragraph(f"<b>{item.description}</b>", style_td),
                    Paragraph(item.size, style_td_center),
                    Paragraph(item_brand, style_td_center),
                    Paragraph(cov_str, style_td_center),
                    Paragraph(qty_sqft_str, style_td_right),
                    Paragraph(f"<b>{rate_sqft_str}</b><br/><font size='5.5' color='#64748B'>{tax_tag}</font>", style_td_right),
                    Paragraph(qty_box_str, style_td_right),
                    Paragraph(f"<b>{rate_box_str}</b><br/><font size='5.5' color='#64748B'>{tax_tag}</font>", style_td_right),
                    Paragraph(f"<b>{total_str}</b>", style_td_right),
                ])
                current_row += 1

        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle(table_styles))
        story.append(items_table)

        footnote_style = ParagraphStyle(
            "TableFootnote",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=6.5,
            leading=8.5,
            textColor=cls.TEXT_MUTED,
        )
        story.append(Spacer(1, 2))
        story.append(Paragraph("* Rates marked '(Incl. 18%)' have 18% GST included; '(+18% GST)' indicates basic rate excluding tax. Detailed GST breakdown itemized below.", footnote_style))

        # UNIFORM SECTION GAP 3
        story.append(Spacer(1, cls.SECTION_GAP))

        # =============================================================
        # 4. FINANCIAL SUMMARY & PAYMENT DETAILS
        # =============================================================
        pay_sub_data = [
            [Paragraph("Account No:", style_sec_body), Paragraph(f"<b>{setting.account_number}</b>", style_sec_body)],
            [Paragraph("Account Name:", style_sec_body), Paragraph(setting.account_name, style_sec_body)],
            [Paragraph("Bank & Branch:", style_sec_body), Paragraph(f"{setting.bank_name}, {setting.branch}", style_sec_body)],
            [Paragraph("IFSC Code:", style_sec_body), Paragraph(f"<b>{setting.ifsc_code}</b>", style_sec_body)],
        ]
        pay_table = Table(pay_sub_data, colWidths=[75, 225])
        pay_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        in_words = number_to_inr_words(quote.net_total)

        left_content = [
            Paragraph("Thank You For Your Business", style_thank_you),
            Spacer(1, 6),
            Paragraph("Payment Method:", style_sec_title),
            Spacer(1, 2),
            pay_table,
            Spacer(1, 4),
            Paragraph(f"<i>Amount in Words: {in_words}</i>", style_sec_body),
        ]

        round_sign = "+" if quote.round_off >= 0 else ""
        round_off_str = f"{round_sign}{quote.round_off:,.2f}"

        taxable_val = float(getattr(quote, "taxable_amount", 0.0) or 0.0)
        cgst_val = float(getattr(quote, "cgst_amount", 0.0) or 0.0)
        sgst_val = float(getattr(quote, "sgst_amount", 0.0) or 0.0)
        total_tax_val = float(getattr(quote, "total_tax", 0.0) or 0.0)

        # Fallback if legacy quotation without tax breakdown
        if taxable_val == 0.0 and quote.gross_total > 0:
            taxable_val = round(quote.gross_total / 1.18, 2)
            total_tax_val = round(quote.gross_total - taxable_val, 2)
            cgst_val = round(total_tax_val / 2.0, 2)
            sgst_val = round(total_tax_val - cgst_val, 2)

        sub_tbl_data = [
            [Paragraph("Taxable Subtotal:", style_summary_label), Paragraph(f"Rs. {taxable_val:,.2f}", style_summary_val)],
            [Paragraph("CGST (9.0%):", style_summary_label), Paragraph(f"Rs. {cgst_val:,.2f}", style_summary_val)],
            [Paragraph("SGST (9.0%):", style_summary_label), Paragraph(f"Rs. {sgst_val:,.2f}", style_summary_val)],
            [Paragraph("Total GST (18.0%):", style_summary_label), Paragraph(f"Rs. {total_tax_val:,.2f}", style_summary_val)],
        ]
        if abs(quote.round_off) >= 0.01:
            sub_tbl_data.append([
                Paragraph("Round Off:", style_summary_label),
                Paragraph(f"Rs. {round_off_str}", style_summary_val)
            ])
        sub_tbl = Table(sub_tbl_data, colWidths=[120, 107])
        sub_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        total_box_data = [
            [Paragraph("<b>Total:</b>", style_total_label), Paragraph(f"<b>Rs. {quote.net_total:,.2f}</b>", style_total_val)]
        ]
        total_box = Table(total_box_data, colWidths=[80, 147])
        total_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cls.PRIMARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))

        sign_block = [
            Spacer(1, 14),
            HRFlowable(width="65%", thickness=0.75, color=cls.DIVIDER_COLOR, hAlign='CENTER', spaceAfter=3),
            Paragraph(f"<b>Authorised sign</b><br/><font size='6.5' color='#64748B'>For {setting.company_name}</font>", style_sign_label),
        ]

        right_content = [
            sub_tbl,
            Spacer(1, 6),
            total_box,
            *sign_block
        ]

        summary_table = Table([[left_content, right_content]], colWidths=[305, 242])
        summary_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        # =============================================================
        # 5. ALL TERMS & CONDITIONS (Full Width 2-Column Grid)
        # =============================================================
        all_terms = setting.get_terms_list()
        half_n = (len(all_terms) + 1) // 2
        col1_terms = []
        col2_terms = []
        for i, term in enumerate(all_terms, start=1):
            p = Paragraph(f"<b>{i}.</b> {term}", style_term_item)
            if i <= half_n:
                col1_terms.append(p)
            else:
                col2_terms.append(p)

        terms_grid = Table([[col1_terms, col2_terms]], colWidths=[270, 277])
        terms_grid.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        terms_section = [
            HRFlowable(width="100%", thickness=0.5, color=cls.DIVIDER_LIGHT, spaceAfter=4, spaceBefore=2),
            Paragraph("<b>Terms & Conditions:</b>", style_sec_title),
            Spacer(1, 3),
            terms_grid,
        ]

        story.append(KeepTogether([
            summary_table,
            Spacer(1, cls.SECTION_GAP),
            *terms_section,
        ]))

        doc.build(story, onFirstPage=cls.draw_background_decorations, onLaterPages=cls.draw_background_decorations)
        return output_filepath
