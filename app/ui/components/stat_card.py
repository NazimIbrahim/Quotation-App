"""
Reusable modern Stat Card widget for CustomTkinter.
"""
import customtkinter as ctk
from app.ui.theme import Theme


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, subtitle: str = "",
                 accent_color: str = Theme.PRIMARY, icon: str = "✦", **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155"),
            **kwargs
        )
        self.accent_color = accent_color

        # Top Accent stripe
        self.stripe = ctk.CTkFrame(
            self,
            height=4,
            corner_radius=2,
            fg_color=accent_color
        )
        self.stripe.pack(fill="x", padx=0, pady=(0, 8))

        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Header Row (Title + Icon)
        header_row = ctk.CTkFrame(content, fg_color="transparent")
        header_row.pack(fill="x")

        self.title_label = ctk.CTkLabel(
            header_row,
            text=title.upper(),
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=("#64748B", "#94A3B8"),
            anchor="w"
        )
        self.title_label.pack(side="left")

        self.icon_badge = ctk.CTkLabel(
            header_row,
            text=icon,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            text_color=accent_color,
            width=24,
            height=24,
            corner_radius=6,
            fg_color=("#F1F5F9", "#0F172A")
        )
        self.icon_badge.pack(side="right")

        # Value Label
        self.value_label = ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=22, weight="bold"),
            text_color=("#0F172A", "#F8FAFC"),
            anchor="w"
        )
        self.value_label.pack(fill="x", pady=(6, 2))

        # Subtitle / Details
        if subtitle:
            self.subtitle_label = ctk.CTkLabel(
                content,
                text=subtitle,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=("#64748B", "#94A3B8"),
                anchor="w"
            )
            self.subtitle_label.pack(fill="x")
        else:
            self.subtitle_label = None

    def update_values(self, value: str, subtitle: str = None):
        self.value_label.configure(text=value)
        if subtitle and self.subtitle_label:
            self.subtitle_label.configure(text=subtitle)
