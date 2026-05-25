import ctypes
import queue
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from engine import AutoRakuEngine, DEFAULT_SETTINGS, load_settings_from_file, save_settings_to_file


LIGHT_THEME = {
	"bg": "#f4f1ea",
	"panel": "#fffdf8",
	"text": "#1f2328",
	"muted": "#69707a",
	"accent": "#1f7a71",
	"accent_active": "#16645d",
	"accent_text": "#ffffff",
	"button": "#ece6da",
	"button_active": "#dfd8ca",
	"entry": "#ffffff",
	"highlight": "#fff4d8",
	"log_bg": "#fffdf8",
}

DARK_THEME = {
	"bg": "#12161b",
	"panel": "#1a2027",
	"text": "#e6edf3",
	"muted": "#9ca7b3",
	"accent": "#2c8c7e",
	"accent_active": "#247267",
	"accent_text": "#f6f7f8",
	"button": "#26313b",
	"button_active": "#313d49",
	"entry": "#202730",
	"highlight": "#2a342d",
	"log_bg": "#161b22",
}


class ScrollableFrame(ttk.Frame):
	def __init__(self, parent):
		super().__init__(parent)
		self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
		self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
		self.content = ttk.Frame(self.canvas)

		self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.canvas.pack(side="left", fill="both", expand=True)
		self.scrollbar.pack(side="right", fill="y")

		self.content.bind("<Configure>", self._on_content_configure)
		self.canvas.bind("<Configure>", self._on_canvas_configure)
		self.content.bind("<Enter>", self._bind_mousewheel)
		self.content.bind("<Leave>", self._unbind_mousewheel)

	def _on_content_configure(self, event=None):
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def _on_canvas_configure(self, event):
		self.canvas.itemconfigure(self.window_id, width=event.width)

	def _bind_mousewheel(self, event=None):
		self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

	def _unbind_mousewheel(self, event=None):
		self.canvas.unbind_all("<MouseWheel>")

	def _on_mousewheel(self, event):
		self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class KeyCaptureField(ttk.Frame):
	def __init__(self, parent, app, label_text, key_name):
		super().__init__(parent, style="Card.TFrame")
		self.app = app
		self.key_name = key_name
		self.is_recording = False
		self.value_var = tk.StringVar(value=str(app.settings.get(key_name, DEFAULT_SETTINGS.get(key_name, ""))))

		self.columnconfigure(1, weight=1)

		self.label = ttk.Label(self, text=label_text, style="Card.TLabel")
		self.label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

		self.entry = ttk.Entry(self, textvariable=self.value_var, width=20, justify="center", style="KeyBind.TEntry")
		self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=4)
		self.entry.bind("<Button-1>", self.begin_recording)
		self.entry.bind("<Return>", self.begin_recording)

		self.record_button = ttk.Button(self, text="Record", style="Accent.TButton", command=self.begin_recording)
		self.record_button.grid(row=0, column=2, sticky="e", pady=4)

	def begin_recording(self, event=None):
		self.app.begin_key_capture(self)
		return "break"

	def set_recording(self, recording):
		self.is_recording = recording
		if recording:
			self.entry.configure(style="Recording.TEntry")
			self.record_button.configure(text="Press key...")
		else:
			self.entry.configure(style="KeyBind.TEntry")
			self.record_button.configure(text="Record")

	def set_value(self, value):
		self.value_var.set(value)

	def get_value(self):
		return self.value_var.get().strip()


