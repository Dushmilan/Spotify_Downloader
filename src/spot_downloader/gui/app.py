import customtkinter as ctk
import os
import subprocess
import json
import threading
from tkinter import messagebox
from PIL import Image

from ..services.download_service import DownloadService, ValidationService
from ..utils.helpers import check_ffmpeg
from ..config import app_config
from ..tracker import DownloadStatus
from .styles import Styles

class App(ctk.CTk):
    def __init__(self, download_service=None):
        super().__init__()

        self.title("Spot-Downloader Premium")
        self.geometry("900x750")
        self.minsize(800, 650)

        # Apply professional theme from styles
        Styles.apply_theme()

        # Dependency injection for testability
        self.download_service = download_service or DownloadService()
        self.download_thread = None
        
        # Initialize internal state
        self.current_downloads = {}
        self.frames = {}
        self.active_tab = "Search"

        self.setup_ui()
        self.load_settings()
        
        # Register the change callback with the tracker
        self.download_service.tracker.set_on_change_callback(self.on_tracker_change)

        if not check_ffmpeg():
            self.after(1500, self.show_ffmpeg_warning)

    def show_ffmpeg_warning(self):
        messagebox.showwarning(
            "FFmpeg Missing",
            "FFmpeg was not found. Download quality and conversion might be affected.\n"
            "Please install FFmpeg or use the bundled version."
        )

    def setup_ui(self):
        # Main layout: Sidebar (static) and Content Area (dynamic)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Frame (Spotify-like)
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=Styles.BG_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Spacer before bottom

        # Logo / Title
        logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Spot-DL", 
            font=Styles.HEADER_FONT, 
            text_color=Styles.ACCENT_GREEN
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(40, 40))

        # Nav Buttons
        self.search_btn = self._create_nav_button("Search", 1, "🔍", self.show_search)
        self.queue_btn = self._create_nav_button("Downloads", 2, "⬇️", self.show_downloads)
        self.settings_btn = self._create_nav_button("Settings", 3, "⚙️", self.show_settings)
        self.history_btn = self._create_nav_button("History", 4, "📜", self.show_history)

        # Bottom section in sidebar
        self.status_pill = ctk.CTkFrame(self.sidebar_frame, fg_color=Styles.BG_CARD, height=40, corner_radius=20)
        self.status_pill.grid(row=7, column=0, padx=15, pady=20, sticky="ew")
        
        self.status_dot = ctk.CTkLabel(self.status_pill, text="●", text_color=Styles.ACCENT_GREEN, font=("Arial", 14))
        self.status_dot.pack(side="left", padx=(15, 5))
        
        self.status_text = ctk.CTkLabel(self.status_pill, text="System Ready", font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_SECONDARY)
        self.status_text.pack(side="left")

        # 2. Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=Styles.BG_DARK)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Initialize Frames
        self._init_search_frame()
        self._init_downloads_frame()
        self._init_settings_frame()
        self._init_history_frame()

        self.show_search()

    def _create_nav_button(self, text, row, icon, command):
        btn = ctk.CTkButton(
            self.sidebar_frame,
            text=f"  {icon}  {text}",
            command=command,
            anchor="w",
            height=45,
            fg_color="transparent",
            text_color=Styles.TEXT_SECONDARY,
            hover_color=Styles.BG_CARD_HOVER,
            font=Styles.BODY_BOLD,
            corner_radius=8
        )
        btn.grid(row=row, column=0, padx=15, pady=4, sticky="ew")
        return btn

    def _init_search_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Search"] = frame
        frame.grid_columnconfigure(0, weight=1)

        # Greeting / Header
        header = ctk.CTkLabel(
            frame, 
            text="High Quality Audio Downloader", 
            font=Styles.SUBHEADER_FONT,
            text_color=Styles.TEXT_SECONDARY
        )
        header.grid(row=0, column=0, padx=40, pady=(100, 10), sticky="w")
        
        title = ctk.CTkLabel(
            frame, 
            text="Convert your Spotify playlists\nto high-quality MP3s.", 
            font=Styles.HEADER_FONT,
            justify="left"
        )
        title.grid(row=1, column=0, padx=40, pady=(0, 40), sticky="w")

        # Modern Search Input
        search_box = ctk.CTkFrame(frame, fg_color=Styles.BG_CARD, height=64, corner_radius=32, border_width=1, border_color=Styles.BORDER_COLOR)
        search_box.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        search_box.grid_columnconfigure(1, weight=1)
        search_box.grid_propagate(False)

        icon_lbl = ctk.CTkLabel(search_box, text="🔗", font=("Arial", 20))
        icon_lbl.grid(row=0, column=0, padx=(25, 10))

        self.url_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="Paste a Spotify URL or Search Query...",
            fg_color="transparent",
            border_width=0,
            font=Styles.BODY_MAIN,
            height=60
        )
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        self.url_entry.bind("<Return>", lambda e: self.start_download())

        # Start Button
        self.download_btn = ctk.CTkButton(
            frame,
            text="START DOWNLOAD",
            command=self.start_download,
            fg_color=Styles.ACCENT_GREEN,
            hover_color=Styles.ACCENT_GREEN_HOVER,
            text_color=Styles.BG_DARK,
            font=Styles.BODY_BOLD,
            height=54,
            width=220,
            corner_radius=27
        )
        self.download_btn.grid(row=3, column=0, padx=40, pady=30, sticky="w")

    def _init_downloads_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Downloads"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header Info
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(top_bar, text="Active Downloads", font=Styles.SUBHEADER_FONT)
        title.grid(row=0, column=0, sticky="w")

        self.cancel_all_btn = ctk.CTkButton(
            top_bar, 
            text="Cancel All", 
            width=100, 
            height=28, 
            fg_color=Styles.BG_DARK, 
            hover_color=Styles.ERROR,
            command=self.cancel_all_downloads
        )
        self.cancel_all_btn.grid(row=0, column=1, padx=10, sticky="e")

        self.overall_stat_lbl = ctk.CTkLabel(top_bar, text="0 files active", font=Styles.BODY_BOLD, text_color=Styles.ACCENT_GREEN)
        self.overall_stat_lbl.grid(row=0, column=2, sticky="e")

        # Scrollable area for cards
        self.downloads_scroll = ctk.CTkScrollableFrame(
            frame, 
            fg_color="transparent", 
            scrollbar_button_color=Styles.BG_CARD_HOVER,
            scrollbar_button_hover_color=Styles.TEXT_DIM
        )
        self.downloads_scroll.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.downloads_scroll.grid_columnconfigure(0, weight=1)

        # Empty State
        self.empty_label = ctk.CTkLabel(
            self.downloads_scroll, 
            text="\n\n\nNo active downloads.\nStart by pasting a link in the Search tab.",
            font=Styles.BODY_MAIN,
            text_color=Styles.TEXT_DIM
        )
        self.empty_label.grid(row=0, column=0, pady=50)

    def _init_settings_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Settings"] = frame
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="Preferences", font=Styles.SUBHEADER_FONT)
        title.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")

        # Settings Card
        card = ctk.CTkFrame(frame, fg_color=Styles.BG_CARD, corner_radius=15, border_width=1, border_color=Styles.BORDER_COLOR)
        card.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # 1. Download Path
        self._add_setting_row(card, 0, "Download Location", "Choose where files are saved", self.select_folder)
        self.path_display = ctk.CTkLabel(card, text="downloads", font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_SECONDARY)
        self.path_display.grid(row=0, column=1, sticky="e", padx=20)

        # 2. Audio Quality
        self._add_setting_row(card, 1, "Audio Quality", "Higher bitrates take more space", None)
        self.quality_var = ctk.StringVar(value=app_config.download_quality)
        quality_menu = ctk.CTkOptionMenu(
            card, 
            values=["128kbps", "256kbps", "320kbps"],
            variable=self.quality_var,
            command=self.save_settings,
            fg_color=Styles.BG_SIDEBAR,
            button_color=Styles.BG_CARD_HOVER,
            dropdown_hover_color=Styles.ACCENT_GREEN
        )
        quality_menu.grid(row=1, column=1, sticky="e", padx=20)

        # 3. Format
        self._add_setting_row(card, 2, "File Format", "Select output audio container", None)
        self.format_var = ctk.StringVar(value=app_config.file_format)
        format_menu = ctk.CTkOptionMenu(
            card, 
            values=["mp3", "m4a", "flac", "opus"],
            variable=self.format_var,
            command=self.save_settings,
            fg_color=Styles.BG_SIDEBAR,
            button_color=Styles.BG_CARD_HOVER
        )
        format_menu.grid(row=2, column=1, sticky="e", padx=20)

    def _add_setting_row(self, parent, row, title, desc, command):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=70)
        row_frame.grid(row=row, column=0, sticky="ew", padx=20, pady=5)
        
        lbl_title = ctk.CTkLabel(row_frame, text=title, font=Styles.BODY_BOLD)
        lbl_title.pack(anchor="w", pady=(10, 0))
        
        lbl_desc = ctk.CTkLabel(row_frame, text=desc, font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_DIM)
        lbl_desc.pack(anchor="w")

        if command:
            btn = ctk.CTkButton(parent, text="Change", width=80, height=32, fg_color=Styles.BG_SIDEBAR, hover_color=Styles.BG_CARD_HOVER, command=command)
            btn.grid(row=row, column=1, sticky="e", padx=20)

    def _init_history_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["History"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(frame, text="Execution Logs", font=Styles.SUBHEADER_FONT)
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        self.log_box = ctk.CTkTextbox(
            frame, 
            fg_color=Styles.BG_CARD, 
            border_width=1, 
            border_color=Styles.BORDER_COLOR,
            font=("Consolas", 12),
            text_color=Styles.TEXT_SECONDARY
        )
        self.log_box.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.log_box.configure(state="disabled")

    def show_frame(self, name):
        self.active_tab = name
        for f_name, frame in self.frames.items():
            if f_name == name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        # Update button highlights
        btns = [
            (self.search_btn, "Search"), 
            (self.queue_btn, "Downloads"), 
            (self.settings_btn, "Settings"), 
            (self.history_btn, "History")
        ]
        for btn, text in btns:
            if text == name:
                btn.configure(fg_color=Styles.BG_CARD_HOVER, text_color=Styles.ACCENT_GREEN)
            else:
                btn.configure(fg_color="transparent", text_color=Styles.TEXT_SECONDARY)

    def show_search(self): self.show_frame("Search")
    def show_downloads(self): self.show_frame("Downloads")
    def show_settings(self): self.show_frame("Settings")
    def show_history(self): self.show_frame("History")

    # --- Logic ---

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{threading.current_thread().name}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
        # Update status pill if it's a short message
        if len(msg) < 50:
            self.status_text.configure(text=msg)

    def load_settings(self):
        self.path_display.configure(text=os.path.basename(app_config.download_path))
        # Logic to sync with config UI elements...

    def save_settings(self, *args):
        app_config.set("download_quality", self.quality_var.get())
        app_config.set("file_format", self.format_var.get())
        app_config.save_config()
        self.log("Preferences updated.")

    def select_folder(self):
        path = ctk.filedialog.askdirectory()
        if path:
            app_config.set("download_path", path)
            self.path_display.configure(text=os.path.basename(path))
            app_config.save_config()
            self.log(f"Path changed to: {path}")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url: return

        self.download_btn.configure(state="disabled", text="PROCESSING...")
        self.url_entry.configure(state="disabled")
        
        # Switch to downloads view to see progress
        if self.active_tab != "Downloads":
            self.show_downloads()

        def run_dl():
            try:
                self.download_service.download(url, log_callback=self.log)
            except Exception as e:
                self.log(f"Error: {e}")
            finally:
                self.after(0, self.reset_ui)

        threading.Thread(target=run_dl, daemon=True).start()

    def cancel_all_downloads(self):
        if messagebox.askyesno("Cancel All", "Are you sure you want to stop all active downloads?"):
            self.download_service.downloader.cancel_all()
            self.log("Stopping all active downloads...")

    def open_download_folder(self):
        path = app_config.download_path
        if os.path.exists(path):
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
        else:
            messagebox.showerror("Error", f"Folder not found: {path}")

    def reset_ui(self):
        self.download_btn.configure(state="normal", text="START DOWNLOAD")
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, 'end')

    def on_tracker_change(self):
        self.after(0, self.update_queue_ui)

    def update_queue_ui(self):
        tracker = self.download_service.tracker
        downloads = tracker.get_all_downloads()
        
        if downloads and self.empty_label.winfo_exists():
            self.empty_label.grid_forget()

        for d in downloads:
            if d.id not in self.current_downloads:
                self.create_download_card(d)
            else:
                self.update_download_card(d)
        
        completed = sum(1 for d in downloads if d.status == DownloadStatus.COMPLETED)
        self.overall_stat_lbl.configure(text=f"{completed}/{len(downloads)} finished")

    def create_download_card(self, d):
        card = ctk.CTkFrame(self.downloads_scroll, fg_color=Styles.BG_CARD, height=80, corner_radius=12)
        card.grid(row=len(self.current_downloads), column=0, sticky="ew", padx=10, pady=5)
        card.grid_columnconfigure(1, weight=1)

        # Icon placeholder
        icon_frame = ctk.CTkFrame(card, width=50, height=50, corner_radius=6, fg_color=Styles.BG_DARK)
        icon_frame.grid(row=0, column=0, padx=15, pady=15)
        icon_lbl = ctk.CTkLabel(icon_frame, text="♪", font=("Arial", 20), text_color=Styles.ACCENT_GREEN)
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w")

        title_lbl = ctk.CTkLabel(info_frame, text=d.title[:45] + "..." if len(d.title) > 45 else d.title, font=Styles.BODY_BOLD)
        title_lbl.pack(anchor="w")
        
        artist_lbl = ctk.CTkLabel(info_frame, text=d.artist, font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_SECONDARY)
        artist_lbl.pack(anchor="w")

        pbar = ctk.CTkProgressBar(card, width=150, height=6, fg_color=Styles.BG_DARK, progress_color=Styles.ACCENT_GREEN)
        pbar.grid(row=0, column=2, padx=20)
        pbar.set(0)

        # Action Buttons Container
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.grid(row=0, column=3, padx=(0, 20))

        status_lbl = ctk.CTkLabel(actions_frame, text="Waiting", font=Styles.SMALL_LABEL_FONT, text_color=Styles.TEXT_DIM, width=70)
        status_lbl.pack(side="left", padx=5)

        folder_btn = ctk.CTkButton(
            actions_frame, 
            text="📁", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            hover_color=Styles.BG_DARK,
            command=self.open_download_folder
        )
        folder_btn.pack(side="left", padx=2)
        folder_btn.configure(state="disabled") # Only enable when finished

        self.current_downloads[d.id] = {
            "pbar": pbar,
            "status": status_lbl,
            "folder_btn": folder_btn,
            "card": card
        }

    def update_download_card(self, d):
        ui = self.current_downloads[d.id]
        ui["pbar"].set(d.progress)
        
        if d.status == DownloadStatus.COMPLETED:
            ui["status"].configure(text="Success", text_color=Styles.SUCCESS)
            ui["pbar"].set(1.0)
            ui["folder_btn"].configure(state="normal")
        elif d.status == DownloadStatus.FAILED:
            ui["status"].configure(text="Failed", text_color=Styles.ERROR)
        elif d.status == DownloadStatus.DOWNLOADING:
            ui["status"].configure(text=f"{int(d.progress*100)}%", text_color=Styles.TEXT_SECONDARY)
