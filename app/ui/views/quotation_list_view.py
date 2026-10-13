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
            command=lambda: self.controller.show_view("quotation_editor", None),
            height=34
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
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        self.status_segment.set("All")
        self.status_segment.pack(side="left")

        # Search box
        search_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        search_box.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="Search quote #, customer, phone...",
            width=260,
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self.search_entry.bind("<Return>", lambda e: self.on_search())

        search_btn = ctk.CTkButton(
            search_box,
            text="Search",
            width=65,
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=(Theme.STONE, "#2B2824"),
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.PRIMARY,
            command=self.on_search
        )
        search_btn.pack(side="left")

        # 3. Main Quotations Table Frame
        self.table_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=1,
            border_color=(Theme.STONE, "#38342E")
        )
        self.table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Table Header Row (Stone)
        self.header_frame = ctk.CTkFrame(self.table_card, fg_color=(Theme.STONE, "#242220"), corner_radius=8, height=38)
        self.header_frame.pack(fill="x", padx=12, pady=(12, 6))
        self.header_frame.grid_columnconfigure(0, weight=2)  # Quote No & Date
        self.header_frame.grid_columnconfigure(1, weight=3)  # Customer & Phone
        self.header_frame.grid_columnconfigure(2, weight=2)  # Sales Person
        self.header_frame.grid_columnconfigure(3, weight=2)  # Net Total
        self.header_frame.grid_columnconfigure(4, weight=2)  # Balance
        self.header_frame.grid_columnconfigure(5, weight=2)  # Status
        self.header_frame.grid_columnconfigure(6, weight=4)  # Actions

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
            search_query=self.search_text
        )

        if not quotes:
            empty_lbl = ctk.CTkLabel(
                self.rows_frame,
                text="No quotations found matching criteria.",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13),
                text_color=("#615D56", "#A8A297")
            )
            empty_lbl.pack(pady=40)
            return

        for q in quotes:
            row_frame = ctk.CTkFrame(self.rows_frame, fg_color=("#F8FAFC", "#111827"), corner_radius=8)
            row_frame.pack(fill="x", pady=3)
            row_frame.grid_columnconfigure(0, weight=2)
            row_frame.grid_columnconfigure(1, weight=3)
            row_frame.grid_columnconfigure(2, weight=2)
            row_frame.grid_columnconfigure(3, weight=2)
            row_frame.grid_columnconfigure(4, weight=2)
            row_frame.grid_columnconfigure(5, weight=2)
            row_frame.grid_columnconfigure(6, weight=4)

            # Col 0: Quote No & Date
            q_date = q.quotation_date.strftime("%d-%b-%Y") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date)
            c0 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c0.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(
                c0,
                text=q.quotation_number,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=Theme.PRIMARY
            ).pack(anchor="w")
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
            ctk.CTkLabel(
                row_frame,
                text=q.sales_person_name,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).grid(row=0, column=2, padx=8, pady=8, sticky="w")

            # Col 3: Net Total
            ctk.CTkLabel(
                row_frame,
                text=f"₹ {q.net_total:,.2f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).grid(row=0, column=3, padx=8, pady=8, sticky="w")

            # Col 4: Outstanding Balance
            bal = q.get_outstanding_balance()
            bal_col = Theme.DANGER if bal > 0 else Theme.SUCCESS
            ctk.CTkLabel(
                row_frame,
                text=f"₹ {bal:,.2f}",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=bal_col
            ).grid(row=0, column=4, padx=8, pady=8, sticky="w")

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
            pmt_status = q.get_payment_status()
            ctk.CTkLabel(
                c5,
                text=pmt_status,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9),
                text_color=("#615D56", "#A8A297")
            ).pack(anchor="w")

            # Col 6: Action Buttons
            c6 = ctk.CTkFrame(row_frame, fg_color="transparent")
            c6.grid(row=0, column=6, padx=8, pady=6, sticky="w")

            # PDF Export & Open Button (Coral)
            pdf_btn = ctk.CTkButton(
                c6,
                text="📄 PDF",
                width=52,
                height=26,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                command=lambda qid=q.id: self.export_pdf(qid)
            )
            pdf_btn.pack(side="left", padx=2)

            # Edit Button
            edit_btn = ctk.CTkButton(
                c6,
                text="✏️ Edit",
                width=50,
                height=26,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=(Theme.STONE, "#2B2824"),
                text_color=(Theme.BLACK, Theme.PAPER),
                hover_color=Theme.PRIMARY,
                command=lambda qid=q.id: self.controller.show_view("quotation_editor", qid)
            )
            edit_btn.pack(side="left", padx=2)

            # Payment Tracking Button
            pmt_btn = ctk.CTkButton(
                c6,
                text="💳 Pay",
                width=50,
                height=26,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=(Theme.STONE, "#2B2824"),
                text_color=(Theme.BLACK, Theme.PAPER),
                hover_color=Theme.SUCCESS,
                command=lambda qid=q.id: self.controller.show_view("payment_tracking", qid)
            )
            pmt_btn.pack(side="left", padx=2)

            # Status / Approval quick dropdown
            status_menu = ctk.CTkOptionMenu(
                c6,
                values=["Open", "In-Review", "Won", "Lost"],
                width=80,
                height=26,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                fg_color=("#F1F5F9", "#1F2937"),
                text_color=(Theme.BLACK, Theme.PAPER),
                button_color=("#CBD5E1", "#4B5563"),
                command=lambda new_val, qid=q.id: self.change_status(qid, new_val)
            )
            status_menu.set(q.status)
            status_menu.pack(side="left", padx=2)

            # Delete button
            del_btn = ctk.CTkButton(
                c6,
                text="🗑️",
                width=28,
                height=26,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                fg_color="transparent",
                text_color=Theme.DANGER,
                hover_color=("#FEE2E2", "#7F1D1D"),
                command=lambda qid=q.id, qnum=q.quotation_number: self.delete_quote(qid, qnum)
            )
            del_btn.pack(side="left", padx=2)

    def export_pdf(self, quote_id: int):
        try:
            pdf_path = CeramicPDFGenerator.generate_quotation_pdf(quote_id)
            msgbox.showinfo(
                "PDF Export Complete",
                f"Quotation PDF generated successfully!\n\nLocation:\n{pdf_path}"
            )
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
