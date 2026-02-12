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
    "Minecraft Launcher": {
        # Legacy MSI is safest for automation
        "url": "https://launcher.mojang.com/download/MinecraftInstaller.msi", 
        "args": ["/qn"],
        "exe_name": "MinecraftLauncher.exe",
        "type": "msi"
    },
    "Voicemeeter Banana": {
        # Voicemeeter Pro (Banana)
        "url": "https://download.vb-audio.com/Download_CABLE/VoicemeeterProSetup.exe",
        "args": ["/S"], # /S is the silent switch
        "exe_name": "voicemeeterpro.exe", # This is the file we check for
        "type": "exe",
        "check_path": r"C:\Program Files (x86)\VB\Voicemeeter" # Explicit check path
    }
}

WALLPAPER_URL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964&auto=format&fit=crop"

# --- MODERN UI CLASS ---

class ModernInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Pro Setup Installer")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Theme Settings (Dark Mode + Blue Accent)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # Grid Config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="#101010", corner_radius=0, height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="SYSTEM DEPLOYMENT TOOL", 
            font=("Roboto Medium", 24),
            text_color="#3B8ED0" # Modern Blue
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")

        # 2. Status Area
        self.status_label = ctk.CTkLabel(
            self, 
            text="System Ready via GitHub Actions", 
            font=("Roboto", 14),
            text_color="#a0a0a0"
        )
        self.status_label.grid(row=1, column=0, pady=(30, 5))

        # 3. Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=450, height=12, corner_radius=6)
        self.progress_bar.grid(row=2, column=0, pady=10)
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="#3B8ED0")

        # 4. Console Log (Terminal Style)
        self.console = ctk.CTkTextbox(
            self, 
            width=500, 
            height=200, 
            corner_radius=10,
            fg_color="#050505", # Pitch black
            text_color="#00ff41", # Hacker Green
            font=("Consolas", 11)
        )
        self.console.grid(row=3, column=0, pady=20)
        self.console.insert("0.0", "> Initialize sequence...\n")
        self.console.configure(state="disabled")

        # 5. Action Button
        self.start_btn = ctk.CTkButton(
            self, 
            text="EXECUTE INSTALL", 
            font=("Roboto Bold", 15),
            height=45,
            width=220,
            fg_color="#3B8ED0",
            hover_color="#276496",
            command=self.start_thread
        )
        self.start_btn.grid(row=4, column=0, pady=(0, 25))

    def log(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", f"> {message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def start_thread(self):
        self.start_btn.configure(state="disabled", text="PROCESSING...")
        threading.Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self):
        total_steps = len(APPS) + 2
        current_step = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # --- INSTALLATION LOOP ---
            for name, config in APPS.items():
                current_step += 1
                progress = current_step / total_steps
                self.update_status(f"Installing {name}...", progress)
                
                # Download
                ext = ".msi" if config.get('type') == "msi" else ".exe"
                installer_path = os.path.join(temp_dir, name.replace(" ", "_") + ext)
                
                self.log(f"Downloading {name} from remote...")
                if self.download_file(config['url'], installer_path):
                    
                    self.log(f"Executing installer for {name}...")
                    try:
                        # Build Command
                        cmd = [installer_path] + config['args']
                        if config.get('type') == "msi":
                            cmd = ["msiexec", "/i", installer_path] + config['args']
                        
                        # Run with Timeout (3 mins max per app)
                        subprocess.run(cmd, check=True, timeout=180) 
                        
                        # VERIFY INSTALL (Crucial for Voicemeeter)
                        if "check_path" in config:
                            self.log(f"Verifying {name} files...")
                            time.sleep(2) # Give file system a moment
                            if os.path.exists(os.path.join(config['check_path'], config['exe_name'])):
                                self.log(f"SUCCESS: {name} verified.")
                            else:
                                self.log(f"WARNING: {name} installer finished, but file not found.")
                        else:
                            self.log(f"SUCCESS: {name} install command finished.")

                    except subprocess.TimeoutExpired:
                        self.log(f"TIMEOUT: {name} took too long. Skipping.")
                    except Exception as e:
                        self.log(f"ERROR: {name} failed. {e}")
                else:
                    self.log(f"ERROR: Download failed for {name}")

            # --- WALLPAPER ---
            current_step += 1
            self.update_status("Configuring Desktop Environment...", current_step / total_steps)
            self.set_wallpaper(WALLPAPER_URL)

            # --- LAUNCHING ---
            self.update_status("Launching Applications...", 0.98)
            self.launch_all_apps()
            
            # --- DONE ---
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Deployment Complete.")
            self.start_btn.configure(text="EXIT", state="normal", fg_color="#229A66", hover_color="#18754d", command=self.destroy)
            self.log("--------------------------------")
            self.log("Setup Finished.")
            self.log("NOTE: RESTART REQUIRED for Voicemeeter.")

    def update_status(self, text, progress):
        self.status_label.configure(text=text)
        self.progress_bar.set(progress)

    def download_file(self, url, dest_path):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            self.log(f"Network Error: {e}")
            return False

    def set_wallpaper(self, url):
        try:
            user_pictures = os.path.join(os.environ['USERPROFILE'], 'Pictures')
            local_path = os.path.join(user_pictures, "managed_wallpaper.jpg")
            if self.download_file(url, local_path):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, local_path, 3)
                self.log("Wallpaper updated successfully.")
        except Exception as e:
            self.log(f"Wallpaper Error: {e}")

    def launch_all_apps(self):
        # Extensive search paths
        search_paths = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Local"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming")
        ]
        
        for name, config in APPS.items():
            exe = config['exe_name']
            found = False
            self.log(f"Searching for {exe}...")
            
            for root_path in search_paths:
                for root, dirs, files in os.walk(root_path):
                    if exe in files:
                        full_path = os.path.join(root, exe)
                        try:
                            subprocess.Popen(full_path)
                            self.log(f"LAUNCHED: {name}")
                            found = True
                        except: 
                            pass
                        break
                    # Depth limit to prevent freezing
                    if root.count(os.sep) - root_path.count(os.sep) > 2:
                        del dirs[:]
                if found: break

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Re-run as Admin
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    app = ModernInstaller()
    app.mainloop()