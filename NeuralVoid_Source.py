import sys
import os
import ctypes
import shutil
import winreg
import customtkinter as ctk

# --- CONFIGURATION ---
APP_NAME = "NeuralVoid"
VERSION = "1.0"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "0.0.0.0"

# --- DOMAINS TO KILL ---
BLOCKED_DOMAINS = [
    # Adobe Telemetry & GenAI
    "cc-api-data.adobe.io",
    "feature-api.adobe.io",
    "firefly.adobe.io",
    "p13n.adobe.io",
    "use.typekit.net",
    "geo2.adobe.com",
    # Microsoft Copilot / Edge / Recall / Telemetry
    "copilot.microsoft.com",
    "edgeservices.bing.com",
    "self.events.data.microsoft.com",
    "mobile.pipe.aria.microsoft.com",
    "browser.events.data.microsoft.com",
    # General AI Scrapers
    "telemetry.grammarly.com",
]

# --- GUI SETUP ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def backup_hosts():
    if not os.path.exists(HOSTS_PATH + ".bak"):
        shutil.copy(HOSTS_PATH, HOSTS_PATH + ".bak")

def toggle_registry_keys(enable_protection):
    # 1. Adobe FeatureLockDown (Disable GenAI)
    try:
        paths = [
            r"SOFTWARE\Policies\Adobe\Acrobat Reader\DC\FeatureLockDown",
            r"SOFTWARE\Policies\Adobe\Adobe Acrobat\DC\FeatureLockDown"
        ]
        val = 1 if enable_protection else 0
        for p in paths:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, p)
            winreg.SetValueEx(key, "bEnableGentech", 0, winreg.REG_DWORD, 0) # 0 = Disable Feature
            winreg.CloseKey(key)
    except Exception as e:
        print(f"Reg Error: {e}")

    # 2. Edge DoH (Disable DNS over HTTPS to prevent bypass)
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge")
        # BuiltInDnsClientEnabled: 0 = Disabled (Forces use of system Hosts file)
        reg_val = 0 if enable_protection else 1
        winreg.SetValueEx(key, "BuiltInDnsClientEnabled", 0, winreg.REG_DWORD, reg_val)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Edge Reg Error: {e}")

def modify_hosts(enable_protection):
    backup_hosts()
    with open(HOSTS_PATH, 'r') as f:
        lines = f.readlines()
    
    # Remove our blocks first to avoid duplicates
    lines = [line for line in lines if "NEURALVOID" not in line]

    if enable_protection:
        lines.append("\n# --- NEURALVOID BLOCKLIST START ---\n")
        for domain in BLOCKED_DOMAINS:
            lines.append(f"{REDIRECT_IP} {domain}\n")
            lines.append(f"{REDIRECT_IP} www.{domain}\n")
        lines.append("# --- NEURALVOID BLOCKLIST END ---\n")
    
    with open(HOSTS_PATH, 'w') as f:
        f.writelines(lines)
        
    # Flush DNS
    os.system("ipconfig /flushdns")

def update_status_ui(is_active):
    if is_active:
        status_label.configure(text="SHIELD ACTIVE", text_color="#00FF41") # Matrix Green
        btn_toggle.configure(text="DEACTIVATE SHIELD", fg_color="#330000", hover_color="#550000", border_color="#FF0000")
    else:
        status_label.configure(text="SHIELD INACTIVE", text_color="#FF0000")
        btn_toggle.configure(text="ACTIVATE SHIELD", fg_color="#003300", hover_color="#005500", border_color="#00FF41")

def on_toggle():
    current_text = status_label.cget("text")
    if "INACTIVE" in current_text:
        # Turn ON
        modify_hosts(True)
        toggle_registry_keys(True)
        update_status_ui(True)
    else:
        # Turn OFF
        modify_hosts(False)
        toggle_registry_keys(False)
        update_status_ui(False)

# --- APP START ---
if not is_admin():
    # Re-run as admin
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

app = ctk.CTk()
app.title(f"{APP_NAME} v{VERSION}")
app.geometry("400x350")
app.resizable(False, False)

# UI Elements
title = ctk.CTkLabel(app, text="NEURALVOID", font=("Courier New", 28, "bold"), text_color="#FFD700")
title.pack(pady=(30, 5))

subtitle = ctk.CTkLabel(app, text="System-Level AI Telemetry Blocker", font=("Arial", 12))
subtitle.pack(pady=(0, 20))

status_label = ctk.CTkLabel(app, text="SYSTEM SCANNING...", font=("Courier New", 18, "bold"))
status_label.pack(pady=20)

btn_toggle = ctk.CTkButton(app, text="INITIALIZE", font=("Arial", 14, "bold"), height=50, width=200, border_width=2, command=on_toggle)
btn_toggle.pack(pady=20)

footer = ctk.CTkLabel(app, text="XORD DEFENSE SYSTEMS", text_color="#555")
footer.pack(side="bottom", pady=10)

# Check initial state (simple check for one domain)
with open(HOSTS_PATH, 'r') as f:
    if "NEURALVOID" in f.read():
        update_status_ui(True)
    else:
        update_status_ui(False)

app.mainloop()
