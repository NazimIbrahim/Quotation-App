"""
Main Application Window: Houses the modern CustomTkinter shell,
navigation sidebar, user role switcher, and dynamic view router.
"""
import tkinter.messagebox as msgbox
import customtkinter as ctk

from app.config import ASSETS_DIR
from app.ui.theme import Theme
from app.database.models import SalesPerson, CompanySetting, init_database
from app.database.seed_data import seed_database
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.quotation_list_view import QuotationListView
from app.ui.views.quotation_editor_view import QuotationEditorView
from app.ui.views.payment_view import PaymentTrackingView
from app.ui.views.customer_view import CustomerManagementView
from app.ui.views.sales_team_view import SalesTeamView
from app.ui.views.reports_view import ReportsView
from app.ui.views.settings_view import CompanySettingsView
from app.ui.views.brand_catalog_view import BrandCatalogView



class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("AMA Ceramics Pvt Ltd - Ceramic & Tile Quotation Management System")
        self.geometry("1320x840")
        self.minsize(1080, 680)

        # Set Window Taskbar and Titlebar Icon
        ico_path = ASSETS_DIR / "app_icon.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        # Configure CustomTkinter Appearance
        ctk.set_appearance_mode("Light")  # Default to architectural Paper & Stone Light mode
        coral_theme_path = ASSETS_DIR / "coral_theme.json"
        if coral_theme_path.exists():
            try:
                ctk.set_default_color_theme(str(coral_theme_path))
            except Exception:
                ctk.set_default_color_theme("blue")
        else:
            ctk.set_default_color_theme("blue")

        # Active User State
        self.active_user = None
        self.users_cache = []

        # Current Active View Reference
        self.current_view = None
        self.nav_buttons = {}

        # Initialize DB & Seed Data if fresh
        init_database()
        seed_database(force=False)
        self.load_users()

        # Build Shell Layout
        self.build_shell()

        # Start on Dashboard
        self.show_view("dashboard")

    def load_users(self):
        self.users_cache = list(SalesPerson.select().where(SalesPerson.is_active == True))
        if self.users_cache:
            # Default to manager if available
            managers = [u for u in self.users_cache if u.role == SalesPerson.ROLE_MANAGER]
            self.active_user = managers[0] if managers else self.users_cache[0]

    def get_active_user(self):
        return self.active_user

    def build_shell(self):
        # Configure Grid: Left Sidebar (width 260), Right Main Container (expand)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=260)
        self.grid_columnconfigure(1, weight=1)

        # -----------------------------------------------------------------
        # Left Sidebar (Stone in Light, Deep Black in Dark)
        # -----------------------------------------------------------------
        self.sidebar = ctk.CTkFrame(
            self,
            width=260,
            corner_radius=0,
            fg_color=(Theme.STONE, "#121110"),
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)  # Spacer pushes bottom items down

        # 1. Branding Header
        brand_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_box.pack(fill="x", padx=18, pady=(20, 16))

        setting = CompanySetting.get_settings()
        self.logo_title = ctk.CTkLabel(
            brand_box,
            text=f"✦ {setting.company_name}",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold"),
            text_color=(Theme.BLACK, Theme.CORAL),
            anchor="w"
        )
        self.logo_title.pack(fill="x")

        self.logo_sub = ctk.CTkLabel(
            brand_box,
            text=f"{setting.tagline}\nGSTIN: {setting.gstin}",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9),
            text_color=("#5A554D", "#A49E92"),
            anchor="w",
            justify="left"
        )
        self.logo_sub.pack(fill="x", pady=(2, 0))

        # 2. Active User Switcher Box
        user_box = ctk.CTkFrame(
            self.sidebar,
            fg_color=("#FAF8F5", "#1E1C1A"),
            corner_radius=Theme.RADIUS_CARD,
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.INSET_BORDER
        )
        user_box.pack(fill="x", padx=14, pady=(0, 16))

        ctk.CTkLabel(
            user_box,
            text="CURRENT ACTIVE ROLE:",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=("#6B665E", "#A49E92")
        ).pack(anchor="w", padx=12, pady=(10, 2))

        self.user_dropdown = ctk.CTkOptionMenu(
            user_box,
            values=[f"{u.name} ({u.role})" for u in self.users_cache],
            command=self.on_user_switched,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            button_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            height=30
        )
        if self.active_user:
            self.user_dropdown.set(f"{self.active_user.name} ({self.active_user.role})")
        self.user_dropdown.pack(fill="x", padx=12, pady=(0, 6))

        self.role_badge_lbl = ctk.CTkLabel(
            user_box,
            text=f"Role: {self.active_user.role if self.active_user else 'Sales Person'}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.PRIMARY
        )
        self.role_badge_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        # 3. Navigation Menu Items
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("quotations", "📑  Quotations"),
            ("quotation_editor", "➕  New Quotation"),
            ("brand_catalog", "🏷️  Brands & Coverage"),
            ("payment_tracking", "💳  Payment Tracking"),
            ("customers", "👥  Customers CRM"),
            ("sales_team", "🎯  Sales Team & Targets"),
            ("reports", "📈  Reports & Analytics"),
            ("settings", "⚙️  Company & PDF Settings"),
        ]

        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=14)

        for view_key, label in nav_items:
            btn = ctk.CTkButton(
                self.nav_container,
                text=label,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
                anchor="w",
                height=40,
                corner_radius=Theme.RADIUS_BUTTON,
                fg_color="transparent",
                text_color=("#2E2B27", "#D5CFC3"),
                hover_color=("#D4CDBC", "#22201D"),
                command=lambda vk=view_key: self.show_view(vk)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[view_key] = btn

        # 4. Bottom Controls in Sidebar
        bottom_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=14, pady=16)

        # Database Status
        ctk.CTkLabel(
            bottom_box,
            text="● SQLite Database Connected",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.SUCCESS
        ).pack(anchor="w", pady=(0, 8))

        # Theme Selector (Light / Dark)
        theme_row = ctk.CTkFrame(bottom_box, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            theme_row,
            text="Mode:",
            font=ctk.CTkFont(size=10),
            text_color=("#6B665E", "#A49E92")
        ).pack(side="left")

        self.theme_segment = ctk.CTkSegmentedButton(
            theme_row,
            values=["Light", "Dark"],
            command=self.toggle_theme,
            selected_color=Theme.PRIMARY,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_INPUT,
            height=26,
            font=ctk.CTkFont(size=10)
        )
        self.theme_segment.set("Light")
        self.theme_segment.pack(side="right")

        # Reset Sample Seed Data Button
        reset_btn = ctk.CTkButton(
            bottom_box,
            text="↺ Reset Demo Seed Data",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=("#3D3A35", "#C4BEB2"),
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_BUTTON,
            hover_color=Theme.DANGER,
            height=28,
            command=self.reset_seed_data
        )
        reset_btn.pack(fill="x")

        # -----------------------------------------------------------------
        # Right Main Content Container (Paper in Light, Black in Dark)
        # -----------------------------------------------------------------
        self.main_container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=(Theme.PAPER, Theme.DARK_BG)
        )
        self.main_container.grid(row=0, column=1, sticky="nsew")

    def on_user_switched(self, val):
        for u in self.users_cache:
            if f"{u.name} ({u.role})" == val:
                self.active_user = u
                self.role_badge_lbl.configure(text=f"Role: {u.role}")
                break

        # Refresh current view to reflect role change if needed
        if self.current_view and hasattr(self.current_view, "refresh_data"):
            self.current_view.refresh_data()
        elif self.current_view and hasattr(self.current_view, "refresh_table"):
            self.current_view.refresh_table()

    def refresh_sidebar_users(self):
        self.load_users()
        vals = [f"{u.name} ({u.role})" for u in self.users_cache]
        self.user_dropdown.configure(values=vals)
        if self.active_user:
            self.user_dropdown.set(f"{self.active_user.name} ({self.active_user.role})")

    def update_sidebar_branding(self):
        s = CompanySetting.get_settings()
        self.logo_title.configure(text=f"✦ {s.company_name}")
        self.logo_sub.configure(text=f"{s.tagline}\nGSTIN: {s.gstin}")

    def toggle_theme(self, mode):
        ctk.set_appearance_mode(mode)
        # Re-apply nav button colors to maintain theme contrast
        if hasattr(self, "current_view_key"):
            self.show_view(self.current_view_key)

    def reset_seed_data(self):
        confirm = msgbox.askyesno(
            "Reset Demo Data",
            "This will reset the database with fresh demo seed quotations, customers, and payments.\nProceed?"
        )
        if confirm:
            seed_database(force=True)
            self.refresh_sidebar_users()
            self.show_view("dashboard")
            msgbox.showinfo("Reset Complete", "Demo seed data reloaded successfully!")

    def show_view(self, view_name: str, param=None):
        """Switches the active view in the main container."""
        self.current_view_key = view_name
        # Update Nav Highlight
        for vk, btn in self.nav_buttons.items():
            if vk == view_name or (view_name == "quotation_editor" and vk == "quotation_editor" and param is None):
                btn.configure(
                    fg_color=Theme.PRIMARY,
                    border_width=Theme.BORDER_WIDTH_BUTTON,
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    border_width=0,
                    text_color=("#2E2B27", "#D5CFC3")
                )

        # Destroy old view
        if self.current_view:
            self.current_view.destroy()

        # Instantiate new view
        if view_name == "dashboard":
            self.current_view = DashboardView(self.main_container, controller=self)
        elif view_name == "quotations":
            self.current_view = QuotationListView(self.main_container, controller=self)
        elif view_name == "quotation_editor":
            self.current_view = QuotationEditorView(self.main_container, controller=self, quote_id=param)
        elif view_name == "brand_catalog":
            self.current_view = BrandCatalogView(self.main_container, controller=self)
        elif view_name == "payment_tracking":
            self.current_view = PaymentTrackingView(self.main_container, controller=self, preselected_quote_id=param)
        elif view_name == "customers":
            self.current_view = CustomerManagementView(self.main_container, controller=self)
        elif view_name == "sales_team":
            self.current_view = SalesTeamView(self.main_container, controller=self)
        elif view_name == "reports":
            self.current_view = ReportsView(self.main_container, controller=self)
        elif view_name == "settings":
            self.current_view = CompanySettingsView(self.main_container, controller=self)
        else:
            self.current_view = DashboardView(self.main_container, controller=self)

        self.current_view.pack(fill="both", expand=True)
