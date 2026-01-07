import customtkinter as ctk
import os
import subprocess
import json
from tkinter import messagebox

from ..core.downloader import SpotDownloader
from ..utils.helpers import check_ffmpeg
from .styles import Styles

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spot-Downloader Desktop")
        self.geometry("750x700")
        
        # Apply professional theme from styles
        Styles.apply_theme()

        self.downloader = SpotDownloader()
        self.setup_ui()
        self.load_settings()

        if not check_ffmpeg():
            self.after(1000, lambda: messagebox.showwarning(
                "FFmpeg Missing", 
                "FFmpeg was not found. Please install FFmpeg and add it to your PATH."
            ))

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(self, text="Spotify Downloader", font=Styles.HEADER_FONT)
        self.header_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Input Frame (URL)
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Paste Spotify Song or Playlist URL here...")
        self.url_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.download_button = ctk.CTkButton(self.input_frame, text="Download", command=self.start_download)
        self.download_button.grid(row=0, column=1, padx=(5, 5), pady=10)

        self.select_destination_button = ctk.CTkButton(
            self.input_frame, 
            text="Select Destination", 
            command=self.select_folder, 
            fg_color=Styles.TRANSPARENT, 
            border_width=2
        )
        self.select_destination_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Path Selection Frame
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.path_frame.grid_columnconfigure(1, weight=1)

        self.path_label_title = ctk.CTkLabel(self.path_frame, text="Current Path:", font=Styles.SUBHEADER_FONT)
        self.path_label_title.grid(row=0, column=0, padx=(10, 5), pady=10)

        self.path_display = ctk.CTkLabel(self.path_frame, text="downloads", font=Styles.LABEL_FONT, anchor="w")
        self.path_display.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.open_current_button = ctk.CTkButton(self.path_frame, text="Open Folder", command=self.open_downloads, width=100)
        self.open_current_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Ready", font=Styles.LABEL_FONT)
        self.status_label.grid(row=3, column=0, padx=20, pady=5)

        # Log Text Area
        self.log_textbox = ctk.CTkTextbox(self, height=200)
        self.log_textbox.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="nsew")
        self.log_textbox.configure(state="disabled")

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    download_path = settings.get("download_path", "downloads")
                    self.downloader.set_download_path(download_path)
                    self.path_display.configure(text=os.path.abspath(download_path))
            else:
                self.path_display.configure(text=os.path.abspath(self.downloader.download_path))
        except Exception as e:
            self.log(f"Error loading settings: {e}")

    def save_settings(self):
        settings = {
            "download_path": self.downloader.download_path
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
            self.log("Settings saved successfully!")
        except Exception as e:
            self.log(f"Error saving settings: {e}")



    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.status_label.configure(text=message)

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log("Please enter a URL.")
            return

        if not url:
            self.log("Please enter a URL.")
            return

        self.download_button.configure(state="disabled")
        self.log(f"Initiating download for: {url}")
        self.downloader.download(url, log_callback=self.log_finish_callback)

    def log_finish_callback(self, message):
        self.after(0, lambda: self.log(message))
        if any(kw in message.lower() for kw in ["completed", "error", "finished"]):
            self.after(0, lambda: self.download_button.configure(state="normal"))

    def open_downloads(self):
        download_path = os.path.abspath(self.downloader.download_path)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        if os.name == 'nt':
            os.startfile(download_path)
        else:
            subprocess.Popen(['open' if os.name == 'mac' else 'xdg-open', download_path])

    def select_folder(self):
        new_path = ctk.filedialog.askdirectory()
        if new_path:
            self.downloader.set_download_path(new_path)
            self.path_display.configure(text=os.path.abspath(new_path))
            self.log(f"Destination changed to: {new_path}")
