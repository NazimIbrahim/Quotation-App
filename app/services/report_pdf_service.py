"""
Report PDF Generation Service for AMA Ceramics Quotation Management System.
Generates minimalistic corporate executive PDF reports:
1. Daily Sales & Collections Audit Report
2. Monthly Performance & Revenue Audit Report
3. Sales Target vs. Achievement Archive Audit Report
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
    Image as RLImage,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics

from app.config import OUTPUT_PDF_DIR
from app.database.models import CompanySetting, Quotation
from app.services.pdf_service import CeramicPDFGenerator
from app.services.report_service import ReportService


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that applies corporate background accents and dynamic Page X of Y."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        dummy_doc = type("Doc", (), {"pagesize": self._pagesize})()
        for state in self._saved_page_states:
            self.__dict__.update(state)
            CeramicPDFGenerator.draw_background_decorations(self, dummy_doc)
            self.saveState()
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            page_text = f"Page {self._pageNumber} of {num_pages}"
            self.drawRightString(self._pagesize[0] - 28, self._pagesize[1] - 18, page_text)
            self.restoreState()
            super().showPage()
        super().save()


class ReportPDFGenerator:
    """Minimalist Corporate Executive PDF Generator for Analytical and Audit Reports."""
    PRIMARY = colors.HexColor("#1565C0")
    SECONDARY = colors.HexColor("#1976D2")
    DARK_NAVY = colors.HexColor("#0D47A1")
    LIGHT_BLUE = colors.HexColor("#42A5F5")
    SUCCESS = colors.HexColor("#059669")
    WARNING = colors.HexColor("#D97706")
    DANGER = colors.HexColor("#DC2626")
    BG_LIGHT = colors.HexColor("#F8FAFC")
    BORDER_LIGHT = colors.HexColor("#CBD5E1")
    TEXT_MAIN = colors.HexColor("#0F172A")
    TEXT_MUTED = colors.HexColor("#64748B")

    SECTION_GAP = 14

    @classmethod
    def _get_styles(cls):
        styles = getSampleStyleSheet()

        return {
            "comp_name": ParagraphStyle(
                "RptCompName",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=cls.TEXT_MAIN,
                alignment=0,
            ),
            "comp_tag": ParagraphStyle(
                "RptCompTag",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                textColor=cls.TEXT_MUTED,
                alignment=0,
            ),
            "report_h1": ParagraphStyle(
                "RptH1",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=19,
                textColor=cls.PRIMARY,
            ),
            "report_sub": ParagraphStyle(
                "RptSub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=cls.TEXT_MUTED,
            ),
            "sec_title": ParagraphStyle(
                "RptSecTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
                textColor=cls.TEXT_MAIN,
            ),
            "th": ParagraphStyle(
                "RptTH",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7,
                leading=9,
                textColor=colors.white,
                alignment=1,
            ),
            "td": ParagraphStyle(
                "RptTD",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.2,
                leading=9.2,
                textColor=cls.TEXT_MAIN,
            ),
            "td_center": ParagraphStyle(
                "RptTDCenter",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.2,
                leading=9.2,
                textColor=cls.TEXT_MAIN,
                alignment=1,
            ),
            "td_right": ParagraphStyle(
                "RptTDRight",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.2,
                leading=9.2,
                textColor=cls.TEXT_MAIN,
                alignment=2,
            ),
            "td_bold_right": ParagraphStyle(
                "RptTDBoldRight",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.2,
                leading=9.2,
                textColor=cls.TEXT_MAIN,
                alignment=2,
            ),
            "total_td": ParagraphStyle(
                "RptTotalTD",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=9.5,
                textColor=colors.white,
            ),
            "total_td_right": ParagraphStyle(
                "RptTotalTDRight",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=9.5,
                textColor=colors.white,
                alignment=2,
            ),
            "kpi_label": ParagraphStyle(
                "KPILabel",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7,
                leading=9,
                textColor=cls.TEXT_MUTED,
            ),
            "kpi_val": ParagraphStyle(
                "KPIVal",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=cls.PRIMARY,
            ),
            "kpi_sub": ParagraphStyle(
                "KPISub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=6.5,
                leading=8.5,
                textColor=cls.TEXT_MUTED,
            ),
            "sign_lbl": ParagraphStyle(
                "SignLbl",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=10,
                textColor=cls.TEXT_MUTED,
                alignment=1,
            ),
        }

    @classmethod
    def _create_header_elements(cls, title_str: str, subtitle_str: str, styles) -> list:
        """Creates top header with right-flush branding and lower report title banner (clears top-left geometric accents)."""
        setting = CompanySetting.get_settings()
        logo_img_path = setting.logo_path if (setting.logo_path and os.path.isfile(setting.logo_path)) else str(Path("assets/company_logo.png").resolve())
        logo_sz = 50

        logo_flowable = None
        if os.path.isfile(logo_img_path):
            try:
                logo_flowable = RLImage(logo_img_path, width=logo_sz, height=logo_sz)
            except Exception:
                logo_flowable = None

        if not logo_flowable:
            logo_flowable = CeramicPDFGenerator.create_minimalist_logo_mark()
            logo_sz = 36

        comp_paras = [
            Paragraph(f"<b>{setting.company_name}</b>", styles["comp_name"]),
            Paragraph(setting.tagline.upper() if setting.tagline else "", styles["comp_tag"]),
        ]
        if setting.gstin:
            comp_paras.append(Paragraph(f"<font color='#94A3B8'>GSTIN:</font> {setting.gstin} | <font color='#94A3B8'>State:</font> {setting.state}", styles["comp_tag"]))

        w_name = pdfmetrics.stringWidth(setting.company_name, "Helvetica-Bold", 13)
        w_tag = pdfmetrics.stringWidth(setting.tagline.upper() if setting.tagline else "", "Helvetica", 7)
        gst_text = f"GSTIN: {setting.gstin} | State: {setting.state}" if setting.gstin else ""
        w_gst = pdfmetrics.stringWidth(gst_text, "Helvetica", 7)
        text_col_w = max(w_name, w_tag, w_gst) + 6
        gap_w = 8
        logo_col_w = logo_sz + gap_w
        branding_w = logo_col_w + text_col_w

        right_branding_inner = Table([[logo_flowable, comp_paras]], colWidths=[logo_col_w, text_col_w])
        right_branding_inner.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        left_w = 547 - branding_w
        top_branding_table = Table([["", right_branding_inner]], colWidths=[left_w, branding_w])
        top_branding_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        left_title_box = [
            Paragraph(f"<b>{title_str}</b>", styles["report_h1"]),
            Spacer(1, 2),
            Paragraph(subtitle_str, styles["report_sub"]),
        ]

        right_meta_box = [
            Paragraph("<b>EXECUTIVE AUDIT</b>", styles["td_bold_right"]),
            Paragraph(f"<font color='#64748B'>Generated:</font> {datetime.now().strftime('%d %b %Y, %I:%M %p')}", styles["td_right"]),
        ]

        title_banner = Table([[left_title_box, right_meta_box]], colWidths=[367, 180])
        title_banner.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LINEBELOW', (0, 0), (-1, -1), 0.75, cls.BORDER_LIGHT),
        ]))

        return [top_branding_table, Spacer(1, 6), title_banner]

    @classmethod
    def _create_kpi_cards_table(cls, cards, styles):
        """Creates 4 equal-width KPI stat cards across 547 pt."""
        card_cells = []
        for label, val, sub, color_code in cards:
            c_p = [
                Paragraph(label.upper(), styles["kpi_label"]),
                Spacer(1, 2),
                Paragraph(f"<font color='{color_code}'><b>{val}</b></font>", styles["kpi_val"]),
                Spacer(1, 1),
                Paragraph(sub, styles["kpi_sub"]),
            ]
            card_cells.append(c_p)

        kpi_table = Table([card_cells], colWidths=[136.75, 136.75, 136.75, 136.75])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cls.BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return kpi_table

    @classmethod
    def _create_sign_off_table(cls, styles):
        """Creates executive audit sign-off block."""
        setting = CompanySetting.get_settings()
        mgr_title = setting.store_manager_title or "Store Manager"
        mgr_name = setting.store_manager_name or "Authorized Signatory"

        sign_data = [
            [
                Paragraph("<b>PREPARED & AUDITED BY</b><br/><br/><br/>________________________________________<br/>Executive System Audit Desk", styles["sign_lbl"]),
                Paragraph(f"<b>VERIFIED & APPROVED BY</b><br/><br/><br/>________________________________________<br/><b>{mgr_name}</b> ({mgr_title})", styles["sign_lbl"]),
            ]
        ]
        t = Table(sign_data, colWidths=[273.5, 273.5])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ]))
        return t

    # =========================================================================
    # 1. GENERATE DAILY REPORT PDF
    # =========================================================================
    @classmethod
    def generate_daily_report_pdf(cls, target_date: date = None, output_filepath: str = None) -> str:
        """Generates executive daily sales, quotes, and payment collections PDF report."""
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except Exception:
                target_date = date.today()

        data = ReportService.get_daily_report_data(target_date)

        if not output_filepath:
            date_str = target_date.strftime("%Y%m%d")
            filename = f"Daily_Sales_Report_{date_str}_{datetime.now().strftime('%H%M%S')}.pdf"
            output_filepath = str(OUTPUT_PDF_DIR / filename)

        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=26,
            bottomMargin=42,
        )

        styles = cls._get_styles()
        story = []

        # 1. Header
        date_display = target_date.strftime("%A, %d %B %Y")
        story.extend(cls._create_header_elements("DAILY SALES & AUDIT REPORT", f"Date: {date_display}", styles))
        story.append(Spacer(1, cls.SECTION_GAP))

        # 2. KPI Cards Row
        cards = [
            ("Quotations Created", str(data["total_quotes"]), f"{data['won_quotes_count']} Won / {data['open_quotes_count']} Open", "#1565C0"),
            ("Won Sales Revenue", f"Rs. {data['won_sales_val']:,.2f}", f"Gross: Rs. {data['total_gross']:,.0f}", "#059669"),
            ("Bank Realized Collections", f"Rs. {data['cleared_total']:,.2f}", f"{data['cleared_payments_count']} payments cleared", "#0D47A1"),
            ("Pending Tokens / Pipeline", f"Rs. {data['pipeline_val']:,.2f}", f"Unconfirmed proposals", "#D97706"),
        ]
        story.append(cls._create_kpi_cards_table(cards, styles))
        story.append(Spacer(1, cls.SECTION_GAP))

        # 3. Quotations Created Today Table
        story.append(Paragraph("<b><font color='#1565C0'>■</font> QUOTATIONS CREATED TODAY</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        q_cols = [22, 80, 105, 80, 50, 70, 70, 70]
        q_data = [[
            Paragraph("S.NO", styles["th"]),
            Paragraph("QUOTE #", styles["th"]),
            Paragraph("CUSTOMER", styles["th"]),
            Paragraph("SALES REP", styles["th"]),
            Paragraph("STATUS", styles["th"]),
            Paragraph("NET (Rs.)", styles["th"]),
            Paragraph("CLEARED (Rs.)", styles["th"]),
            Paragraph("BALANCE (Rs.)", styles["th"]),
        ]]

        if data["quotes"]:
            for idx, q in enumerate(data["quotes"], start=1):
                stat_col = "#059669" if q.status == Quotation.STATUS_WON else ("#1565C0" if q.status == Quotation.STATUS_OPEN else "#D97706")
                q_data.append([
                    Paragraph(str(idx), styles["td_center"]),
                    Paragraph(f"<b>{q.quotation_number}</b>", styles["td"]),
                    Paragraph(q.customer_name[:24], styles["td"]),
                    Paragraph(q.sales_person_name[:18], styles["td"]),
                    Paragraph(f"<font color='{stat_col}'><b>{q.status}</b></font>", styles["td_center"]),
                    Paragraph(f"Rs. {q.net_total:,.2f}", styles["td_right"]),
                    Paragraph(f"Rs. {q.get_cleared_payments():,.2f}", styles["td_right"]),
                    Paragraph(f"Rs. {q.get_outstanding_balance():,.2f}", styles["td_right"]),
                ])
            # Total row
            q_data.append([
                Paragraph("", styles["total_td"]),
                Paragraph("<b>TOTAL</b>", styles["total_td"]),
                Paragraph(f"{len(data['quotes'])} Quotes", styles["total_td"]),
                Paragraph("", styles["total_td"]),
                Paragraph("", styles["total_td"]),
                Paragraph(f"Rs. {data['total_net']:,.2f}", styles["total_td_right"]),
                Paragraph(f"Rs. {sum(q.get_cleared_payments() for q in data['quotes']):,.2f}", styles["total_td_right"]),
                Paragraph(f"Rs. {sum(q.get_outstanding_balance() for q in data['quotes']):,.2f}", styles["total_td_right"]),
            ])
        else:
            q_data.append([Paragraph("No quotations recorded on this date.", styles["td_center"])] * 8)

        t_quotes = Table(q_data, colWidths=q_cols)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
        ]
        if data["quotes"]:
            for r in range(1, len(data["quotes"]) + 1):
                if r % 2 == 0:
                    t_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
            t_style.append(('BACKGROUND', (0, -1), (-1, -1), cls.DARK_NAVY))
        t_quotes.setStyle(TableStyle(t_style))
        story.append(t_quotes)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 4. Payment Collections Table
        story.append(Paragraph("<b><font color='#1565C0'>■</font> PAYMENT COLLECTIONS REALIZED TODAY</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        p_cols = [22, 95, 85, 120, 85, 60, 80]
        p_data = [[
            Paragraph("S.NO", styles["th"]),
            Paragraph("RECEIPT / REF #", styles["th"]),
            Paragraph("QUOTE #", styles["th"]),
            Paragraph("CUSTOMER", styles["th"]),
            Paragraph("MODE", styles["th"]),
            Paragraph("STATUS", styles["th"]),
            Paragraph("AMOUNT (Rs.)", styles["th"]),
        ]]

        if data["payments"]:
            for idx, p in enumerate(data["payments"], start=1):
                stat_col = "#059669" if p.status == "Cleared" else "#D97706"
                p_data.append([
                    Paragraph(str(idx), styles["td_center"]),
                    Paragraph(f"<b>{p.reference_number or 'N/A'}</b>", styles["td"]),
                    Paragraph(p.quotation.quotation_number if p.quotation else "N/A", styles["td"]),
                    Paragraph((p.quotation.customer_name if p.quotation else "N/A")[:26], styles["td"]),
                    Paragraph(p.payment_mode, styles["td_center"]),
                    Paragraph(f"<font color='{stat_col}'><b>{p.status}</b></font>", styles["td_center"]),
                    Paragraph(f"Rs. {p.amount:,.2f}", styles["td_right"]),
                ])
            p_data.append([
                Paragraph("", styles["total_td"]),
                Paragraph("<b>TOTAL COLLECTIONS</b>", styles["total_td"]),
                Paragraph(f"{len(data['payments'])} Payments", styles["total_td"]),
                Paragraph("", styles["total_td"]),
                Paragraph("", styles["total_td"]),
                Paragraph("", styles["total_td"]),
                Paragraph(f"Rs. {data['cleared_total'] + data['pending_total']:,.2f}", styles["total_td_right"]),
            ])
        else:
            p_data.append([Paragraph("No payments received on this date.", styles["td_center"])] * 7)

        t_pay = Table(p_data, colWidths=p_cols)
        t_pay_style = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
        ]
        if data["payments"]:
            for r in range(1, len(data["payments"]) + 1):
                if r % 2 == 0:
                    t_pay_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
            t_pay_style.append(('BACKGROUND', (0, -1), (-1, -1), cls.DARK_NAVY))
        t_pay.setStyle(TableStyle(t_pay_style))
        story.append(t_pay)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 5. Sales Representatives Daily Activity
        story.append(Paragraph("<b><font color='#1565C0'>■</font> SALES REPRESENTATIVE DAILY ACTIVITY & TARGETS</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        rep_cols = [22, 110, 75, 75, 75, 70, 55, 65]
        rep_data = [[
            Paragraph("S.NO", styles["th"]),
            Paragraph("SALES EXECUTIVE", styles["th"]),
            Paragraph("ROLE", styles["th"]),
            Paragraph("QUOTES MADE", styles["th"]),
            Paragraph("WON SALES (Rs.)", styles["th"]),
            Paragraph("PRO-RATA TARGET", styles["th"]),
            Paragraph("% ACHIEVED", styles["th"]),
            Paragraph("STATUS", styles["th"]),
        ]]

        for idx, rep in enumerate(data["team_perf"], start=1):
            stat_col = "#059669" if rep["percentage"] >= 100 else ("#1565C0" if rep["percentage"] >= 50 else "#64748B")
            rep_data.append([
                Paragraph(str(idx), styles["td_center"]),
                Paragraph(f"<b>{rep['name']}</b>", styles["td"]),
                Paragraph(rep["role"], styles["td"]),
                Paragraph(str(rep["quotes_count"]), styles["td_center"]),
                Paragraph(f"Rs. {rep['achieved']:,.2f}", styles["td_right"]),
                Paragraph(f"Rs. {rep['daily_target']:,.2f}", styles["td_right"]),
                Paragraph(f"<b>{rep['percentage']:.1f}%</b>", styles["td_center"]),
                Paragraph(f"<font color='{stat_col}'><b>{'Achieved' if rep['percentage'] >= 100 else 'In Progress'}</b></font>", styles["td_center"]),
            ])

        t_rep = Table(rep_data, colWidths=rep_cols)
        t_rep_style = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
        ]
        for r in range(1, len(data["team_perf"]) + 1):
            if r % 2 == 0:
                t_rep_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
        t_rep.setStyle(TableStyle(t_rep_style))
        story.append(t_rep)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 6. Audit Sign-off
        story.append(KeepTogether([cls._create_sign_off_table(styles)]))

        doc.build(story, canvasmaker=NumberedCanvas)
        return output_filepath

    # =========================================================================
    # 2. GENERATE MONTHLY REPORT PDF
    # =========================================================================
    @classmethod
    def generate_monthly_report_pdf(cls, year: int = None, month: int = None, output_filepath: str = None) -> str:
        """Generates executive monthly performance, sales leaderboard, and revenue audit PDF."""
        data = ReportService.get_monthly_report_data(year, month)

        if not output_filepath:
            date_str = f"{data['year']}_{data['month']:02d}"
            filename = f"Monthly_Performance_Report_{date_str}_{datetime.now().strftime('%H%M%S')}.pdf"
            output_filepath = str(OUTPUT_PDF_DIR / filename)

        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=26,
            bottomMargin=42,
        )

        styles = cls._get_styles()
        story = []

        # 1. Header
        story.extend(cls._create_header_elements(
            "MONTHLY PERFORMANCE & REVENUE AUDIT",
            f"Period: {data['month_name']} ({data['start_date'].strftime('%d %b %Y')} - {data['end_date'].strftime('%d %b %Y')})",
            styles
        ))
        story.append(Spacer(1, cls.SECTION_GAP))

        # 2. KPI Cards Row
        cards = [
            ("Monthly Won Revenue", f"Rs. {data['won_sales_val']:,.2f}", f"{data['won_quotes_count']} closed contracts", "#059669"),
            ("Team Target Allocated", f"Rs. {data['team_total_target']:,.2f}", f"Balance: Rs. {data['team_balance']:,.0f}", "#1565C0"),
            ("Target Achievement", f"{data['team_percentage']:.1f}%", f"Conversion: {data['conversion_rate']:.1f}%", "#0D47A1"),
            ("Realized Collections", f"Rs. {data['cleared_total']:,.2f}", f"Outstanding: Rs. {data['total_outstanding']:,.0f}", "#D97706"),
        ]
        story.append(cls._create_kpi_cards_table(cards, styles))
        story.append(Spacer(1, cls.SECTION_GAP))

        # 3. Sales Team Target vs Achievement Leaderboard
        story.append(Paragraph("<b><font color='#1565C0'>■</font> SALES REPRESENTATIVE TARGET VS ACHIEVEMENT LEADERBOARD</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        lead_cols = [22, 110, 75, 75, 75, 70, 55, 65]
        lead_data = [[
            Paragraph("S.NO", styles["th"]),
            Paragraph("SALES EXECUTIVE", styles["th"]),
            Paragraph("ROLE", styles["th"]),
            Paragraph("TARGET (Rs.)", styles["th"]),
            Paragraph("ACHIEVED (Rs.)", styles["th"]),
            Paragraph("BALANCE (Rs.)", styles["th"]),
            Paragraph("% ACHIEVED", styles["th"]),
            Paragraph("STATUS", styles["th"]),
        ]]

        for idx, rep in enumerate(data["team_individuals"], start=1):
            stat_col = "#059669" if rep["percentage"] >= 100 else ("#1565C0" if rep["percentage"] >= 50 else "#DC2626")
            lead_data.append([
                Paragraph(str(idx), styles["td_center"]),
                Paragraph(f"<b>{rep['name']}</b>", styles["td"]),
                Paragraph(rep["role"], styles["td"]),
                Paragraph(f"Rs. {rep['target']:,.2f}", styles["td_right"]),
                Paragraph(f"Rs. {rep['achieved']:,.2f}", styles["td_right"]),
                Paragraph(f"Rs. {rep['balance']:,.2f}", styles["td_right"]),
                Paragraph(f"<b>{rep['percentage']:.1f}%</b>", styles["td_center"]),
                Paragraph(f"<font color='{stat_col}'><b>{rep['status']}</b></font>", styles["td_center"]),
            ])

        lead_data.append([
            Paragraph("", styles["total_td"]),
            Paragraph("<b>TEAM AGGREGATE</b>", styles["total_td"]),
            Paragraph("Full Team", styles["total_td"]),
            Paragraph(f"Rs. {data['team_total_target']:,.2f}", styles["total_td_right"]),
            Paragraph(f"Rs. {data['team_total_achieved']:,.2f}", styles["total_td_right"]),
            Paragraph(f"Rs. {data['team_balance']:,.2f}", styles["total_td_right"]),
            Paragraph(f"<b>{data['team_percentage']:.1f}%</b>", styles["total_td"]),
            Paragraph("Team Total", styles["total_td"]),
        ])

        t_lead = Table(lead_data, colWidths=lead_cols)
        t_lead_style = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BACKGROUND', (0, -1), (-1, -1), cls.DARK_NAVY),
        ]
        for r in range(1, len(data["team_individuals"]) + 1):
            if r % 2 == 0:
                t_lead_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
        t_lead.setStyle(TableStyle(t_lead_style))
        story.append(t_lead)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 4. Pipeline Conversion & Status Breakdown
        story.append(Paragraph("<b><font color='#1565C0'>■</font> QUOTATION STATUS BREAKDOWN & CONVERSION VELOCITY</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        st_cols = [110, 55, 82, 150, 150]
        total_q = max(1, data["total_quotes"])
        st_data = [
            [
                Paragraph("STATUS CATEGORY", styles["th"]),
                Paragraph("COUNT", styles["th"]),
                Paragraph("PIPELINE %", styles["th"]),
                Paragraph("GROSS VALUE (Rs.)", styles["th"]),
                Paragraph("NET VALUE (Rs.)", styles["th"]),
            ],
            [
                Paragraph("<font color='#059669'>● <b>Won (Closed Contracts)</b></font>", styles["td"]),
                Paragraph(str(data["won_quotes_count"]), styles["td_center"]),
                Paragraph(f"{data['won_quotes_count'] / total_q * 100:.1f}%", styles["td_center"]),
                Paragraph(f"Rs. {sum(q.gross_total for q in data['quotes'] if q.status == Quotation.STATUS_WON):,.2f}", styles["td_right"]),
                Paragraph(f"<b>Rs. {data['won_sales_val']:,.2f}</b>", styles["td_right"]),
            ],
            [
                Paragraph("<font color='#1565C0'>● <b>In-Review (Manager Approval)</b></font>", styles["td"]),
                Paragraph(str(data["in_review_quotes_count"]), styles["td_center"]),
                Paragraph(f"{data['in_review_quotes_count'] / total_q * 100:.1f}%", styles["td_center"]),
                Paragraph(f"Rs. {sum(q.gross_total for q in data['quotes'] if q.status == Quotation.STATUS_IN_REVIEW):,.2f}", styles["td_right"]),
                Paragraph(f"Rs. {sum(q.net_total for q in data['quotes'] if q.status == Quotation.STATUS_IN_REVIEW):,.2f}", styles["td_right"]),
            ],
            [
                Paragraph("<font color='#42A5F5'>● <b>Open (Active Proposals)</b></font>", styles["td"]),
                Paragraph(str(data["open_quotes_count"]), styles["td_center"]),
                Paragraph(f"{data['open_quotes_count'] / total_q * 100:.1f}%", styles["td_center"]),
                Paragraph(f"Rs. {sum(q.gross_total for q in data['quotes'] if q.status == Quotation.STATUS_OPEN):,.2f}", styles["td_right"]),
                Paragraph(f"Rs. {sum(q.net_total for q in data['quotes'] if q.status == Quotation.STATUS_OPEN):,.2f}", styles["td_right"]),
            ],
            [
                Paragraph("<font color='#DC2626'>● <b>Lost / Cancelled</b></font>", styles["td"]),
                Paragraph(str(data["lost_quotes_count"]), styles["td_center"]),
                Paragraph(f"{data['lost_quotes_count'] / total_q * 100:.1f}%", styles["td_center"]),
                Paragraph(f"Rs. {sum(q.gross_total for q in data['quotes'] if q.status == Quotation.STATUS_LOST):,.2f}", styles["td_right"]),
                Paragraph(f"Rs. {sum(q.net_total for q in data['quotes'] if q.status == Quotation.STATUS_LOST):,.2f}", styles["td_right"]),
            ],
        ]

        t_status = Table(st_data, colWidths=st_cols)
        t_status.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BACKGROUND', (0, 2), (-1, 2), cls.BG_LIGHT),
            ('BACKGROUND', (0, 4), (-1, 4), cls.BG_LIGHT),
        ]))
        story.append(t_status)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 5. Top Won Contracts of the Month
        story.append(Paragraph("<b><font color='#1565C0'>■</font> TOP WON CONTRACTS & CLOSED ORDERS</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        won_quotes = [q for q in data["quotes"] if q.status == Quotation.STATUS_WON]
        wq_cols = [22, 80, 105, 80, 70, 70, 60, 60]
        wq_data = [[
            Paragraph("S.NO", styles["th"]),
            Paragraph("QUOTE #", styles["th"]),
            Paragraph("CUSTOMER", styles["th"]),
            Paragraph("SALES REP", styles["th"]),
            Paragraph("NET (Rs.)", styles["th"]),
            Paragraph("CLEARED (Rs.)", styles["th"]),
            Paragraph("BALANCE (Rs.)", styles["th"]),
            Paragraph("STATUS", styles["th"]),
        ]]

        if won_quotes:
            for idx, q in enumerate(won_quotes[:8], start=1):
                p_stat = q.get_payment_status()
                p_col = "#059669" if p_stat == "Fully Paid" else ("#D97706" if p_stat == "Partially Paid" else "#DC2626")
                wq_data.append([
                    Paragraph(str(idx), styles["td_center"]),
                    Paragraph(f"<b>{q.quotation_number}</b>", styles["td"]),
                    Paragraph(q.customer_name[:24], styles["td"]),
                    Paragraph(q.sales_person_name[:18], styles["td"]),
                    Paragraph(f"Rs. {q.net_total:,.2f}", styles["td_right"]),
                    Paragraph(f"Rs. {q.get_cleared_payments():,.2f}", styles["td_right"]),
                    Paragraph(f"Rs. {q.get_outstanding_balance():,.2f}", styles["td_right"]),
                    Paragraph(f"<font color='{p_col}'><b>{p_stat}</b></font>", styles["td_center"]),
                ])
        else:
            wq_data.append([Paragraph("No closed contracts in this month.", styles["td_center"])] * 8)

        t_won = Table(wq_data, colWidths=wq_cols)
        t_won_style = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
        ]
        if won_quotes:
            for r in range(1, len(won_quotes[:8]) + 1):
                if r % 2 == 0:
                    t_won_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
        t_won.setStyle(TableStyle(t_won_style))
        story.append(t_won)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 6. Audit Sign-off
        story.append(KeepTogether([cls._create_sign_off_table(styles)]))

        doc.build(story, canvasmaker=NumberedCanvas)
        return output_filepath

    # =========================================================================
    # 3. GENERATE TARGET ARCHIVE REPORT PDF
    # =========================================================================
    @classmethod
    def generate_target_archive_pdf(cls, output_filepath: str = None) -> str:
        """Generates historical target vs achievement performance archive audit PDF."""
        data = ReportService.get_target_archive_data()

        if not output_filepath:
            filename = f"Target_Archive_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_filepath = str(OUTPUT_PDF_DIR / filename)

        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=26,
            bottomMargin=42,
        )

        styles = cls._get_styles()
        story = []

        # 1. Header
        story.extend(cls._create_header_elements(
            "SALES TARGET & REVENUE ARCHIVE AUDIT",
            f"Historical Performance Tracking across {data['total_periods_count']} Audit Periods",
            styles
        ))
        story.append(Spacer(1, cls.SECTION_GAP))

        # 2. Lifetime Archive KPI Summary Cards
        cards = [
            ("Cumulative Target Allocated", f"Rs. {data['total_archive_target']:,.0f}", f"Across {data['total_periods_count']} Periods", "#1565C0"),
            ("Total Won Sales Achieved", f"Rs. {data['total_archive_achieved']:,.0f}", f"Variance: Rs. {data['total_archive_variance']:,.0f}", "#059669"),
            ("Lifetime Achievement %", f"{data['overall_percentage']:.1f}%", f"Overall Company Rate", "#0D47A1"),
            ("Realized Bank Collections", f"Rs. {data['total_archive_collections']:,.0f}", f"Realized Cash Flow", "#D97706"),
        ]
        story.append(cls._create_kpi_cards_table(cards, styles))
        story.append(Spacer(1, cls.SECTION_GAP))

        # 3. Period-by-Period Archive Breakdown
        arch_cols = [20, 105, 65, 65, 65, 62, 45, 45, 75]

        for period in data["periods"]:
            period_title = f"<b><font color='#1565C0'>■</font> ARCHIVE AUDIT: {period['period_label'].upper()}</b> (Target: Rs. {period['total_target']:,.0f} | Won: Rs. {period['total_achieved']:,.0f} | {period['percentage']:.1f}%)"
            story.append(Paragraph(period_title, styles["sec_title"]))
            story.append(Spacer(1, 4))

            p_table_data = [[
                Paragraph("S.NO", styles["th"]),
                Paragraph("SALES EXECUTIVE", styles["th"]),
                Paragraph("ROLE", styles["th"]),
                Paragraph("TARGET", styles["th"]),
                Paragraph("ACHIEVED", styles["th"]),
                Paragraph("VARIANCE", styles["th"]),
                Paragraph("%", styles["th"]),
                Paragraph("DEALS", styles["th"]),
                Paragraph("REALIZED (Rs.)", styles["th"]),
            ]]

            for idx, rep in enumerate(period["representatives"], start=1):
                v_col = "#059669" if rep["variance"] >= 0 else "#DC2626"
                p_table_data.append([
                    Paragraph(str(idx), styles["td_center"]),
                    Paragraph(f"<b>{rep['name']}</b>", styles["td"]),
                    Paragraph(rep["role"], styles["td"]),
                    Paragraph(f"Rs. {rep['target']:,.0f}", styles["td_right"]),
                    Paragraph(f"Rs. {rep['achieved']:,.0f}", styles["td_right"]),
                    Paragraph(f"<font color='{v_col}'>Rs. {rep['variance']:,.0f}</font>", styles["td_right"]),
                    Paragraph(f"<b>{rep['percentage']:.1f}%</b>", styles["td_center"]),
                    Paragraph(str(rep["won_count"]), styles["td_center"]),
                    Paragraph(f"Rs. {rep['collections']:,.0f}", styles["td_right"]),
                ])

            p_table_data.append([
                Paragraph("", styles["total_td"]),
                Paragraph(f"<b>TOTAL {period['period_label'].upper()}</b>", styles["total_td"]),
                Paragraph("Team", styles["total_td"]),
                Paragraph(f"Rs. {period['total_target']:,.0f}", styles["total_td_right"]),
                Paragraph(f"Rs. {period['total_achieved']:,.0f}", styles["total_td_right"]),
                Paragraph(f"Rs. {period['variance']:,.0f}", styles["total_td_right"]),
                Paragraph(f"<b>{period['percentage']:.1f}%</b>", styles["total_td"]),
                Paragraph(str(period["won_count"]), styles["total_td"]),
                Paragraph(f"Rs. {period['collections']:,.0f}", styles["total_td_right"]),
            ])

            t_period = Table(p_table_data, colWidths=arch_cols)
            t_period_style = [
                ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
                ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
                ('BACKGROUND', (0, -1), (-1, -1), cls.DARK_NAVY),
            ]
            for r in range(1, len(period["representatives"]) + 1):
                if r % 2 == 0:
                    t_period_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
            t_period.setStyle(TableStyle(t_period_style))
            story.append(t_period)
            story.append(Spacer(1, cls.SECTION_GAP))

        # 4. Cumulative Career / YTD Archive Summary
        story.append(Paragraph("<b><font color='#1565C0'>■</font> CUMULATIVE SALES REPRESENTATIVE ARCHIVE SUMMARY</b>", styles["sec_title"]))
        story.append(Spacer(1, 4))

        cum_cols = [20, 105, 65, 65, 65, 62, 45, 45, 75]
        cum_data = [[
            Paragraph("S.NO", styles["th"]),
            Paragraph("SALES EXECUTIVE", styles["th"]),
            Paragraph("ROLE", styles["th"]),
            Paragraph("CUM. TARGET", styles["th"]),
            Paragraph("WON SALES", styles["th"]),
            Paragraph("NET VARIANCE", styles["th"]),
            Paragraph("OVERALL %", styles["th"]),
            Paragraph("WON DEALS", styles["th"]),
            Paragraph("COLLECTIONS", styles["th"]),
        ]]

        for idx, rep in enumerate(data["cumulative"], start=1):
            v_col = "#059669" if rep["variance"] >= 0 else "#DC2626"
            cum_data.append([
                Paragraph(str(idx), styles["td_center"]),
                Paragraph(f"<b>{rep['name']}</b>", styles["td"]),
                Paragraph(rep["role"], styles["td"]),
                Paragraph(f"Rs. {rep['total_target']:,.0f}", styles["td_right"]),
                Paragraph(f"Rs. {rep['total_achieved']:,.0f}", styles["td_right"]),
                Paragraph(f"<font color='{v_col}'>Rs. {rep['variance']:,.0f}</font>", styles["td_right"]),
                Paragraph(f"<b>{rep['percentage']:.1f}%</b>", styles["td_center"]),
                Paragraph(str(rep["won_count"]), styles["td_center"]),
                Paragraph(f"Rs. {rep['collections']:,.0f}", styles["td_right"]),
            ])

        cum_data.append([
            Paragraph("", styles["total_td"]),
            Paragraph("<b>OVERALL COMPANY TOTAL</b>", styles["total_td"]),
            Paragraph("All Personnel", styles["total_td"]),
            Paragraph(f"Rs. {data['total_archive_target']:,.0f}", styles["total_td_right"]),
            Paragraph(f"Rs. {data['total_archive_achieved']:,.0f}", styles["total_td_right"]),
            Paragraph(f"Rs. {data['total_archive_variance']:,.0f}", styles["total_td_right"]),
            Paragraph(f"<b>{data['overall_percentage']:.1f}%</b>", styles["total_td"]),
            Paragraph(str(sum(r["won_count"] for r in data["cumulative"])), styles["total_td"]),
            Paragraph(f"Rs. {data['total_archive_collections']:,.0f}", styles["total_td_right"]),
        ])

        t_cum = Table(cum_data, colWidths=cum_cols)
        t_cum_style = [
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_LIGHT),
            ('BACKGROUND', (0, -1), (-1, -1), cls.DARK_NAVY),
        ]
        for r in range(1, len(data["cumulative"]) + 1):
            if r % 2 == 0:
                t_cum_style.append(('BACKGROUND', (0, r), (-1, r), cls.BG_LIGHT))
        t_cum.setStyle(TableStyle(t_cum_style))
        story.append(t_cum)
        story.append(Spacer(1, cls.SECTION_GAP))

        # 5. Audit Sign-off
        story.append(KeepTogether([cls._create_sign_off_table(styles)]))

        doc.build(story, canvasmaker=NumberedCanvas)
        return output_filepath
