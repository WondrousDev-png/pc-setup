import os
import sys
import threading
import subprocess
import requests
import time
import webview # The library that lets us use HTML/CSS
import ctypes
import json

# --- CONFIGURATION ---
APPS = {
    "Google Chrome": {
        "url": "https://dl.google.com/chrome/install/googlechromestandaloneenterprise64.msi",
        "args": ["/qn"],
        "exe": "chrome.exe",
        "type": "msi",
        "launch": ["--start-minimized"]
    },
    "Discord": {
        "url": "https://discord.com/api/downloads/distributions/app/installers/latest?channel=stable&platform=win&arch=x64",
        "args": ["/s"],
        "exe": "Discord.exe",
        "type": "exe",
        "launch": ["--start-minimized"]
    },
    "Spotify": {
        "url": "https://download.scdn.co/SpotifySetup.exe",
        "args": ["/silent"],
        "exe": "Spotify.exe",
        "type": "exe",
        "launch": ["--minimized"]
    },
    "Steam": {
        "url": "https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe",
        "args": ["/S"],
        "exe": "Steam.exe",
        "type": "exe",
        "launch": ["-silent"]
    },
    "Voicemeeter": {
        "url": "https://download.vb-audio.com/Download_CABLE/VoicemeeterProSetup.exe",
        "args": ["/S"],
        "exe": "voicemeeterpro.exe",
        "type": "exe",
        "check": r"C:\Program Files (x86)\VB\Voicemeeter"
    }
}

WALLPAPER = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964&auto=format&fit=crop"

# --- THE HTML/CSS/JS UI ---
# We embed this directly so you only need one file.
HTML_UI = """
<!DOCTYPE html>
<html>
<head>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --primary: #00f2ff;
        --secondary: #0066ff;
        --bg: #050505;
        --glass: rgba(255, 255, 255, 0.05);
    }

    body {
        margin: 0;
        padding: 0;
        background-color: var(--bg);
        color: white;
        font-family: 'Inter', sans-serif;
        overflow: hidden;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* ANIMATED BACKGROUND GRADIENT */
    .bg-gradient {
        position: absolute;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, #000000, #1a0b2e, #0f0524, #000000);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        z-index: -1;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* GLASS CARD */
    .container {
        width: 700px;
        background: var(--glass);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    /* HEADER */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    
    h1 {
        margin: 0;
        font-weight: 800;
        font-size: 32px;
        background: linear-gradient(to right, #fff, #aaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    .version {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: rgba(255,255,255,0.4);
    }

    /* TERMINAL */
    .terminal {
        background: rgba(0,0,0,0.6);
        border-radius: 12px;
        height: 200px;
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: var(--primary);
        overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }

    .log-entry { margin-bottom: 6px; opacity: 0; animation: fadeIn 0.3s forwards; }
    .log-entry.error { color: #ff4444; }
    .log-entry.success { color: #00ff88; }

    @keyframes fadeIn { to { opacity: 1; } }

    /* PROGRESS BAR */
    .progress-container {
        height: 6px;
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        overflow: hidden;
        margin-top: 10px;
    }
    
    .progress-bar {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, var(--secondary), var(--primary));
        box-shadow: 0 0 20px var(--secondary);
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* BUTTON */
    button {
        background: white;
        color: black;
        border: none;
        padding: 18px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(255,255,255,0.2);
    }

    button:disabled {
        background: #333;
        color: #666;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }

</style>
</head>
<body>
    <div class="bg-gradient"></div>
    
    <div class="container">
        <div class="header">
            <div>
                <h1>NEXUS INSTALLER</h1>
                <div style="color: rgba(255,255,255,0.5); margin-top: 5px;">Automated Deployment System</div>
            </div>
            <div class="version">v5.0.0 [WEB-ENGINE]</div>
        </div>

        <div class="terminal" id="console"></div>

        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 14px; font-weight: 600;">STATUS</span>
                <span id="percent" style="font-family: 'JetBrains Mono'; color: var(--primary);">0%</span>
            </div>
            <div class="progress-container">
                <div class="progress-bar" id="bar"></div>
            </div>
        </div>

        <button id="btn" onclick="startInstall()">Initialize System</button>
    </div>

<script>
    // FUNCTIONS CALLED BY PYTHON
    function addLog(text, type='info') {
        const console = document.getElementById('console');
        const div = document.createElement('div');
        div.className = 'log-entry ' + type;
        div.textContent = '> ' + text;
        console.appendChild(div);
        console.scrollTop = console.scrollHeight;
    }

    function updateProgress(percent) {
        document.getElementById('bar').style.width = percent + '%';
        document.getElementById('percent').textContent = Math.round(percent) + '%';
    }

    function finish() {
        const btn = document.getElementById('btn');
        btn.textContent = 'EXIT';
        btn.disabled = false;
        btn.onclick = function() { pywebview.api.close_window() };
        btn.style.background = '#00ff88';
    }

    // CALL PYTHON
    function startInstall() {
        document.getElementById('btn').disabled = true;
        document.getElementById('btn').textContent = 'INSTALLING...';
        pywebview.api.start_install();
    }
</script>
</body>
</html>
"""

