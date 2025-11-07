import os
import json
import shutil
import uuid
import secrets
import subprocess
import ctypes
import time
import winreg
from datetime import datetime
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("[ERREUR] Ce script doit être exécuté en tant qu'administrateur.")
    input("Appuyez sur Entrée pour quitter...")
    exit(1)

APPDATA = os.getenv("APPDATA")
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
storage_file = Path(APPDATA) / "Cursor" / "User" / "globalStorage" / "storage.json"
backup_dir = Path(APPDATA) / "Cursor" / "User" / "globalStorage" / "backups"
cursor_path = Path(LOCALAPPDATA) / "Programs" / "cursor" / "Cursor.exe"
updater_path = Path(LOCALAPPDATA) / "cursor-updater"

backup_dir.mkdir(parents=True, exist_ok=True)
if storage_file.exists():
    backup_name = f"storage.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(storage_file, backup_dir / backup_name)
    print(f"[INFO] Sauvegarde créée : {backup_name}")

def close_process(name):
    try:
        subprocess.run(["taskkill", "/F", "/IM", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible de fermer {name}: {e}")

close_process("Cursor.exe")

def random_hex(length):
    return secrets.token_hex(length // 2)

def new_standard_uuid():
    return str(uuid.uuid4())

prefix = "auth0|user_".encode("utf-8").hex()
machine_id = prefix + random_hex(64)
mac_machine_id = new_standard_uuid()
dev_device_id = new_standard_uuid()
sqm_id = "{" + str(uuid.uuid4()).upper() + "}"

print("[INFO] Nouveaux identifiants générés :")
print("machineId:", machine_id)
print("macMachineId:", mac_machine_id)
print("devDeviceId:", dev_device_id)
print("sqmId:", sqm_id)

def update_machine_guid():
    key_path = r"SOFTWARE\Microsoft\Cryptography"
    backup_file = backup_dir / f"MachineGuid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.reg"
    
    subprocess.run(["reg", "export", key_path, str(backup_file)], shell=True)
    
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
        new_guid = str(uuid.uuid4())
        winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, new_guid)
        print(f"[INFO] MachineGuid mis à jour : {new_guid}")

update_machine_guid()

if not storage_file.exists():
    print("[ERREUR] Fichier de configuration introuvable :", storage_file)
    exit(1)

with open(storage_file, "r", encoding="utf-8") as f:
    config = json.load(f)

telemetry = config.get("telemetry", {})
telemetry["machineId"] = machine_id
telemetry["macMachineId"] = mac_machine_id
telemetry["devDeviceId"] = dev_device_id
telemetry["sqmId"] = sqm_id
config["telemetry"] = telemetry

with open(storage_file, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("[INFO] Fichier de configuration mis à jour avec succès.")

if updater_path.exists():
    try:
        if updater_path.is_dir():
            shutil.rmtree(updater_path)
        else:
            updater_path.unlink()
        print("[INFO] Dossier de mise à jour supprimé.")
    except Exception as e:
        print(f"[ERREUR] Impossible de supprimer {updater_path}: {e}")

try:
    updater_path.touch(exist_ok=True)
    os.chmod(updater_path, 0o444)
    print("[INFO] Blocage des mises à jour appliqué avec succès.")
except Exception as e:
    print(f"[ERREUR] Échec du blocage des mises à jour : {e}")

if cursor_path.exists():
    subprocess.Popen([str(cursor_path)])
    print("[INFO] Cursor relancé.")
else:
    print("[AVERTISSEMENT] Impossible de trouver Cursor.exe")

input("\nAppuyez sur Entrée pour quitter...")
