"""
UI Theme and Styling constants for CustomTkinter GUI.
"""

class Theme:
    # 4-Color Architectural Palette
    PAPER = "#F6F4F1"           # Warm clean editorial paper canvas
    STONE = "#E4DED2"           # Architectural limestone / structural tone
    CORAL = "#F95C4B"           # Vibrant terracotta / coral brand accent
    BLACK = "#000000"           # Deep rich contrast & bold typography

    # Primary Hero Colors (Coral)
    PRIMARY = "#F95C4B"
    PRIMARY_HOVER = "#E04838"
    PRIMARY_DARK = "#C73626"
    
    # Secondary Structural Colors (Stone)
    SECONDARY = "#E4DED2"
    SECONDARY_HOVER = "#D4CDBC"
    STONE_BORDER = "#D4CDBC"
    STONE_MUTED = "#6B665E"
    
    # Accent Aliases
    ACCENT_CORAL = "#F95C4B"
    ACCENT_GOLD = "#F95C4B"     # Unified with signature Coral
    ACCENT_GOLD_HOVER = "#E04838"
    
    # Semantic Status Accents
    SUCCESS = "#16A34A"         # Botanical Emerald
    SUCCESS_HOVER = "#15803D"
    
    WARNING = "#D97706"         # Warm Ochre
    DANGER = "#DC2626"          # Crimson Red
    DANGER_HOVER = "#B91C1C"
    
    INFO = "#F95C4B"            # Coral Accent
    
    # Backgrounds & Cards (Light: Paper & Stone / Dark: Black & Charcoal Stone)
    LIGHT_BG = "#F6F4F1"        # Paper
    LIGHT_SURFACE = "#FAF8F5"    # Soft Paper tint
    LIGHT_CARD = "#FFFFFF"      # Crisp White Card on Paper
    LIGHT_CARD_HOVER = "#F5F2EB"
    LIGHT_BORDER = "#E4DED2"    # Stone Border
    
    DARK_BG = "#0D0D0D"         # Pitch Obsidian Black
    DARK_SURFACE = "#171615"
    DARK_CARD = "#211F1D"
    DARK_CARD_HOVER = "#2D2A27"
    DARK_BORDER = "#38342E"
    
    # Typography Font Specs
    FONT_FAMILY = "Segoe UI"
    
    @classmethod
    def get_status_color(cls, status: str):
        mapping = {
            "Won": (cls.SUCCESS, "#DCFCE7"),
            "Open": (cls.PRIMARY, "#FEECE9"),
            "In-Review": ("#D97706", "#FEF3C7"),
            "Lost": (cls.DANGER, "#FEE2E2"),
            "Cleared": (cls.SUCCESS, "#DCFCE7"),
            "Pending": (cls.PRIMARY, "#FEECE9"),
            "Fully Paid": (cls.SUCCESS, "#DCFCE7"),
            "Partially Paid": ("#D97706", "#FEF3C7"),
            "Unpaid": (cls.DANGER, "#FEE2E2"),
        }
        return mapping.get(status, (cls.STONE_MUTED, "#F5F2EB"))

