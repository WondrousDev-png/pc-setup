import os
import sys
import ctypes
import subprocess
import requests
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk

# --- CONFIGURATION ---

# App Definitions
# 'exe_name' is the name of the final executable file installed on the PC.
# We need this to launch the app later.
APPS = {
    "Comet": {
        "url": "https://www.perplexity.ai/download-comet?referrer=singular_click_id%3D5f6f8a8c-3d12-473d-8ee6-d3174c8aecd5",
        "args": ["/verysilent", "/install"],
        "exe_name": "Perplexity.exe", # Guessing based on standard install paths
        "type": "exe"
    },
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
        "url": "https://launcher.mojang.com/download/MinecraftInstaller.msi",
        "args": ["/qn"],
        "exe_name": "MinecraftLauncher.exe",
        "type": "msi"
    },
    "Voicemeeter Banana": {
        "url": "https://download.vb-audio.com/Download_CABLE/VoicemeeterProSetup.exe",
        "args": ["/S"],
        "exe_name": "voicemeeterpro.exe",
        "type": "exe"
    }
}

WALLPAPER_URL = "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=1170&auto=format&fit=crop"

# ---------------------

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Setup Installer")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        self.label_title = tk.Label(root, text="System Setup", font=("Segoe UI", 16, "bold"))
        self.label_title.pack(pady=20)

        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        self.label_status = tk.Label(root, textvariable=self.status_var, font=("Segoe UI", 10))
        self.label_status.pack(pady=10)

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=20)
        
        # Console Output (Optional, for details)
        self.console = tk.Text(root, height=8, width=45, font=("Consolas", 8))
        self.console.pack(pady=5)
        self.console.config(state=tk.DISABLED)

        # Start Button
        self.start_btn = ttk.Button(root, text="Start Install", command=self.start_thread)
        self.start_btn.pack(pady=10)

    def log(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def start_thread(self):
        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self):
        total_steps = len(APPS) + 2 # +1 for Wallpaper, +1 for Launching
        current_step = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # 1. Install Apps
            for name, config in APPS.items():
                current_step += 1
                self.status_var.set(f"Installing {name}...")
                self.progress['value'] = (current_step / total_steps) * 100
                self.root.update_idletasks()
                
                self.log(f"Downloading {name}...")
                
                # Determine extension
                ext = ".msi" if config['type'] == "msi" else ".exe"
                installer_path = os.path.join(temp_dir, name.replace(" ", "_") + ext)
                
                if self.download_file(config['url'], installer_path):
                    self.log(f"Installing {name}...")
                    try:
                        cmd = [installer_path] + config['args']
                        if config['type'] == "msi":
                            cmd = ["msiexec", "/i", installer_path] + config['args']
                            
                        subprocess.run(cmd, check=True)
                        self.log(f"SUCCESS: {name}")
                    except Exception as e:
                        self.log(f"ERROR: {name} failed: {e}")
                else:
                    self.log(f"ERROR: Download failed for {name}")

            # 2. Wallpaper
            current_step += 1
            self.status_var.set("Setting Wallpaper...")
            self.progress['value'] = (current_step / total_steps) * 100
            self.set_wallpaper(WALLPAPER_URL)
            self.log("Wallpaper updated.")

            # 3. Launch Apps
            self.status_var.set("Launching Applications...")
            self.launch_all_apps()
            
            # Finish
            self.progress['value'] = 100
            self.status_var.set("Installation Complete!")
            self.start_btn.config(text="Close", command=self.root.destroy, state=tk.NORMAL)

    def download_file(self, url, dest_path):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            self.log(str(e))
            return False

    def set_wallpaper(self, url):
        try:
            user_pictures = os.path.join(os.environ['USERPROFILE'], 'Pictures')
            local_path = os.path.join(user_pictures, "managed_wallpaper.jpg")
            if self.download_file(url, local_path):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, local_path, 3)
        except Exception as e:
            self.log(f"Wallpaper Error: {e}")

    def launch_all_apps(self):
        # We search common install locations for the exe_names
        common_paths = [
            os.environ["ProgramFiles"],
            os.environ["ProgramFiles(x86)"],
            os.path.join(os.environ["USERPROFILE"], "AppData", "Local"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming")
        ]
        
        for name, config in APPS.items():
            found = False
            exe = config['exe_name']
            self.log(f"Attempting to launch {name}...")
            
            for root_path in common_paths:
                # Walk through directories to find the exe (limit depth to save time)
                # This is a simplified search. Ideally, you know the exact path.
                for root, dirs, files in os.walk(root_path):
                    if exe in files:
                        full_path = os.path.join(root, exe)
                        try:
                            subprocess.Popen(full_path)
                            self.log(f"Launched: {name}")
                            found = True
                        except:
                            pass
                        break
                    # Stop if we go too deep to prevent freezing
                    if root.count(os.sep) - root_path.count(os.sep) > 3:
                        del dirs[:] 
                if found: break
            
            if not found:
                self.log(f"Could not auto-launch {name} (Path not found)")

if __name__ == "__main__":
    # Admin Check
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()