# --- PYTHON BACKEND CLASS ---
class InstallerAPI:
    def __init__(self):
        self.window = None

    def set_window(self, window):
        self.window = window

    def close_window(self):
        self.window.destroy()

    def log(self, text, type='info'):
        # Send javascript to the window to update the UI
        if self.window:
            safe_text = text.replace("'", "\\'")
            self.window.evaluate_js(f"addLog('{safe_text}', '{type}')")

    def progress(self, percent):
        if self.window:
            self.window.evaluate_js(f"updateProgress({percent})")

    def start_install(self):
        # Run in a separate thread to keep the UI smooth
        threading.Thread(target=self._install_logic, daemon=True).start()

    def _install_logic(self):
        total = len(APPS) + 2
        step = 0

        with tempfile.TemporaryDirectory() as temp_dir:
            self.log(f"Temp Dir created: {temp_dir}")

            for name, config in APPS.items():
                step += 1
                self.progress((step / total) * 100)
                
                # Download
                self.log(f"Downloading {name}...")
                ext = ".msi" if config.get('type') == "msi" else ".exe"
                local_path = os.path.join(temp_dir, name.replace(" ", "_") + ext)

                if self.download_file(config['url'], local_path):
                    # Install
                    self.log(f"Installing {name} (Silent)...")
                    try:
                        cmd = [local_path] + config['args']
                        if config.get('type') == "msi":
                            cmd = ["msiexec", "/i", local_path] + config['args']
                        
                        # Hide Window Flags
                        si = subprocess.STARTUPINFO()
                        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                        subprocess.run(cmd, check=True, startupinfo=si, timeout=300)
                        
                        # Verify
                        if "check" in config:
                            time.sleep(2)
                            if os.path.exists(os.path.join(config['check'], config['exe'])):
                                self.log(f"{name} Verified.", "success")
                            else:
                                self.log(f"Warning: {name} file missing.", "error")
                        else:
                            self.log(f"{name} Installed.", "success")
                            
                    except Exception as e:
                        self.log(f"Error installing {name}: {e}", "error")
                else:
                    self.log(f"Download failed: {name}", "error")

            # Wallpaper
            step += 1
            self.progress((step / total) * 100)
            self.log("Downloading Wallpaper...")
            self.set_wallpaper(WALLPAPER)

            # Launch
            self.log("Launching apps in background...")
            self.launch_apps()

            self.progress(100)
            self.log("All tasks complete.", "success")
            if self.window:
                self.window.evaluate_js("finish()")

    def download_file(self, url, dest):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            r = requests.get(url, headers=headers, stream=True)
            r.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            self.log(str(e), "error")
            return False

    def set_wallpaper(self, url):
        try:
            path = os.path.join(os.environ['USERPROFILE'], 'Pictures', "nexus_wp.jpg")
            if self.download_file(url, path):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
                self.log("Wallpaper updated.", "success")
        except: pass

    def launch_apps(self):
        paths = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Local")
        ]
        for name, config in APPS.items():
            exe = config['exe']
            flags = config.get('launch', [])
            found = False
            for root_path in paths:
                for root, dirs, files in os.walk(root_path):
                    if exe in files:
                        try:
                            subprocess.Popen([os.path.join(root, exe)] + flags)
                            self.log(f"Launched {name}", "success")
                            found = True
                        except: pass
                        break
                    if root.count(os.sep) - root_path.count(os.sep) > 3: del dirs[:]
                if found: break

# --- MAIN ---
if __name__ == '__main__':
    # Admin Check
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    api = InstallerAPI()
    
    # Create the window with the HTML above
    window = webview.create_window(
        "Nexus Installer", 
        html=HTML_UI, 
        js_api=api,
        width=800, 
        height=600,
        resizable=False,
        background_color='#000000'
    )
    
    api.set_window(window)
    webview.start(debug=False)