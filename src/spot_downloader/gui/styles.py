import customtkinter as ctk

class Styles:
    # Colors - Premium Spotify Palette
    BG_DARK = "#000000"         # True black for the main backgrounds
    BG_SIDEBAR = "#121212"      # Deep matte black for the sidebar
    BG_CARD = "#181818"         # Slightly lighter black for cards
    BG_CARD_HOVER = "#282828"   # Hover state for cards
    
    ACCENT_GREEN = "#1DB954"    # Spotify brand green
    ACCENT_GREEN_HOVER = "#1ED760" # Brighter green for hover
    
    TEXT_PRIMARY = "#FFFFFF"    # Pure white for main headings
    TEXT_SECONDARY = "#B3B3B3"  # Soft gray for subtext
    TEXT_DIM = "#535353"        # Dark gray for subtle hints
    
    TRANSPARENT = "transparent"
    BORDER_COLOR = "#333333"    # Subtle borders
    
    # Fonts
    HEADER_FONT = ("Inter", 28, "bold")
    SUBHEADER_FONT = ("Inter", 18, "bold")
    BODY_BOLD = ("Inter", 14, "bold")
    BODY_MAIN = ("Inter", 14)
    LABEL_FONT = ("Inter", 12)
    SMALL_LABEL_FONT = ("Inter", 11)
    
    @staticmethod
    def apply_theme():
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue") # We will use custom colors mostly, but blue is the base
