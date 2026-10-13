"""
Company & PDF Settings View: In-app management of company branding,
logo image upload, GST details, bank accounts, signatures, and printable PDF terms.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
import tkinter.messagebox as msgbox
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image as PILImage

from app.ui.theme import Theme
from app.config import (
    BASE_DIR,
    COMPANY_CONFIG,
    BANK_DETAILS,
    STANDARD_TERMS_AND_CONDITIONS,
    SIGNATORIES,
)
from app.database.models import CompanySetting, Quotation
from app.services.pdf_service import CeramicPDFGenerator


class CompanySettingsView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.setting = CompanySetting.get_settings()
        self.logo_preview_image = None

        self.build_ui()
        self.load_settings()

    def build_ui(self):
        # 1. Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 12))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Company & PDF Settings",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Configure company branding, logo, GSTIN, bank details & quotation terms in PDF",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right")

        preview_btn = ctk.CTkButton(
            btn_box,
            text="📄 Preview PDF",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SECONDARY_BORDER,
            command=self.preview_sample_pdf,
            height=36
        )
        preview_btn.pack(side="left", padx=4)

        save_btn = ctk.CTkButton(
            btn_box,
            text="💾 Save Settings",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SUCCESS_BORDER,
            command=self.save_settings,
            height=36
        )
        save_btn.pack(side="left", padx=4)

        # 2. Tabview for Settings Categories
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            segmented_button_selected_color=Theme.PRIMARY,
            segmented_button_selected_hover_color=Theme.PRIMARY_HOVER,
        )
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Add tabs
        self.tab_brand = self.tabview.add("🏢 Company Branding")
        self.tab_logo = self.tabview.add("🖼️ Company Logo")
        self.tab_bank = self.tabview.add("🏦 Bank & Payments")
        self.tab_sigs = self.tabview.add("✍️ Signatures")
        self.tab_terms = self.tabview.add("📜 Terms & Conditions")

        self.build_brand_tab()
        self.build_logo_tab()
        self.build_bank_tab()
        self.build_sigs_tab()
        self.build_terms_tab()

    def build_brand_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_brand, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        f = ctk.CTkFrame(scroll, fg_color="transparent")
        f.pack(fill="x")
        f.grid_columnconfigure((0, 1), weight=1)

        # Helper for input fields
        def make_entry(font_weight="normal"):
            return ctk.CTkEntry(
                f,
                height=34,
                corner_radius=Theme.RADIUS_INPUT,
                fg_color=Theme.INSET_BG,
                border_color=Theme.INSET_BORDER,
                border_width=Theme.BORDER_WIDTH_INPUT,
                font=ctk.CTkFont(size=11, weight=font_weight)
            )

        # Company Name
        ctk.CTkLabel(f, text="Company / Showroom Name:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=8, pady=(4, 2), sticky="w")
        self.c_name_entry = make_entry("bold")
        self.c_name_entry.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="ew")

        # Tagline
        ctk.CTkLabel(f, text="Tagline / Brand Subtitle:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=8, pady=(4, 2), sticky="w")
        self.c_tagline_entry = make_entry()
        self.c_tagline_entry.grid(row=1, column=1, padx=8, pady=(0, 10), sticky="ew")

        # Address Line 1
        ctk.CTkLabel(f, text="Showroom Address Line 1:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, padx=8, pady=(4, 2), sticky="w")
        self.c_addr1_entry = make_entry()
        self.c_addr1_entry.grid(row=3, column=0, padx=8, pady=(0, 10), sticky="ew")

        # Address Line 2
        ctk.CTkLabel(f, text="Address Line 2 (City, Pincode, State):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=1, padx=8, pady=(4, 2), sticky="w")
        self.c_addr2_entry = make_entry()
        self.c_addr2_entry.grid(row=3, column=1, padx=8, pady=(0, 10), sticky="ew")

        # Contact Phone
        ctk.CTkLabel(f, text="Contact Numbers (Phone / Landline):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=0, padx=8, pady=(4, 2), sticky="w")
        self.c_phone_entry = make_entry()
        self.c_phone_entry.grid(row=5, column=0, padx=8, pady=(0, 10), sticky="ew")

        # Email
        ctk.CTkLabel(f, text="Official Email Address:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=1, padx=8, pady=(4, 2), sticky="w")
        self.c_email_entry = make_entry()
        self.c_email_entry.grid(row=5, column=1, padx=8, pady=(0, 10), sticky="ew")

        # Website
        ctk.CTkLabel(f, text="Website URL:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=6, column=0, padx=8, pady=(4, 2), sticky="w")
        self.c_web_entry = make_entry()
        self.c_web_entry.grid(row=7, column=0, padx=8, pady=(0, 10), sticky="ew")

        # GSTIN Number
        ctk.CTkLabel(f, text="GSTIN Number:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=6, column=1, padx=8, pady=(4, 2), sticky="w")
        self.c_gst_entry = make_entry()
        self.c_gst_entry.grid(row=7, column=1, padx=8, pady=(0, 10), sticky="ew")

        # State & State Code
        ctk.CTkLabel(f, text="State & State Code:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=8, column=0, padx=8, pady=(4, 2), sticky="w")
        self.c_state_entry = make_entry()
        self.c_state_entry.grid(row=9, column=0, padx=8, pady=(0, 10), sticky="ew")

    def build_logo_tab(self):
        f = ctk.CTkFrame(self.tab_logo, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            f,
            text="Official Showroom / Company Logo for Printable Quotations",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        tip_lbl = ctk.CTkLabel(
            f,
            text="Upload your company logo in PNG, JPG, or JPEG format. It will be printed at the top-left of every generated PDF quotation.",
            font=ctk.CTkFont(size=11),
            text_color=("#615D56", "#A8A297"),
            wraplength=650,
            justify="left"
        )
        tip_lbl.pack(anchor="w", pady=(0, 14))

        # Preview Container
        preview_card = ctk.CTkFrame(
            f,
            width=320,
            height=140,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=Theme.INSET_BG,
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.INSET_BORDER
        )
        preview_card.pack(pady=(0, 14))
        preview_card.pack_propagate(False)

        self.logo_preview_lbl = ctk.CTkLabel(
            preview_card,
            text="No Logo Selected",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#615D56", "#A8A297")
        )
        self.logo_preview_lbl.pack(expand=True)

        # File Path display & Browse controls
        path_row = ctk.CTkFrame(f, fg_color="transparent")
        path_row.pack(fill="x", pady=(0, 10))

        self.logo_path_entry = ctk.CTkEntry(
            path_row,
            placeholder_text="Logo file path (e.g. C:/path/to/logo.png)",
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11)
        )
        self.logo_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            path_row,
            text="📁 Browse File...",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            command=self.browse_logo,
            height=34
        )
        browse_btn.pack(side="left", padx=(0, 8))

        remove_btn = ctk.CTkButton(
            path_row,
            text="🗑️ Remove Logo",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=Theme.DANGER,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            command=self.remove_logo,
            height=34
        )
        remove_btn.pack(side="left")

    def build_bank_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_bank, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        f = ctk.CTkFrame(scroll, fg_color="transparent")
        f.pack(fill="x")
        f.grid_columnconfigure((0, 1), weight=1)

        def make_bank_entry(font_weight="normal"):
            return ctk.CTkEntry(
                f,
                height=34,
                corner_radius=Theme.RADIUS_INPUT,
                fg_color=Theme.INSET_BG,
                border_color=Theme.INSET_BORDER,
                border_width=Theme.BORDER_WIDTH_INPUT,
                font=ctk.CTkFont(size=11, weight=font_weight)
            )

        # Bank Name
        ctk.CTkLabel(f, text="Bank Name:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=8, pady=(4, 2), sticky="w")
        self.bank_name_entry = make_bank_entry()
        self.bank_name_entry.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="ew")

        # Account Name
        ctk.CTkLabel(f, text="Beneficiary / Account Name:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=8, pady=(4, 2), sticky="w")
        self.bank_acc_name_entry = make_bank_entry()
        self.bank_acc_name_entry.grid(row=1, column=1, padx=8, pady=(0, 10), sticky="ew")

        # Account Number
        ctk.CTkLabel(f, text="Account Number:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, padx=8, pady=(4, 2), sticky="w")
        self.bank_acc_num_entry = make_bank_entry("bold")
        self.bank_acc_num_entry.grid(row=3, column=0, padx=8, pady=(0, 10), sticky="ew")

        # IFSC Code
        ctk.CTkLabel(f, text="IFSC Code:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=1, padx=8, pady=(4, 2), sticky="w")
        self.bank_ifsc_entry = make_bank_entry()
        self.bank_ifsc_entry.grid(row=3, column=1, padx=8, pady=(0, 10), sticky="ew")

        # Branch
        ctk.CTkLabel(f, text="Bank Branch Name:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=0, padx=8, pady=(4, 2), sticky="w")
        self.bank_branch_entry = make_bank_entry()
        self.bank_branch_entry.grid(row=5, column=0, padx=8, pady=(0, 10), sticky="ew")

        # Account Type
        ctk.CTkLabel(f, text="Account Type (Current / Savings):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=1, padx=8, pady=(4, 2), sticky="w")
        self.bank_type_entry = make_bank_entry()
        self.bank_type_entry.grid(row=5, column=1, padx=8, pady=(0, 10), sticky="ew")

        # UPI / Digital Remittance notes
        ctk.CTkLabel(f, text="UPI / QR Code & Payment Instructions on PDF:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=6, column=0, columnspan=2, padx=8, pady=(4, 2), sticky="w")
        self.bank_upi_text = ctk.CTkTextbox(
            f,
            height=65,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11)
        )
        self.bank_upi_text.grid(row=7, column=0, columnspan=2, padx=8, pady=(0, 10), sticky="ew")

    def build_sigs_tab(self):
        f = ctk.CTkFrame(self.tab_sigs, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=16)
        f.grid_columnconfigure((0, 1), weight=1)

        def make_sig_entry():
            return ctk.CTkEntry(
                f,
                height=34,
                corner_radius=Theme.RADIUS_INPUT,
                fg_color=Theme.INSET_BG,
                border_color=Theme.INSET_BORDER,
                border_width=Theme.BORDER_WIDTH_INPUT,
                font=ctk.CTkFont(size=11)
            )

        # Store Manager Title
        ctk.CTkLabel(f, text="Manager Signatory Title:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=8, pady=(4, 2), sticky="w")
        self.mgr_title_entry = make_sig_entry()
        self.mgr_title_entry.grid(row=1, column=0, padx=8, pady=(0, 12), sticky="ew")

        # Store Manager Name
        ctk.CTkLabel(f, text="Store Manager Name:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=8, pady=(4, 2), sticky="w")
        self.mgr_name_entry = make_sig_entry()
        self.mgr_name_entry.grid(row=1, column=1, padx=8, pady=(0, 12), sticky="ew")

        # Store Manager Phone
        ctk.CTkLabel(f, text="Store Manager Phone / Contact:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, padx=8, pady=(4, 2), sticky="w")
        self.mgr_phone_entry = make_sig_entry()
        self.mgr_phone_entry.grid(row=3, column=0, padx=8, pady=(0, 12), sticky="ew")

        # Sales Associate Title
        ctk.CTkLabel(f, text="Showroom Sales Associate Title:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=1, padx=8, pady=(4, 2), sticky="w")
        self.sales_title_entry = make_sig_entry()
        self.sales_title_entry.grid(row=3, column=1, padx=8, pady=(0, 12), sticky="ew")

    def build_terms_tab(self):
        f = ctk.CTkFrame(self.tab_terms, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=14)

        t_header = ctk.CTkFrame(f, fg_color="transparent")
        t_header.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            t_header,
            text="Standard Terms & Conditions (1 per line for PDF Footer):",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold")
        ).pack(side="left")

        reset_terms_btn = ctk.CTkButton(
            t_header,
            text="↺ Reset to Standard 13-Point",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=(Theme.BLACK, Theme.PAPER),
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            command=self.reset_terms_defaults,
            height=28
        )
        reset_terms_btn.pack(side="right")

        self.terms_textbox = ctk.CTkTextbox(
            f,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.terms_textbox.pack(fill="both", expand=True, pady=(4, 10))

    def load_settings(self):
        s = self.setting

        # Brand
        self.c_name_entry.delete(0, "end")
        self.c_name_entry.insert(0, s.company_name)

        self.c_tagline_entry.delete(0, "end")
        self.c_tagline_entry.insert(0, s.tagline)

        self.c_addr1_entry.delete(0, "end")
        self.c_addr1_entry.insert(0, s.address_line1)

        self.c_addr2_entry.delete(0, "end")
        self.c_addr2_entry.insert(0, s.address_line2)

        self.c_phone_entry.delete(0, "end")
        self.c_phone_entry.insert(0, s.phone)

        self.c_email_entry.delete(0, "end")
        self.c_email_entry.insert(0, s.email)

        self.c_web_entry.delete(0, "end")
        self.c_web_entry.insert(0, s.website)

        self.c_gst_entry.delete(0, "end")
        self.c_gst_entry.insert(0, s.gstin)

        self.c_state_entry.delete(0, "end")
        self.c_state_entry.insert(0, s.state)

        # Logo
        if s.logo_path and os.path.isfile(s.logo_path):
            self.logo_path_entry.delete(0, "end")
            self.logo_path_entry.insert(0, s.logo_path)
            self.update_logo_preview(s.logo_path)
        else:
            self.logo_path_entry.delete(0, "end")
            self.logo_preview_lbl.configure(text="No Logo Selected", image="")

        # Bank
        self.bank_name_entry.delete(0, "end")
        self.bank_name_entry.insert(0, s.bank_name)

        self.bank_acc_name_entry.delete(0, "end")
        self.bank_acc_name_entry.insert(0, s.account_name)

        self.bank_acc_num_entry.delete(0, "end")
        self.bank_acc_num_entry.insert(0, s.account_number)

        self.bank_ifsc_entry.delete(0, "end")
        self.bank_ifsc_entry.insert(0, s.ifsc_code)

        self.bank_branch_entry.delete(0, "end")
        self.bank_branch_entry.insert(0, s.branch)

        self.bank_type_entry.delete(0, "end")
        self.bank_type_entry.insert(0, s.account_type)

        self.bank_upi_text.delete("1.0", "end")
        self.bank_upi_text.insert("1.0", s.upi_details)

        # Sigs
        self.mgr_title_entry.delete(0, "end")
        self.mgr_title_entry.insert(0, s.store_manager_title)

        self.mgr_name_entry.delete(0, "end")
        self.mgr_name_entry.insert(0, s.store_manager_name)

        self.mgr_phone_entry.delete(0, "end")
        self.mgr_phone_entry.insert(0, s.store_manager_phone)

        self.sales_title_entry.delete(0, "end")
        self.sales_title_entry.insert(0, s.sales_associate_title)

        # Terms
        terms_list = s.get_terms_list()
        self.terms_textbox.delete("1.0", "end")
        self.terms_textbox.insert("1.0", "\n".join(terms_list))

    def update_logo_preview(self, file_path):
        try:
            with PILImage.open(file_path) as pimg:
                # Resize for thumbnail preview (max 260x100)
                aspect = pimg.width / max(1, pimg.height)
                target_w = 200
                target_h = int(target_w / aspect)
                if target_h > 100:
                    target_h = 100
                    target_w = int(target_h * aspect)

                resized = pimg.resize((target_w, target_h), PILImage.Resampling.LANCZOS)
                self.logo_preview_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=(target_w, target_h))
                self.logo_preview_lbl.configure(text="", image=self.logo_preview_image)
        except Exception:
            self.logo_preview_lbl.configure(text=f"Logo Loaded: {os.path.basename(file_path)}", image="")

    def browse_logo(self):
        f_types = [
            ("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp"),
            ("PNG Files", "*.png"),
            ("JPEG Files", "*.jpg *.jpeg"),
            ("All Files", "*.*"),
        ]
        chosen = filedialog.askopenfilename(title="Select Showroom Logo", filetypes=f_types)
        if chosen and os.path.isfile(chosen):
            # Save a managed copy in assets directory
            assets_dir = BASE_DIR / "assets"
            assets_dir.mkdir(exist_ok=True)
            ext = Path(chosen).suffix
            dest = assets_dir / f"company_logo{ext}"
            shutil.copy2(chosen, dest)

            self.logo_path_entry.delete(0, "end")
            self.logo_path_entry.insert(0, str(dest))
            self.update_logo_preview(str(dest))

    def remove_logo(self):
        self.logo_path_entry.delete(0, "end")
        self.logo_preview_lbl.configure(text="No Logo Selected", image="")
        self.logo_preview_image = None

    def reset_terms_defaults(self):
        self.terms_textbox.delete("1.0", "end")
        self.terms_textbox.insert("1.0", "\n".join(STANDARD_TERMS_AND_CONDITIONS))

    def save_settings(self):
        s = self.setting

        # Brand
        s.company_name = self.c_name_entry.get().strip() or "AMA CERAMICS PVT LTD"
        s.tagline = self.c_tagline_entry.get().strip()
        s.address_line1 = self.c_addr1_entry.get().strip()
        s.address_line2 = self.c_addr2_entry.get().strip()
        s.phone = self.c_phone_entry.get().strip()
        s.email = self.c_email_entry.get().strip()
        s.website = self.c_web_entry.get().strip()
        s.gstin = self.c_gst_entry.get().strip()
        s.state = self.c_state_entry.get().strip()

        # Logo
        logo_val = self.logo_path_entry.get().strip()
        s.logo_path = logo_val if (logo_val and os.path.isfile(logo_val)) else None

        # Bank
        s.bank_name = self.bank_name_entry.get().strip()
        s.account_name = self.bank_acc_name_entry.get().strip()
        s.account_number = self.bank_acc_num_entry.get().strip()
        s.ifsc_code = self.bank_ifsc_entry.get().strip()
        s.branch = self.bank_branch_entry.get().strip()
        s.account_type = self.bank_type_entry.get().strip()
        s.upi_details = self.bank_upi_text.get("1.0", "end").strip()

        # Sigs
        s.store_manager_title = self.mgr_title_entry.get().strip()
        s.store_manager_name = self.mgr_name_entry.get().strip()
        s.store_manager_phone = self.mgr_phone_entry.get().strip()
        s.sales_associate_title = self.sales_title_entry.get().strip()

        # Terms
        raw_terms = self.terms_textbox.get("1.0", "end").strip().splitlines()
        terms_cleaned = [t.strip() for t in raw_terms if t.strip()]
        s.set_terms_list(terms_cleaned or STANDARD_TERMS_AND_CONDITIONS)

        s.updated_at = datetime.now()
        s.save()

        if hasattr(self.controller, "update_sidebar_branding"):
            self.controller.update_sidebar_branding()

        msgbox.showinfo(
            "Settings Saved",
            "Company and PDF details saved successfully!\nAll future quotation exports will reflect these updated details."
        )

    def preview_sample_pdf(self):
        # Save first
        self.save_settings()

        # Find or use latest quote
        q = Quotation.select().order_by(Quotation.id.desc()).first()
        if not q:
            msgbox.showwarning("Notice", "No quotation exists yet to generate a preview. Please create a quotation first.")
            return

        try:
            pdf_path = CeramicPDFGenerator.generate_quotation_pdf(q.id)
            msgbox.showinfo(
                "PDF Preview Ready",
                f"Generated preview PDF with updated settings:\n\n{pdf_path}"
            )
            try:
                os.startfile(pdf_path)
            except Exception:
                pass
        except Exception as e:
            msgbox.showerror("Error", f"Failed to generate preview PDF:\n{str(e)}")
