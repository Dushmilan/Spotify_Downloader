import customtkinter as ctk

class Styles:
    # Colors
    SPOTIFY_GREEN = "#1DB954"
    SPOTIFY_GREEN_HOVER = "#18a34a"
    TRANSPARENT = "transparent"
    
    # Fonts
    HEADER_FONT = ("Inter", 24, "bold")
    SUBHEADER_FONT = ("Inter", 14, "bold")
    LABEL_FONT = ("Inter", 12)
    SMALL_LABEL_FONT = ("Inter", 11)
    
    @staticmethod
    def apply_theme():
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
