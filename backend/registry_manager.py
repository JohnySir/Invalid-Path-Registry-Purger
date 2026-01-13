import winreg
import logging

class RegistryManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Define the registry paths to scan
        self.registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", 0)
        ]

    def get_installed_apps(self):
        """
        Scans all defined registry paths and returns a list of installed applications.
        """
        apps = []
        seen_keys = set() # To avoid duplicates if any

        for hkey, subpath, extra_flags in self.registry_paths:
            try:
                # Open the key with appropriate permissions (Read + optional WOW64 flag)
                access_mask = winreg.KEY_READ | extra_flags
                with winreg.OpenKey(hkey, subpath, 0, access_mask) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            full_registry_path = f"{subpath}\\{subkey_name}"
                            
                            # Construct a unique ID for deduplication/reference
                            # Using the tuple of (root_hkey, path) might be hard to serialize, 
                            # so we'll store string representation of root.
                            root_str = "HKLM" if hkey == winreg.HKEY_LOCAL_MACHINE else "HKCU"
                            unique_id = f"{root_str}\\{full_registry_path}"

                            if unique_id in seen_keys:
                                continue
                            
                            with winreg.OpenKey(hkey, full_registry_path, 0, access_mask) as subkey:
                                app_info = self._extract_app_info(subkey)
                                app_info['registry_path'] = full_registry_path
                                app_info['root_key'] = root_str
                                app_info['key_name'] = subkey_name
                                app_info['wow64_flag'] = extra_flags
                                
                                # Filter out items without a DisplayName (usually not user-facing apps)
                                if app_info.get('DisplayName'):
                                    if self._is_safe(app_info):
                                        apps.append(app_info)
                                        seen_keys.add(unique_id)
                                    
                        except WindowsError as e:
                            # Permission denied or key missing for specific subkey
                            self.logger.warning(f"Error accessing subkey index {i} in {subpath}: {e}")
                            continue
                            
            except WindowsError as e:
                self.logger.error(f"Failed to open registry path {subpath}: {e}")
                continue

        return apps

    def _is_safe(self, app_info):
        """
        Determines if an app entry is safe to display/modify.
        Filters out SystemComponents and known hardware/OS artifacts.
        """
        # 1. Check SystemComponent flag (usually 1 if it should be hidden)
        sys_comp = app_info.get('SystemComponent')
        if sys_comp == 1:
            return False
            
        name = app_info.get('DisplayName', '').strip()
        if not name:
            return False
            
        name_lower = name.lower()
        
        # 2. Block specific hardware/system patterns
        # User reported entries ending in " HAL" (Hardware Abstraction Layer)
        if name_lower.endswith(" hal"):
            return False
            
        if "hardware abstraction layer" in name_lower:
            return False
            
        # Windows Updates often appear as entries but shouldn't be touched by this tool
        # (Usually KBXXXXXXX)
        # if "update for windows" in name_lower or "security update for" in name_lower:
        #    return False
            
        return True

    def _extract_app_info(self, key):
        """
        Helper to extract common values from a registry key.
        """
        info = {}
        fields = [
            'DisplayName', 'DisplayVersion', 'Publisher', 
            'InstallLocation', 'UninstallString', 'QuietUninstallString',
            'SystemComponent', 'WindowsInstaller'
        ]
        
        for field in fields:
            try:
                value, _ = winreg.QueryValueEx(key, field)
                info[field] = value
            except FileNotFoundError:
                info[field] = None
                
        return info

    def delete_registry_key(self, root_str, registry_path, wow64_flag):
        """
        Deletes a registry key.
        WARNING: This is destructive. Backup should be handled before calling this.
        """
        hkey = winreg.HKEY_LOCAL_MACHINE if root_str == "HKLM" else winreg.HKEY_CURRENT_USER
        
        # KEY_ALL_ACCESS might be needed to delete, or at least KEY_WRITE
        # Note: winreg.DeleteKey doesn't take flags for WOW64 views directly in older python versions?
        # Actually winreg.DeleteKey(key, sub_key) deletes the sub_key. 
        # But we need to open the PARENT key first with the correct view.
        
        parent_path, key_name = registry_path.rsplit('\\', 1)
        
        try:
            # Open parent with write access and correct view
            access_mask = winreg.KEY_WRITE | wow64_flag
            with winreg.OpenKey(hkey, parent_path, 0, access_mask) as parent_key:
                winreg.DeleteKey(parent_key, key_name)
                self.logger.info(f"Successfully deleted key: {registry_path}")
                return True
        except WindowsError as e:
            self.logger.error(f"Failed to delete key {registry_path}: {e}")
            raise e
