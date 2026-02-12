import os
import sys
import ctypes
import subprocess
import requests
import tempfile
import threading
import time
import customtkinter as ctk 

# --- CONFIGURATION ---

APPS = {
    "Discord": {
        "url": "https://discord.com/api/downloads/distributions/app/installers/latest?channel=stable&platform=win&arch=x64",
        "args": ["/s"],
        "exe_name": "Discord.exe",
        "type": "exe"
    },
    "Spotify": {
        "url": "https://download.scdn.co/SpotifySetup.exe",
        "args": ["/silent"],
        "exe_name": "Spotify.exe",
        "type": "exe"
    },
    "Steam": {
        "url": "https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe",
        "args": ["/S"],
        "exe_name": "Steam.exe",
        "type": "exe"
    },
    "Minecraft": {
        "url": "https://launcher.mojang.com/download/MinecraftInstaller.msi", 
        "args": ["/qn"],
        "exe_name": "MinecraftLauncher.exe",
        "type": "msi"
    },
    "Voicemeeter": {
        "url": "https://download.vb-audio.com/Download_CABLE/VoicemeeterProSetup.exe",
        "args": ["/S"],
        "exe_name": "voicemeeterpro.exe",
        "type": "exe",
        "check_path": r"C:\Program Files (x86)\VB\Voicemeeter"
    }
}

WALLPAPER_URL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964&auto=format&fit=crop"

# --- BENTO UI CLASS ---

class BentoInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW SETUP ---
        self.title("System Installer")
        self.geometry("700x500")
        self.resizable(False, False)
        
        # Color Palette (Apple Dark Mode Style)
        self.col_bg = "#000000"       # Pure Black Background
        self.col_card = "#1c1c1e"     # Apple Card Grey
        self.col_accent = "#0A84FF"   # iOS Blue
        self.col_text = "#FFFFFF"     # White
        self.col_sub = "#8E8E93"      # Subtitle Grey

        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.col_bg)

        # --- GRID LAYOUT SETUP ---
        # We create a 2x2 grid for our 'Bento Boxes'
        self.grid_columnconfigure(0, weight=1) # Left Col (Status)
        self.grid_columnconfigure(1, weight=2) # Right Col (Console)
        self.grid_rowconfigure(0, weight=1)    # Top Row
        self.grid_rowconfigure(1, weight=0)    # Bottom Row (Button)

        # --- CARD 1: HEADER & STATUS (Top Left) ---
        self.card_status = ctk.CTkFrame(self, fg_color=self.col_card, corner_radius=20)
        self.card_status.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        
        # Title
        self.lbl_title = ctk.CTkLabel(self.card_status, text="iOS Installer", font=("Segoe UI Display", 28, "bold"), text_color=self.col_text)
        self.lbl_title.pack(pady=(40, 5), padx=20, anchor="w")
        
        # Subtitle
        self.lbl_sub = ctk.CTkLabel(self.card_status, text="Automated Setup", font=("Segoe UI", 14), text_color=self.col_sub)
        self.lbl_sub.pack(pady=(0, 30), padx=20, anchor="w")

        # Big Percentage Text
        self.lbl_percent = ctk.CTkLabel(self.card_status, text="0%", font=("Segoe UI", 60, "bold"), text_color=self.col_accent)
        self.lbl_percent.pack(pady=10)
        
        # Status Text
        self.lbl_status = ctk.CTkLabel(self.card_status, text="Ready", font=("Segoe UI", 16), text_color=self.col_sub)
        self.lbl_status.pack(pady=5)

        # --- CARD 2: CONSOLE / TERMINAL (Top Right) ---
        self.card_console = ctk.CTkFrame(self, fg_color=self.col_card, corner_radius=20)
        self.card_console.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

        # "Terminal" Label
        self.lbl_term = ctk.CTkLabel(self.card_console, text="Activity Log", font=("Segoe UI", 12, "bold"), text_color=self.col_sub)
        self.lbl_term.pack(pady=(15, 5), padx=15, anchor="w")

        # The Textbox
        self.console = ctk.CTkTextbox(
            self.card_console,
            font=("Consolas", 11),
            text_color="#00FF41",   # Hacker Green text
            fg_color="#101010",     # Darker inner bg
            corner_radius=10
        )
        self.console.pack(expand=True, fill="both", padx=15, pady=(0, 15))
        self.console.insert("0.0", "> Waiting for user...\n")
        self.console.configure(state="disabled")

        # --- CARD 3: CONTROLS (Bottom Spanning) ---
        self.card_controls = ctk.CTkFrame(self, fg_color=self.col_card, corner_radius=20, height=80)
        self.card_controls.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        # Progress Bar (Thin Apple Style)
        self.progress_bar = ctk.CTkProgressBar(self.card_controls, height=8, corner_radius=5, progress_color=self.col_accent)
        self.progress_bar.pack(fill="x", padx=30, pady=(25, 5))
        self.progress_bar.set(0)

        # Start Button (Floating Pill)
        self.btn_start = ctk.CTkButton(
            self.card_controls,
            text="Install Everything",
            font=("Segoe UI", 14, "bold"),
            fg_color=self.col_text,     # White Button
            text_color="black",         # Black Text
            hover_color="#e0e0e0",
            height=40,
            corner_radius=20,
            command=self.start_thread
        )
        self.btn_start.pack(pady=(5, 20))

    def log(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", f"> {message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def start_thread(self):
        self.btn_start.configure(state="disabled", text="Running...")
        threading.Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self):
        total_steps = len(APPS) + 2
        current_step = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # --- APPS ---
            for name, config in APPS.items():
                current_step += 1
                progress = current_step / total_steps
                self.update_ui(f"Installing {name}...", progress)
                
                # Logic
                ext = ".msi" if config.get('type') == "msi" else ".exe"
                path = os.path.join(temp_dir, name.replace(" ", "_") + ext)
                
                self.log(f"Downloading {name}...")
                if self.download_file(config['url'], path):
                    self.log(f"Installing {name}...")
                    try:
                        cmd = [path] + config['args']
                        if config.get('type') == "msi": cmd = ["msiexec", "/i", path] + config['args']
                        
                        subprocess.run(cmd, check=True, timeout=180) 
                        
                        # Voicemeeter Check
                        if "check_path" in config:
                            time.sleep(2)
                            if os.path.exists(os.path.join(config['check_path'], config['exe_name'])):
                                self.log(f"VERIFIED: {name}")
                            else:
                                self.log(f"WARNING: {name} check failed.")
                        else:
                            self.log(f"INSTALLED: {name}")

                    except subprocess.TimeoutExpired:
                        self.log(f"TIMEOUT: {name} skipped.")
                    except Exception as e:
                        self.log(f"ERROR: {name} - {e}")

            # --- WALLPAPER ---
            current_step += 1
            self.update_ui("Setting Wallpaper", current_step / total_steps)
            self.set_wallpaper(WALLPAPER_URL)

            # --- LAUNCH ---
            self.update_ui("Launching Apps", 1.0)
            self.launch_all_apps()
            
            # --- FINISH ---
            self.lbl_percent.configure(text="100%")
            self.lbl_status.configure(text="Complete")
            self.btn_start.configure(text="Close", state="normal", fg_color=self.col_accent, text_color="white", command=self.destroy)

    def update_ui(self, text, progress):
        self.lbl_status.configure(text=text)
        self.lbl_percent.configure(text=f"{int(progress * 100)}%")
        self.progress_bar.set(progress)

    def download_file(self, url, dest_path):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            r = requests.get(url, headers=headers, stream=True)
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            return True
        except Exception as e:
            self.log(f"DL Error: {e}")
            return False

    def set_wallpaper(self, url):
        try:
            path = os.path.join(os.environ['USERPROFILE'], 'Pictures', "bento_wp.jpg")
            if self.download_file(url, path):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
                self.log("Wallpaper set.")
        except: pass

    def launch_all_apps(self):
        paths = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Local"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming")
        ]
        for name, config in APPS.items():
            exe = config['exe_name']
            found = False
            for root_path in paths:
                for root, dirs, files in os.walk(root_path):
                    if exe in files:
                        try:
                            subprocess.Popen(os.path.join(root, exe))
                            self.log(f"Launched {name}")
                            found = True
                        except: pass
                        break
                    if root.count(os.sep) - root_path.count(os.sep) > 2: del dirs[:]
                if found: break

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    app = BentoInstaller()
    app.mainloop()