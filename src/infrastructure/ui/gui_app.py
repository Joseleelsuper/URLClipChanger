"""Main GUI application for URL Clip Changer."""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from win32com.client import Dispatch
import win32con
import ctypes
from typing import List, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, src_path)

from infrastructure.logging.logger import logger  # noqa: E402
from infrastructure.config.config_loader import load_rules # noqa: E402
from core.models.rules import Rule # noqa: E402
from infrastructure.platform.windows.clipboard_watcher import ClipboardWatcher # noqa: E402

# For system tray functionality
pystray_available = False
try:
    from PIL import Image
    import pystray
    pystray_available = True
except ImportError:
    logger.warning("PIL and/or pystray not found. System tray icon will not be available.")


class URLClipChangerGUI:
    """Main GUI for URL Clip Changer application."""
    
    def __init__(self, master: tk.Tk):
        """Initialize the GUI.
        
        Args:
            master: Root Tkinter window
        """
        self.master = master
        self.master.title("URLClipChanger")
        self.master.minsize(600, 400)
        self.master.geometry("800x500")
        
        # Set icon if available
        try:
            base_path = None
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                try:
                    base_path = sys._MEIPASS  # type: ignore
                except AttributeError:
                    base_path = os.path.dirname(sys.executable)
            else:
                # Running as script
                base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            
            icon_path = os.path.join(base_path, "icon", "URLClipChanger.ico")
            if os.path.exists(icon_path):
                self.master.iconbitmap(icon_path)
                self.icon_path = icon_path
            else:
                self.icon_path = None
        except Exception as e:
            logger.debug(f"Could not load icon: {e}")
            self.icon_path = None
        
        # Initialize variables
        self.rules: List[Rule] = []
        self.clipboard_watcher: Optional[ClipboardWatcher] = None
        self.watcher_running = False
        self.tray_icon = None
        self.minimized_to_tray = False
        
        # Create UI components
        self._create_widgets()
        self._load_rules()
        
        # Start clipboard watcher when GUI starts
        self._start_clipboard_watcher()
        
        # Handle window close - minimize to tray instead of closing
        self.master.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
        
        # Create system tray icon
        self._setup_system_tray()
        
        # Create startup shortcut
        self._create_startup_shortcut()
    
    def _create_widgets(self):
        """Create the main UI components."""
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Rules label
        rules_label = ttk.Label(main_frame, text="Rules", font=("Helvetica", 16))
        rules_label.pack(anchor="w", pady=(0, 10))
        
        # Rules treeview (table)
        columns = ("domains", "suffix")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("domains", text="Domains")
        self.tree.heading("suffix", text="Suffix")
        self.tree.column("domains", width=350, anchor="w")
        self.tree.column("suffix", width=400, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Button frame
        button_frame = ttk.Frame(self.master, padding="10")
        button_frame.pack(fill=tk.X)
        
        # Buttons with equal width
        btn_width = 15
        
        # Add Rule button
        self.add_btn = ttk.Button(button_frame, text="Add Rule", width=btn_width, command=self._add_rule)
        self.add_btn.pack(side=tk.LEFT, padx=5)
        
        # Edit Rule button
        self.edit_btn = ttk.Button(button_frame, text="Edit Rule", width=btn_width, command=self._edit_rule)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        
        # Remove Rule button
        self.remove_btn = ttk.Button(button_frame, text="Remove Rule", width=btn_width, command=self._remove_rule)
        self.remove_btn.pack(side=tk.LEFT, padx=5)
        
        # Import button
        self.import_btn = ttk.Button(button_frame, text="Import Ruleset", width=btn_width, command=self._import_rules)
        self.import_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        self.export_btn = ttk.Button(button_frame, text="Export Ruleset", width=btn_width, command=self._export_rules)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _load_rules(self):
        """Load rules from config file and populate the treeview."""
        try:
            # Clear current treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Load rules
            self.rules = load_rules()
            
            # Populate treeview
            for i, (domains, suffix) in enumerate(self.rules):
                domains_str = ", ".join(domains)
                self.tree.insert("", tk.END, values=(domains_str, suffix), iid=str(i))
            
            self.status_var.set(f"Loaded {len(self.rules)} rules")
            logger.info(f"GUI: Loaded {len(self.rules)} rules from config file")
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            messagebox.showerror("Error", f"Failed to load rules: {e}")
            self.status_var.set("Error: Failed to load rules")
    
    def _setup_system_tray(self):
        """Set up system tray icon and menu."""
        # Skip if pystray is not available
        if not pystray_available:
            logger.warning("pystray module not found, system tray icon will not be available")
            return

        try:
            # Fix icon loading
            if self.icon_path and os.path.exists(self.icon_path):
                # Use win32 API to load the icon file which is more reliable for Windows
                try:
                    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                    self.hicon = ctypes.windll.user32.LoadImageW(
                        0, self.icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags
                    )
                    # If direct icon loading doesn't work, fallback to PIL
                    icon_image = Image.open(self.icon_path)  # type: ignore
                except Exception as e:
                    logger.warning(f"Failed to load icon using win32 API: {e}")
                    # Create a simple square icon as fallback
                    icon_image = Image.new('RGB', (64, 64), color='blue')  # type: ignore
            else:
                # Create a simple square icon if no icon file is available
                icon_image = Image.new('RGB', (64, 64), color='blue')  # type: ignore
            
            # Define menu items
            menu_items = (
                pystray.MenuItem("Show", self._restore_window),  # type: ignore
                pystray.MenuItem("Exit", self._quit_app)  # type: ignore
            )
            
            # Create tray icon
            self.tray_icon = pystray.Icon("URLClipChanger")  # type: ignore
            self.tray_icon.icon = icon_image
            self.tray_icon.title = "URL Clip Changer"
            self.tray_icon.menu = pystray.Menu(*menu_items)  # type: ignore
            
            # Start tray icon in a separate thread
            import threading
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            logger.info("System tray icon initialized")
        except Exception as e:
            logger.error(f"Failed to set up system tray icon: {e}")
    
    def _create_startup_shortcut(self):
        """Create a shortcut in the Windows startup folder to run the application at system startup."""
        try:
            if not getattr(sys, "frozen", False):
                # Only create shortcut when running as a frozen executable
                logger.info("Not creating startup shortcut - application is running in development mode")
                return
            
            # Get the path to the startup folder
            startup_folder = os.path.join(
                os.environ.get("APPDATA", ""), 
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )
            
            if not os.path.exists(startup_folder):
                logger.warning(f"Startup folder does not exist: {startup_folder}")
                return
            
            # Get the path to the executable
            executable_path = sys.executable
            
            # Create shortcut path
            shortcut_path = os.path.join(startup_folder, "URLClipChanger.lnk")
            
            # Check if the shortcut already exists
            if os.path.exists(shortcut_path):
                logger.info("Startup shortcut already exists")
                return
            
            # Create the shortcut
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = executable_path
            shortcut.WorkingDirectory = os.path.dirname(executable_path)
            shortcut.IconLocation = self.icon_path or executable_path
            shortcut.Description = "Start URL Clip Changer on system startup"
            shortcut.save()
            
            logger.info(f"Created startup shortcut: {shortcut_path}")
        except Exception as e:
            logger.error(f"Failed to create startup shortcut: {e}")
    
    def _minimize_to_tray(self):
        """Minimize the application to the system tray."""
        if self.tray_icon:
            self.master.withdraw()  # Hide window
            self.minimized_to_tray = True
            logger.debug("Minimized to system tray")
        else:
            # If tray icon is not available, just close the app
            self._on_close()
    
    def _restore_window(self, icon=None, item=None):
        """Restore the window from system tray."""
        self.master.deiconify()  # Restore window
        self.master.lift()  # Bring to front
        self.master.focus_force()  # Force focus
        self.minimized_to_tray = False
        logger.debug("Restored window from system tray")
    
    def _quit_app(self, icon=None, item=None):
        """Quit the application from system tray menu."""
        if self.tray_icon:
            self.tray_icon.stop()
        self._on_close()
    
    def _start_clipboard_watcher(self):
        """Start the clipboard watcher in the background."""
        if self.watcher_running:
            # Clean up any existing watcher before starting a new one
            if self.clipboard_watcher:
                try:
                    self.clipboard_watcher.cleanup()
                except Exception as e:
                    logger.debug(f"Error cleaning up clipboard watcher: {e}")
            self.watcher_running = False
            
        try:
            # Create a separate thread for clipboard watcher
            import threading
            
            def run_watcher():
                try:
                    # Create and start the clipboard watcher
                    self.clipboard_watcher = ClipboardWatcher(self.rules)
                    self.watcher_running = True
                    self.status_var.set("Clipboard watcher running")
                    logger.info("GUI: Clipboard watcher started")
                    self.clipboard_watcher.run()
                except Exception as e:
                    logger.error(f"Clipboard watcher failed: {e}")
                finally:
                    self.watcher_running = False
                    
            # Start the watcher thread
            self.watcher_thread = threading.Thread(target=run_watcher, daemon=True)
            self.watcher_thread.start()
        except Exception as e:
            logger.error(f"Failed to start clipboard watcher: {e}")
            self.status_var.set("Error: Clipboard watcher not running")
    
    def _add_rule(self):
        """Open dialog to add a new rule."""
        add_dialog = tk.Toplevel(self.master)
        add_dialog.title("Add Rule")
        add_dialog.geometry("500x200")
        add_dialog.resizable(False, False)
        add_dialog.transient(self.master)
        add_dialog.grab_set()
        
        # Center the dialog
        add_dialog.geometry("+%d+%d" % (
            self.master.winfo_rootx() + self.master.winfo_width() // 2 - 250,
            self.master.winfo_rooty() + self.master.winfo_height() // 2 - 100
        ))
        
        # Domains frame
        domains_frame = ttk.Frame(add_dialog, padding="10")
        domains_frame.pack(fill=tk.X)
        
        ttk.Label(domains_frame, text="Domains (comma separated):").pack(side=tk.LEFT)
        domains_var = tk.StringVar()
        domains_entry = ttk.Entry(domains_frame, textvariable=domains_var, width=40)
        domains_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Suffix frame
        suffix_frame = ttk.Frame(add_dialog, padding="10")
        suffix_frame.pack(fill=tk.X)
        
        ttk.Label(suffix_frame, text="Suffix:").pack(side=tk.LEFT)
        suffix_var = tk.StringVar()
        suffix_entry = ttk.Entry(suffix_frame, textvariable=suffix_var, width=40)
        suffix_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Buttons frame
        btn_frame = ttk.Frame(add_dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        def save_rule():
            domains_input = domains_var.get().strip()
            suffix_input = suffix_var.get().strip()
            
            if not domains_input or not suffix_input:
                messagebox.showerror("Error", "Both fields are required")
                return
            
            domains_list = [d.strip() for d in domains_input.split(",")]
            new_rule = (domains_list, suffix_input)
            
            try:
                # Add to internal list
                self.rules.append(new_rule)
                
                # Update treeview
                domains_str = ", ".join(domains_list)
                self.tree.insert("", tk.END, values=(domains_str, suffix_input), iid=str(len(self.rules) - 1))
                
                # Save to file
                self._save_rules()
                
                # Close dialog
                add_dialog.destroy()
                
                # Update status
                self.status_var.set(f"Added rule for {domains_input}")
            except Exception as e:
                logger.error(f"Failed to add rule: {e}")
                messagebox.showerror("Error", f"Failed to add rule: {e}")
        
        ttk.Button(btn_frame, text="Cancel", command=add_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Save", command=save_rule).pack(side=tk.RIGHT, padx=5)
        
        # Set focus
        domains_entry.focus_set()
    
    def _edit_rule(self):
        """Open dialog to edit an existing rule."""
        # Get selected rule
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a rule to edit")
            return
        
        # Get the selected rule's index and data
        idx = int(selected[0])
        rule = self.rules[idx]
        domains_str = ", ".join(rule[0])
        suffix = rule[1]
        
        # Create edit dialog
        edit_dialog = tk.Toplevel(self.master)
        edit_dialog.title("Edit Rule")
        edit_dialog.geometry("500x200")
        edit_dialog.resizable(False, False)
        edit_dialog.transient(self.master)
        edit_dialog.grab_set()
        
        # Center the dialog
        edit_dialog.geometry("+%d+%d" % (
            self.master.winfo_rootx() + self.master.winfo_width() // 2 - 250,
            self.master.winfo_rooty() + self.master.winfo_height() // 2 - 100
        ))
        
        # Domains frame
        domains_frame = ttk.Frame(edit_dialog, padding="10")
        domains_frame.pack(fill=tk.X)
        
        ttk.Label(domains_frame, text="Domains (comma separated):").pack(side=tk.LEFT)
        domains_var = tk.StringVar(value=domains_str)
        domains_entry = ttk.Entry(domains_frame, textvariable=domains_var, width=40)
        domains_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Suffix frame
        suffix_frame = ttk.Frame(edit_dialog, padding="10")
        suffix_frame.pack(fill=tk.X)
        
        ttk.Label(suffix_frame, text="Suffix:").pack(side=tk.LEFT)
        suffix_var = tk.StringVar(value=suffix)
        suffix_entry = ttk.Entry(suffix_frame, textvariable=suffix_var, width=40)
        suffix_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Buttons frame
        btn_frame = ttk.Frame(edit_dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        def save_edited_rule():
            domains_input = domains_var.get().strip()
            suffix_input = suffix_var.get().strip()
            
            if not domains_input or not suffix_input:
                messagebox.showerror("Error", "Both fields are required")
                return
            
            domains_list = [d.strip() for d in domains_input.split(",")]
            edited_rule = (domains_list, suffix_input)
            
            try:
                # Update internal list
                self.rules[idx] = edited_rule
                
                # Update treeview (remove all and re-add to keep indices aligned)
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                for i, (domains, suffix) in enumerate(self.rules):
                    domains_str = ", ".join(domains)
                    self.tree.insert("", tk.END, values=(domains_str, suffix), iid=str(i))
                
                # Save to file
                self._save_rules()
                
                # Close dialog
                edit_dialog.destroy()
                
                # Update status
                self.status_var.set(f"Updated rule for {domains_input}")
            except Exception as e:
                logger.error(f"Failed to update rule: {e}")
                messagebox.showerror("Error", f"Failed to update rule: {e}")
        
        ttk.Button(btn_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Save", command=save_edited_rule).pack(side=tk.RIGHT, padx=5)
        
        # Set focus
        domains_entry.focus_set()
    
    def _remove_rule(self):
        """Remove the selected rule."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a rule to remove")
            return
        
        try:
            # Get the selected rule's index
            idx = int(selected[0])
            
            # Remove from internal list
            removed_rule = self.rules.pop(idx)
            removed_domains = ", ".join(removed_rule[0])
            
            # Update treeview (remove all and re-add to keep indices aligned)
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            for i, (domains, suffix) in enumerate(self.rules):
                domains_str = ", ".join(domains)
                self.tree.insert("", tk.END, values=(domains_str, suffix), iid=str(i))
            
            # Save to file
            self._save_rules()
            
            # Update status
            self.status_var.set(f"Removed rule for {removed_domains}")
        except Exception as e:
            logger.error(f"Failed to remove rule: {e}")
            messagebox.showerror("Error", f"Failed to remove rule: {e}")
    
    def _import_rules(self):
        """Import rules from a JSON file."""
        filepath = filedialog.askopenfilename(
            title="Import Rules",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate format
            if not isinstance(data, list):
                raise ValueError("Invalid format: file must contain a list of rules")
            
            for rule in data:
                if not isinstance(rule, dict) or "domains" not in rule or "suffix" not in rule:
                    raise ValueError("Invalid rule format: each rule must have 'domains' and 'suffix' fields")
            
            # Convert data to rules
            imported_rules = [(r["domains"], r["suffix"]) for r in data]
            
            # Get the config directory path
            app_name = "URLClipChanger"
            
            if getattr(sys, "frozen", False):
                # When running as an executable, config dir is next to the exe
                base_dir = os.path.dirname(sys.executable)
                config_dir = os.path.join(base_dir, "configs")
            else:
                # When running as a script, use appdirs or project directory
                try:
                    import appdirs
                    config_dir = appdirs.user_config_dir(app_name)
                except ImportError:
                    # Fallback if appdirs is not available
                    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                            "..", "..", "..", "configs")
            
            # Ensure config directory exists
            os.makedirs(config_dir, exist_ok=True)
            
            # Default target file is rules.json
            target_file = os.path.join(config_dir, "rules.json")
            
            # Check if rules.json already exists
            if os.path.exists(target_file):
                # Create a dialog to ask the user what to do
                import_dialog = tk.Toplevel(self.master)
                import_dialog.title("Import Rules")
                import_dialog.geometry("450x200")
                import_dialog.resizable(False, False)
                import_dialog.transient(self.master)
                import_dialog.grab_set()
                
                # Center the dialog
                import_dialog.geometry("+%d+%d" % (
                    self.master.winfo_rootx() + self.master.winfo_width() // 2 - 225,
                    self.master.winfo_rooty() + self.master.winfo_height() // 2 - 100
                ))
                
                # Dialog content
                ttk.Label(
                    import_dialog, 
                    text=f"The file 'rules.json' already exists and will be overwritten.\n"
                         f"Importing will replace your current {len(self.rules)} rules with {len(imported_rules)} new rules.",
                    wraplength=400, justify="center"
                ).pack(pady=20)
                
                # User decision variable
                user_choice = {"action": "cancel"}
                
                def overwrite_action():
                    user_choice["action"] = "overwrite"
                    import_dialog.destroy()
                    
                def rename_action():
                    user_choice["action"] = "rename"
                    import_dialog.destroy()
                    
                def cancel_action():
                    user_choice["action"] = "cancel"
                    import_dialog.destroy()
                
                # Buttons frame
                btn_frame = ttk.Frame(import_dialog)
                btn_frame.pack(side="bottom", pady=20)
                
                ttk.Button(
                    btn_frame, 
                    text="Overwrite", 
                    command=overwrite_action
                ).pack(side="left", padx=10)
                
                ttk.Button(
                    btn_frame, 
                    text="Save As...", 
                    command=rename_action
                ).pack(side="left", padx=10)
                
                ttk.Button(
                    btn_frame, 
                    text="Cancel", 
                    command=cancel_action
                ).pack(side="left", padx=10)
                
                # Wait for dialog to close
                self.master.wait_window(import_dialog)
                
                # Process user choice
                if user_choice["action"] == "cancel":
                    return
                elif user_choice["action"] == "rename":
                    # Ask for new filename
                    new_filepath = filedialog.asksaveasfilename(
                        title="Save Rules As",
                        defaultextension=".json",
                        initialdir=config_dir,
                        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                    )
                    
                    if not new_filepath:
                        return  # User canceled
                    
                    target_file = new_filepath
            
            # Now proceed with the import
            self.rules = imported_rules
            
            # Update treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            for i, (domains, suffix) in enumerate(self.rules):
                domains_str = ", ".join(domains)
                self.tree.insert("", tk.END, values=(domains_str, suffix), iid=str(i))
            
            # Save the rules
            if target_file == os.path.join(config_dir, "rules.json"):
                # If saving to the default location, use the standard save method
                self._save_rules()
            else:
                # Otherwise save to the specified file
                rules_json = [{"domains": domains, "suffix": suffix} for domains, suffix in self.rules]
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(rules_json, f, indent=4)
                    
                # Also update the standard rules file to reflect current state
                self._save_rules()
            
            # Update status
            target_filename = os.path.basename(target_file)
            self.status_var.set(f"Imported {len(imported_rules)} rules to {target_filename}")
            logger.info(f"Imported {len(imported_rules)} rules from {filepath} to {target_file}")
        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            messagebox.showerror("Error", f"Failed to import rules: {e}")
    
    def _export_rules(self):
        """Export rules to a JSON file."""
        if not self.rules:
            messagebox.showinfo("Info", "No rules to export")
            return
            
        filepath = filedialog.asksaveasfilename(
            title="Export Rules",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Convert rules to JSON-compatible format
            rules_json = [{"domains": domains, "suffix": suffix} for domains, suffix in self.rules]
            
            # Save to file with nice formatting
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(rules_json, f, indent=4)
            
            # Update status
            self.status_var.set(f"Exported {len(self.rules)} rules to {os.path.basename(filepath)}")
            logger.info(f"Exported {len(self.rules)} rules to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
            messagebox.showerror("Error", f"Failed to export rules: {e}")
    
    def _save_rules(self):
        """Save rules to the config file."""
        try:
            # Define a reliable location for config files
            app_name = "URLClipChanger"
            
            if getattr(sys, "frozen", False):
                # When running as an executable, save next to the exe
                base_dir = os.path.dirname(sys.executable)
                config_dir = os.path.join(base_dir, "configs")
            else:
                # When running as a script, use appdirs or project directory
                try:
                    import appdirs
                    config_dir = appdirs.user_config_dir(app_name)
                except ImportError:
                    # Fallback if appdirs is not available
                    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                            "..", "..", "..", "configs")
            
            # Ensure config directory exists
            os.makedirs(config_dir, exist_ok=True)
            
            # Define the full path to the rules file
            config_file = os.path.join(config_dir, "rules.json")
            
            # Convert rules to JSON format
            rules_json = [{"domains": domains, "suffix": suffix} for domains, suffix in self.rules]
            
            # Save to file with nice formatting
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(rules_json, f, indent=4)
            
            logger.info(f"Saved {len(self.rules)} rules to {config_file}")
            
            # Restart clipboard watcher to apply new rules
            if self.clipboard_watcher:
                self.clipboard_watcher.cleanup()
            self.watcher_running = False
            self._start_clipboard_watcher()
            
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")
            messagebox.showerror("Error", f"Failed to save rules: {e}")
            raise
    
    def _on_close(self):
        """Handle window close event."""
        try:
            # Clean up the clipboard watcher
            if self.clipboard_watcher:
                self.clipboard_watcher.cleanup()
            
            # Stop the system tray icon if it exists
            if self.tray_icon:
                self.tray_icon.stop()
            
            logger.info("GUI closed")
            self.master.destroy()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.master.destroy()
            sys.exit(1)


def start_gui():
    """Start the GUI application."""
    root = tk.Tk()
    URLClipChangerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    start_gui()
