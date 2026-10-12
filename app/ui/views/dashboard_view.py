"""
Dashboard View: Modern executive analytics dashboard with timeframe filters,
sales targets vs achievements, and receivables breakdown.
"""
import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.components.stat_card import StatCard
from app.services.report_service import ReportService
from app.services.quotation_service import QuotationService
from app.database.models import Quotation


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.current_timeframe = "Monthly"

        # Build View Layout
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        # 1. Top Bar: Title + Timeframe Segmented Control + Quick Action
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 16))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Sales & Quotation Dashboard",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="AMA Ceramics Pvt Ltd • Real-time targets, pipelines & receivables",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#64748B", "#94A3B8"),
        )
        subtitle.pack(anchor="w")

        # Timeframe filter selector
        filter_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        filter_box.pack(side="right")

        self.timeframe_segmented = ctk.CTkSegmentedButton(
            filter_box,
            values=["Daily", "Weekly", "Monthly", "All-Time"],
            command=self.on_timeframe_change,
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold")
        )
        self.timeframe_segmented.set("Monthly")
        self.timeframe_segmented.pack(side="left", padx=8)

        new_quote_btn = ctk.CTkButton(
            filter_box,
            text="+ New Quotation",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.ACCENT_GOLD,
            hover_color=Theme.ACCENT_GOLD_HOVER,
            command=lambda: self.controller.show_view("quotation_editor", None),
            height=34
        )
        new_quote_btn.pack(side="left")

        # Scrollable container for dashboard body
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 2. KPI Stat Cards Row
        self.kpi_container = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        self.kpi_container.pack(fill="x", pady=(0, 16))
        self.kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self.card_won = StatCard(
            self.kpi_container,
            title="Won Closed Sales",
            value="₹ 0.00",
            subtitle="Closed orders",
            accent_color=Theme.SUCCESS,
            icon="🏆"
        )
        self.card_won.grid(row=0, column=0, padx=6, sticky="ew")

        self.card_pipeline = StatCard(
            self.kpi_container,
            title="Active Pipeline",
            value="₹ 0.00",
            subtitle="Open & In-Review",
            accent_color=Theme.PRIMARY,
            icon="📊"
        )
        self.card_pipeline.grid(row=0, column=1, padx=6, sticky="ew")

        self.card_cleared = StatCard(
            self.kpi_container,
            title="Cleared Receipts",
            value="₹ 0.00",
            subtitle="Realized bank funds",
            accent_color=Theme.INFO,
            icon="💳"
        )
        self.card_cleared.grid(row=0, column=2, padx=6, sticky="ew")

        self.card_outstanding = StatCard(
            self.kpi_container,
            title="Pending Receivables",
            value="₹ 0.00",
            subtitle="Outstanding balance",
            accent_color=Theme.DANGER,
            icon="⏳"
        )
        self.card_outstanding.grid(row=0, column=3, padx=6, sticky="ew")

        # 3. Middle Section: Two Columns (Left: Target vs Achievement, Right: Receivables Breakdown)
        middle_row = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        middle_row.pack(fill="x", pady=(0, 16))
        middle_row.grid_columnconfigure(0, weight=3)
        middle_row.grid_columnconfigure(1, weight=2)

        # Left: Salesperson Target vs Achievement Progress Bars
        self.target_card = ctk.CTkFrame(
            middle_row,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.target_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        target_header = ctk.CTkFrame(self.target_card, fg_color="transparent")
        target_header.pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            target_header,
            text="🎯 Salesperson Target vs. Achievement",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        self.team_target_summary_lbl = ctk.CTkLabel(
            target_header,
            text="Team Goal: -",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=Theme.PRIMARY
        )
        self.team_target_summary_lbl.pack(side="right")

        self.targets_list_frame = ctk.CTkFrame(self.target_card, fg_color="transparent")
        self.targets_list_frame.pack(fill="x", padx=16, pady=(0, 16))

        # Right: Payment Clearance vs Pending Receivables
        self.receivables_card = ctk.CTkFrame(
            middle_row,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.receivables_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        rec_header = ctk.CTkFrame(self.receivables_card, fg_color="transparent")
        rec_header.pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            rec_header,
            text="💰 Payment Clearance & Receivables",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        self.rec_details_frame = ctk.CTkFrame(self.receivables_card, fg_color="transparent")
        self.rec_details_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # 4. Bottom Section: Recent Quotations Table
        recent_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        recent_card.pack(fill="x", pady=(0, 10))

        recent_header = ctk.CTkFrame(recent_card, fg_color="transparent")
        recent_header.pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            recent_header,
            text="📑 Recent Quotations",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        ctk.CTkButton(
            recent_header,
            text="View All Quotes →",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent",
            text_color=Theme.PRIMARY,
            hover_color=("#F1F5F9", "#0F172A"),
            command=lambda: self.controller.show_view("quotations", None),
            height=26
        ).pack(side="right")

        self.recent_table_frame = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_table_frame.pack(fill="x", padx=16, pady=(0, 16))

    def on_timeframe_change(self, val):
        self.current_timeframe = val
        self.refresh_data()

    def refresh_data(self):
        metrics = ReportService.get_dashboard_metrics(self.current_timeframe)
        perf = ReportService.get_salesperson_performances(self.current_timeframe)

        # Update KPI cards
        self.card_won.update_values(
            f"₹ {metrics['won_sales_value']:,.2f}",
            f"{metrics['won_quotes']} won quotes • {metrics['conversion_rate']}% conv."
        )
        self.card_pipeline.update_values(
            f"₹ {metrics['pipeline_value']:,.2f}",
            f"{metrics['open_quotes']} open • {metrics['in_review_quotes']} in-review"
        )
        self.card_cleared.update_values(
            f"₹ {metrics['cleared_payments']:,.2f}",
            f"₹ {metrics['pending_payments']:,.2f} pending clearance"
        )
        self.card_outstanding.update_values(
            f"₹ {metrics['total_outstanding']:,.2f}",
            "Balance across won orders"
        )

        # Update Salesperson Progress Bars
        for widget in self.targets_list_frame.winfo_children():
            widget.destroy()

        self.team_target_summary_lbl.configure(
            text=f"Achieved: ₹ {perf['team_total_achieved']:,.0f} / ₹ {perf['team_total_target']:,.0f} ({perf['team_percentage']}%)"
        )

        for person in perf["individuals"]:
            p_frame = ctk.CTkFrame(self.targets_list_frame, fg_color=("#F8FAFC", "#0F172A"), corner_radius=8)
            p_frame.pack(fill="x", pady=4, padx=2)

            info_row = ctk.CTkFrame(p_frame, fg_color="transparent")
            info_row.pack(fill="x", padx=12, pady=(8, 2))

            name_lbl = ctk.CTkLabel(
                info_row,
                text=f"{person['name']}  ({person['role']})",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
                text_color=("#0F172A", "#F8FAFC")
            )
            name_lbl.pack(side="left")

            stat_lbl = ctk.CTkLabel(
                info_row,
                text=f"Achieved: ₹ {person['achieved']:,.0f} / Target: ₹ {person['target']:,.0f}  •  Bal: ₹ {person['balance']:,.0f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=("#64748B", "#94A3B8")
            )
            stat_lbl.pack(side="right")

            # Progress bar + badge row
            bar_row = ctk.CTkFrame(p_frame, fg_color="transparent")
            bar_row.pack(fill="x", padx=12, pady=(2, 8))

            progress_val = min(1.0, max(0.0, person["percentage"] / 100.0))
            bar_color = Theme.SUCCESS if person["percentage"] >= 100 else (Theme.PRIMARY if person["percentage"] >= 50 else Theme.WARNING)

            p_bar = ctk.CTkProgressBar(
                bar_row,
                height=9,
                corner_radius=4,
                progress_color=bar_color,
                fg_color=("#E2E8F0", "#334155")
            )
            p_bar.set(progress_val)
            p_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

            pct_badge = ctk.CTkLabel(
                bar_row,
                text=f"{person['percentage']}%",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=bar_color,
                width=45,
                anchor="e"
            )
            pct_badge.pack(side="right")

        # Update Receivables Breakdown Widget
        for widget in self.rec_details_frame.winfo_children():
            widget.destroy()

        cleared_amt = metrics["cleared_payments"]
        pending_amt = metrics["pending_payments"]
        outstanding_amt = metrics["total_outstanding"]
        total_rec_base = max(1.0, cleared_amt + outstanding_amt)
        cleared_pct = round((cleared_amt / total_rec_base) * 100, 1)

        # Metric breakdown rows
        rec_box = ctk.CTkFrame(self.rec_details_frame, fg_color=("#F8FAFC", "#0F172A"), corner_radius=8)
        rec_box.pack(fill="both", expand=True, pady=4)

        items = [
            ("Bank Realized / Cleared:", f"₹ {cleared_amt:,.2f}", Theme.SUCCESS),
            ("Pending Cheques / UPI Tokens:", f"₹ {pending_amt:,.2f}", Theme.WARNING),
            ("Uncollected Balance (Won):", f"₹ {outstanding_amt:,.2f}", Theme.DANGER),
        ]

        for lbl, val, col in items:
            row = ctk.CTkFrame(rec_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(
                row,
                text=lbl,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=("#475569", "#94A3B8")
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=val,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
                text_color=col
            ).pack(side="right")

        # Visual clearance bar
        clearance_bar_frame = ctk.CTkFrame(rec_box, fg_color="transparent")
        clearance_bar_frame.pack(fill="x", padx=12, pady=(6, 12))

        ctk.CTkLabel(
            clearance_bar_frame,
            text=f"Realization Rate: {cleared_pct}% Cleared",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
            text_color=Theme.SUCCESS
        ).pack(anchor="w", pady=(0, 3))

        c_bar = ctk.CTkProgressBar(
            clearance_bar_frame,
            height=10,
            corner_radius=4,
            progress_color=Theme.SUCCESS,
            fg_color=("#E2E8F0", "#334155")
        )
        c_bar.set(min(1.0, cleared_pct / 100.0))
        c_bar.pack(fill="x")

        # Update Recent Quotations Table
        for widget in self.recent_table_frame.winfo_children():
            widget.destroy()

        quotes = list(Quotation.select().order_by(Quotation.id.desc()).limit(5))
        if not quotes:
            ctk.CTkLabel(self.recent_table_frame, text="No quotations created yet.").pack(pady=10)
            return

        # Table Header
        h_row = ctk.CTkFrame(self.recent_table_frame, fg_color=("#F1F5F9", "#0F172A"), corner_radius=6)
        h_row.pack(fill="x", pady=(0, 4))
        h_row.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        headers = ["Quote #", "Customer", "Date", "Net Total", "Status", "Action"]
        for col_idx, h_text in enumerate(headers):
            ctk.CTkLabel(
                h_row,
                text=h_text,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=("#475569", "#94A3B8"),
                anchor="w"
            ).grid(row=0, column=col_idx, padx=8, pady=6, sticky="w")

        # Table Rows
        for q in quotes:
            r_frame = ctk.CTkFrame(self.recent_table_frame, fg_color="transparent")
            r_frame.pack(fill="x", pady=2)
            r_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

            ctk.CTkLabel(
                r_frame,
                text=q.quotation_number,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=Theme.PRIMARY,
                anchor="w"
            ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

            ctk.CTkLabel(
                r_frame,
                text=q.customer_name[:24],
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                anchor="w"
            ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

            q_d_str = q.quotation_date.strftime("%d-%b-%Y") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date)
            ctk.CTkLabel(
                r_frame,
                text=q_d_str,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=("#64748B", "#94A3B8"),
                anchor="w"
            ).grid(row=0, column=2, padx=8, pady=4, sticky="w")

            ctk.CTkLabel(
                r_frame,
                text=f"₹ {q.net_total:,.2f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                anchor="w"
            ).grid(row=0, column=3, padx=8, pady=4, sticky="w")

            # Status pill
            status_fg, _ = Theme.get_status_color(q.status)
            ctk.CTkLabel(
                r_frame,
                text=f"● {q.status}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=status_fg,
                anchor="w"
            ).grid(row=0, column=4, padx=8, pady=4, sticky="w")

            # Action button
            act_btn = ctk.CTkButton(
                r_frame,
                text="View / Edit",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                width=75,
                height=24,
                fg_color=("#E2E8F0", "#334155"),
                text_color=("#0F172A", "#F8FAFC"),
                hover_color=Theme.PRIMARY,
                command=lambda qid=q.id: self.controller.show_view("quotation_editor", qid)
            )
            act_btn.grid(row=0, column=5, padx=8, pady=4, sticky="w")
