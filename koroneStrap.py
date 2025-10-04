import os
import subprocess
import sys
import json
import platform
import glob
import urllib.request
from colorama import Fore, Style, init

init(autoreset=True)

FASTFLAGS_FILE = "fastFlags.json"
BOOTSTRAPPER_URL = "https://github.com/umepa/korone-clients/releases/download/Client/KoronePlayerLauncher.exe"
BOOTSTRAPPER_FILE = "KoronePlayerLauncher.exe"
FPS_UNLOCKER_URL = "https://github.com/umepa/korone-clients/releases/download/Client/KoroneFpsUnlocker.exe"
FPS_UNLOCKER_FILE = "KoroneFpsUnlocker.exe"

if os.name == "nt":
    import msvcrt
    def press_any_key(prompt="Press any key to continue..."):
        print(Fore.MAGENTA + prompt, end="", flush=True)
        msvcrt.getch()
        print()
else:
    def press_any_key(prompt="Press any key to continue..."):
        input(Fore.MAGENTA + prompt)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def get_system_info():
    system = platform.system().lower()
    return {
        'is_windows': system == 'windows',
        'is_linux': system == 'linux',
        'is_macos': system == 'darwin',
        'system_name': system
    }

def get_version_roots():
    sys_info = get_system_info()
    roots = []
    if sys_info['is_windows']:
        roots.extend([
            os.path.expandvars(r"%localappdata%\ProjectX\Versions"),
            os.path.expandvars(r"%localappdata%\Pekora\Versions"),
        ])
    elif sys_info['is_linux']:
        user = os.getenv('USER', 'user')
        roots.extend([
            os.path.expanduser(f"~/.wine/drive_c/users/{user}/AppData/Local/ProjectX/Versions"),
            os.path.expanduser(f"~/.wine/drive_c/users/{user}/AppData/Local/Pekora/Versions"),
        ])
    elif sys_info['is_macos']:
        user = os.getenv('USER', 'user')
        roots.extend([
            os.path.expanduser(f"~/.wine/drive_c/users/{user}/AppData/Local/ProjectX/Versions"),
            os.path.expanduser(f"~/.wine/drive_c/users/{user}/AppData/Local/Pekora/Versions"),
        ])
        roots.extend(glob.glob(os.path.expanduser(f"~/Library/Application Support/CrossOver/Bottles/*/drive_c/users/{user}/AppData/Local/ProjectX/Versions")))
        roots.extend(glob.glob(os.path.expanduser(f"~/Library/Application Support/CrossOver/Bottles/*/drive_c/users/{user}/AppData/Local/Pekora/Versions")))
    return [p for p in roots if isinstance(p, str)]

def iter_version_dirs():
    for root in get_version_roots():
        if os.path.isdir(root):
            for d in sorted(glob.glob(os.path.join(root, "*"))):
                if os.path.isdir(d):
                    yield d

def get_clientsettings_targets():
    targets = []
    for ver in iter_version_dirs():
        for folder in ["2020L", "2021M"]:
            folder_path = os.path.join(ver, folder)
            if os.path.isdir(folder_path):
                client_dir = os.path.join(folder_path, "ClientSettings")
                settings_path = os.path.join(client_dir, "ClientAppSettings.json")
                targets.append((client_dir, settings_path, folder))
    return targets

def get_executable_paths(folder):
    paths = []
    for ver in iter_version_dirs():
        if folder in ["2017", "2018"]:
            # 2017/2018 için doğru klasör
            for exe_path in glob.glob(os.path.join(ver, f"{folder}L", "ProjectXPlayerBeta.exe")):
                paths.append(exe_path)
        else:
            exe = os.path.join(ver, folder, "ProjectXPlayerBeta.exe")
            if os.path.isfile(exe):
                paths.append(exe)
    return paths

