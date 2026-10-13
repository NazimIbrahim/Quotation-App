"""
Reports & Analytics View: Deep analytics report with Daily, Weekly, Monthly
and All-Time filters, conversion ratios, and receivables breakdown.
"""
import csv
import os
import tkinter.messagebox as msgbox
from datetime import date, datetime
from pathlib import Path
import customtkinter as ctk

from app.ui.theme import Theme
from app.services.report_service import ReportService
from app.services.report_pdf_service import ReportPDFGenerator
from app.database.models import Quotation, Payment


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.timeframe = "Monthly"

        self.build_ui()
        self.refresh_report()

    def build_ui(self):
        # 1. Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Executive Reports & Analytics",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Periodic sales audits, realization velocities & pipeline conversions",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right")

        # Timeframe Filter Buttons
        self.timeframe_segment = ctk.CTkSegmentedButton(
            btn_box,
            values=["Daily", "Weekly", "Monthly", "All-Time"],
            command=self.on_filter_changed,
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            height=34,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        self.timeframe_segment.set("Monthly")
        self.timeframe_segment.pack(side="left", padx=8)

        export_pdf_btn = ctk.CTkButton(
            btn_box,
            text="Export PDF 📄",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            command=self.export_active_pdf,
            height=36
        )
        export_pdf_btn.pack(side="left", padx=(0, 6))

        export_csv_btn = ctk.CTkButton(
            btn_box,
            text="Export CSV 📥",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SECONDARY_BORDER,
            command=self.export_csv,
            height=36
        )
        export_csv_btn.pack(side="left")

        # Scrollable container
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 1.5 Executive Report Exports Toolbar
        export_toolbar = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        export_toolbar.pack(fill="x", pady=(0, 16))

        tb_box = ctk.CTkFrame(export_toolbar, fg_color="transparent")
        tb_box.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            tb_box,
            text="📑 Executive Exports:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            tb_box,
            text="📄 Daily Report (PDF)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            command=self.export_daily_pdf,
            height=30
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            tb_box,
            text="📄 Monthly Report (PDF)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=(Theme.BLACK, Theme.PAPER),
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            command=self.export_monthly_pdf,
            height=30
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            tb_box,
            text="🎯 Target Archive Report (PDF)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            command=self.export_target_archive_pdf,
            height=30
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            tb_box,
            text="📊 Target Archive (CSV)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            command=self.export_target_archive_csv,
            height=30
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            tb_box,
            text="⚙️ Custom Date/Month...",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            fg_color="transparent",
            text_color=Theme.PRIMARY,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=1,
            border_color=Theme.BTN_PRIMARY_BORDER,
            command=self.open_export_modal,
            height=30
        ).pack(side="right")

        # 2. Key Metrics Card
        self.metrics_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        self.metrics_card.pack(fill="x", pady=(0, 16))

        m_header = ctk.CTkFrame(self.metrics_card, fg_color="transparent")
        m_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            m_header,
            text="📊 Sales Performance & Conversion Metrics",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left")

        self.date_range_lbl = ctk.CTkLabel(
            m_header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#615D56", "#A8A297")
        )
        self.date_range_lbl.pack(side="right")

        self.metrics_grid = ctk.CTkFrame(self.metrics_card, fg_color="transparent")
        self.metrics_grid.pack(fill="x", padx=16, pady=(0, 16))
        self.metrics_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # 3. Middle Section: Two Columns (Left: Target Progress, Right: Payment Clearance)
        mid_row = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        mid_row.pack(fill="x", pady=(0, 16))
        mid_row.grid_columnconfigure(0, weight=3)
        mid_row.grid_columnconfigure(1, weight=2)

        # Team Performance Card
        self.team_card = ctk.CTkFrame(
            mid_row,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        self.team_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            self.team_card,
            text="🎯 Sales Representative Progress in Timeframe",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w", padx=16, pady=(14, 10))

        self.team_progress_container = ctk.CTkFrame(self.team_card, fg_color="transparent")
        self.team_progress_container.pack(fill="x", padx=16, pady=(0, 16))

        # Financial Clearance Card
        self.clearance_card = ctk.CTkFrame(
            mid_row,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        self.clearance_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            self.clearance_card,
            text="💳 Payment Realization Breakdown",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w", padx=16, pady=(14, 10))

        self.clearance_container = ctk.CTkFrame(self.clearance_card, fg_color="transparent")
        self.clearance_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # 4. Status Distribution Breakdown Table
        self.status_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        self.status_card.pack(fill="x")

        ctk.CTkLabel(
            self.status_card,
            text="📑 Quotations Status Breakdown (Selected Period)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w", padx=16, pady=(14, 8))

        self.status_table_container = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.status_table_container.pack(fill="x", padx=16, pady=(0, 16))

    def on_filter_changed(self, val):
        self.timeframe = val
        self.refresh_report()

    def refresh_report(self):
        m = ReportService.get_dashboard_metrics(self.timeframe)
        p = ReportService.get_salesperson_performances(self.timeframe)

        self.date_range_lbl.configure(
            text=f"Period: {m['start_date'].strftime('%d %b %Y')} to {m['end_date'].strftime('%d %b %Y')}"
        )

        # 1. Populate Metrics Grid
        for widget in self.metrics_grid.winfo_children():
            widget.destroy()

        cells = [
            ("TOTAL QUOTATIONS", str(m["total_quotes"]), "Generated in period", Theme.PRIMARY),
            ("WON SALES VALUE", f"₹ {m['won_sales_value']:,.2f}", f"{m['won_quotes']} closed deals", Theme.SUCCESS),
            ("PIPELINE PIPELINE", f"₹ {m['pipeline_value']:,.2f}", f"{m['open_quotes']} open / {m['in_review_quotes']} in-review", Theme.INFO),
            ("CONVERSION RATE", f"{m['conversion_rate']}%", "Won / Total Quotes", Theme.ACCENT_GOLD),
        ]

        for idx, (title, val, sub, col) in enumerate(cells):
            f = ctk.CTkFrame(self.metrics_grid, fg_color=(Theme.PAPER, "#1E1C1A"), corner_radius=8)
            f.grid(row=0, column=idx, padx=6, pady=4, sticky="nsew")

            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color=("#615D56", "#A8A297")).pack(anchor="w", padx=12, pady=(10, 2))
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=col).pack(anchor="w", padx=12, pady=(0, 2))
            ctk.CTkLabel(f, text=sub, font=ctk.CTkFont(size=10), text_color=("#615D56", "#A8A297")).pack(anchor="w", padx=12, pady=(0, 10))

        # 2. Populate Sales Team Progress
        for widget in self.team_progress_container.winfo_children():
            widget.destroy()

        for person in p["individuals"]:
            pf = ctk.CTkFrame(self.team_progress_container, fg_color=(Theme.PAPER, "#1E1C1A"), corner_radius=8)
            pf.pack(fill="x", pady=3)

            r1 = ctk.CTkFrame(pf, fg_color="transparent")
            r1.pack(fill="x", padx=12, pady=(6, 2))

            ctk.CTkLabel(r1, text=f"{person['name']} ({person['role']})", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
            ctk.CTkLabel(r1, text=f"₹ {person['achieved']:,.0f} / ₹ {person['target']:,.0f}", font=ctk.CTkFont(size=11)).pack(side="right")

            r2 = ctk.CTkFrame(pf, fg_color="transparent")
            r2.pack(fill="x", padx=12, pady=(2, 6))

            bar_col = Theme.SUCCESS if person["percentage"] >= 100 else Theme.PRIMARY
            bar = ctk.CTkProgressBar(r2, height=8, corner_radius=4, progress_color=bar_col)
            bar.set(min(1.0, person["percentage"] / 100.0))
            bar.pack(side="left", fill="x", expand=True, padx=(0, 8))

            ctk.CTkLabel(r2, text=f"{person['percentage']}%", font=ctk.CTkFont(size=10, weight="bold"), text_color=bar_col).pack(side="right")

        # 3. Populate Clearance Breakdown
        for widget in self.clearance_container.winfo_children():
            widget.destroy()

        c_box = ctk.CTkFrame(self.clearance_container, fg_color=(Theme.PAPER, "#1E1C1A"), corner_radius=8)
        c_box.pack(fill="both", expand=True, pady=2)

        c_rows = [
            ("Realized Bank Collections:", f"₹ {m['cleared_payments']:,.2f}", Theme.SUCCESS),
            ("Uncleared Cheques / UPI Tokens:", f"₹ {m['pending_payments']:,.2f}", Theme.WARNING),
            ("Total Outstanding Balance:", f"₹ {m['total_outstanding']:,.2f}", Theme.DANGER),
        ]

        for lbl, val, col in c_rows:
            r = ctk.CTkFrame(c_box, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=8)
            ctk.CTkLabel(r, text=lbl, font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(r, text=val, font=ctk.CTkFont(size=12, weight="bold"), text_color=col).pack(side="right")

        # 4. Status Distribution Breakdown Table
        for widget in self.status_table_container.winfo_children():
            widget.destroy()

        status_grid = ctk.CTkFrame(self.status_table_container, fg_color=(Theme.STONE, "#242220"), corner_radius=10, height=36)
        status_grid.pack(fill="x", pady=(0, 4))
        weights = [3, 1, 2, 5]
        for idx, w in enumerate(weights):
            status_grid.grid_columnconfigure(idx, weight=w, uniform="status_breakdown")

        headers = ["STATUS CATEGORY", "COUNT", "PERCENTAGE", "CATEGORY DEFINITION"]
        for idx, h in enumerate(headers):
            ctk.CTkLabel(
                status_grid,
                text=h,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER),
                anchor="w"
            ).grid(row=0, column=idx, padx=10, pady=8, sticky="w")

        total_q = max(1, m["total_quotes"])
        breakdown_rows = [
            ("Won (Closed)", m["won_quotes"], round(m["won_quotes"] / total_q * 100, 1), "Confirmed deal & material delivery", Theme.SUCCESS),
            ("In-Review", m["in_review_quotes"], round(m["in_review_quotes"] / total_q * 100, 1), "Awaiting manager discount approval", Theme.INFO),
            ("Open", m["open_quotes"], round(m["open_quotes"] / total_q * 100, 1), "Active proposal presented to client", Theme.PRIMARY),
            ("Lost", m["lost_quotes"], round(m["lost_quotes"] / total_q * 100, 1), "Cancelled or rejected by client", Theme.DANGER),
        ]

        for r_idx, (s_name, count, pct, defn, color) in enumerate(breakdown_rows, start=1):
            rf = ctk.CTkFrame(self.status_table_container, fg_color=("#FAF8F5", "#181615"), corner_radius=8)
            rf.pack(fill="x", pady=2)
            for idx, w in enumerate(weights):
                rf.grid_columnconfigure(idx, weight=w, uniform="status_breakdown")

            ctk.CTkLabel(rf, text=f"● {s_name}", font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"), text_color=color, anchor="w").grid(row=0, column=0, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(rf, text=str(count), font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"), anchor="w").grid(row=0, column=1, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(rf, text=f"{pct}%", font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11), anchor="w").grid(row=0, column=2, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(rf, text=defn, font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10), text_color=("#615D56", "#A8A297"), anchor="w").grid(row=0, column=3, padx=10, pady=6, sticky="w")

    def export_csv(self):
        try:
            start_date, end_date = ReportService.get_timeframe_dates(self.timeframe)
            quotes = list(
                Quotation.select().where(
                    (Quotation.quotation_date >= start_date) &
                    (Quotation.quotation_date <= end_date)
                ).order_by(Quotation.quotation_date.desc())
            )

            csv_path = Path("sales_report_export.csv").resolve()
            with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Quotation No", "Date", "Customer", "Contact", "Sales Person", "Gross Total", "Round Off", "Net Total", "Status", "Cleared Paid", "Outstanding Balance"])
                for q in quotes:
                    writer.writerow([
                        q.quotation_number,
                        q.quotation_date,
                        q.customer_name,
                        q.customer_phone,
                        q.sales_person_name,
                        q.gross_total,
                        q.round_off,
                        q.net_total,
                        q.status,
                        q.get_cleared_payments(),
                        q.get_outstanding_balance()
                    ])

            msgbox.showinfo("Export Successful", f"Sales Report successfully exported to:\n{csv_path}")
            try:
                os.startfile(csv_path)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Error", str(e))

    def export_active_pdf(self):
        """Exports PDF matching the currently selected timeframe."""
        if self.timeframe == "Daily":
            self.export_daily_pdf()
        else:
            self.export_monthly_pdf()

    def export_daily_pdf(self, target_date: date = None):
        """Generates and opens the Daily Sales & Collections PDF Report."""
        try:
            if target_date is None:
                start_date, _ = ReportService.get_timeframe_dates(self.timeframe)
                target_date = start_date if self.timeframe == "Daily" else date.today()

            out_pdf = ReportPDFGenerator.generate_daily_report_pdf(target_date)
            msgbox.showinfo("Export Successful", f"Daily Sales Report PDF successfully generated:\n{out_pdf}")
            try:
                os.startfile(out_pdf)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Error", f"Failed to generate Daily Report PDF:\n{str(e)}")

    def export_monthly_pdf(self, year: int = None, month: int = None):
        """Generates and opens the Monthly Performance & Revenue PDF Report."""
        try:
            today = date.today()
            if year is None:
                year = today.year
            if month is None:
                month = today.month

            out_pdf = ReportPDFGenerator.generate_monthly_report_pdf(year, month)
            msgbox.showinfo("Export Successful", f"Monthly Performance Report PDF successfully generated:\n{out_pdf}")
            try:
                os.startfile(out_pdf)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Error", f"Failed to generate Monthly Report PDF:\n{str(e)}")

    def export_target_archive_pdf(self):
        """Generates and opens the historical Target vs. Achievement Archive PDF Report."""
        try:
            out_pdf = ReportPDFGenerator.generate_target_archive_pdf()
            msgbox.showinfo("Export Successful", f"Sales Target Archive Report PDF successfully generated:\n{out_pdf}")
            try:
                os.startfile(out_pdf)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Error", f"Failed to generate Target Archive PDF:\n{str(e)}")

    def export_target_archive_csv(self):
        """Generates and opens the historical Target vs. Achievement Archive CSV Report."""
        try:
            out_csv = ReportService.export_target_archive_csv()
            msgbox.showinfo("Export Successful", f"Sales Target Archive Report CSV successfully generated:\n{out_csv}")
            try:
                os.startfile(out_csv)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Error", f"Failed to generate Target Archive CSV:\n{str(e)}")

    def open_export_modal(self):
        """Opens interactive modal to configure and export customized Daily, Monthly, or Archive reports."""
        modal = ctk.CTkToplevel(self)
        modal.title("Export Executive Reports")
        modal.geometry("520x460")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        # Modal Header
        header_f = ctk.CTkFrame(modal, fg_color=Theme.PRIMARY, corner_radius=0, height=64)
        header_f.pack(fill="x")
        header_f.pack_propagate(False)

        ctk.CTkLabel(
            header_f,
            text="📑 Executive Report Export Hub",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold"),
            text_color="white"
        ).pack(anchor="w", padx=20, pady=(12, 2))

        ctk.CTkLabel(
            header_f,
            text="Generate printable minimalist PDFs or CSV spreadsheets",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color="#E0F2FE"
        ).pack(anchor="w", padx=20)

        body_f = ctk.CTkFrame(modal, fg_color="transparent")
        body_f.pack(fill="both", expand=True, padx=24, pady=16)

        # 1. Report Type Selection
        ctk.CTkLabel(
            body_f,
            text="Select Report Type:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        report_type_var = ctk.StringVar(value="Monthly Performance & Revenue Audit")
        report_dropdown = ctk.CTkOptionMenu(
            body_f,
            values=[
                "Daily Sales & Collections Audit",
                "Monthly Performance & Revenue Audit",
                "Sales Target vs. Achievement Archive",
            ],
            variable=report_type_var,
            width=470,
            height=34,
            corner_radius=Theme.RADIUS_INPUT
        )
        report_dropdown.pack(fill="x", pady=(0, 14))

        # 2. Dynamic Scope Container
        scope_frame = ctk.CTkFrame(
            body_f,
            fg_color=("#FFFFFF", "#201E1C"),
            corner_radius=Theme.RADIUS_CARD,
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        scope_frame.pack(fill="x", pady=(0, 14), ipady=8)

        scope_lbl = ctk.CTkLabel(
            scope_frame,
            text="Report Parameters / Date Scope:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=("#615D56", "#A8A297")
        )
        scope_lbl.pack(anchor="w", padx=12, pady=(6, 4))

        param_container = ctk.CTkFrame(scope_frame, fg_color="transparent")
        param_container.pack(fill="x", padx=12, pady=(0, 6))

        date_entry_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        month_var = ctk.StringVar(value=str(date.today().month))
        year_var = ctk.StringVar(value=str(date.today().year))

        def update_params_ui(choice):
            for w in param_container.winfo_children():
                w.destroy()

            if choice == "Daily Sales & Collections Audit":
                row = ctk.CTkFrame(param_container, fg_color="transparent")
                row.pack(fill="x")
                ctk.CTkLabel(row, text="Audit Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 8))
                ctk.CTkEntry(
                    row,
                    textvariable=date_entry_var,
                    width=160,
                    height=32,
                    corner_radius=Theme.RADIUS_INPUT,
                    fg_color=Theme.INSET_BG,
                    border_color=Theme.INSET_BORDER,
                    border_width=Theme.BORDER_WIDTH_INPUT
                ).pack(side="left")
                ctk.CTkLabel(row, text=f"(Today: {date.today().strftime('%Y-%m-%d')})", font=ctk.CTkFont(size=10), text_color="#64748B").pack(side="left", padx=8)

            elif choice == "Monthly Performance & Revenue Audit":
                row = ctk.CTkFrame(param_container, fg_color="transparent")
                row.pack(fill="x")
                ctk.CTkLabel(row, text="Month (1-12):", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
                ctk.CTkOptionMenu(
                    row,
                    values=[str(i) for i in range(1, 13)],
                    variable=month_var,
                    width=75,
                    height=32,
                    corner_radius=Theme.RADIUS_INPUT
                ).pack(side="left", padx=(0, 12))
                ctk.CTkLabel(row, text="Year:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
                ctk.CTkEntry(
                    row,
                    textvariable=year_var,
                    width=90,
                    height=32,
                    corner_radius=Theme.RADIUS_INPUT,
                    fg_color=Theme.INSET_BG,
                    border_color=Theme.INSET_BORDER,
                    border_width=Theme.BORDER_WIDTH_INPUT
                ).pack(side="left")

            else:  # Target Archive
                ctk.CTkLabel(
                    param_container,
                    text="Scope: Covers ALL recorded historical months and current active targets.",
                    font=ctk.CTkFont(size=11),
                    text_color=Theme.SUCCESS
                ).pack(anchor="w")

        report_dropdown.configure(command=update_params_ui)
        update_params_ui(report_type_var.get())

        # 3. Format Selection
        ctk.CTkLabel(
            body_f,
            text="Select Export Format:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        format_seg = ctk.CTkSegmentedButton(
            body_f,
            values=["PDF Document (*.pdf)", "CSV Spreadsheet (*.csv)"],
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            height=34
        )
        format_seg.set("PDF Document (*.pdf)")
        format_seg.pack(fill="x", pady=(0, 20))

        # 4. Action Buttons
        btn_row = ctk.CTkFrame(body_f, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        def do_export():
            rtype = report_type_var.get()
            is_pdf = "PDF" in format_seg.get()

            try:
                out_file = None
                if rtype == "Daily Sales & Collections Audit":
                    try:
                        t_date = datetime.strptime(date_entry_var.get().strip(), "%Y-%m-%d").date()
                    except Exception:
                        t_date = date.today()

                    if is_pdf:
                        out_file = ReportPDFGenerator.generate_daily_report_pdf(t_date)
                    else:
                        out_file = ReportService.export_daily_report_csv(t_date)

                elif rtype == "Monthly Performance & Revenue Audit":
                    try:
                        m_val = int(month_var.get())
                        y_val = int(year_var.get().strip())
                    except Exception:
                        m_val = date.today().month
                        y_val = date.today().year

                    if is_pdf:
                        out_file = ReportPDFGenerator.generate_monthly_report_pdf(y_val, m_val)
                    else:
                        out_file = ReportService.export_monthly_report_csv(y_val, m_val)

                else:  # Target Archive
                    if is_pdf:
                        out_file = ReportPDFGenerator.generate_target_archive_pdf()
                    else:
                        out_file = ReportService.export_target_archive_csv()

                modal.destroy()
                msgbox.showinfo("Export Successful", f"Report successfully exported:\n{out_file}")
                try:
                    os.startfile(out_file)
                except Exception:
                    pass

            except Exception as ex:
                msgbox.showerror("Export Failed", str(ex))

        ctk.CTkButton(
            btn_row,
            text="Generate & Open Report 🚀",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            command=do_export,
            height=36
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            fg_color="transparent",
            text_color=("#615D56", "#A8A297"),
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            command=modal.destroy,
            height=36
        ).pack(side="right")
