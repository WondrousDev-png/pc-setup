import os
import sys
import ctypes
import subprocess
import requests
import tempfile
import shutil

# --- CONFIGURATION ---

APPS = {
    "Comet": {
        # This looks like the Perplexity Desktop App
        "url": "https://www.perplexity.ai/download-comet?referrer=singular_click_id%3D5f6f8a8c-3d12-473d-8ee6-d3174c8aecd5",
        "args": ["/verysilent", "/install"] # Fixed typo here
    },
    "Discord": {
        "url": "https://discord.com/api/downloads/distributions/app/installers/latest?channel=stable&platform=win&arch=x64",
        "args": ["/s"] # Discord uses /s for silent
    },
    "Spotify": {
        "url": "https://download.scdn.co/SpotifySetup.exe",
        "args": ["/silent"] # Spotify uses /silent
    }
}

WALLPAPER_URL = "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=1170&auto=format&fit=crop"

# ---------------------

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def download_file(url, dest_path):
    print(f"Downloading from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def install_app(name, config, temp_dir):
    installer_path = os.path.join(temp_dir, name + ".exe")
    print(f"\n--- Installing {name} ---")
    
    if download_file(config['url'], installer_path):
        print(f"Running installer...")
        try:
            cmd = [installer_path] + config['args']
            subprocess.run(cmd, check=True)
            print(f"Installed {name}.")
        except Exception as e:
            print(f"Failed to install {name}: {e}")

def set_wallpaper(image_url):
    print("\n--- Setting Wallpaper ---")
    try:
        user_pictures = os.path.join(os.environ['USERPROFILE'], 'Pictures')
        local_path = os.path.join(user_pictures, "managed_wallpaper.jpg")
        
        if download_file(image_url, local_path):
            ctypes.windll.user32.SystemParametersInfoW(20, 0, local_path, 3)
            print("Wallpaper updated.")
    except Exception as e:
        print(f"Wallpaper error: {e}")

def main():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    with tempfile.TemporaryDirectory() as temp_dir:
        for name, config in APPS.items():
            install_app(name, config, temp_dir)
        set_wallpaper(WALLPAPER_URL)

    print("\nSetup Complete.")

if __name__ == "__main__":
    main()