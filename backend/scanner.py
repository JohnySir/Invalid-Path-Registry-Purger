import os
import shlex

class AppScanner:
    def check_app_health(self, app_info):
        """
        Determines if an app is Valid, Ghost, or Unknown.
        Returns:
            status (str): 'Valid', 'Ghost', 'Unknown'
            reason (str): Details about the check.
        """
        install_loc = app_info.get('InstallLocation')
        uninstall_str = app_info.get('UninstallString')
        
        # Method 1: Check InstallLocation
        if install_loc:
            # Clean up quotes just in case
            clean_loc = install_loc.strip('"')
            if os.path.exists(clean_loc):
                return "Valid", f"Installation folder found: {clean_loc}"
            else:
                # If InstallLocation is explicit but missing, it's likely a ghost
                # But sometimes InstallLocation points to a specific file? Rare for the property name.
                pass 

        # Method 2: Check UninstallString
        if uninstall_str:
            exe_path = self._extract_path_from_command(uninstall_str)
            if exe_path:
                if os.path.exists(exe_path):
                    return "Valid", f"Uninstaller found: {exe_path}"
                else:
                    return "Ghost", f"Uninstaller missing: {exe_path}"
            else:
                # Could not parse path
                pass
        
        # If neither check passes
        if not install_loc and not uninstall_str:
            return "Unknown", "No path information available"
            
        # If we had paths but they failed verification
        return "Ghost", "Files referenced in registry are missing"

    def _extract_path_from_command(self, cmd_str):
        """
        Parses a command string to find the executable path.
        Handles quoted paths and arguments.
        """
        if not cmd_str:
            return None
            
        # specific MsiExec handling
        # e.g., MsiExec.exe /I{GUID}
        if "msiexec" in cmd_str.lower():
            return self._resolve_msi(cmd_str)

        try:
            # Use shlex to split by spaces respecting quotes
            # Windows paths with backslashes might confuse shlex if not careful, 
            # but usually it handles "C:\Path With Spaces\exe" fine.
            # However, shlex is POSIX compliant, might need care with Windows backslashes being escapes?
            # Actually, shlex(posix=False) works better for Windows? 
            # Or just simple quote parsing.
            
            # Simple approach: Check if it starts with quote
            clean_cmd = cmd_str.strip()
            if clean_cmd.startswith('"'):
                # Extract content between first and second quote
                end_quote = clean_cmd.find('"', 1)
                if end_quote != -1:
                    return clean_cmd[1:end_quote]
            
            # If no quotes, take the first token (space separated)
            # But assume the path might contain spaces and NOT be quoted? (Bad practice but happens)
            # If so, we iterate checking if file exists.
            
            parts = clean_cmd.split()
            if not parts:
                return None
            
            # Optimistic: First part is the command
            candidate = parts[0]
            if os.path.exists(candidate):
                return candidate
            
            # If first part doesn't exist, maybe it's "C:\Program Files\..." unquoted
            # Try joining parts until we find a match
            for i in range(1, len(parts)):
                candidate = " ".join(parts[:i+1])
                if os.path.exists(candidate):
                    return candidate
                # Also try with .exe appended?
                if os.path.exists(candidate + ".exe"):
                    return candidate + ".exe"
                    
            return parts[0] # Fallback
            
        except Exception:
            return None

    def _resolve_msi(self, cmd_str):
        # MsiExec uninstall strings don't point to a file, they point to a cached MSI or GUID.
        # Windows Installer caches MSIs in C:\Windows\Installer
        # Verifying this is harder without resolving the GUID.
        # For now, we assume MSI apps are VALID to avoid false positives, 
        # unless we can verify the source.
        # OR we can assume Unknown.
        return "C:\\Windows\\System32\\msiexec.exe" # This exists, so it will mark as Valid.
        # TODO: Better MSI detection logic.
