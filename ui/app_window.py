import customtkinter as ctk
from backend.registry_manager import RegistryManager
from backend.scanner import AppScanner
from backend.backup_manager import BackupManager
import threading
from tkinter import messagebox
import os
import sys
import subprocess

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppWindow(ctk.CTk):
# ... existing code ...
    def show_history_window(self):
        # ... existing code ...
        pass # (content of show_history_window is already there)

    def trigger_restart(self):
        """
        Restarts the application, attempting to elevate permissions.
        """
        self.destroy()
        
        python_exe = sys.executable
        # We assume main.py is in the parent directory of this file's package, 
        # OR we can reconstruct it from sys.argv if we were called from main.py
        # Safest is to use sys.argv[0] if it's the script path.
        script_path = os.path.abspath(sys.argv[0])
        
        # PowerShell command to run as admin
        # We use the same logic as in main.py
        args = f'"{script_path}"'
        ps_cmd = f"Start-Process '{python_exe}' -ArgumentList '{args}' -Verb RunAs"
        
        try:
            subprocess.Popen(["powershell", "-Command", ps_cmd])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart: {e}")

    def __init__(self, is_admin=False):
        super().__init__()

        self.is_admin = is_admin
        mode_str = "Administrator" if self.is_admin else "Limited Mode"
        self.title(f"Uninstall Cleaner - {mode_str}")
        self.geometry("1100x700")

        # Managers
        self.reg_mgr = RegistryManager()
        self.scanner = AppScanner()
        self.backup_mgr = BackupManager()
        self.all_apps = []
        self.search_delay = None
        self.current_limit = 50

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Push help to bottom

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Uninstall\nCleaner", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Mode Indicator
        color = "green" if self.is_admin else "orange"
        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text=f"Status: {mode_str}", text_color=color, font=ctk.CTkFont(size=12, weight="bold"))
        self.mode_label.grid(row=0, column=0, padx=20, pady=(0, 20))

        self.btn_scan = ctk.CTkButton(self.sidebar_frame, text="Rescan Apps", command=self.refresh_list)
        self.btn_scan.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_history = ctk.CTkButton(self.sidebar_frame, text="Undo History", command=self.show_history_window)
        self.btn_history.grid(row=2, column=0, padx=20, pady=10)

        # Ghosts Only Switch
        self.var_show_ghosts = ctk.BooleanVar(value=False)
        self.switch_ghosts = ctk.CTkSwitch(
            self.sidebar_frame, 
            text="Ghosts Only", 
            variable=self.var_show_ghosts, 
            command=self.reset_and_filter
        )
        self.switch_ghosts.grid(row=3, column=0, padx=20, pady=10)

        if not self.is_admin:
            self.btn_restart = ctk.CTkButton(
                self.sidebar_frame, 
                text="Restart as Admin", 
                fg_color="orange", 
                hover_color="darkorange",
                command=self.trigger_restart
            )
            self.btn_restart.grid(row=4, column=0, padx=20, pady=10)

        # Help Text Area in Sidebar
        self.help_label = ctk.CTkLabel(self.sidebar_frame, text="Details:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.help_label.grid(row=6, column=0, padx=20, pady=(10,0), sticky="w")
        
        self.help_textbox = ctk.CTkTextbox(self.sidebar_frame, width=180, height=200)
        self.help_textbox.grid(row=7, column=0, padx=10, pady=10)
        self.help_textbox.insert("0.0", "Select an app to see details here.")
        self.help_textbox.configure(state="disabled")

        # --- Main Area ---
        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_list_debounced)
        self.entry_search = ctk.CTkEntry(self, placeholder_text="Search apps...", textvariable=self.search_var)
        self.entry_search.grid(row=0, column=1, padx=(20, 20), pady=(20, 10), sticky="ew")

        # Scrollable List
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Installed Applications")
        self.scrollable_frame.grid(row=1, column=1, padx=(20, 20), pady=(10, 20), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1) # Name
        self.scrollable_frame.grid_columnconfigure(1, weight=0) # Status
        self.scrollable_frame.grid_columnconfigure(2, weight=0) # Action

        # Initial Load
        self.refresh_list()

    def refresh_list(self):
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.help_textbox.configure(state="normal")
        self.help_textbox.delete("0.0", "end")
        self.help_textbox.insert("0.0", "Scanning registry...")
        self.help_textbox.configure(state="disabled")
        self.update() # Force redraw to show scanning text

        # Threading scanning to prevent freeze
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        apps = self.reg_mgr.get_installed_apps()
        # Analyze ghosts
        for app in apps:
            status, reason = self.scanner.check_app_health(app)
            app['Status'] = status
            app['Reason'] = reason
        
        self.all_apps = apps
        # Update UI in main thread
        self.after(0, lambda: self.reset_and_filter())

    def filter_list_debounced(self, *args):
        # Triggered by typing: reset limit and debounce
        if self.search_delay:
            self.after_cancel(self.search_delay)
        self.search_delay = self.after(300, self.reset_and_filter)

    def reset_and_filter(self):
        # Triggered by Search or Toggle
        self.current_limit = 50
        self._perform_filter()
        # Fix scroll bug: Reset to top when filter changes
        self.scrollable_frame._parent_canvas.yview_moveto(0.0)

    def _perform_filter(self):
        query = self.search_var.get().lower()
        show_ghosts = self.var_show_ghosts.get()
        
        filtered = []
        for a in self.all_apps:
            # 1. Ghost Filter
            if show_ghosts and a.get('Status') != "Ghost":
                continue
            
            # 2. Search Filter
            if query in a.get('DisplayName', '').lower():
                filtered.append(a)
                
        self.render_list(filtered)

    def render_list(self, apps_to_show):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.help_textbox.configure(state="normal")
        self.help_textbox.delete("0.0", "end")
        self.help_textbox.insert("0.0", f"Found {len(apps_to_show)} apps.\nSelect one for details.")
        self.help_textbox.configure(state="disabled")

        # Pagination
        displayed_apps = apps_to_show[:self.current_limit]

        for i, app in enumerate(displayed_apps):
            # Use grid in scrollable frame
            name = app.get('DisplayName', 'Unknown')
            status = app.get('Status', 'Unknown')
            
            # Color coding
            status_color = "green" if status == "Valid" else "red" if status == "Ghost" else "orange"
            
            # Truncate long names
            display_name = (name[:40] + '...') if len(name) > 40 else name
            
            lbl_name = ctk.CTkLabel(self.scrollable_frame, text=display_name, anchor="w")
            lbl_name.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            # Bind click for details
            lbl_name.bind("<Button-1>", lambda event, a=app: self.show_details(a))

            lbl_status = ctk.CTkLabel(self.scrollable_frame, text=status, text_color=status_color, width=60)
            lbl_status.grid(row=i, column=1, padx=10, pady=5)
            lbl_status.bind("<Button-1>", lambda event, a=app: self.show_details(a))

            btn_action = ctk.CTkButton(
                self.scrollable_frame, 
                text="Remove" if status == "Ghost" else "Force Del",
                fg_color="darkred" if status == "Ghost" else "#D97706", # Red for Ghost, Orange for Force
                hover_color="#B91C1C" if status == "Ghost" else "#B45309",
                width=80,
                command=lambda a=app: self.confirm_remove(a)
            )
            btn_action.grid(row=i, column=2, padx=10, pady=5)
            
        # Load More Button
        if len(apps_to_show) > self.current_limit:
            remaining = len(apps_to_show) - self.current_limit
            btn_load_more = ctk.CTkButton(
                self.scrollable_frame,
                text=f"Load More ({remaining})",
                fg_color="transparent",
                border_width=1,
                text_color=("gray10", "gray90"),
                command=self.load_more
            )
            btn_load_more.grid(row=len(displayed_apps), column=0, columnspan=3, pady=20)

    def load_more(self):
        self.current_limit += 50
        self._perform_filter()

    def show_details(self, app):
        text = f"Name: {app.get('DisplayName')}\n"
        text += f"Status: {app.get('Status')}\n"
        text += f"Reason: {app.get('Reason')}\n\n"
        text += f"Registry Path: {app.get('registry_path')}\n\n"
        text += f"Install Location: {app.get('InstallLocation')}\n"
        text += f"Uninstall String: {app.get('UninstallString')}\n"
        
        self.help_textbox.configure(state="normal")
        self.help_textbox.delete("0.0", "end")
        self.help_textbox.insert("0.0", text)
        self.help_textbox.configure(state="disabled")

    def confirm_remove(self, app):
        msg = f"Are you sure you want to remove the registry entry for:\n\n{app.get('DisplayName')}\n\nA backup will be created before deletion."
        
        if app['Status'] == "Valid":
            # Advanced Warning for Valid Apps
            msg = (f"WARNING: Advanced Feature\n\n"
                   f"The app '{app.get('DisplayName')}' appears to be correctly installed.\n\n"
                   f"Force removing this entry will NOT delete the program files. "
                   f"It will only remove the record from Windows Settings.\n\n"
                   f"Are you strictly sure you want to proceed?")

        confirm = messagebox.askyesno("Confirm Deletion", msg)
        
        if confirm:
            try:
                # 1. Backup
                backup_file = self.backup_mgr.backup_registry_key(app['root_key'], app['registry_path'], app['DisplayName'])
                
                # 2. Delete
                self.reg_mgr.delete_registry_key(app['root_key'], app['registry_path'], app['wow64_flag'])
                
                messagebox.showinfo("Success", f"Entry removed.\nBackup saved to: {backup_file}")
                self.refresh_list()
                
            except Exception as e:
                messagebox.showerror("Error", f"Operation failed: {str(e)}\n\nTry running as Administrator.")

    def show_history_window(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("Restore Backup")
        history_window.geometry("600x400")
        
        # Ensure it pops up in front of the main UI
        history_window.lift()
        history_window.focus_force()
        history_window.after(10, history_window.lift) # Extra nudge for some Windows versions
        
        lbl_title = ctk.CTkLabel(history_window, text="Backup History", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_title.pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(history_window)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        backups = [f for f in os.listdir(self.backup_mgr.backup_dir) if f.endswith(".reg")]
        backups.sort(key=lambda x: os.path.getmtime(os.path.join(self.backup_mgr.backup_dir, x)), reverse=True)
        
        if not backups:
            ctk.CTkLabel(scroll_frame, text="No backups found.").pack(pady=20)
            return

        for f in backups:
            row = ctk.CTkFrame(scroll_frame)
            row.pack(fill="x", padx=5, pady=5)
            
            lbl_name = ctk.CTkLabel(row, text=f, anchor="w")
            lbl_name.pack(side="left", padx=10)
            
            btn_restore = ctk.CTkButton(
                row, 
                text="Restore", 
                width=80,
                command=lambda fname=f: self.perform_restore(fname, history_window)
            )
            btn_restore.pack(side="right", padx=10)

    def perform_restore(self, filename, window):
        confirm = messagebox.askyesno("Confirm Restore", f"Are you sure you want to restore:\n{filename}?")
        if confirm:
            try:
                filepath = os.path.join(self.backup_mgr.backup_dir, filename)
                self.backup_mgr.restore_backup(filepath)
                messagebox.showinfo("Success", "Registry key restored successfully.\nYou may need to restart the app or computer to see changes.")
                window.destroy()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Restore failed: {str(e)}")

    def trigger_restart(self):
        """
        Restarts the application, attempting to elevate permissions.
        """
        self.destroy()
        
        python_exe = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        
        # PowerShell command to run as admin
        args = f'"{script_path}"'
        ps_cmd = f"Start-Process '{python_exe}' -ArgumentList '{args}' -Verb RunAs"
        
        try:
            # Popen allows us to detach and exit this process
            subprocess.Popen(["powershell", "-Command", ps_cmd])
        except Exception as e:
            # Since window is destroyed, we can't show messagebox easily, 
            # but usually Popen works fine.
            print(f"Failed to restart: {e}")


if __name__ == "__main__":
    app = AppWindow()
    app.mainloop()
