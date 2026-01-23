import customtkinter as ctk
import os
import subprocess
import json
from tkinter import messagebox
import threading

from ..services.download_service import DownloadService, ValidationService
from ..utils.helpers import check_ffmpeg
from ..config import app_config
from ..tracker import DownloadTracker, DownloadStatus
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
        # Initialize download tracking
        self.current_downloads = {}  # Track ongoing downloads
        self.completed_downloads = []  # Track completed downloads
        self.failed_downloads = []  # Track failed downloads

        # Register the change callback with the tracker
        self.download_service.tracker.set_on_change_callback(self.on_tracker_change)

        if not check_ffmpeg():
            self.after(1000, lambda: messagebox.showwarning(
                "FFmpeg Missing",
                "FFmpeg was not found. Please install FFmpeg and add it to your PATH."
            ))

    def setup_ui(self):
        # Configure grid for sidebar and main content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=Styles.BG_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Spacer

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SPOT-DL", font=Styles.HEADER_FONT, text_color=Styles.ACCENT_GREEN)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        # Sidebar Buttons
        self.search_btn = self._create_sidebar_button("Search", 1, self.show_search)
        self.downloads_btn = self._create_sidebar_button("Downloads", 2, self.show_downloads)
        self.settings_btn = self._create_sidebar_button("Settings", 3, self.show_settings)
        self.history_btn = self._create_sidebar_button("History", 4, self.show_history)

        # 2. Main Content Area
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=Styles.BG_DARK)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # 3. Initialize Frames
        self.frames = {}
        self._init_search_frame()
        self._init_downloads_frame()
        self._init_settings_frame()
        self._init_history_frame()

        # Show Search by default
        self.show_search()

    def _create_sidebar_button(self, text, row, command):
        btn = ctk.CTkButton(
            self.sidebar_frame, 
            text=text, 
            command=command,
            anchor="w",
            height=40,
            fg_color="transparent",
            text_color=Styles.TEXT_SECONDARY,
            hover_color=Styles.BG_CARD_HOVER,
            font=Styles.BODY_BOLD
        )
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def _init_search_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Search"] = frame
        
        frame.grid_columnconfigure(0, weight=1)
        
        # Hero Section
        hero_label = ctk.CTkLabel(frame, text="Download tracks and playlists", font=Styles.HEADER_FONT)
        hero_label.grid(row=0, column=0, padx=40, pady=(100, 20), sticky="w")

        # Input Area (Mocking Spotify Search)
        input_container = ctk.CTkFrame(frame, fg_color=Styles.BG_CARD, height=60, corner_radius=30)
        input_container.grid(row=1, column=0, padx=40, pady=10, sticky="ew")
        input_container.grid_columnconfigure(0, weight=1)
        input_container.grid_propagate(False)

        self.url_entry = ctk.CTkEntry(
            input_container, 
            placeholder_text="What do you want to download?",
            fg_color="transparent",
            border_width=0,
            font=Styles.BODY_MAIN,
            height=40
        )
        self.url_entry.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="ew")

        self.download_button = ctk.CTkButton(
            frame, 
            text="START DOWNLOAD", 
            command=self.start_download,
            fg_color=Styles.ACCENT_GREEN,
            hover_color=Styles.ACCENT_GREEN_HOVER,
            text_color=Styles.BG_DARK,
            font=Styles.BODY_BOLD,
            height=50,
            corner_radius=25
        )
        self.download_button.grid(row=2, column=0, padx=40, pady=20, sticky="w")

    def _init_downloads_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Downloads"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text="Active Downloads", font=Styles.SUBHEADER_FONT)
        title.grid(row=0, column=0, sticky="w")

        # Current Status Label in Downloads
        self.downloads_status = ctk.CTkLabel(header, text="Ready to download", font=Styles.SMALL_LABEL_FONT, text_color=Styles.ACCENT_GREEN)
        self.downloads_status.grid(row=0, column=1, sticky="e")

        # Overall progress
        progress_container = ctk.CTkFrame(frame, fg_color=Styles.BG_CARD, corner_radius=10)
        progress_container.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)

        self.overall_progress_bar = ctk.CTkProgressBar(progress_container, fg_color=Styles.BG_DARK, progress_color=Styles.ACCENT_GREEN)
        self.overall_progress_bar.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        self.overall_progress_bar.set(0)
        
        self.overall_progress_label = ctk.CTkLabel(progress_container, text="0/0 tracks", font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_SECONDARY)
        self.overall_progress_label.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        self.downloads_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.downloads_scroll.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.downloads_scroll.grid_columnconfigure(0, weight=1)

    def _init_settings_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Settings"] = frame
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="Settings", font=Styles.SUBHEADER_FONT)
        title.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w")

        # Path setting card
        path_card = ctk.CTkFrame(frame, fg_color=Styles.BG_CARD, corner_radius=10)
        path_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        path_card.grid_columnconfigure(0, weight=1)

        path_title = ctk.CTkLabel(path_card, text="Download Location", font=Styles.BODY_BOLD)
        path_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.path_display = ctk.CTkLabel(path_card, text="downloads", font=Styles.LABEL_FONT, text_color=Styles.TEXT_SECONDARY)
        self.path_display.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        btn_frame = ctk.CTkFrame(path_card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, rowspan=2, padx=15, pady=15)

        self.select_destination_button = ctk.CTkButton(
            btn_frame, text="Change", command=self.select_folder, width=80, 
            fg_color=Styles.BG_CARD_HOVER, border_width=1, border_color=Styles.BORDER_COLOR
        )
        self.select_destination_button.grid(row=0, column=0, padx=5)

        self.open_current_button = ctk.CTkButton(
            btn_frame, text="Open Folder", command=self.open_downloads, width=80,
            fg_color=Styles.ACCENT_GREEN, text_color=Styles.BG_DARK
        )
        self.open_current_button.grid(row=0, column=1, padx=5)

    def _init_history_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["History"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(frame, text="Download Logs", font=Styles.SUBHEADER_FONT)
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.log_textbox = ctk.CTkTextbox(frame, fg_color=Styles.BG_DARK, border_color=Styles.BORDER_COLOR, border_width=1)
        self.log_textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_textbox.configure(state="disabled")

        self.status_label = ctk.CTkLabel(frame, text="Ready", font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_SECONDARY)
        self.status_label.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="w")

    def show_frame(self, name):
        for f_name, frame in self.frames.items():
            if f_name == name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()
        
        # Update button styles
        for btn, text in [(self.search_btn, "Search"), (self.downloads_btn, "Downloads"), 
                          (self.settings_btn, "Settings"), (self.history_btn, "History")]:
            if text == name:
                btn.configure(fg_color=Styles.BG_CARD_HOVER, text_color=Styles.ACCENT_GREEN)
            else:
                btn.configure(fg_color="transparent", text_color=Styles.TEXT_SECONDARY)

    def show_search(self): self.show_frame("Search")
    def show_downloads(self): self.show_frame("Downloads")
    def show_settings(self): self.show_frame("Settings")
    def show_history(self): self.show_frame("History")

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
        self.download_button.configure(state="disabled", text="DOWNLOADING...")
        self.url_entry.configure(state="disabled")
        
        # Switch to downloads view
        self.show_downloads()

        self.log(f"Initiating download for: {url}")

        # Start download in a separate thread to keep UI responsive
        self.download_thread = self.download_service.download(url, log_callback=self.log_finish_callback)

    def on_tracker_change(self):
        """Called when the tracker changes from a background thread."""
        # Use after to schedule the UI update in the main thread with debouncing
        if not hasattr(self, '_tracker_update_scheduled') or not self._tracker_update_scheduled:
            self._tracker_update_scheduled = True
            self.after(100, self._update_ui_from_tracker_delayed)

    def _update_ui_from_tracker_delayed(self):
        """Delayed UI update to prevent flooding the main thread."""
        self._tracker_update_scheduled = False
        self.update_ui_from_tracker()

    def update_ui_from_tracker(self):
        """Update the UI based on the tracker data."""
        tracker = self.download_service.tracker
        all_downloads = tracker.get_all_downloads()
        
        # 1. Add new items incrementally to avoid UI hang
        new_items_count = 0
        for download in all_downloads:
            if download.id not in self.current_downloads:
                self.add_download_progress(download.id, download.title, download.artist)
                new_items_count += 1
                # Limit to 5 new cards per update cycle (100ms) to keep UI responsive
                if new_items_count >= 5:
                    self._tracker_update_scheduled = True
                    self.after(20, self._update_ui_from_tracker_delayed)
                    break

        # 2. Update progress bars for existing items
        for download in all_downloads:
            if download.id in self.current_downloads:
                self.update_download_progress(download.id, download.progress, download.status)

        # 3. Update overall summary
        summary = tracker.get_summary()
        total = len(all_downloads)
        # Summary keys are strings like 'completed', 'failed', etc.
        completed = summary.get(DownloadStatus.COMPLETED.value, 0)
        self.update_overall_progress(completed, total)

    def log_finish_callback(self, message):
        self.after(0, lambda: self.update_ui_with_message(message))
        if any(kw in message.lower() for kw in ["all downloads finished"]):
            self.after(2000, self.reset_ui_after_download)

    def update_ui_with_message(self, message):
        """Update UI elements based on log messages"""
        self.log(message)
        if hasattr(self, 'downloads_status'):
            self.downloads_status.configure(text=message[:40] + "..." if len(message) > 40 else message)

    def reset_ui_after_download(self):
        """Reset UI elements after download completion"""
        self.download_button.configure(state="normal", text="START DOWNLOAD")
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, 'end')
        
        # Reset progress components
        self.overall_progress_bar.set(0)
        self.overall_progress_label.configure(text="0/0 tracks")
        
        # We don't necessarily clear the cards immediately so user can see completion
        # but for a "reset" we might want to if they start a new one.

    def add_download_progress(self, download_id, title, artist):
        """Add a premium card for a specific download."""
        card = ctk.CTkFrame(self.downloads_scroll, fg_color=Styles.BG_CARD, corner_radius=10)
        card.grid(row=len(self.current_downloads), column=0, sticky="ew", padx=10, pady=5)
        card.grid_columnconfigure(0, weight=1)

        # Content Frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        content.grid_columnconfigure(0, weight=1)

        # Labels
        title_label = ctk.CTkLabel(content, text=title, font=Styles.BODY_BOLD, anchor="w")
        title_label.grid(row=0, column=0, sticky="w")
        
        artist_label = ctk.CTkLabel(content, text=artist, font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_SECONDARY, anchor="w")
        artist_label.grid(row=1, column=0, sticky="w")

        # Progress bar
        pbar = ctk.CTkProgressBar(card, height=4, fg_color=Styles.BG_DARK, progress_color=Styles.ACCENT_GREEN)
        pbar.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        pbar.set(0)

        # Status label (right side)
        status_label = ctk.CTkLabel(content, text="Waiting...", font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_DIM)
        status_label.grid(row=0, column=1, rowspan=2, padx=(10, 0))

        self.current_downloads[download_id] = {
            'card': card,
            'pbar': pbar,
            'status': status_label
        }

    def update_download_progress(self, download_id, progress, status=None):
        """Update the progress card with value and status text."""
        if download_id in self.current_downloads:
            info = self.current_downloads[download_id]
            info['pbar'].set(progress)
            
            # Status display logic
            if status == DownloadStatus.COMPLETED or progress >= 1.0:
                info['status'].configure(text="DONE", text_color=Styles.ACCENT_GREEN)
                info['pbar'].set(1.0)
            elif status == DownloadStatus.FAILED:
                info['status'].configure(text="FAILED", text_color="#FF4444")
            elif status == DownloadStatus.DOWNLOADING or progress > 0:
                percent = int(progress * 100)
                info['status'].configure(text=f"{percent}%", text_color=Styles.TEXT_SECONDARY)
            else:
                info['status'].configure(text="Waiting...", text_color=Styles.TEXT_DIM)

    def update_overall_progress(self, completed, total):
        """Update the main progress bar and counter."""
        if total > 0:
            progress = completed / total
            self.overall_progress_bar.set(progress)
            self.overall_progress_label.configure(
                text=f"Downloaded {completed} of {total} tracks",
                text_color=Styles.ACCENT_GREEN if completed == total else Styles.TEXT_SECONDARY
            )
        else:
            self.overall_progress_bar.set(0)
            self.overall_progress_label.configure(text="0/0 tracks", text_color=Styles.TEXT_SECONDARY)

    def open_downloads(self):
        path = os.path.abspath(self.download_service.download_path)
        if not os.path.exists(path): os.makedirs(path)
        cmd = 'open' if os.sys.platform == 'darwin' else 'xdg-open' if os.name != 'nt' else 'start'
        if os.name == 'nt': os.startfile(path)
        else: subprocess.Popen([cmd, path])

    def select_folder(self):
        new_path = ctk.filedialog.askdirectory()
        if new_path:
            try:
                self.download_service.set_download_path(new_path)
                self.path_display.configure(text=os.path.abspath(new_path))
                self.save_settings()
            except ValueError as e:
                messagebox.showerror("Invalid Path", str(e))