class AutoRakuGUI:
	def __init__(self, root):
		self.root = root
		self.root.title("AutoRaku")
		self.root.geometry("1020x760")
		self.root.minsize(880, 640)
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)

		self.style = ttk.Style()
		if "clam" in self.style.theme_names():
			self.style.theme_use("clam")

		self.settings = load_settings_from_file()
		self.settings.setdefault("dark_mode", False)
		self.settings_vars = {}
		self.key_fields = {}
		self.log_queue = queue.Queue()
		self.status_var = tk.StringVar(value="Stopped")
		self.capture_status_var = tk.StringVar(value="Click a key field, then press the new key.")
		self.dark_mode_var = tk.BooleanVar(value=bool(self.settings.get("dark_mode", False)))
		self.capture_target = None

		self.engine = AutoRakuEngine(
			self.settings,
			log_callback=self.enqueue_log,
			state_callback=self.on_engine_state_change,
		)

		self.build_ui()
		self.apply_theme()
		self.sync_settings_to_vars()
		self.root.after(100, self.process_log_queue)
		self.enqueue_log("GUI ready.")

	def build_ui(self):
		self.outer = ttk.Frame(self.root, padding=14)
		self.outer.pack(fill="both", expand=True)

		head = ttk.Frame(self.outer, style="Card.TFrame")
		head.pack(fill="x", pady=(0, 12))

		title_row = ttk.Frame(head, style="Card.TFrame")
		title_row.pack(fill="x", padx=16, pady=(14, 2))
		self.title_label = ttk.Label(title_row, text="AutoRaku", style="Header.TLabel")
		self.title_label.pack(side="left")

		self.theme_toggle = ttk.Checkbutton(
			title_row,
			text="Dark mode",
			variable=self.dark_mode_var,
			command=self.on_theme_toggle,
		)
		self.theme_toggle.pack(side="right")

		subtitle_row = ttk.Frame(head, style="Card.TFrame")
		subtitle_row.pack(fill="x", padx=16, pady=(0, 14))
		self.subtitle_label = ttk.Label(
			subtitle_row,
			text="An automation program to play the RakuRaku jobs while you do something else.",
			style="Subtle.TLabel",
		)
		self.subtitle_label.pack(side="left")

		self.notebook = ttk.Notebook(self.outer)
		self.notebook.pack(fill="both", expand=True)

		self.control_tab = ttk.Frame(self.notebook, padding=14)
		self.settings_tab = ttk.Frame(self.notebook)

		self.notebook.add(self.control_tab, text="Control")
		self.notebook.add(self.settings_tab, text="Settings")

		self.build_control_tab()
		self.build_settings_tab()

	def build_control_tab(self):
		control_card = ttk.Frame(self.control_tab, style="Card.TFrame")
		control_card.pack(fill="x", pady=(0, 12))

		button_row = ttk.Frame(control_card, style="Card.TFrame")
		button_row.pack(fill="x", padx=16, pady=(14, 8))

		self.start_button = ttk.Button(button_row, text="Start Automation", style="Accent.TButton", command=self.start_automation)
		self.start_button.pack(side="left")

		self.stop_button = ttk.Button(button_row, text="Stop Automation", command=self.stop_automation, state="disabled")
		self.stop_button.pack(side="left", padx=(10, 0))

		self.save_button = ttk.Button(button_row, text="Save Settings", command=self.save_settings)
		self.save_button.pack(side="left", padx=(10, 0))

		self.clear_button = ttk.Button(button_row, text="Clear Log", command=self.clear_log)
		self.clear_button.pack(side="right")

		status_row = ttk.Frame(control_card, style="Card.TFrame")
		status_row.pack(fill="x", padx=16, pady=(0, 10))
		self.status_badge = ttk.Label(status_row, textvariable=self.status_var, style="CardHeader.TLabel")
		self.status_badge.pack(side="left")
		self.status_hint = ttk.Label(
			status_row,
			text=f"{self.settings.get('stop_hotkey', 'f8').upper()} will stop the automation from anywhere.",
			style="Subtle.TLabel",
		)
		self.status_hint.pack(side="right")
		self.update_stop_hotkey_hint()

		log_card = ttk.Frame(self.control_tab, style="Card.TFrame")
		log_card.pack(fill="both", expand=True)
		log_header = ttk.Label(log_card, text="Live Log", style="CardHeader.TLabel")
		log_header.pack(anchor="w", padx=16, pady=(14, 6))

		self.log_text = scrolledtext.ScrolledText(log_card, wrap="word", height=18, borderwidth=0, highlightthickness=0)
		self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
		self.log_text.configure(state="disabled")

	def build_settings_tab(self):
		scrollable = ScrollableFrame(self.settings_tab)
		scrollable.pack(fill="both", expand=True)
		content = scrollable.content

		top_card = ttk.Frame(content, style="Card.TFrame")
		top_card.pack(fill="x", pady=(0, 12))
		self.capture_status = ttk.Label(top_card, textvariable=self.capture_status_var, style="Card.TLabel")
		self.capture_status.pack(anchor="w", padx=16, pady=(14, 8))
		top_row = ttk.Frame(top_card, style="Card.TFrame")
		top_row.pack(fill="x", padx=16, pady=(0, 14))
		ttk.Button(top_row, text="Save Settings", style="Accent.TButton", command=self.save_settings).pack(side="left")
		ttk.Button(top_row, text="Reload from File", command=self.reload_settings).pack(side="left", padx=(10, 0))

		appearance_card = ttk.Frame(content, style="Card.TFrame")
		appearance_card.pack(fill="x", pady=(0, 12))
		appearance_header = ttk.Label(appearance_card, text="Appearance", style="CardHeader.TLabel")
		appearance_header.pack(anchor="w", padx=16, pady=(14, 8))
		appearance_row = ttk.Frame(appearance_card, style="Card.TFrame")
		appearance_row.pack(fill="x", padx=16, pady=(0, 14))
		appearance_text = ttk.Label(
			appearance_row,
			text="Switch between a lighter and darker treatment without restarting.",
			style="Card.TLabel",
		)
		appearance_text.pack(side="left")
		self.settings_dark_toggle = ttk.Checkbutton(
			appearance_row,
			text="Dark mode",
			variable=self.dark_mode_var,
			command=self.on_theme_toggle,
		)
		self.settings_dark_toggle.pack(side="right")

		timing_card = ttk.Frame(content, style="Card.TFrame")
		timing_card.pack(fill="x", pady=(0, 12))
		self.make_section_header(timing_card, "Timing")
		self.create_setting_row(timing_card, "Scan interval (seconds)", "scan_interval_seconds")

		keys_card = ttk.Frame(content, style="Card.TFrame")
		keys_card.pack(fill="x", pady=(0, 12))
		self.make_section_header(keys_card, "Key Bindings")

		for label, key_name in [
			("Stop hotkey", "stop_hotkey"),
			("Map key", "map_key"),
			("Auto-drive prepare key", "auto_drive_prepare_key"),
			("Auto-drive toggle key", "auto_drive_toggle_key"),
			("Exit menu key", "menu_exit_key"),
			("Menu right key", "menu_right_key"),
			("Confirm key", "confirm_key"),
			("Move left key", "move_left_key"),
			("Move down key", "move_down_key"),
			("Move up key", "move_up_key"),
			("Move forward key", "move_forward_key"),
			("Action key", "action_key"),
		]:
			field = KeyCaptureField(keys_card, self, label, key_name)
			field.pack(fill="x", padx=16, pady=4)
			self.key_fields[key_name] = field

	def make_section_header(self, parent, title):
		header = ttk.Label(parent, text=title, style="CardHeader.TLabel")
		header.pack(anchor="w", padx=16, pady=(14, 6))

	def create_setting_row(self, parent, label_text, key_name):
		row = ttk.Frame(parent, style="Card.TFrame")
		row.pack(fill="x", padx=16, pady=4)

		label = ttk.Label(row, text=label_text, style="Card.TLabel")
		label.pack(side="left")

		var = tk.StringVar(value=str(self.settings.get(key_name, DEFAULT_SETTINGS.get(key_name, ""))))
		self.settings_vars[key_name] = var

		entry = ttk.Entry(row, textvariable=var, width=24, style="KeyBind.TEntry")
		entry.pack(side="right")

	def sync_settings_to_vars(self):
		self.dark_mode_var.set(bool(self.settings.get("dark_mode", False)))
		for key, default_value in DEFAULT_SETTINGS.items():
			if key == "dark_mode":
				continue
			if key not in self.settings_vars:
				self.settings_vars[key] = tk.StringVar()
			self.settings_vars[key].set(str(self.settings.get(key, default_value)))
		for key_name, field in self.key_fields.items():
			field.set_value(str(self.settings.get(key_name, DEFAULT_SETTINGS.get(key_name, ""))))

	def update_stop_hotkey_hint(self):
		if hasattr(self, "status_hint"):
			self.status_hint.configure(text=f"{str(self.settings.get('stop_hotkey', 'f8')).upper()} will stop the automation from anywhere.")

	def on_theme_toggle(self):
		self.settings["dark_mode"] = bool(self.dark_mode_var.get())
		self.engine.settings = self.settings
		self.apply_theme()
		self.update_stop_hotkey_hint()
		self.enqueue_log("Theme updated.")

	def apply_theme(self):
		palette = DARK_THEME if self.dark_mode_var.get() else LIGHT_THEME
		self.palette = palette

		self.root.configure(bg=palette["bg"])
		self.outer.configure(style="Outer.TFrame")
		self.style.configure(".", background=palette["bg"], foreground=palette["text"], font=("Segoe UI", 10))
		self.style.configure("Outer.TFrame", background=palette["bg"])
		self.style.configure("TFrame", background=palette["bg"])
		self.style.configure("Card.TFrame", background=palette["panel"])
		self.style.configure("TLabel", background=palette["bg"], foreground=palette["text"])
		self.style.configure("Card.TLabel", background=palette["panel"], foreground=palette["text"])
		self.style.configure("Header.TLabel", background=palette["bg"], foreground=palette["text"], font=("Segoe UI", 22, "bold"))
		self.style.configure("Subtle.TLabel", background=palette["bg"], foreground=palette["muted"])
		self.style.configure("CardHeader.TLabel", background=palette["panel"], foreground=palette["text"], font=("Segoe UI", 11, "bold"))
		self.style.configure("TNotebook", background=palette["bg"], borderwidth=0)
		self.style.configure("TNotebook.Tab", background=palette["panel"], foreground=palette["text"], padding=(14, 8))
		self.style.map(
			"TNotebook.Tab",
			background=[("selected", palette["accent"]), ("active", palette["button_active"])],
			foreground=[("selected", palette["accent_text"]), ("active", palette["text"])],
		)
		self.style.configure("TButton", background=palette["button"], foreground=palette["text"], padding=(12, 7))
		self.style.map("TButton", background=[("active", palette["button_active"])])
		self.style.configure("Accent.TButton", background=palette["accent"], foreground=palette["accent_text"], padding=(12, 7))
		self.style.map("Accent.TButton", background=[("active", palette["accent_active"])])
		self.style.configure("TCheckbutton", background=palette["panel"], foreground=palette["text"])
		self.style.map("TCheckbutton", foreground=[("active", palette["text"])])
		self.style.configure("TLabelframe", background=palette["bg"], foreground=palette["text"])
		self.style.configure("TLabelframe.Label", background=palette["bg"], foreground=palette["text"])
		self.style.configure("KeyBind.TEntry", fieldbackground=palette["entry"], foreground=palette["text"], insertcolor=palette["text"])
		self.style.configure("Recording.TEntry", fieldbackground=palette["highlight"], foreground=palette["text"], insertcolor=palette["text"])

		self.log_text.configure(
			bg=palette["log_bg"],
			fg=palette["text"],
			insertbackground=palette["text"],
			highlightthickness=0,
			selectbackground=palette["accent"],
			selectforeground=palette["accent_text"],
		)
		self.log_text.configure(font=("Consolas", 10))
		self.root.update_idletasks()

	def begin_key_capture(self, field):
		if self.capture_target is not None and self.capture_target is not field:
			self.capture_target.set_recording(False)

		self.capture_target = field
		self.capture_status_var.set(f"Recording {field.key_name}. Press the new key now.")
		field.set_recording(True)
		self.root.bind("<KeyPress>", self.on_key_capture, add="+")
		self.root.focus_force()

	def finish_key_capture(self, key_name):
		if self.capture_target is None:
			return

		field = self.capture_target
		field.set_value(key_name)
		field.set_recording(False)
		self.settings[field.key_name] = key_name
		self.engine.settings = self.settings
		self.capture_target = None
		self.capture_status_var.set("Key captured. Save settings to keep the change.")
		self.root.unbind("<KeyPress>")
		self.enqueue_log(f"Captured {field.key_name}: {key_name}")

	def cancel_key_capture(self):
		if self.capture_target is not None:
			self.capture_target.set_recording(False)
			self.capture_target = None
			self.capture_status_var.set("Key capture canceled.")
		self.root.unbind("<KeyPress>")

	def on_key_capture(self, event):
		if self.capture_target is None:
			return

		key_name = self.normalize_event_to_key_name(event)
		if key_name is None:
			return "break"

		self.finish_key_capture(key_name)
		return "break"

	def normalize_event_to_key_name(self, event):
		keysym_map = {
			"Return": "enter",
			"Escape": "esc",
			"space": "space",
			"BackSpace": "backspace",
			"Tab": "tab",
			"Up": "up",
			"Down": "down",
			"Left": "left",
			"Right": "right",
			"Delete": "delete",
			"Home": "home",
			"End": "end",
			"Prior": "page_up",
			"Next": "page_down",
			"Shift_L": "shift",
			"Shift_R": "shift",
			"Control_L": "ctrl",
			"Control_R": "ctrl",
			"Alt_L": "alt",
			"Alt_R": "alt",
		}
		if event.keysym in keysym_map:
			return keysym_map[event.keysym]

		translated_char = self.translate_windows_key_event(event)
		if translated_char is None:
			translated_char = event.char
		if translated_char and len(translated_char) == 1 and translated_char.isprintable():
			return translated_char.lower()

		keysym = event.keysym.lower()
		if len(keysym) == 1:
			return keysym
		if keysym.startswith("f") and keysym[1:].isdigit():
			return keysym
		return None

	def translate_windows_key_event(self, event):
		if not sys.platform.startswith("win"):
			return None

		keycode = getattr(event, "keycode", None)
		if not keycode:
			return None

		try:
			user32 = ctypes.windll.user32
			layout = user32.GetKeyboardLayout(0)
			keyboard_state = (ctypes.c_ubyte * 256)()
			if not user32.GetKeyboardState(keyboard_state):
				return None
			scan_code = user32.MapVirtualKeyExW(int(keycode), 0, layout)
			if not scan_code:
				return None
			buffer = ctypes.create_unicode_buffer(8)
			result = user32.ToUnicodeEx(int(keycode), int(scan_code), keyboard_state, buffer, len(buffer), 0, layout)
			if result > 0:
				return buffer.value[:result]
		except Exception:
			return None

		return None

	def reload_settings(self):
		if self.engine.is_running:
			messagebox.showwarning("Automation running", "Stop the automation before reloading settings.")
			return

		self.settings = load_settings_from_file()
		self.settings.setdefault("dark_mode", False)
		self.settings.setdefault("stop_hotkey", DEFAULT_SETTINGS["stop_hotkey"])
		self.engine.settings = self.settings
		self.sync_settings_to_vars()
		self.apply_theme()
		self.update_stop_hotkey_hint()
		self.enqueue_log("Settings reloaded from file.")

	def collect_ui_settings(self, show_error=True):
		try:
			scan_interval = float(self.settings_vars["scan_interval_seconds"].get())
			if scan_interval <= 0:
				raise ValueError
		except (KeyError, ValueError):
			if show_error:
				messagebox.showerror("Invalid setting", "Scan interval must be a positive number.")
			return False

		self.settings["scan_interval_seconds"] = scan_interval
		self.settings["dark_mode"] = bool(self.dark_mode_var.get())

		for key_name, field in self.key_fields.items():
			field_value = field.get_value()
			self.settings[key_name] = field_value or DEFAULT_SETTINGS[key_name]

		self.engine.settings = self.settings
		return True

	def save_settings(self):
		if not self.collect_ui_settings(show_error=True):
			return

		try:
			save_settings_to_file(self.settings)
		except Exception as error:
			messagebox.showerror("Save failed", f"Could not save settings:\n{error}")
			return

		self.engine.settings = self.settings
		self.update_stop_hotkey_hint()
		self.apply_theme()
		self.enqueue_log("Settings saved.")
		messagebox.showinfo("Saved", "Settings saved successfully.")

	def enqueue_log(self, message):
		self.log_queue.put(message)

	def process_log_queue(self):
		updated = False
		while not self.log_queue.empty():
			message = self.log_queue.get_nowait()
			self.log_text.configure(state="normal")
			self.log_text.insert(tk.END, message + "\n")
			self.log_text.see(tk.END)
			self.log_text.configure(state="disabled")
			updated = True

		if updated:
			self.root.update_idletasks()
		self.root.after(100, self.process_log_queue)

	def clear_log(self):
		self.log_text.configure(state="normal")
		self.log_text.delete("1.0", tk.END)
		self.log_text.configure(state="disabled")

	def on_engine_state_change(self, is_running):
		self.root.after(0, lambda: self.update_running_state(is_running))

	def update_running_state(self, is_running):
		if is_running:
			self.status_var.set("Running")
			self.start_button.configure(state="disabled")
			self.stop_button.configure(state="normal")
		else:
			self.status_var.set("Stopped")
			self.start_button.configure(state="normal")
			self.stop_button.configure(state="disabled")

	def start_automation(self):
		if not self.collect_ui_settings(show_error=True):
			return
		try:
			save_settings_to_file(self.settings)
		except Exception as error:
			messagebox.showerror("Save failed", f"Could not save settings before starting:\n{error}")
			return
		self.engine.start()

	def stop_automation(self):
		self.engine.stop("Automation stopped.")

	def on_close(self):
		self.cancel_key_capture()
		self.collect_ui_settings(show_error=False)
		self.engine.shutdown()
		try:
			save_settings_to_file(self.settings)
		except Exception:
			pass
		self.root.destroy()


def main():
	root = tk.Tk()
	AutoRakuGUI(root)
	root.mainloop()


if __name__ == "__main__":
	main()
