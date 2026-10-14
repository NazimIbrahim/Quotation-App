"""
Quotation List View: Comprehensive table of all quotes with search,
status filters, approvals, and one-click PDF generation.
"""
import os
import subprocess
import tkinter.messagebox as msgbox
import customtkinter as ctk

from app.ui.theme import Theme
from app.services.quotation_service import QuotationService
from app.services.pdf_service import CeramicPDFGenerator
from app.database.models import Quotation, SalesPerson


class QuotationListView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.selected_status = "All"
        self.selected_salesperson_id = None
        self.salespersons_cache = []
        self.search_text = ""

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        # 1. Top Bar: Header & Actions
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 12))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Quotations Management",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="View, filter, manage approvals, and export printable ceramic quotations",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right")

        new_btn = ctk.CTkButton(
            btn_box,
            text="+ Create Quotation",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            command=lambda: self.controller.show_view("quotation_editor", None),
            height=36
        )
        new_btn.pack(side="right", padx=(8, 0))

        # 2. Filter & Search Controls Bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=24, pady=(0, 12))

        # Status Filter Pills
        self.status_segment = ctk.CTkSegmentedButton(
            filter_bar,
            values=["All", "Open", "In-Review", "Won", "Lost"],
            command=self.on_status_filter,
            selected_color=Theme.PRIMARY,
            selected_hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_INPUT,
            height=34,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        self.status_segment.set("All")
        self.status_segment.pack(side="left")

        # Salesperson Filter Dropdown
        sp_filter_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        sp_filter_box.pack(side="left", padx=(14, 0))

        ctk.CTkLabel(
            sp_filter_box,
            text="👤 Salesperson:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left", padx=(0, 6))

        self.sp_filter_menu = ctk.CTkOptionMenu(
            sp_filter_box,
            values=["All Sales Associates"],
            command=self.on_salesperson_filter,
            width=210,
            height=34,
            corner_radius=Theme.RADIUS_PILL,
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            button_color=Theme.PRIMARY,
            button_hover_color=Theme.PRIMARY_HOVER,
            dropdown_font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        self.sp_filter_menu.pack(side="left")
        self.load_salespersons()

        # Search box
        search_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        search_box.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="Search quote #, customer, phone...",
            width=260,
            height=34,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self.search_entry.bind("<Return>", lambda e: self.on_search())

        search_btn = ctk.CTkButton(
            search_box,
            text="Search",
            width=70,
            height=34,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            hover_color=Theme.PRIMARY,
            command=self.on_search
        )
        search_btn.pack(side="left")

        # 3. Main Quotations Table Frame
        self.table_card = ctk.CTkFrame(
            self,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        self.table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Table Banner Frame (Shown when salesperson or other filter is active)
        self.banner_frame = ctk.CTkFrame(self.table_card, fg_color=("#F5EBE1", "#2D2620"), corner_radius=8)

        # Table Header Row (Stone)
        self.header_frame = ctk.CTkFrame(self.table_card, fg_color=(Theme.STONE, "#242220"), corner_radius=10, height=36)
        self.header_frame.pack(fill="x", padx=(18, 29), pady=(12, 6))

        weights = [3, 3, 2, 2, 2, 2, 5]
        for idx, w in enumerate(weights):
            self.header_frame.grid_columnconfigure(idx, weight=w, uniform="quotelist")

        cols = ["QUOTATION # / DATE", "CUSTOMER / PHONE", "SALES REP", "NET TOTAL", "OUTSTANDING", "STATUS", "ACTIONS"]
        for idx, text in enumerate(cols):
            ctk.CTkLabel(
                self.header_frame,
                text=text,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER),
                anchor="w"
            ).grid(row=0, column=idx, padx=8, pady=8, sticky="w")

        # Scrollable rows frame
        self.rows_frame = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def load_salespersons(self):
        try:
            self.salespersons_cache = list(
                SalesPerson.select().where(SalesPerson.is_active == True).order_by(SalesPerson.name.asc())
            )
            options = ["All Sales Associates"] + [
                f"{s.name} ({s.role})" if s.role else s.name
                for s in self.salespersons_cache
            ]
            self.sp_filter_menu.configure(values=options)
            if self.selected_salesperson_id is None:
                self.sp_filter_menu.set("All Sales Associates")
        except Exception as e:
            print(f"Error loading salespersons: {e}")

    def on_salesperson_filter(self, val):
        if val == "All Sales Associates":
            self.selected_salesperson_id = None
        else:
            matched = None
            for s in self.salespersons_cache:
                formatted = f"{s.name} ({s.role})" if s.role else s.name
                if val == formatted or val == s.name:
                    matched = s
                    break
            self.selected_salesperson_id = matched.id if matched else None
        self.refresh_table()

    def clear_salesperson_filter(self):
        self.selected_salesperson_id = None
        self.sp_filter_menu.set("All Sales Associates")
        self.refresh_table()

    def _on_search_key(self, event=None):
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(250, self.on_search)

    def on_status_filter(self, val):
        self.selected_status = val
        self.refresh_table()

    def on_search(self):
        self.search_text = self.search_entry.get().strip()
        self.refresh_table()

    def refresh_table(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        quotes = QuotationService.get_all_quotations(
            status=self.selected_status,
            sales_person_id=self.selected_salesperson_id,
            search_query=self.search_text
        )

        # Update salesperson filter banner
        for w in self.banner_frame.winfo_children():
            w.destroy()

        if self.selected_salesperson_id:
            sp = next((s for s in self.salespersons_cache if s.id == self.selected_salesperson_id), None)
            sp_name = sp.name if sp else "Selected Salesperson"
            sp_role = f" ({sp.role})" if sp and sp.role else ""

            total_count = len(quotes)
            won_credit = sum(q.get_credit_for_salesperson(self.selected_salesperson_id) for q in quotes if q.status == "Won")
            pipe_credit = sum(q.get_credit_for_salesperson(self.selected_salesperson_id) for q in quotes if q.status in ["Open", "In-Review"])
            total_credit = won_credit + pipe_credit

            self.banner_frame.pack(fill="x", padx=(18, 29), pady=(8, 2), before=self.header_frame)

            banner_left = ctk.CTkFrame(self.banner_frame, fg_color="transparent")
            banner_left.pack(side="left", padx=12, pady=6)

            ctk.CTkLabel(
                banner_left,
                text=f"👤 Filtered by: {sp_name}{sp_role}  •  {total_count} quotes  |  Won Achieved: ₹{won_credit:,.2f}  |  Active Pipeline: ₹{pipe_credit:,.2f}  |  Total Credit: ₹{total_credit:,.2f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).pack(side="left")

            ctk.CTkButton(
                self.banner_frame,
                text="✕ Clear Filter",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                width=100,
                height=24,
                corner_radius=Theme.RADIUS_PILL,
                fg_color=Theme.BTN_SECONDARY_BG,
                text_color=(Theme.BLACK, Theme.PAPER),
                border_width=Theme.BORDER_WIDTH_BUTTON,
                hover_color=Theme.DANGER,
                command=self.clear_salesperson_filter
            ).pack(side="right", padx=12, pady=6)
        else:
            self.banner_frame.pack_forget()

        if not quotes:
            empty_lbl = ctk.CTkLabel(
                self.rows_frame,
                text="No quotations found matching criteria.",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13),
                text_color=("#615D56", "#A8A297")
            )
            empty_lbl.pack(pady=40)
            return

        weights = [3, 3, 2, 2, 2, 2, 5]
        for q in quotes:
            row_frame = ctk.CTkFrame(self.rows_frame, fg_color=("#FAF8F5", "#181615"), corner_radius=8)
            row_frame.pack(fill="x", pady=3)
            for idx, w in enumerate(weights):
                row_frame.grid_columnconfigure(idx, weight=w, uniform="quotelist")

            # Col 0: Quote No & Date
            q_date = q.quotation_date.strftime("%d-%b-%Y") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date)
            c0 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c0.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            q_num_lbl = ctk.CTkLabel(
                c0,
                text=q.quotation_number,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=Theme.PRIMARY,
                cursor="hand2"
            )
            q_num_lbl.pack(anchor="w")
            q_num_lbl.bind("<Button-1>", lambda e, qid=q.id: self.controller.show_view("quotation_editor", qid))
            ctk.CTkLabel(
                c0,
                text=q_date,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                text_color=("#615D56", "#A8A297")
            ).pack(anchor="w")

            # Col 1: Customer & Phone
            c1 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c1.grid(row=0, column=1, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(
                c1,
                text=q.customer_name[:26],
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).pack(anchor="w")
            ctk.CTkLabel(
                c1,
                text=q.customer_phone,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                text_color=("#615D56", "#A8A297")
            ).pack(anchor="w")

            # Col 2: Sales Person
            c2 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c2.grid(row=0, column=2, padx=8, pady=8, sticky="w")
            lead_name = q.sales_person_name or "Unassigned"
            has_assisted = bool(getattr(q, "assisted_by_name", None))

            if self.selected_salesperson_id:
                my_credit = q.get_credit_for_salesperson(self.selected_salesperson_id)
                if q.sales_person_id == self.selected_salesperson_id:
                    role_tag = "👑 Lead Rep"
                    col_role = Theme.PRIMARY
                else:
                    role_tag = "🤝 Assisted Partner"
                    col_role = Theme.SUCCESS

                ctk.CTkLabel(
                    c2,
                    text=lead_name,
                    font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold" if q.sales_person_id == self.selected_salesperson_id else "normal"),
                    text_color=(Theme.BLACK, Theme.PAPER)
                ).pack(anchor="w")

                ctk.CTkLabel(
                    c2,
                    text=f"{role_tag} • Credit: ₹{my_credit:,.0f}",
                    font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9, weight="bold"),
                    text_color=col_role
                ).pack(anchor="w")
            else:
                ctk.CTkLabel(
                    c2,
                    text=lead_name,
                    font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                    text_color=(Theme.BLACK, Theme.PAPER)
                ).pack(anchor="w")
                if has_assisted:
                    split_info = f"🤝 + {q.assisted_by_name} ({q.assisted_share_value:.0f}%)" if q.split_type == "percentage" else f"🤝 + {q.assisted_by_name} (₹{q.assisted_share_amount:,.0f})"
                    ctk.CTkLabel(
                        c2,
                        text=split_info,
                        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9, weight="bold"),
                        text_color=Theme.PRIMARY
                    ).pack(anchor="w")

            # Col 3: Net Total
            ctk.CTkLabel(
                row_frame,
                text=f"₹ {q.net_total:,.2f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).grid(row=0, column=3, padx=8, pady=8, sticky="w")

            # Col 4: Outstanding Balance & Payment State
            bal = q.get_outstanding_balance()
            bal_col = Theme.DANGER if bal > 0 else Theme.SUCCESS
            c4 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c4.grid(row=0, column=4, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(
                c4,
                text=f"₹ {bal:,.2f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=bal_col
            ).pack(anchor="w")
            pmt_status = q.get_payment_status()
            ctk.CTkLabel(
                c4,
                text=pmt_status,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9),
                text_color=("#615D56", "#A8A297")
            ).pack(anchor="w")

            # Col 5: Status Badge
            status_col, _ = Theme.get_status_color(q.status)
            c5 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c5.grid(row=0, column=5, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(
                c5,
                text=f"● {q.status}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=status_col
            ).pack(anchor="w")

            # Col 6: Action Buttons
            c6 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c6.grid(row=0, column=6, padx=6, pady=6, sticky="w")

            # PDF Export & Open Button (Coral)
            pdf_btn = ctk.CTkButton(
                c6,
                text="📄 PDF",
                width=46,
                height=26,
                corner_radius=Theme.RADIUS_SM,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                command=lambda qid=q.id: self.export_pdf(qid)
            )
            pdf_btn.pack(side="left", padx=2)

            # Encrypted PDF Button (Muted slate)
            enc_pdf_btn = ctk.CTkButton(
                c6,
                text="🔒 Enc",
                width=46,
                height=26,
                corner_radius=Theme.RADIUS_SM,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=("#475569", "#334155"),
                text_color="#FFFFFF",
                hover_color=("#334155", "#1E293B"),
                command=lambda qid=q.id: self.export_pdf(qid, encrypted=True)
            )
            enc_pdf_btn.pack(side="left", padx=2)

            # Edit Button
            edit_btn = ctk.CTkButton(
                c6,
                text="✏️ Edit",
                width=48,
                height=26,
                corner_radius=Theme.RADIUS_SM,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=Theme.BTN_SECONDARY_BG,
                text_color=(Theme.BLACK, Theme.PAPER),
                hover_color=Theme.PRIMARY,
                command=lambda qid=q.id: self.controller.show_view("quotation_editor", qid)
            )
            edit_btn.pack(side="left", padx=2)

            # Payment Tracking Button
            pmt_btn = ctk.CTkButton(
                c6,
                text="💳 Pay",
                width=46,
                height=26,
                corner_radius=Theme.RADIUS_SM,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=Theme.BTN_SECONDARY_BG,
                text_color=(Theme.BLACK, Theme.PAPER),
                hover_color=Theme.SUCCESS,
                command=lambda qid=q.id: self.controller.show_view("payment_tracking", qid)
            )
            pmt_btn.pack(side="left", padx=2)

            # Status / Approval quick dropdown
            status_menu = ctk.CTkOptionMenu(
                c6,
                values=["Open", "In-Review", "Won", "Lost"],
                width=78,
                height=26,
                corner_radius=Theme.RADIUS_SM,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                fg_color=Theme.BTN_SECONDARY_BG,
                text_color=(Theme.BLACK, Theme.PAPER),
                button_color=Theme.PRIMARY,
                command=lambda new_val, qid=q.id: self.change_status(qid, new_val)
            )
            status_menu.set(q.status)
            status_menu.pack(side="left", padx=2)

            # Delete button
            del_btn = ctk.CTkButton(
                c6,
                text="🗑️",
                width=26,
                height=26,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                fg_color="transparent",
                text_color=Theme.DANGER,
                hover_color=("#FEE2E2", "#7F1D1D"),
                command=lambda qid=q.id, qnum=q.quotation_number: self.delete_quote(qid, qnum)
            )
            del_btn.pack(side="left", padx=2)

    def export_pdf(self, quote_id: int, encrypted: bool = False):
        try:
            pdf_path = CeramicPDFGenerator.generate_quotation_pdf(quote_id, encrypted=encrypted)
            title = "Encrypted PDF Export Complete" if encrypted else "PDF Export Complete"
            desc = (
                f"Encrypted Quotation PDF generated successfully!\n\n"
                f"• Brands have been removed.\n"
                f"• Products masked with AMA codes (e.g. HSDS-AMA).\n"
                f"• Database records remain 100% untouched.\n\n"
                f"Location:\n{pdf_path}"
            ) if encrypted else f"Quotation PDF generated successfully!\n\nLocation:\n{pdf_path}"

            msgbox.showinfo(title, desc)
            # Open PDF in default viewer
            try:
                os.startfile(pdf_path)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Export Failed", f"Could not generate PDF:\n{str(e)}")

    def change_status(self, quote_id: int, new_status: str):
        active_user = self.controller.get_active_user()
        QuotationService.update_status(quote_id, new_status, manager=active_user)
        self.refresh_table()

    def delete_quote(self, quote_id: int, quote_num: str):
        confirm = msgbox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete Quotation {quote_num}?\nThis action cannot be undone."
        )
        if confirm:
            QuotationService.delete_quotation(quote_id)
            self.refresh_table()
