import subprocess
import os
import datetime
import logging

class BackupManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        self.logger = logging.getLogger(__name__)
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def backup_registry_key(self, root_str, subpath, app_name):
        """
        Exports a registry key to a .reg file.
        root_str: "HKLM" or "HKCU"
        subpath: "SOFTWARE\Microsoft\..."
        app_name: Name of the app (used for filename)
        """
        full_path = f"{root_str}\\{subpath}"
        
        # Sanitize app name for filename
        safe_name = "".join(x for x in app_name if x.isalnum() or x in " -_").strip()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.reg"
        filepath = os.path.join(self.backup_dir, filename)
        
        # reg export "Key" "File" /y
        cmd = ["reg", "export", full_path, filepath, "/y"]
        
        try:
            # shell=True might be needed for some windows commands, but subprocess.run usually prefers list without shell=True
            # reg.exe is in PATH.
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Backup created: {filepath}")
            return filepath
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Backup failed for {full_path}: {e.stderr}")
            raise Exception(f"Failed to backup registry key: {e.stderr}")

    def restore_backup(self, filepath):
        """
        Restores a .reg file.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Backup file not found: {filepath}")
            
        cmd = ["reg", "import", filepath]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Restored backup: {filepath}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Restore failed: {e.stderr}")
            raise Exception(f"Failed to restore registry key: {e.stderr}")
