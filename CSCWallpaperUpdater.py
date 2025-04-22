import os
import requests
import time
import threading
import ctypes
from pathlib import Path
from tkinter import Tk, Menu, messagebox
import pystray
from PIL import Image
import sys
import shutil
import winreg

SETTINGS_FILE = "link.txt"
IMAGE_FILE = "wallpaper.png"
ICON_FILE = "icon.png"
UPDATE_INTERVAL = 900  # 15 minutes in seconds
STARTUP_FLAG_FILE = "startup_enabled.txt"


def read_image_url():
    if not os.path.exists(SETTINGS_FILE):
        raise FileNotFoundError(f"Settings file '{SETTINGS_FILE}' not found.")
    with open(SETTINGS_FILE, 'r') as f:
        return f.read().strip()


def download_image():
    url = read_image_url()
    response = requests.get(url)
    if response.status_code == 200:
        with open(IMAGE_FILE, 'wb') as f:
            f.write(response.content)
        return True
    return False


def set_wallpaper():
    abs_path = os.path.abspath(IMAGE_FILE)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)


def update_wallpaper():
    try:
        if download_image():
            set_wallpaper()
    except Exception as e:
        print(f"Error updating wallpaper: {e}")


def schedule_updates():
    while True:
        update_wallpaper()
        time.sleep(UPDATE_INTERVAL)


def add_to_startup():
    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    name = "WallpaperUpdater"
    key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, exe_path)
        with open(STARTUP_FLAG_FILE, 'w') as f:
            f.write('1')
    except Exception as e:
        print(f"Failed to add to startup: {e}")


def remove_from_startup():
    name = "WallpaperUpdater"
    key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.DeleteValue(reg_key, name)
        if os.path.exists(STARTUP_FLAG_FILE):
            os.remove(STARTUP_FLAG_FILE)
    except Exception as e:
        print(f"Failed to remove from startup: {e}")


def is_startup_enabled():
    return os.path.exists(STARTUP_FLAG_FILE)


def toggle_startup(icon, item):
    if is_startup_enabled():
        remove_from_startup()
        messagebox.showinfo("Wallpaper Updater", "Removed from startup.")
    else:
        add_to_startup()
        messagebox.showinfo("Wallpaper Updater", "Added to startup.")


def on_quit(icon, item):
    icon.stop()
    os._exit(0)


def on_update_now(icon, item):
    update_wallpaper()
    messagebox.showinfo("Wallpaper Updater", "Wallpaper updated successfully.")


def create_icon():
    if not os.path.exists(ICON_FILE):
        image = Image.new('RGB', (64, 64), color='yellow')
    else:
        image = Image.open(ICON_FILE)
    icon = pystray.Icon("WallpaperUpdater", image, "Wallpaper Updater", menu=pystray.Menu(
        pystray.MenuItem("Update Now", on_update_now),
        pystray.MenuItem("Toggle Startup", toggle_startup),
        pystray.MenuItem("Quit", on_quit)
    ))
    icon.run()


def main():
    if is_startup_enabled():
        add_to_startup()
    threading.Thread(target=schedule_updates, daemon=True).start()
    create_icon()


if __name__ == "__main__":
    main()