def load_fastflags():
    if not os.path.exists(FASTFLAGS_FILE):
        with open(FASTFLAGS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(FASTFLAGS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(Fore.RED + "[!] Error reading fastFlags.json - invalid JSON format")
        return {}

def save_fastflags(fastflags):
    try:
        with open(FASTFLAGS_FILE, "w") as f:
            json.dump(fastflags, f, indent=2)
        print(Fore.GREEN + "[*] FastFlags saved successfully!")
    except Exception as e:
        print(Fore.RED + f"[!] Failed to save FastFlags: {e}")

def apply_fastflags(fastflags):
    success = False
    for client_dir, settings_path, folder in get_clientsettings_targets():
        try:
            os.makedirs(client_dir, exist_ok=True)
            if os.path.exists(settings_path):
                try:
                    os.replace(settings_path, settings_path + ".bak")
                except Exception:
                    pass
            with open(settings_path, "w") as f:
                json.dump(fastflags, f, indent=2)
            print(Fore.GREEN + f"[*] Applied FastFlags to {folder}/ClientSettings")
            print(Fore.CYAN + f"[*] Location: {settings_path}")
            success = True
        except Exception as e:
            print(Fore.RED + f"[!] Failed to write to {folder}: {e}")
    return success

def auto_detect_value_type(value_str):
    value_str = value_str.strip()
    if value_str.lower() in ['true', 'false']:
        return value_str.lower() == 'true'
    try:
        if '.' not in value_str and 'e' not in value_str.lower():
            return int(value_str)
    except ValueError:
        pass
    try:
        return float(value_str)
    except ValueError:
        pass
    return value_str

def ask_fastflags():
    while True:
        clear()
        print(Fore.YELLOW + "FastFlags Configuration")
        fastflags = load_fastflags()
        if fastflags:
            print(Fore.CYAN + "Current FFlags:")
            for i, (k, v) in enumerate(fastflags.items(), 1):
                value_type = type(v).__name__
                print(Fore.YELLOW + f" {i}. {k} = {v} ({value_type})")
        else:
            print(Fore.MAGENTA + "No fflags set yet")
        print(Fore.GREEN + "\nOptions:")
        print("1. Add FastFlag")
        print("2. Remove FastFlag")
        print("3. Clear all FastFlags")
        print("4. Apply FastFlags")
        print("5. Import FastFlags from JSON")
        print("0. Back to main menu")
        choice = input(Fore.WHITE + "\nEnter choice: ").strip()
        if choice == "1":
            add_fastflag(fastflags)
        elif choice == "2":
            remove_fastflag(fastflags)
        elif choice == "3":
            clear_fastflags()
        elif choice == "4":
            if fastflags:
                apply_fastflags(fastflags)
                print(Fore.GREEN + "[*] FastFlags applied successfully.")
            else:
                print(Fore.YELLOW + "[*] No FastFlags to apply")
            press_any_key()
        elif choice == "5":
            import_fastflags()
        elif choice == "0":
            break
        else:
            print(Fore.RED + "Invalid choice!")
            press_any_key()

def add_fastflag(fastflags):
    print(Fore.GREEN + "\nAdd New FastFlag:")
    key = input(Fore.WHITE + "\nKey: ").strip()
    if not key:
        print(Fore.RED + "[*] Cancelled - no key provided")
        press_any_key()
        return
    value_input = input(Fore.WHITE + "Value: ").strip()
    if value_input == "":
        print(Fore.RED + "[*] Cancelled - no value provided")
        press_any_key()
        return
    value = auto_detect_value_type(value_input)
    fastflags[key] = value
    save_fastflags(fastflags)
    value_type = type(value).__name__
    print(Fore.GREEN + f"[*] Added FastFlag: {key} = {value} ({value_type})")
    press_any_key()

def remove_fastflag(fastflags):
    if not fastflags:
        print(Fore.YELLOW + "[*] No FastFlags to remove")
        press_any_key()
        return
    key = input(Fore.WHITE + "Enter key to remove: ").strip()
    if key in fastflags:
        del fastflags[key]
        save_fastflags(fastflags)
        print(Fore.GREEN + f"[*] Removed FastFlag: {key}")
    else:
        print(Fore.RED + f"[!] FastFlag '{key}' not found")
    press_any_key()

def clear_fastflags():
    confirm = input(Fore.RED + "Are you sure you want to clear ALL FastFlags? (y/N): ").strip().lower()
    if confirm == 'y':
        save_fastflags({})
        print(Fore.GREEN + "[*] All FastFlags cleared")
    else:
        print(Fore.YELLOW + "[*] Cancelled")
    press_any_key()

def import_fastflags():
    print(Fore.CYAN + "\nImport FastFlags from JSON:")
    lines = []
    empty_count = 0
    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2 or (len(lines) > 0 and lines[-1] == ""):
                break
        else:
            empty_count = 0
        lines.append(line)
    while lines and lines[-1] == "":
        lines.pop()
    json_text = "\n".join(lines)
    if not json_text.strip():
        print(Fore.YELLOW + "[*] No content provided")
        press_any_key()
        return
    try:
        imported_flags = json.loads(json_text)
        if not isinstance(imported_flags, dict):
            print(Fore.RED + "[!] JSON must be an object/dictionary")
            press_any_key()
            return
        current_flags = load_fastflags()
        current_flags.update(imported_flags)
        save_fastflags(current_flags)
        print(Fore.GREEN + f"[*] Imported {len(imported_flags)} FastFlag(s)")
        for k, v in imported_flags.items():
            print(Fore.CYAN + f"  + {k} = {v}")
    except json.JSONDecodeError as e:
        print(Fore.RED + f"[!] Invalid JSON format: {e}")
    press_any_key()

def download_bootstrapper():
    clear()
    print(Fore.CYAN + "Download/Update Bootstrapper")
    print(Fore.YELLOW + f"Downloading from: {BOOTSTRAPPER_URL}")
    print(Fore.YELLOW + f"Saving to: {BOOTSTRAPPER_FILE}")
    
    if os.path.exists(BOOTSTRAPPER_FILE):
        overwrite = input(Fore.WHITE + f"{BOOTSTRAPPER_FILE} already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print(Fore.YELLOW + "[*] Download cancelled")
            press_any_key()
            return
    
    try:
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, downloaded * 100 // total_size)
                print(Fore.GREEN + f"\rDownloading: {percent}% ", end="")
        
        urllib.request.urlretrieve(BOOTSTRAPPER_URL, BOOTSTRAPPER_FILE, reporthook=show_progress)
        print(Fore.GREEN + "\n[*] Download completed successfully!")
        
        # Windows için direkt aç
        if get_system_info()['is_windows']:
            os.startfile(BOOTSTRAPPER_FILE)
        else:
            wine_cmd = "wine64"
            try:
                subprocess.check_output([wine_cmd, "--version"], stderr=subprocess.DEVNULL)
            except Exception:
                wine_cmd = "wine"
            subprocess.Popen([wine_cmd, BOOTSTRAPPER_FILE])
        print(Fore.GREEN + "[*] Bootstrapper launched successfully!")
    except Exception as e:
        print(Fore.RED + f"[!] Download/launch failed: {e}")
    press_any_key()

def download_and_launch_fps_unlocker():
    clear()
    print(Fore.CYAN + "Download/Launch Korone FPS Unlocker")
    
    if not os.path.exists(FPS_UNLOCKER_FILE):
        print(Fore.YELLOW + f"Downloading from: {FPS_UNLOCKER_URL}")
        try:
            def show_progress(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, downloaded * 100 // total_size)
                    print(Fore.GREEN + f"\rDownloading: {percent}% ", end="")
            urllib.request.urlretrieve(FPS_UNLOCKER_URL, FPS_UNLOCKER_FILE, reporthook=show_progress)
            print(Fore.GREEN + "\n[*] Download completed successfully!")
        except Exception as e:
            print(Fore.RED + f"[!] Download failed: {e}")
            press_any_key()
            return

    try:
        if get_system_info()['is_windows']:
            os.startfile(FPS_UNLOCKER_FILE)
        else:
            wine_cmd = "wine64"
            try:
                subprocess.check_output([wine_cmd, "--version"], stderr=subprocess.DEVNULL)
            except Exception:
                wine_cmd = "wine"
            subprocess.Popen([wine_cmd, FPS_UNLOCKER_FILE])
        print(Fore.GREEN + "[*] FPS Unlocker launched successfully!")
    except Exception as e:
        print(Fore.RED + f"[!] Launch failed: {e}")
    press_any_key()

def launch_version(folder, only_browser=False):
    clear()
    sys_info = get_system_info()
    paths = get_executable_paths(folder)
    fastflags = load_fastflags()
    
    if fastflags and not only_browser:
        print(Fore.CYAN + f"[*] Applying {len(fastflags)} FastFlag(s)...")
        apply_fastflags(fastflags)

    if folder in ["2020L", "2021M"]:
        print(Fore.CYAN + f"Launch options for {folder}:")
        print("1) Launch Client (app)")
        print("2) Launch Browser")
        choice = input(Fore.WHITE + "Choose option: ").strip()
        if choice == "1":
            only_browser = False
        elif choice == "2":
            only_browser = True
        else:
            print(Fore.RED + "[!] Invalid choice, defaulting to Browser")
            only_browser = True

    exe_path = None
    for path in paths:
        if os.path.isfile(path):
            exe_path = path
            break

    if exe_path:
        try:
            cmd = [exe_path]
            if not only_browser:
                cmd.append("--app")
            if sys_info['is_windows']:
                subprocess.Popen(cmd)
            else:
                env = os.environ.copy()
                if sys_info['is_linux']:
                    env.update({
                        "__NV_PRIME_RENDER_OFFLOAD": "1",
                        "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
                    })
                wine_cmd = "wine64"
                try:
                    subprocess.check_output([wine_cmd, "--version"], stderr=subprocess.DEVNULL)
                except Exception:
                    wine_cmd = "wine"
                subprocess.Popen([wine_cmd] + cmd, env=env)
            print(Fore.GREEN + "[*] Launch Successful!")
        except Exception as e:
            print(Fore.RED + f"Error while launching:\n{e}")
    else:
        print(Fore.RED + "Could not find executable. Error code: EXECNFOUND")
        for path in paths:
            print(Fore.YELLOW + f"  - {path}")

    press_any_key()

def main_menu():
    while True:
        clear()
        sys_info = get_system_info()
        print(Fore.MAGENTA + "made by umepa on korone (forked from https://github.com/reprovision/koroneStrap)\n")
        print(Fore.YELLOW + "Select your option:")
        print(Fore.GREEN + "1 - 2017 (Only Browser)")
        print(Fore.GREEN + "2 - 2018 (Only Browser)")
        print(Fore.GREEN + "3 - 2020 (Browser or Client)")
        print(Fore.GREEN + "4 - 2021 (Browser or Client)")
        print(Fore.GREEN + "5 - Korone Fps Unlocker")
        print(Fore.GREEN + "6 - Set FastFlags")
        print(Fore.BLUE + "7 - Download/Update Bootstrapper")
        print(Fore.RED + "0 - Exit")
        
        choice = input(Fore.YELLOW + "\nEnter your choice: ").strip()
        if choice == "1":
            launch_version("2017", only_browser=True)
        elif choice == "2":
            launch_version("2018", only_browser=True)
        elif choice == "3":
            launch_version("2020L")
        elif choice == "4":
            launch_version("2021M")
        elif choice == "5":
            download_and_launch_fps_unlocker()
        elif choice == "6":
            ask_fastflags()
        elif choice == "7":
            download_bootstrapper()
        elif choice == "0":
            print(Fore.CYAN + "Goodbye!")
            sys.exit()
        else:
            print(Fore.RED + "Invalid choice! Try again.")
            press_any_key()

if __name__ == "__main__":
    main_menu()
