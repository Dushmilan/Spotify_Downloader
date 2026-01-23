import customtkinter as ctk
import os
import subprocess
import json
from tkinter import messagebox
import threading

from ..services.download_service import DownloadService, ValidationService
from ..utils.helpers import check_ffmpeg
from ..config import app_config
from .styles import Styles

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spot-Downloader Desktop")
        self.geometry("750x700")

        # Apply professional theme from styles
        Styles.apply_theme()

        self.download_service = DownloadService()
        self.download_thread = None
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

        # Add a progress bar for better UX
        # Progress bar for overall download progress
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)  # Initially set to 0
        self.progress_bar.grid_remove()  # Hide initially

        # Add a label to show progress percentage
        self.progress_label = ctk.CTkLabel(self, text="0%", font=Styles.LABEL_FONT)
        self.progress_label.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_label.grid_remove()  # Hide initially

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    download_path = settings.get("download_path", app_config.download_path)
                    self.download_service.set_download_path(download_path)
                    self.path_display.configure(text=os.path.abspath(download_path))
                    # Update config with loaded settings
                    app_config.set("download_path", download_path)
            else:
                self.path_display.configure(text=os.path.abspath(self.download_service.download_path))
        except Exception as e:
            self.log(f"Error loading settings: {e}")

    def save_settings(self):
        settings = {
            "download_path": self.download_service.download_path
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
            # Also save to the app config
            app_config.update(settings)
            app_config.save_config()
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

        # Validate URL format if safe mode is enabled
        if app_config.safe_mode and not ValidationService.validate_spotify_url(url):
            self.log("Invalid Spotify URL. Please enter a valid Spotify track, playlist, or album URL.")
            return

        # Disable UI elements during download
        self.download_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.select_destination_button.configure(state="disabled")

        # Show progress bar
        self.progress_bar.grid()
        self.progress_bar.set(0)

        self.log(f"Initiating download for: {url}")

        # Start download in a separate thread to keep UI responsive
        self.download_thread = self.download_service.download(url, log_callback=self.log_finish_callback)

    def log_finish_callback(self, message):
        self.after(0, lambda: self.update_ui_with_message(message))

        if any(kw in message.lower() for kw in ["completed", "error", "finished", "all downloads finished"]):
            self.after(0, self.reset_ui_after_download)

    def update_ui_with_message(self, message):
        """Update UI elements based on log messages"""
        self.log(message)

        # Update progress based on message content
        if "download complete" in message.lower() or "successfully downloaded" in message.lower():
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="100%")
        elif "downloading" in message.lower() or "processing" in message.lower():
            # Simple progress indication - in a real app, you'd have actual progress
            current_val = self.progress_bar.get()
            if current_val < 0.8:  # Don't exceed 80% until final completion
                new_val = min(current_val + 0.1, 0.8)
                self.progress_bar.set(new_val)
                self.progress_label.configure(text=f"{int(new_val * 100)}%")
        elif "all downloads finished" in message.lower():
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="100%")

    def reset_ui_after_download(self):
        """Reset UI elements after download completion"""
        self.download_button.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.select_destination_button.configure(state="normal")
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")

    def open_downloads(self):
        download_path = os.path.abspath(self.download_service.download_path)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        if os.name == 'nt':
            os.startfile(download_path)
        else:
            subprocess.Popen(['open' if os.name == 'mac' else 'xdg-open', download_path])

    def select_folder(self):
        new_path = ctk.filedialog.askdirectory()
        if new_path:
            try:
                self.download_service.set_download_path(new_path)
                self.path_display.configure(text=os.path.abspath(new_path))
                self.log(f"Destination changed to: {new_path}")
                self.save_settings()
            except ValueError as e:
                messagebox.showerror("Invalid Path", str(e))
                self.log(f"Error setting download path: {e}")
