"""
UI Theme and Styling constants for CustomTkinter GUI.
"""

class Theme:
    # Color Palette
    PRIMARY = "#0284C7"         # Ceramic Sky/Sapphire
    PRIMARY_HOVER = "#0369A1"
    PRIMARY_DARK = "#075985"
    
    SECONDARY = "#334155"       # Slate
    SECONDARY_HOVER = "#1E293B"
    
    ACCENT_GOLD = "#D97706"     # Amber / Gold accent
    ACCENT_GOLD_HOVER = "#B45309"
    
    SUCCESS = "#10B981"         # Emerald Green
    SUCCESS_HOVER = "#059669"
    
    WARNING = "#F59E0B"         # Warning Amber
    DANGER = "#EF4444"          # Crimson Red
    DANGER_HOVER = "#DC2626"
    
    INFO = "#6366F1"            # Indigo
    
    # Backgrounds & Cards (Dark & Light support)
    DARK_BG = "#0B0F19"
    DARK_SURFACE = "#111827"
    DARK_CARD = "#1F2937"
    DARK_CARD_HOVER = "#374151"
    DARK_BORDER = "#374151"
    
    LIGHT_BG = "#F8FAFC"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_CARD = "#FFFFFF"
    LIGHT_CARD_HOVER = "#F1F5F9"
    LIGHT_BORDER = "#E2E8F0"
    
    # Typography Font Specs
    FONT_FAMILY = "Segoe UI"
    
    @classmethod
    def get_status_color(cls, status: str):
        mapping = {
            "Won": (cls.SUCCESS, "#D1FAE5"),
            "Open": (cls.PRIMARY, "#E0F2FE"),
            "In-Review": (cls.INFO, "#EDE9FE"),
            "Lost": (cls.DANGER, "#FEE2E2"),
            "Cleared": (cls.SUCCESS, "#D1FAE5"),
            "Pending": (cls.WARNING, "#FEF3C7"),
            "Fully Paid": (cls.SUCCESS, "#D1FAE5"),
            "Partially Paid": (cls.WARNING, "#FEF3C7"),
            "Unpaid": (cls.DANGER, "#FEE2E2"),
        }
        return mapping.get(status, (cls.SECONDARY, "#F1F5F9"))
