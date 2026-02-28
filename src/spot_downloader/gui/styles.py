import customtkinter as ctk

class Styles:
    # Colors - Premium Spotify Palette
    BG_DARK = "#000000"         # True black for the main backgrounds
    BG_SIDEBAR = "#080808"      # Deeper black for sidebar
    BG_CARD = "#121212"         # Card background
    BG_CARD_HOVER = "#282828"   # Hover state for cards
    
    ACCENT_GREEN = "#1DB954"    # Spotify brand green
    ACCENT_GREEN_HOVER = "#1ED760" # Brighter green for hover
    
    TEXT_PRIMARY = "#FFFFFF"    # Pure white for main headings
    TEXT_SECONDARY = "#B3B3B3"  # Soft gray for subtext
    TEXT_DIM = "#535353"        # Dark gray for subtle hints
    
    # Status Colors
    SUCCESS = "#1DB954"
    ERROR = "#E91429"
    WARNING = "#FFA42B"
    INFO = "#2E77D0"
    
    TRANSPARENT = "transparent"
    BORDER_COLOR = "#222222"    # Subtle borders
    
    # Fonts
    HEADER_FONT = ("Segoe UI", 32, "bold")
    SUBHEADER_FONT = ("Segoe UI", 20, "bold")
    BODY_BOLD = ("Segoe UI", 14, "bold")
    BODY_MAIN = ("Segoe UI", 14)
    LABEL_FONT = ("Segoe UI", 12)
    SMALL_LABEL_FONT = ("Segoe UI", 11)
    
    @staticmethod
    def apply_theme():
        ctk.set_appearance_mode("Dark")
        # Use a custom color theme or build on dark-blue
        ctk.set_default_color_theme("dark-blue")
