import sys
import ctypes
import logging
import subprocess
import os
from ui.app_window import AppWindow

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """
    Attempts to restart the script with admin privileges using PowerShell.
    Returns True if the restart command was issued successfully.
    """
    # Get the python executable and the script path
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)
    
    # Construct the arguments
    # We need to wrap paths in quotes to handle spaces
    args = f'"{script_path}"'
    
    # PowerShell command: Start-Process "python" -ArgumentList "script.py" -Verb RunAs
    # We use -WindowStyle Normal to ensure it's visible
    ps_cmd = f"Start-Process '{python_exe}' -ArgumentList '{args}' -Verb RunAs"
    
    try:
        subprocess.run(["powershell", "-Command", ps_cmd], check=True)
        return True
    except Exception as e:
        print(f"Failed to launch admin process: {e}")
        return False

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    admin_status = is_admin()
    
    if not admin_status:
        # Ask the user if they want to try elevating
        MB_YESNO = 0x04
        MB_ICONQUESTION = 0x20
        title = "Administrator Privileges Required"
        message = (
            "This application works best with Administrator privileges to remove system-wide programs.\n\n"
            "Do you want to restart as Administrator?\n"
            "(Select 'No' to continue in Limited Mode)"
        )
        
        response = ctypes.windll.user32.MessageBoxW(None, message, title, MB_YESNO | MB_ICONQUESTION)
        
        if response == 6: # IDYES
            logger.info("User requested elevation.")
            if run_as_admin():
                sys.exit() # Exit this instance, assuming the new one started
            else:
                logger.error("Elevation failed. Continuing in limited mode.")
                ctypes.windll.user32.MessageBoxW(None, "Failed to restart as Admin. Opening in Limited Mode.", "Error", 0)

    logger.info(f"Starting AppWindow (Admin: {admin_status})...")
    app = AppWindow(is_admin=admin_status)
    app.mainloop()

if __name__ == "__main__":
    main()
