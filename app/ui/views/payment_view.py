"""
Payment View: Track and record incoming payments against quotations,
manage clearance of Cheques/UPI, and monitor outstanding receivables.
"""
from datetime import date
import tkinter.messagebox as msgbox
import customtkinter as ctk

from app.ui.theme import Theme
from app.services.payment_service import PaymentService
from app.database.models import Quotation, Payment


class PaymentTrackingView(ctk.CTkFrame):
    def __init__(self, master, controller, preselected_quote_id=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.selected_quote_id = preselected_quote_id
        self.quotes_cache = []

        self.build_ui()
        self.load_quotations()

    def build_ui(self):
        # 1. Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Payment Tracking & Receivables",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Record client advances, track GPay/PhonePe/Bank/Cheques, and monitor balances",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        # Scrollable container
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 2. Quotation Selector Card
        select_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        select_card.pack(fill="x", pady=(0, 14))

        s_bar = ctk.CTkFrame(select_card, fg_color="transparent")
        s_bar.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            s_bar,
            text="Select Quotation to Manage Payments:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left", padx=(0, 10))

        self.quote_selector = ctk.CTkComboBox(
            s_bar,
            values=["Loading..."],
            width=420,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            font=ctk.CTkFont(size=11),
            command=self.on_quote_change
        )
        self.quote_selector.pack(side="left")

        # 3. Financial Summary KPI Row for Selected Quotation
        self.summary_row = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        self.summary_row.pack(fill="x", pady=(0, 14))
        self.summary_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Net Total Box
        self.box_net = self.create_mini_kpi(self.summary_row, 0, "NET PAYABLE", "₹ 0.00", Theme.PRIMARY)
        self.box_cleared = self.create_mini_kpi(self.summary_row, 1, "CLEARED PAYMENTS", "₹ 0.00", Theme.SUCCESS)
        self.box_pending = self.create_mini_kpi(self.summary_row, 2, "PENDING CLEARANCE", "₹ 0.00", Theme.WARNING)
        self.box_balance = self.create_mini_kpi(self.summary_row, 3, "OUTSTANDING BALANCE", "₹ 0.00", Theme.DANGER)

        # 4. Middle Section: Two Columns (Left: Record Payment Entry, Right: Payment History Table)
        split_frame = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        split_frame.pack(fill="x", pady=(0, 14))
        split_frame.grid_columnconfigure(0, weight=2)
        split_frame.grid_columnconfigure(1, weight=3)

        # Left Column: "Record Payment Entry"
        record_card = ctk.CTkFrame(
            split_frame,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        record_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            record_card,
            text="➕ Record New Payment",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w", padx=16, pady=(14, 10))

        form = ctk.CTkFrame(record_card, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=(0, 14))

        # Amount
        ctk.CTkLabel(form, text="Payment Amount (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(2, 2))
        self.amount_entry = ctk.CTkEntry(
            form,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=12, weight="bold"),
            placeholder_text="e.g. 50000"
        )
        self.amount_entry.pack(fill="x", pady=(0, 8))

        # Payment Mode
        ctk.CTkLabel(form, text="Payment Mode:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(2, 2))
        self.mode_combo = ctk.CTkComboBox(
            form,
            values=[Payment.MODE_GPAY, Payment.MODE_PHONEPE, Payment.MODE_BANK, Payment.MODE_CHEQUE, Payment.MODE_CASH],
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            font=ctk.CTkFont(size=11)
        )
        self.mode_combo.set(Payment.MODE_GPAY)
        self.mode_combo.pack(fill="x", pady=(0, 8))

        # Date
        ctk.CTkLabel(form, text="Payment Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(2, 2))
        self.date_entry = ctk.CTkEntry(
            form,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11)
        )
        self.date_entry.insert(0, str(date.today()))
        self.date_entry.pack(fill="x", pady=(0, 8))

        # Clearance Status
        ctk.CTkLabel(form, text="Clearance Status:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(2, 2))
        self.status_segment = ctk.CTkSegmentedButton(
            form,
            values=[Payment.STATUS_CLEARED, Payment.STATUS_PENDING],
            selected_color=Theme.SUCCESS,
            selected_hover_color=Theme.SUCCESS_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.status_segment.set(Payment.STATUS_CLEARED)
        self.status_segment.pack(fill="x", pady=(0, 8))

        # Reference No / Cheque
        ctk.CTkLabel(form, text="Reference / Cheque / UTR No:", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(2, 2))
        self.ref_entry = ctk.CTkEntry(
            form,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11),
            placeholder_text="UPI Ref / Cheque #"
        )
        self.ref_entry.pack(fill="x", pady=(0, 8))

        # Notes
        ctk.CTkLabel(form, text="Notes / Remarks:", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(2, 2))
        self.notes_entry = ctk.CTkEntry(
            form,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11),
            placeholder_text="e.g. 50% order booking advance"
        )
        self.notes_entry.pack(fill="x", pady=(0, 12))

        # Submit button
        submit_btn = ctk.CTkButton(
            form,
            text="✓ Record Payment Entry",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SUCCESS_BORDER,
            corner_radius=Theme.RADIUS_PILL,
            command=self.submit_payment,
            height=36
        )
        submit_btn.pack(fill="x")

        # Right Column: Existing Payments History
        history_card = ctk.CTkFrame(
            split_frame,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        history_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            history_card,
            text="📜 Payments Recorded for This Quotation",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w", padx=16, pady=(14, 10))

        # Table Header
        h_frame = ctk.CTkFrame(history_card, fg_color=(Theme.STONE, "#242220"), height=30, corner_radius=Theme.RADIUS_SM)
        h_frame.pack(fill="x", padx=12, pady=(0, 4))
        h_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        cols = ["Date", "Amount", "Mode & Ref", "Status", "Actions"]
        for i, c in enumerate(cols):
            ctk.CTkLabel(h_frame, text=c, font=ctk.CTkFont(size=10, weight="bold"), text_color=(Theme.BLACK, Theme.PAPER)).grid(row=0, column=i, padx=4, pady=4, sticky="w")

        self.history_rows_frame = ctk.CTkFrame(history_card, fg_color="transparent")
        self.history_rows_frame.pack(fill="both", expand=True, padx=12, pady=(0, 14))

        # 5. Global Pending Clearances Section
        pending_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        pending_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            pending_card,
            text="⏳ All Pending Uncleared Payments Across Showroom",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=Theme.WARNING
        ).pack(anchor="w", padx=16, pady=(14, 8))

        self.pending_global_frame = ctk.CTkFrame(pending_card, fg_color="transparent")
        self.pending_global_frame.pack(fill="x", padx=16, pady=(0, 14))

    def create_mini_kpi(self, parent, col_idx, title, val, color):
        card = ctk.CTkFrame(
            parent,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        card.grid(row=0, column=col_idx, padx=4, sticky="ew")

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
            text_color=("#615D56", "#A8A297")
        ).pack(anchor="w", padx=12, pady=(10, 2))

        val_lbl = ctk.CTkLabel(
            card,
            text=val,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold"),
            text_color=color
        )
        val_lbl.pack(anchor="w", padx=12, pady=(0, 10))
        return val_lbl

    def load_quotations(self):
        self.quotes_cache = list(Quotation.select().order_by(Quotation.id.desc()))
        if not self.quotes_cache:
            self.quote_selector.configure(values=["No Quotations Available"])
            return

        values = []
        selected_index = 0
        for idx, q in enumerate(self.quotes_cache):
            bal = q.get_outstanding_balance()
            entry = f"{q.quotation_number} - {q.customer_name[:20]} | Net: ₹{q.net_total:,.0f} | Bal: ₹{bal:,.0f}"
            values.append(entry)
            if self.selected_quote_id and q.id == self.selected_quote_id:
                selected_index = idx

        self.quote_selector.configure(values=values)
        self.quote_selector.set(values[selected_index])
        self.selected_quote_id = self.quotes_cache[selected_index].id
        self.refresh_quote_details()
        self.refresh_global_pending()

    def on_quote_change(self, val):
        for q in self.quotes_cache:
            bal = q.get_outstanding_balance()
            entry = f"{q.quotation_number} - {q.customer_name[:20]} | Net: ₹{q.net_total:,.0f} | Bal: ₹{bal:,.0f}"
            if entry == val:
                self.selected_quote_id = q.id
                break
        self.refresh_quote_details()

    def refresh_quote_details(self):
        if not self.selected_quote_id:
            return

        q = Quotation.get_by_id(self.selected_quote_id)
        fin = PaymentService.get_financial_summary(q.id)

        self.box_net.configure(text=f"₹ {fin['net_total']:,.2f}")
        self.box_cleared.configure(text=f"₹ {fin['cleared_amount']:,.2f}")
        self.box_pending.configure(text=f"₹ {fin['pending_amount']:,.2f}")
        self.box_balance.configure(text=f"₹ {fin['outstanding_balance']:,.2f}")

        # Refresh Payments Table
        for widget in self.history_rows_frame.winfo_children():
            widget.destroy()

        payments = PaymentService.get_payments_for_quotation(q.id)
        if not payments:
            ctk.CTkLabel(self.history_rows_frame, text="No payments recorded yet for this quotation.").pack(pady=15)
            return

        for p in payments:
            r = ctk.CTkFrame(self.history_rows_frame, fg_color=("#F8FAFC", "#111827"), corner_radius=Theme.RADIUS_SM)
            r.pack(fill="x", pady=2)
            r.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            p_date_str = p.payment_date.strftime("%d-%b-%Y") if hasattr(p.payment_date, "strftime") else str(p.payment_date)
            ctk.CTkLabel(r, text=p_date_str, font=ctk.CTkFont(size=10)).grid(row=0, column=0, padx=4, pady=4, sticky="w")
            ctk.CTkLabel(r, text=f"₹ {p.amount:,.2f}", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=4, pady=4, sticky="w")

            ref_str = f"{p.payment_mode}" + (f" ({p.reference_number})" if p.reference_number else "")
            ctk.CTkLabel(r, text=ref_str[:22], font=ctk.CTkFont(size=10), text_color=("#615D56", "#A8A297")).grid(row=0, column=2, padx=4, pady=4, sticky="w")

            status_col = Theme.SUCCESS if p.status == Payment.STATUS_CLEARED else Theme.WARNING
            ctk.CTkLabel(r, text=f"● {p.status}", font=ctk.CTkFont(size=10, weight="bold"), text_color=status_col).grid(row=0, column=3, padx=4, pady=4, sticky="w")

            # Action: Toggle Clearance or Delete
            act_box = ctk.CTkFrame(r, fg_color="transparent")
            act_box.grid(row=0, column=4, padx=4, pady=2, sticky="w")

            if p.status == Payment.STATUS_PENDING:
                toggle_btn = ctk.CTkButton(
                    act_box,
                    text="Clear ✓",
                    width=58,
                    height=24,
                    corner_radius=Theme.RADIUS_PILL,
                    border_width=Theme.BORDER_WIDTH_BUTTON,
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color=Theme.SUCCESS,
                    hover_color=Theme.SUCCESS_HOVER,
                    command=lambda pid=p.id: self.toggle_status(pid, Payment.STATUS_CLEARED)
                )
                toggle_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                act_box,
                text="✕",
                width=26,
                height=24,
                corner_radius=Theme.RADIUS_PILL,
                border_width=1,
                border_color=Theme.BTN_DANGER_BORDER,
                fg_color="transparent",
                text_color=Theme.DANGER,
                command=lambda pid=p.id: self.delete_pmt(pid)
            )
            del_btn.pack(side="left", padx=2)

    def refresh_global_pending(self):
        for widget in self.pending_global_frame.winfo_children():
            widget.destroy()

        pending_list = list(
            Payment.select()
            .where(Payment.status == Payment.STATUS_PENDING)
            .order_by(Payment.payment_date.desc())
        )

        if not pending_list:
            ctk.CTkLabel(
                self.pending_global_frame,
                text="No pending cheques or unverified payments. All transactions are cleared!",
                font=ctk.CTkFont(size=11),
                text_color=Theme.SUCCESS
            ).pack(anchor="w", pady=4)
            return

        for p in pending_list:
            r = ctk.CTkFrame(self.pending_global_frame, fg_color=("#FEF3C7", "#78350F"), corner_radius=Theme.RADIUS_SM)
            r.pack(fill="x", pady=2)

            ctk.CTkLabel(
                r,
                text=f"Quote: {p.quotation.quotation_number} ({p.quotation.customer_name})  •  ₹ {p.amount:,.2f} via {p.payment_mode}  •  Ref: {p.reference_number or 'N/A'}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#92400E", "#FDE68A")
            ).pack(side="left", padx=10, pady=6)

            clear_btn = ctk.CTkButton(
                r,
                text="Mark Cleared ✓",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=Theme.SUCCESS,
                hover_color=Theme.SUCCESS_HOVER,
                corner_radius=Theme.RADIUS_PILL,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                width=100,
                height=28,
                command=lambda pid=p.id: self.toggle_status(pid, Payment.STATUS_CLEARED)
            )
            clear_btn.pack(side="right", padx=10)

    def submit_payment(self):
        if not self.selected_quote_id:
            msgbox.showwarning("Notice", "Please select a quotation first.")
            return

        try:
            amt = float(self.amount_entry.get().strip())
            if amt <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError:
            msgbox.showerror("Invalid Input", "Please enter a valid numeric amount.")
            return

        mode = self.mode_combo.get()
        p_status = self.status_segment.get()
        ref = self.ref_entry.get().strip()
        notes = self.notes_entry.get().strip()

        PaymentService.add_payment(
            quotation_id=self.selected_quote_id,
            amount=amt,
            mode=mode,
            status=p_status,
            reference_number=ref,
            notes=notes
        )

        # Clear inputs
        self.amount_entry.delete(0, "end")
        self.ref_entry.delete(0, "end")
        self.notes_entry.delete(0, "end")

        msgbox.showinfo("Payment Recorded", f"Payment of ₹ {amt:,.2f} recorded successfully!")
        self.refresh_quote_details()
        self.refresh_global_pending()

    def toggle_status(self, payment_id: int, new_status: str):
        PaymentService.update_payment_status(payment_id, new_status)
        self.refresh_quote_details()
        self.refresh_global_pending()

    def delete_pmt(self, payment_id: int):
        confirm = msgbox.askyesno("Confirm Delete", "Are you sure you want to remove this payment record?")
        if confirm:
            PaymentService.delete_payment(payment_id)
            self.refresh_quote_details()
            self.refresh_global_pending()
