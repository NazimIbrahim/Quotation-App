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
            text_color=("#0F172A", "#F8FAFC"),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Monthly targets, sales performance tracking & discount approval workflows",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#64748B", "#94A3B8"),
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
            command=self.open_alter_target_modal,
            height=34
        )
        alter_target_btn.pack(side="left", padx=(0, 8))

        export_archive_btn = ctk.CTkButton(
            top_btn_box,
            text="📊 Target Archive PDF",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=self.export_target_archive_report,
            height=34
        )
        export_archive_btn.pack(side="left", padx=(0, 8))

        add_rep_btn = ctk.CTkButton(
            top_btn_box,
            text="+ Add Team Member",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.SECONDARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.open_member_modal,
            height=34
        )
        add_rep_btn.pack(side="left")

        # Scroll body
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 2. Manager Approvals Queue (Highlighted if any quotes in-review)
        self.approval_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
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
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        self.scope_segment = ctk.CTkSegmentedButton(
            target_toolbar,
            values=["This Month", "This Week", "Base Monthly"],
            command=self.on_scope_changed,
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
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
                r = ctk.CTkFrame(self.approvals_container, fg_color=("#EDE9FE", "#1E1B4B"), corner_radius=8)
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
                    height=28,
                    command=lambda qid=q.id: self.approve_quote(qid, Quotation.STATUS_WON)
                ).pack(side="left", padx=3)

                ctk.CTkButton(
                    act_box,
                    text="Reject ✕",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=Theme.DANGER,
                    hover_color=Theme.DANGER_HOVER,
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
                corner_radius=12,
                fg_color=("white", "#1E293B"),
                border_width=1,
                border_color=("#E2E8F0", "#334155")
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
                text_color=("#0F172A", "#F8FAFC")
            ).pack(side="left")

            role_bg = Theme.INFO if sp.role == SalesPerson.ROLE_MANAGER else Theme.PRIMARY
            ctk.CTkLabel(
                name_box,
                text=f"  [{sp.role.upper()}]  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white",
                fg_color=role_bg,
                corner_radius=4
            ).pack(side="left", padx=8)

            ctk.CTkLabel(
                name_box,
                text=f"📞 {sp.contact_number}  |  ✉ {sp.email or 'N/A'}",
                font=ctk.CTkFont(size=11),
                text_color=("#64748B", "#94A3B8")
            ).pack(side="left", padx=8)

            btn_box = ctk.CTkFrame(top_r, fg_color="transparent")
            btn_box.pack(side="right")

            alter_btn = ctk.CTkButton(
                btn_box,
                text="🎯 Alter Target",
                font=ctk.CTkFont(size=10, weight="bold"),
                width=95,
                height=26,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                command=lambda m=sp: self.open_alter_target_modal(m)
            )
            alter_btn.pack(side="left", padx=(0, 6))

            edit_btn = ctk.CTkButton(
                btn_box,
                text="Edit Info",
                font=ctk.CTkFont(size=10),
                width=75,
                height=26,
                fg_color=("#E2E8F0", "#334155"),
                text_color=("#0F172A", "#F8FAFC"),
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

            metrics_grid = ctk.CTkFrame(card, fg_color=("#F8FAFC", "#0F172A"), corner_radius=8)
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
                    text_color=("#64748B", "#94A3B8")
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
                fg_color=("#E2E8F0", "#334155")
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
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color=("#64748B", "#94A3B8")).pack(anchor="w")
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

    def open_member_modal(self, member=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Team Member" if member else "Add Team Member")
        dialog.geometry("460x420")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Sales Team Member", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(f, text="Full Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        name_ent = ctk.CTkEntry(f)
        if member:
            name_ent.insert(0, member.name)
        name_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Contact Number:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        phone_ent = ctk.CTkEntry(f)
        if member:
            phone_ent.insert(0, member.contact_number)
        phone_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Role:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        role_combo = ctk.CTkComboBox(f, values=[SalesPerson.ROLE_SALES, SalesPerson.ROLE_MANAGER])
        if member:
            role_combo.set(member.role)
        role_combo.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Monthly Sales Target (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        target_ent = ctk.CTkEntry(f)
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
