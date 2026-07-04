import os
import json

CONFIG_PATH = "data/email_configs.json"

DEFAULT_SYSTEM_CONFIG = {
    "active_email": "",
    "profiles": {}
}

def load_email_config() -> dict:
    """Reads the configuration file, supporting multiple profiles."""
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SYSTEM_CONFIG, f, indent=2)
        return DEFAULT_SYSTEM_CONFIG
        
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # MIGRATION: If the old single-dict format is detected, convert it safely
            if "profiles" not in data:
                migrated_data = {"active_email": data.get("email", ""), "profiles": {}}
                if data.get("email"):
                    migrated_data["profiles"][data["email"]] = {
                        "app_password": data.get("app_password", ""),
                        "imap_server": data.get("imap_server", "imap.gmail.com"),
                        "port": data.get("port", 993)
                    }
                return migrated_data
                
            return data
    except Exception:
        return DEFAULT_SYSTEM_CONFIG

def save_email_config(single_profile_payload: dict) -> bool:
    """Adds or updates a single profile and sets it as the active listener target."""
    try:
        current_data = load_email_config()
        email_key = str(single_profile_payload.get("email", "")).strip()
        
        if not email_key:
            return False
            
        # Update the specific profile
        current_data["profiles"][email_key] = {
            "app_password": str(single_profile_payload.get("app_password", "")).strip(),
            "imap_server": str(single_profile_payload.get("imap_server", "imap.gmail.com")).strip(),
            "port": int(single_profile_payload.get("port", 993))
        }
        
        # Set this newly saved/updated profile as the active one
        current_data["active_email"] = email_key
        
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)
            
        return True
    except Exception as e:
        print(f"[CONFIG ERROR] Failed to write settings to JSON: {e}")
        return False