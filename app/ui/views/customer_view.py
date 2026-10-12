"""
Customer Management View: Customer CRM directory, contact profiles,
and full history of past quotations and site orders.
"""
import tkinter.messagebox as msgbox
import customtkinter as ctk

from app.ui.theme import Theme
from app.database.models import Customer, Quotation
from app.services.pdf_service import CeramicPDFGenerator


class CustomerManagementView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.selected_customer = None

        self.build_ui()
        self.refresh_customer_list()

    def build_ui(self):
        # 1. Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Customer & Client Management",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Architects, builders, home owners directory & quotation history",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#64748B", "#94A3B8"),
        )
        subtitle.pack(anchor="w")

        add_cust_btn = ctk.CTkButton(
            top_bar,
            text="+ Add New Customer",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.open_customer_editor_modal,
            height=34
        )
        add_cust_btn.pack(side="right")

        # 2. Main Two-Column Layout (Left: Customer Directory List, Right: Profile & Quote History)
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        main_split.grid_columnconfigure(0, weight=2)
        main_split.grid_columnconfigure(1, weight=3)

        # Left Column: Customer Directory Card
        left_card = ctk.CTkFrame(
            main_split,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        left_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        left_header = ctk.CTkFrame(left_card, fg_color="transparent")
        left_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            left_header,
            text="👥 Customer Directory",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            left_card,
            placeholder_text="Filter customer name or phone...",
            height=30,
            font=ctk.CTkFont(size=11)
        )
        self.search_entry.pack(fill="x", padx=16, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_customer_list())

        self.customer_scroll = ctk.CTkScrollableFrame(left_card, fg_color="transparent")
        self.customer_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Right Column: Customer Details & Past Quotes History Card
        self.right_card = ctk.CTkFrame(
            main_split,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.right_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        self.profile_container = ctk.CTkFrame(self.right_card, fg_color="transparent")
        self.profile_container.pack(fill="both", expand=True, padx=16, pady=16)

    def refresh_customer_list(self):
        for widget in self.customer_scroll.winfo_children():
            widget.destroy()

        query_text = self.search_entry.get().strip()
        customers = Customer.select().order_by(Customer.name)
        if query_text:
            pat = f"%{query_text}%"
            customers = customers.where(
                (Customer.name.ilike(pat)) |
                (Customer.mobile_number.ilike(pat)) |
                (Customer.delivery_address.ilike(pat))
            )

        cust_list = list(customers)
        if not cust_list:
            ctk.CTkLabel(self.customer_scroll, text="No matching customers found.").pack(pady=20)
            return

        for c in cust_list:
            is_active = self.selected_customer and self.selected_customer.id == c.id
            card_bg = (Theme.PRIMARY, "#0284C7") if is_active else ("#F8FAFC", "#0F172A")
            text_color = "white" if is_active else ("#0F172A", "#F8FAFC")
            sub_color = "#E0F2FE" if is_active else ("#64748B", "#94A3B8")

            btn_text = f"{c.name}\n{c.mobile_number}  •  {c.get_quote_count()} Quotes"
            c_btn = ctk.CTkButton(
                self.customer_scroll,
                text=btn_text,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=text_color,
                fg_color=card_bg,
                hover_color=Theme.PRIMARY_HOVER,
                corner_radius=8,
                anchor="w",
                height=46,
                command=lambda cust=c: self.select_customer(cust)
            )
            c_btn.pack(fill="x", pady=3)

        # Select first by default if none selected
        if not self.selected_customer and cust_list:
            self.select_customer(cust_list[0])

    def select_customer(self, customer: Customer):
        self.selected_customer = customer
        self.render_customer_profile()

    def render_customer_profile(self):
        for widget in self.profile_container.winfo_children():
            widget.destroy()

        if not self.selected_customer:
            ctk.CTkLabel(self.profile_container, text="Select a customer from the left directory.").pack(pady=40)
            return

        c = self.selected_customer

        # Header with Name & Edit button
        header_row = ctk.CTkFrame(self.profile_container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))

        title_box = ctk.CTkFrame(header_row, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=c.name,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=18, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text=f"📞 {c.mobile_number}  |  ✉ {c.email or 'No email'}",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color=("#64748B", "#94A3B8")
        ).pack(anchor="w")

        edit_btn = ctk.CTkButton(
            header_row,
            text="✏️ Edit Info",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=80,
            height=28,
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            command=lambda: self.open_customer_editor_modal(c)
        )
        edit_btn.pack(side="right")

        # Stats summary row
        stats_frame = ctk.CTkFrame(self.profile_container, fg_color=("#F8FAFC", "#0F172A"), corner_radius=8)
        stats_frame.pack(fill="x", pady=(0, 12))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        q_count = c.get_quote_count()
        total_won = c.get_total_won_value()

        self.create_profile_stat(stats_frame, 0, "Total Quotations", str(q_count))
        self.create_profile_stat(stats_frame, 1, "Won Closed Orders", f"₹ {total_won:,.2f}")
        self.create_profile_stat(stats_frame, 2, "Site Location", c.site_location or "Standard Delivery")

        # Delivery Address Box
        addr_box = ctk.CTkFrame(self.profile_container, fg_color=("#F1F5F9", "#111827"), corner_radius=8)
        addr_box.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            addr_box,
            text="📍 Default Delivery Address:",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            addr_box,
            text=c.delivery_address,
            font=ctk.CTkFont(size=11),
            text_color=("#334155", "#CBD5E1"),
            wraplength=480,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Quotations History Section
        ctk.CTkLabel(
            self.profile_container,
            text="📜 Quotation History for This Client",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(anchor="w", pady=(0, 6))

        history_scroll = ctk.CTkScrollableFrame(self.profile_container, fg_color="transparent", height=240)
        history_scroll.pack(fill="both", expand=True)

        quotes = list(c.quotations.order_by(Quotation.id.desc()))
        if not quotes:
            ctk.CTkLabel(history_scroll, text="No quotes generated for this customer yet.").pack(pady=20)
            return

        for q in quotes:
            r = ctk.CTkFrame(history_scroll, fg_color=("#F8FAFC", "#0F172A"), corner_radius=6)
            r.pack(fill="x", pady=3)
            r.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            q_d_str = q.quotation_date.strftime("%d-%b-%Y") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date)

            ctk.CTkLabel(
                r,
                text=q.quotation_number,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Theme.PRIMARY
            ).grid(row=0, column=0, padx=8, pady=6, sticky="w")

            ctk.CTkLabel(
                r,
                text=q_d_str,
                font=ctk.CTkFont(size=10),
                text_color=("#64748B", "#94A3B8")
            ).grid(row=0, column=1, padx=8, pady=6, sticky="w")

            ctk.CTkLabel(
                r,
                text=f"₹ {q.net_total:,.2f}",
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=0, column=2, padx=8, pady=6, sticky="w")

            status_col, _ = Theme.get_status_color(q.status)
            ctk.CTkLabel(
                r,
                text=f"● {q.status}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=status_col
            ).grid(row=0, column=3, padx=8, pady=6, sticky="w")

            # Actions
            btn_box = ctk.CTkFrame(r, fg_color="transparent")
            btn_box.grid(row=0, column=4, padx=8, pady=4, sticky="e")

            ctk.CTkButton(
                btn_box,
                text="PDF",
                width=45,
                height=22,
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=Theme.ACCENT_GOLD,
                command=lambda qid=q.id: self.export_pdf(qid)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_box,
                text="Edit",
                width=45,
                height=22,
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=Theme.PRIMARY,
                command=lambda qid=q.id: self.controller.show_view("quotation_editor", qid)
            ).pack(side="left", padx=2)

    def create_profile_stat(self, parent, col, title, val):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=10), text_color=("#64748B", "#94A3B8")).pack(anchor="w")
        ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.PRIMARY).pack(anchor="w")

    def export_pdf(self, quote_id: int):
        try:
            pdf_path = CeramicPDFGenerator.generate_quotation_pdf(quote_id)
            msgbox.showinfo("PDF Generated", f"PDF exported successfully:\n{pdf_path}")
            import os
            os.startfile(pdf_path)
        except Exception as e:
            msgbox.showerror("Error", str(e))

    def open_customer_editor_modal(self, customer=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Customer" if customer else "New Customer Profile")
        dialog.geometry("480x440")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Customer Profile Details",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(f, text="Customer / Architect Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        name_ent = ctk.CTkEntry(f, font=ctk.CTkFont(size=11))
        if customer:
            name_ent.insert(0, customer.name)
        name_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Mobile Number:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        phone_ent = ctk.CTkEntry(f, font=ctk.CTkFont(size=11))
        if customer:
            phone_ent.insert(0, customer.mobile_number)
        phone_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Email Address (Optional):", font=ctk.CTkFont(size=11)).pack(anchor="w")
        email_ent = ctk.CTkEntry(f, font=ctk.CTkFont(size=11))
        if customer and customer.email:
            email_ent.insert(0, customer.email)
        email_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Site / Project Location Reference:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        site_ent = ctk.CTkEntry(f, font=ctk.CTkFont(size=11))
        if customer and customer.site_location:
            site_ent.insert(0, customer.site_location)
        site_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Delivery / Godown Address:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        addr_ent = ctk.CTkEntry(f, font=ctk.CTkFont(size=11))
        if customer:
            addr_ent.insert(0, customer.delivery_address)
        addr_ent.pack(fill="x", pady=(2, 14))

        def save_profile():
            n = name_ent.get().strip()
            p = phone_ent.get().strip()
            if not n or not p:
                msgbox.showwarning("Notice", "Name and Mobile number are required.", parent=dialog)
                return
            if customer:
                customer.name = n
                customer.mobile_number = p
                customer.email = email_ent.get().strip() or None
                customer.site_location = site_ent.get().strip() or None
                customer.delivery_address = addr_ent.get().strip()
                customer.save()
            else:
                new_c = Customer.create(
                    name=n,
                    mobile_number=p,
                    email=email_ent.get().strip() or None,
                    site_location=site_ent.get().strip() or None,
                    delivery_address=addr_ent.get().strip()
                )
                self.selected_customer = new_c
            dialog.destroy()
            self.refresh_customer_list()
            self.render_customer_profile()

        ctk.CTkButton(
            dialog,
            text="Save Profile",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=save_profile
        ).pack(pady=(0, 20))
