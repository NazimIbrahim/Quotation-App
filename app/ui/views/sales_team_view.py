"""
Sales Team View: Manage salespersons and managers, monitor target vs. achievement,
and manage quotation approval workflows.
"""
import tkinter.messagebox as msgbox
from datetime import date, datetime, timedelta
import customtkinter as ctk

from app.ui.theme import Theme
from app.database.models import SalesPerson, Quotation, SalesTarget
from app.services.quotation_service import QuotationService


class SalesTeamView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.target_scope = "This Month"

        self.build_ui()
        self.refresh_team_data()

    def build_ui(self):
        # 1. Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Sales Team & Manager Approvals",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Monthly targets, sales performance tracking & discount approval workflows",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        top_btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_btn_box.pack(side="right")

        alter_target_btn = ctk.CTkButton(
            top_btn_box,
            text="🎯 Set / Alter Targets",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            command=self.open_alter_target_modal,
            height=36
        )
        alter_target_btn.pack(side="left", padx=(0, 8))

        export_archive_btn = ctk.CTkButton(
            top_btn_box,
            text="📊 Target Archive PDF",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SUCCESS_BORDER,
            command=self.export_target_archive_report,
            height=36
        )
        export_archive_btn.pack(side="left", padx=(0, 8))

        add_rep_btn = ctk.CTkButton(
            top_btn_box,
            text="+ Add Team Member",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=(Theme.BLACK, Theme.PAPER),
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SECONDARY_BORDER,
            command=self.open_member_modal,
            height=36
        )
        add_rep_btn.pack(side="left")

        # Scroll body
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 2. Manager Approvals Queue (Highlighted if any quotes in-review)
        self.approval_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=(Theme.STONE, "#38342E")
        )
        self.approval_card.pack(fill="x", pady=(0, 16))

        appr_header = ctk.CTkFrame(self.approval_card, fg_color="transparent")
        appr_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            appr_header,
            text="🛡️ Manager Approval Queue (In-Review Quotes)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=Theme.INFO
        ).pack(side="left")

        self.appr_count_lbl = ctk.CTkLabel(
            appr_header,
            text="0 Pending",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.INFO
        )
        self.appr_count_lbl.pack(side="right")

        self.approvals_container = ctk.CTkFrame(self.approval_card, fg_color="transparent")
        self.approvals_container.pack(fill="x", padx=16, pady=(0, 14))

        # 3. Sales Team Target Performance Cards Section & Scope Toolbar
        target_toolbar = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        target_toolbar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            target_toolbar,
            text="🎯 Salesperson Performance & Target Tracking",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left")

        self.scope_segment = ctk.CTkSegmentedButton(
            target_toolbar,
            values=["This Month", "This Week", "Base Monthly"],
            command=self.on_scope_changed,
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            height=34,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        self.scope_segment.set("This Month")
        self.scope_segment.pack(side="right")

        self.team_cards_container = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        self.team_cards_container.pack(fill="x")

    def on_scope_changed(self, value):
        self.target_scope = value
        self.refresh_team_data()

    def refresh_team_data(self):
        # Refresh Approval Queue
        for widget in self.approvals_container.winfo_children():
            widget.destroy()

        in_review_quotes = list(
            Quotation.select()
            .where(Quotation.status == Quotation.STATUS_IN_REVIEW)
            .order_by(Quotation.id.desc())
        )

        self.appr_count_lbl.configure(text=f"{len(in_review_quotes)} Pending Approvals")

        if not in_review_quotes:
            ctk.CTkLabel(
                self.approvals_container,
                text="✓ No quotations pending manager approval. All clear!",
                font=ctk.CTkFont(size=11),
                text_color=Theme.SUCCESS
            ).pack(anchor="w", pady=6)
        else:
            for q in in_review_quotes:
                r = ctk.CTkFrame(self.approvals_container, fg_color=("#EDE9FE", "#1E1B4B"), corner_radius=Theme.RADIUS_SM)
                r.pack(fill="x", pady=4)

                info_box = ctk.CTkFrame(r, fg_color="transparent")
                info_box.pack(side="left", padx=12, pady=10)

                ctk.CTkLabel(
                    info_box,
                    text=f"{q.quotation_number} • {q.customer_name}  (by {q.sales_person_name})",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=("#4338CA", "#C7D2FE")
                ).pack(anchor="w")

                notes_text = f"Net Total: ₹ {q.net_total:,.2f}  |  Round-off/Discount: ₹ {q.round_off:,.2f}  |  Notes: {q.special_notes or 'Special rate approval request'}"
                ctk.CTkLabel(
                    info_box,
                    text=notes_text,
                    font=ctk.CTkFont(size=11),
                    text_color=("#6D28D9", "#DDD6FE")
                ).pack(anchor="w")

                act_box = ctk.CTkFrame(r, fg_color="transparent")
                act_box.pack(side="right", padx=12)

                ctk.CTkButton(
                    act_box,
                    text="Approve (Won) ✓",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=Theme.SUCCESS,
                    hover_color=Theme.SUCCESS_HOVER,
                    corner_radius=Theme.RADIUS_PILL,
                    border_width=1,
                    border_color=Theme.BTN_SUCCESS_BORDER,
                    height=28,
                    command=lambda qid=q.id: self.approve_quote(qid, Quotation.STATUS_WON)
                ).pack(side="left", padx=3)

                ctk.CTkButton(
                    act_box,
                    text="Reject ✕",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=Theme.DANGER,
                    hover_color=Theme.DANGER_HOVER,
                    corner_radius=Theme.RADIUS_PILL,
                    border_width=1,
                    border_color=Theme.BTN_DANGER_BORDER,
                    height=28,
                    command=lambda qid=q.id: self.approve_quote(qid, Quotation.STATUS_LOST)
                ).pack(side="left", padx=3)

        # Refresh Sales Team Cards
        for widget in self.team_cards_container.winfo_children():
            widget.destroy()

        today = date.today()
        if self.target_scope == "This Week":
            start_d = today - timedelta(days=today.weekday())
            end_d = start_d + timedelta(days=6)
            scope_title = f"WEEKLY TARGET ({start_d.strftime('%d %b')} - {end_d.strftime('%d %b')})"
        elif self.target_scope == "Base Monthly":
            start_d = None
            end_d = None
            scope_title = "BASE MONTHLY TARGET"
        else:  # "This Month"
            start_d = today.replace(day=1)
            next_m = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
            end_d = next_m - timedelta(days=1)
            scope_title = f"TARGET ({today.strftime('%B %Y').upper()})"

        members = list(SalesPerson.select().order_by(SalesPerson.id))
        for sp in members:
            card = ctk.CTkFrame(
                self.team_cards_container,
                corner_radius=Theme.RADIUS_CARD,
                fg_color=("#FFFFFF", "#201E1C"),
                border_width=Theme.BORDER_WIDTH_CARD,
                border_color=(Theme.STONE, "#38342E")
            )
            card.pack(fill="x", pady=6)

            # Top Row
            top_r = ctk.CTkFrame(card, fg_color="transparent")
            top_r.pack(fill="x", padx=16, pady=(12, 6))

            name_box = ctk.CTkFrame(top_r, fg_color="transparent")
            name_box.pack(side="left")

            ctk.CTkLabel(
                name_box,
                text=sp.name,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).pack(side="left")

            role_bg = Theme.INFO if sp.role == SalesPerson.ROLE_MANAGER else Theme.PRIMARY
            ctk.CTkLabel(
                name_box,
                text=f"  [{sp.role.upper()}]  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white",
                fg_color=role_bg,
                corner_radius=Theme.RADIUS_SM
            ).pack(side="left", padx=8)

            ctk.CTkLabel(
                name_box,
                text=f"📞 {sp.contact_number}  |  ✉ {sp.email or 'N/A'}",
                font=ctk.CTkFont(size=11),
                text_color=("#615D56", "#A8A297")
            ).pack(side="left", padx=8)

            btn_box = ctk.CTkFrame(top_r, fg_color="transparent")
            btn_box.pack(side="right")

            alter_btn = ctk.CTkButton(
                btn_box,
                text="🎯 Alter Target",
                font=ctk.CTkFont(size=10, weight="bold"),
                width=100,
                height=28,
                corner_radius=Theme.RADIUS_PILL,
                border_width=1,
                border_color=Theme.BTN_PRIMARY_BORDER,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                command=lambda m=sp: self.open_alter_target_modal(m)
            )
            alter_btn.pack(side="left", padx=(0, 6))

            edit_btn = ctk.CTkButton(
                btn_box,
                text="Edit Info",
                font=ctk.CTkFont(size=10),
                width=80,
                height=28,
                corner_radius=Theme.RADIUS_PILL,
                border_width=1,
                border_color=Theme.BTN_SECONDARY_BORDER,
                fg_color=Theme.BTN_SECONDARY_BG,
                hover_color=Theme.BTN_SECONDARY_HOVER,
                text_color=(Theme.BLACK, Theme.PAPER),
                command=lambda m=sp: self.open_member_modal(m)
            )
            edit_btn.pack(side="left")

            # Performance Numbers Grid for Selected Scope
            if start_d and end_d:
                target_val = sp.get_target_for_period(start_d, end_d)
                achieved = sp.get_sales_achieved(start_date=start_d, end_date=end_d)
            else:
                target_val = sp.monthly_target
                achieved = sp.get_sales_achieved()

            balance = max(0.0, round(target_val - achieved, 2))
            pct = (achieved / target_val * 100.0) if target_val > 0 else 0.0

            metrics_grid = ctk.CTkFrame(card, fg_color=(Theme.PAPER, "#1E1C1A"), corner_radius=Theme.RADIUS_SM, border_width=1, border_color=(Theme.STONE, "#38342E"))
            metrics_grid.pack(fill="x", padx=16, pady=(0, 8))
            metrics_grid.grid_columnconfigure((0, 1, 2), weight=1)

            self.create_metric_cell(metrics_grid, 0, scope_title, f"₹ {target_val:,.2f}", Theme.SECONDARY)
            self.create_metric_cell(metrics_grid, 1, "SALES ACHIEVED", f"₹ {achieved:,.2f}", Theme.SUCCESS)
            self.create_metric_cell(metrics_grid, 2, "BALANCE TO TARGET", f"₹ {balance:,.2f}", Theme.DANGER if balance > 0 else Theme.SUCCESS)

            # Active Target Rules Badges
            configured_targets = list(
                SalesTarget.select()
                .where(SalesTarget.sales_person == sp)
                .order_by(SalesTarget.start_date.desc())[:4]
            )
            if configured_targets:
                tags_row = ctk.CTkFrame(card, fg_color="transparent")
                tags_row.pack(fill="x", padx=16, pady=(0, 6))

                ctk.CTkLabel(
                    tags_row,
                    text="Altered Targets:",
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=("#615D56", "#A8A297")
                ).pack(side="left", padx=(0, 6))

                for st in configured_targets:
                    tag_col = Theme.PRIMARY if st.target_type == "Monthly" else (Theme.SUCCESS if st.target_type == "Weekly" else Theme.WARNING)
                    tag_bg = ("#E0F2FE", "#075985") if st.target_type == "Monthly" else (("#DCFCE7", "#166534") if st.target_type == "Weekly" else ("#FEF3C7", "#92400E"))
                    ctk.CTkLabel(
                        tags_row,
                        text=f" {st.target_type}: {st.period_label} → ₹{st.target_amount:,.0f} ",
                        font=ctk.CTkFont(size=9, weight="bold"),
                        text_color=tag_col,
                        fg_color=tag_bg,
                        corner_radius=4
                    ).pack(side="left", padx=2)

            # Progress Bar Row
            bar_frame = ctk.CTkFrame(card, fg_color="transparent")
            bar_frame.pack(fill="x", padx=16, pady=(0, 12))

            bar_color = Theme.SUCCESS if pct >= 100 else (Theme.PRIMARY if pct >= 50 else Theme.WARNING)

            p_bar = ctk.CTkProgressBar(
                bar_frame,
                height=10,
                corner_radius=4,
                progress_color=bar_color,
                fg_color=(Theme.STONE, "#2B2824")
            )
            p_bar.set(min(1.0, pct / 100.0))
            p_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))

            ctk.CTkLabel(
                bar_frame,
                text=f"{pct:.1f}% Completed",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=bar_color,
                width=90,
                anchor="e"
            ).pack(side="right")

    def create_metric_cell(self, parent, col, title, val, color):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color=("#615D56", "#A8A297")).pack(anchor="w")
        ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(anchor="w")

    def approve_quote(self, quote_id: int, new_status: str):
        active_u = self.controller.get_active_user()
        QuotationService.update_status(
            quote_id,
            new_status,
            manager=active_u,
            note="Approved by Manager via Approvals Queue"
        )
        msgbox.showinfo("Status Updated", f"Quotation status updated to '{new_status}'!")
        self.refresh_team_data()

    def open_alter_target_modal(self, preselected_member=None):
        """
        Interactive modal dialog to set or alter sales targets for:
        1. A specific single month (without affecting base targets for other months)
        2. A 7-day weekly sprint (Monday to Sunday)
        3. A custom date range (promotions / campaigns)
        Also manages and allows deleting active custom targets.
        """
        if not isinstance(preselected_member, SalesPerson):
            preselected_member = None

        dialog = ctk.CTkToplevel(self)
        dialog.title("Set / Alter Sales Targets")
        dialog.geometry("640x740")
        dialog.minsize(600, 650)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Main scroll container
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Header
        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            header_frame,
            text="🎯 Set & Alter Salesperson Targets",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=18, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="Override targets for an individual month, a 7-day sprint, or custom campaign dates.",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color=("#615D56", "#A8A297")
        ).pack(anchor="w", pady=(2, 0))

        # Member Selection Card
        member_card = ctk.CTkFrame(
            scroll,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=(Theme.STONE, "#38342E")
        )
        member_card.pack(fill="x", pady=(0, 12), ipady=6)

        ctk.CTkLabel(
            member_card,
            text="1. SELECT SALESPERSON",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(anchor="w", padx=14, pady=(10, 4))

        all_members = list(SalesPerson.select().where(SalesPerson.is_active == True).order_by(SalesPerson.name))
        if not all_members:
            all_members = list(SalesPerson.select().order_by(SalesPerson.name))

        member_map = {f"{m.name} ({m.role}) - Base: ₹{m.monthly_target:,.0f}": m for m in all_members}
        member_options = list(member_map.keys())

        default_str = None
        if preselected_member:
            for k, m in member_map.items():
                if m.id == preselected_member.id:
                    default_str = k
                    break
        if not default_str and member_options:
            default_str = member_options[0]

        member_combo = ctk.CTkComboBox(
            member_card,
            values=member_options,
            width=500,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            font=ctk.CTkFont(size=12)
        )
        if default_str:
            member_combo.set(default_str)
        member_combo.pack(fill="x", padx=14, pady=(0, 10))

        # Target Type & Parameters Card
        config_card = ctk.CTkFrame(
            scroll,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=(Theme.STONE, "#38342E")
        )
        config_card.pack(fill="x", pady=(0, 12), ipady=6)

        ctk.CTkLabel(
            config_card,
            text="2. TARGET PERIOD SCOPE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(anchor="w", padx=14, pady=(10, 6))

        scope_segment = ctk.CTkSegmentedButton(
            config_card,
            values=["📅 Specific Month", "📆 Weekly (7 Days)", "🎯 Custom Date Range"],
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        scope_segment.set("📅 Specific Month")
        scope_segment.pack(fill="x", padx=14, pady=(0, 12))

        # Dynamic Fields Container
        fields_container = ctk.CTkFrame(config_card, fg_color="transparent")
        fields_container.pack(fill="x", padx=14, pady=(0, 8))

        today = date.today()
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        # Field References
        month_combo_ref = [None]
        year_combo_ref = [None]
        week_date_entry_ref = [None]
        week_calc_lbl_ref = [None]
        start_date_entry_ref = [None]
        end_date_entry_ref = [None]
        custom_label_entry_ref = [None]

        def update_week_calc_label(*args):
            lbl = week_calc_lbl_ref[0]
            ent = week_date_entry_ref[0]
            if not lbl or not ent:
                return
            try:
                ref_d = datetime.strptime(ent.get().strip(), "%Y-%m-%d").date()
                mon = ref_d - timedelta(days=ref_d.weekday())
                sun = mon + timedelta(days=6)
                lbl.configure(text=f"✓ Computed 7-Day Sprint: Mon {mon.strftime('%d %b %Y')} to Sun {sun.strftime('%d %b %Y')}", text_color=Theme.SUCCESS)
            except Exception:
                lbl.configure(text="⚠ Please enter date in YYYY-MM-DD format (e.g. 2026-10-15)", text_color=Theme.DANGER)

        def render_scope_fields(selected_scope):
            for child in fields_container.winfo_children():
                child.destroy()

            if selected_scope == "📅 Specific Month":
                ctk.CTkLabel(
                    fields_container,
                    text="Select Calendar Month & Year:",
                    font=ctk.CTkFont(size=11, weight="bold")
                ).pack(anchor="w", pady=(0, 4))

                m_row = ctk.CTkFrame(fields_container, fg_color="transparent")
                m_row.pack(fill="x", pady=(0, 6))

                cur_month_name = month_names[today.month - 1]
                month_combo = ctk.CTkComboBox(m_row, values=month_names, width=180, height=34, corner_radius=Theme.RADIUS_INPUT)
                month_combo.set(cur_month_name)
                month_combo.pack(side="left", padx=(0, 8))
                month_combo_ref[0] = month_combo

                years = [str(today.year - 1), str(today.year), str(today.year + 1), str(today.year + 2)]
                year_combo = ctk.CTkComboBox(m_row, values=years, width=120, height=34, corner_radius=Theme.RADIUS_INPUT)
                year_combo.set(str(today.year))
                year_combo.pack(side="left")
                year_combo_ref[0] = year_combo

                ctk.CTkLabel(
                    fields_container,
                    text="ℹ️ Overrides target ONLY for this chosen month. Other months automatically retain default base targets.",
                    font=ctk.CTkFont(size=10),
                    text_color=("#615D56", "#A8A297"),
                    wraplength=520,
                    justify="left"
                ).pack(anchor="w", pady=(2, 0))

            elif selected_scope == "📆 Weekly (7 Days)":
                ctk.CTkLabel(
                    fields_container,
                    text="Any Date in Week (YYYY-MM-DD):",
                    font=ctk.CTkFont(size=11, weight="bold")
                ).pack(anchor="w", pady=(0, 4))

                w_ent = ctk.CTkEntry(
                    fields_container,
                    width=220,
                    height=34,
                    corner_radius=Theme.RADIUS_INPUT,
                    fg_color=Theme.INSET_BG,
                    border_color=Theme.INSET_BORDER,
                    border_width=Theme.BORDER_WIDTH_INPUT
                )
                w_ent.insert(0, today.strftime("%Y-%m-%d"))
                w_ent.pack(anchor="w", pady=(0, 4))
                week_date_entry_ref[0] = w_ent

                w_lbl = ctk.CTkLabel(
                    fields_container,
                    text="",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=Theme.SUCCESS
                )
                w_lbl.pack(anchor="w", pady=(0, 4))
                week_calc_lbl_ref[0] = w_lbl
                update_week_calc_label()
                w_ent.bind("<KeyRelease>", update_week_calc_label)

                ctk.CTkLabel(
                    fields_container,
                    text="ℹ️ Automatically calculates the Monday to Sunday 7-day sprint containing this date.",
                    font=ctk.CTkFont(size=10),
                    text_color=("#615D56", "#A8A297")
                ).pack(anchor="w")

            else:  # "🎯 Custom Date Range"
                ctk.CTkLabel(
                    fields_container,
                    text="Custom Start Date & End Date (YYYY-MM-DD):",
                    font=ctk.CTkFont(size=11, weight="bold")
                ).pack(anchor="w", pady=(0, 4))

                d_row = ctk.CTkFrame(fields_container, fg_color="transparent")
                d_row.pack(fill="x", pady=(0, 6))

                s_ent = ctk.CTkEntry(
                    d_row,
                    width=150,
                    height=34,
                    corner_radius=Theme.RADIUS_INPUT,
                    fg_color=Theme.INSET_BG,
                    border_color=Theme.INSET_BORDER,
                    border_width=Theme.BORDER_WIDTH_INPUT
                )
                s_ent.insert(0, today.strftime("%Y-%m-%d"))
                s_ent.pack(side="left", padx=(0, 8))
                start_date_entry_ref[0] = s_ent

                ctk.CTkLabel(d_row, text="to", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 8))

                e_ent = ctk.CTkEntry(
                    d_row,
                    width=150,
                    height=34,
                    corner_radius=Theme.RADIUS_INPUT,
                    fg_color=Theme.INSET_BG,
                    border_color=Theme.INSET_BORDER,
                    border_width=Theme.BORDER_WIDTH_INPUT
                )
                default_end = today + timedelta(days=14)
                e_ent.insert(0, default_end.strftime("%Y-%m-%d"))
                e_ent.pack(side="left")
                end_date_entry_ref[0] = e_ent

                ctk.CTkLabel(
                    fields_container,
                    text="Sprint / Campaign Name (Optional):",
                    font=ctk.CTkFont(size=11, weight="bold")
                ).pack(anchor="w", pady=(4, 2))

                lbl_ent = ctk.CTkEntry(
                    fields_container,
                    height=34,
                    corner_radius=Theme.RADIUS_INPUT,
                    fg_color=Theme.INSET_BG,
                    border_color=Theme.INSET_BORDER,
                    border_width=Theme.BORDER_WIDTH_INPUT,
                    placeholder_text="e.g. Diwali Mega Promotion, Q4 Surge"
                )
                lbl_ent.pack(fill="x", pady=(0, 4))
                custom_label_entry_ref[0] = lbl_ent

                ctk.CTkLabel(
                    fields_container,
                    text="ℹ️ Target will be applied strictly between Start Date and End Date.",
                    font=ctk.CTkFont(size=10),
                    text_color=("#615D56", "#A8A297")
                ).pack(anchor="w")

        scope_segment.configure(command=render_scope_fields)
        render_scope_fields("📅 Specific Month")

        # Amount & Notes Section
        amount_card = ctk.CTkFrame(
            scroll,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=(Theme.STONE, "#38342E")
        )
        amount_card.pack(fill="x", pady=(0, 12), ipady=6)

        ctk.CTkLabel(
            amount_card,
            text="3. TARGET AMOUNT & NOTES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(anchor="w", padx=14, pady=(10, 6))

        ctk.CTkLabel(amount_card, text="Target Amount (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(0, 2))
        amount_ent = ctk.CTkEntry(
            amount_card,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT
        )
        cur_selected_sp = member_map.get(member_combo.get())
        default_amt = str(cur_selected_sp.monthly_target) if cur_selected_sp else "600000.0"
        amount_ent.insert(0, default_amt)
        amount_ent.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkLabel(amount_card, text="Notes / Reason (Optional):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(0, 2))
        notes_ent = ctk.CTkEntry(
            amount_card,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. Festival Season Surge, S-Tier Incentive Sprint"
        )
        notes_ent.pack(fill="x", padx=14, pady=(0, 10))

        # Save Button
        def save_target():
            selected_sp_str = member_combo.get()
            sp = member_map.get(selected_sp_str)
            if not sp:
                msgbox.showerror("Error", "Please select a valid salesperson.", parent=dialog)
                return

            amt_str = amount_ent.get().strip()
            try:
                amt = float(amt_str)
                if amt <= 0:
                    raise ValueError
            except ValueError:
                msgbox.showerror("Error", "Target amount must be a positive number.", parent=dialog)
                return

            notes = notes_ent.get().strip() or None
            scope_mode = scope_segment.get()

            try:
                if scope_mode == "📅 Specific Month":
                    m_name = month_combo_ref[0].get()
                    m_idx = month_names.index(m_name) + 1
                    y_val = int(year_combo_ref[0].get().strip())
                    SalesTarget.set_monthly_target(sp, y_val, m_idx, amt, notes)
                    msgbox.showinfo("Success", f"Target for {sp.name} for {m_name} {y_val} set to ₹{amt:,.2f}!", parent=dialog)

                elif scope_mode == "📆 Weekly (7 Days)":
                    w_str = week_date_entry_ref[0].get().strip()
                    ref_d = datetime.strptime(w_str, "%Y-%m-%d").date()
                    rec = SalesTarget.set_weekly_target(sp, ref_d, amt, notes)
                    msgbox.showinfo("Success", f"Weekly target for {sp.name} set to ₹{amt:,.2f} ({rec.period_label})!", parent=dialog)

                else:  # Custom
                    s_str = start_date_entry_ref[0].get().strip()
                    e_str = end_date_entry_ref[0].get().strip()
                    lbl_val = custom_label_entry_ref[0].get().strip() or None
                    s_d = datetime.strptime(s_str, "%Y-%m-%d").date()
                    e_d = datetime.strptime(e_str, "%Y-%m-%d").date()
                    if e_d < s_d:
                        msgbox.showerror("Error", "End Date must be on or after Start Date.", parent=dialog)
                        return
                    rec = SalesTarget.set_custom_target(sp, s_d, e_d, amt, lbl_val, notes)
                    msgbox.showinfo("Success", f"Custom target for {sp.name} set to ₹{amt:,.2f} ({rec.period_label})!", parent=dialog)

                self.refresh_team_data()
                refresh_active_targets_table()
            except Exception as err:
                msgbox.showerror("Error", f"Failed to save target: {str(err)}", parent=dialog)

        save_btn = ctk.CTkButton(
            scroll,
            text="Save / Alter Target 💾",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            height=36,
            command=save_target
        )
        save_btn.pack(fill="x", pady=(0, 16))

        # Active Altered Targets List Container
        active_targets_frame = ctk.CTkFrame(
            scroll,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=(Theme.STONE, "#38342E")
        )
        active_targets_frame.pack(fill="x", pady=(0, 16), ipady=6)

        targets_header_lbl = ctk.CTkLabel(
            active_targets_frame,
            text="📋 ACTIVE ALTERED TARGETS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.PRIMARY
        )
        targets_header_lbl.pack(anchor="w", padx=14, pady=(10, 4))

        targets_sub_lbl = ctk.CTkLabel(
            active_targets_frame,
            text="Configured target overrides for the selected salesperson:",
            font=ctk.CTkFont(size=10),
            text_color=("#615D56", "#A8A297")
        )
        targets_sub_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        targets_items_box = ctk.CTkFrame(active_targets_frame, fg_color="transparent")
        targets_items_box.pack(fill="x", padx=14, pady=(0, 10))

        def refresh_active_targets_table():
            for child in targets_items_box.winfo_children():
                child.destroy()

            selected_sp_str = member_combo.get()
            sp = member_map.get(selected_sp_str)
            if not sp:
                return

            targets_header_lbl.configure(text=f"📋 ACTIVE ALTERED TARGETS — {sp.name.upper()}")
            targets_sub_lbl.configure(text=f"Base Monthly Target: ₹{sp.monthly_target:,.2f}  |  Custom overrides below:")

            # Fetch active targets
            configured = list(
                SalesTarget.select()
                .where(SalesTarget.sales_person == sp)
                .order_by(SalesTarget.start_date.desc())
            )

            if not configured:
                ctk.CTkLabel(
                    targets_items_box,
                    text="✓ No altered targets currently configured. Member uses base monthly target for all periods.",
                    font=ctk.CTkFont(size=11),
                    text_color=Theme.SUCCESS
                ).pack(anchor="w", pady=6)
                return

            for tgt in configured:
                row_card = ctk.CTkFrame(targets_items_box, fg_color=(Theme.PAPER, "#1E1C1A"), corner_radius=6)
                row_card.pack(fill="x", pady=3)

                info_f = ctk.CTkFrame(row_card, fg_color="transparent")
                info_f.pack(side="left", padx=10, pady=8)

                type_bg = ("#E0F2FE", "#075985") if tgt.target_type == "Monthly" else (("#DCFCE7", "#166534") if tgt.target_type == "Weekly" else ("#FEF3C7", "#92400E"))
                type_fg = Theme.PRIMARY if tgt.target_type == "Monthly" else (Theme.SUCCESS if tgt.target_type == "Weekly" else Theme.WARNING)

                badge_row = ctk.CTkFrame(info_f, fg_color="transparent")
                badge_row.pack(anchor="w")

                ctk.CTkLabel(
                    badge_row,
                    text=f" {tgt.target_type} ",
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color=type_bg,
                    text_color=type_fg,
                    corner_radius=4
                ).pack(side="left", padx=(0, 6))

                ctk.CTkLabel(
                    badge_row,
                    text=tgt.period_label,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=(Theme.BLACK, Theme.PAPER)
                ).pack(side="left")

                notes_txt = f"  •  {tgt.notes}" if tgt.notes else ""
                ctk.CTkLabel(
                    info_f,
                    text=f"Target: ₹ {tgt.target_amount:,.2f}  ({tgt.start_date} to {tgt.end_date}){notes_txt}",
                    font=ctk.CTkFont(size=10),
                    text_color=("#615D56", "#A8A297")
                ).pack(anchor="w", pady=(2, 0))

                del_btn = ctk.CTkButton(
                    row_card,
                    text="Delete ✕",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=Theme.DANGER,
                    hover_color=Theme.DANGER_HOVER,
                    corner_radius=Theme.RADIUS_PILL,
                    border_width=1,
                    border_color=Theme.BTN_DANGER_BORDER,
                    width=75,
                    height=26,
                    command=lambda tid=tgt.id: delete_target_record(tid)
                )
                del_btn.pack(side="right", padx=10)

        def delete_target_record(tid):
            try:
                SalesTarget.delete_by_id(tid)
                msgbox.showinfo("Deleted", "Altered target removed. Reverted to standard target.", parent=dialog)
                self.refresh_team_data()
                refresh_active_targets_table()
            except Exception as e:
                msgbox.showerror("Error", f"Failed to delete target: {str(e)}", parent=dialog)

        def on_member_selection_changed(new_val):
            sp = member_map.get(new_val)
            if sp:
                amount_ent.delete(0, "end")
                amount_ent.insert(0, str(sp.monthly_target))
            refresh_active_targets_table()

        member_combo.configure(command=on_member_selection_changed)
        refresh_active_targets_table()

    def open_member_modal(self, member=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Team Member" if member else "Add Team Member")
        dialog.geometry("460x440")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Sales Team Member", font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(f, text="Full Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        name_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT
        )
        if member:
            name_ent.insert(0, member.name)
        name_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Contact Number:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        phone_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT
        )
        if member:
            phone_ent.insert(0, member.contact_number)
        phone_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Role:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        role_combo = ctk.CTkComboBox(
            f,
            values=[SalesPerson.ROLE_SALES, SalesPerson.ROLE_MANAGER],
            height=34,
            corner_radius=Theme.RADIUS_INPUT
        )
        if member:
            role_combo.set(member.role)
        role_combo.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Monthly Sales Target (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        target_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT
        )
        if member:
            target_ent.insert(0, str(member.monthly_target))
        else:
            target_ent.insert(0, "800000.0")
        target_ent.pack(fill="x", pady=(2, 14))

        def save_m():
            n = name_ent.get().strip()
            p = phone_ent.get().strip()
            r = role_combo.get()
            try:
                t = float(target_ent.get().strip())
            except ValueError:
                msgbox.showerror("Error", "Target must be numeric.", parent=dialog)
                return
            if not n or not p:
                msgbox.showerror("Error", "Name and Contact number are required.", parent=dialog)
                return

            if member:
                member.name = n
                member.contact_number = p
                member.role = r
                member.monthly_target = t
                member.save()
            else:
                SalesPerson.create(name=n, contact_number=p, role=r, monthly_target=t)
            dialog.destroy()
            self.refresh_team_data()
            self.controller.refresh_sidebar_users()

        ctk.CTkButton(
            dialog,
            text="Save Member",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            height=36,
            command=save_m
        ).pack(pady=(0, 20))

    def export_target_archive_report(self):
        """Generates and opens the historical Target vs. Achievement Archive PDF Report."""
        try:
            from app.services.report_pdf_service import ReportPDFGenerator
            out_pdf = ReportPDFGenerator.generate_target_archive_pdf()
            msgbox.showinfo("Export Successful", f"Sales Target Archive Report PDF successfully generated:\n{out_pdf}")
            try:
                import os
                os.startfile(out_pdf)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Error", f"Failed to export Target Archive Report:\n{str(e)}")
