import json
import os
import threading
import time
from datetime import datetime

import cv2
import numpy
import pyautogui
import pytesseract
from pynput import keyboard as pynput_keyboard
from pynput.keyboard import Controller, Key, KeyCode


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "autoraku_settings.json")
BAD_PHRASES = [
	"drift",
	"drift drive",
	"drift score",
	"drift points",
	"wreckage",
	"perform",
	"wrecking",
	"skill points",
	"perform near-miss",
	"near-miss",
]

DEFAULT_SETTINGS = {
	"scan_interval_seconds": 5.0,
	"dark_mode": False,
	"stop_hotkey": "f8",
	"map_key": "m",
	"ask_anna_key": "c",
	"auto_drive_toggle_key": "2",
	"menu_exit_key": "esc",
	"menu_right_key": "right",
	"confirm_key": "enter",
	"move_left_key": "a",
	"move_down_key": "s",
	"move_up_key": "up",
	"move_forward_key": "w",
	"map_action_key": "x",
}


class AutoRakuEngine:
	def __init__(self, settings, log_callback=None, state_callback=None):
		self.settings = settings
		self.log_callback = log_callback
		self.state_callback = state_callback
		self.stop_event = threading.Event()
		self.is_running = False
		self.automation_thread = None
		self.listener = None
		self.controller = Controller()
		self.press_detected_count = 0
		self.resetting = False

		tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
		if os.path.exists(tesseract_path):
			pytesseract.pytesseract.tesseract_cmd = tesseract_path

	def set_callbacks(self, log_callback=None, state_callback=None):
		self.log_callback = log_callback
		self.state_callback = state_callback

	def add_log(self, message):
		timestamp = datetime.now().strftime("%H:%M:%S")
		formatted_message = f"[{timestamp}] {message}"
		if self.log_callback is not None:
			self.log_callback(formatted_message)
		else:
			print(formatted_message)

	def notify_state(self):
		if self.state_callback is not None:
			self.state_callback(self.is_running)

	def start(self):
		if self.is_running:
			return

		self.stop_event.clear()
		self.is_running = True
		self.press_detected_count = 0
		self.resetting = False
		self.notify_state()
		self.add_log("Automation started.")

		self.automation_thread = threading.Thread(target=self.automation_loop, daemon=True)
		self.automation_thread.start()

		self.listener = pynput_keyboard.Listener(on_press=self.on_global_key_press)
		self.listener.start()

	def stop(self, reason="Automation stopped."):
		if not self.is_running and not self.stop_event.is_set():
			return

		self.stop_event.set()
		self.is_running = False
		self.notify_state()
		self.add_log(reason)

		listener = self.listener
		if listener is not None:
			try:
				listener.stop()
			except Exception:
				pass
			self.listener = None

		thread = self.automation_thread
		if thread is not None and thread.is_alive() and threading.current_thread() is not thread:
			thread.join(timeout=1)

	def shutdown(self):
		self.stop("Automation stopped.")

	def on_global_key_press(self, key):
		try:
			stop_hotkey = self.resolve_key(str(self.settings.get("stop_hotkey", "f8")))
		except ValueError:
			stop_hotkey = pynput_keyboard.Key.f8

		if key == stop_hotkey:
			self.stop(f"Automation stopped with {str(self.settings.get('stop_hotkey', 'f8')).upper()}.")
			return False

	def automation_loop(self):
		try:
			while not self.stop_event.is_set():
				self.screen_scanning()
				self.sleep_interruptible(float(self.settings.get("scan_interval_seconds", 5.0)))
		except Exception as error:
			self.add_log(f"Automation error: {error}")
			self.stop_event.set()
			self.is_running = False
			self.notify_state()
		finally:
			self.resetting = False

	def sleep_interruptible(self, duration):
		elapsed = 0.0
		while elapsed < duration and not self.stop_event.is_set():
			sleep_amount = min(0.1, duration - elapsed)
			time.sleep(sleep_amount)
			elapsed += sleep_amount

	def resolve_key(self, key_name):
		key_name = key_name.strip().lower()
		if not key_name:
			raise ValueError("Empty key name")

		special_keys = {
			"enter": Key.enter,
			"esc": Key.esc,
			"escape": Key.esc,
			"space": Key.space,
			"tab": Key.tab,
			"backspace": Key.backspace,
			"delete": Key.delete,
			"up": Key.up,
			"down": Key.down,
			"left": Key.left,
			"right": Key.right,
			"shift": Key.shift,
			"ctrl": Key.ctrl,
			"alt": Key.alt,
			"cmd": Key.cmd,
			"home": Key.home,
			"end": Key.end,
			"page_up": Key.page_up,
			"page_down": Key.page_down,
		}
		if key_name in special_keys:
			return special_keys[key_name]
		if key_name.startswith("f") and key_name[1:].isdigit():
			function_key = getattr(Key, key_name, None)
			if function_key is not None:
				return function_key
		if len(key_name) == 1:
			return KeyCode.from_char(key_name)
		if hasattr(Key, key_name):
			return getattr(Key, key_name)
		raise ValueError(f"Unsupported key: {key_name}")

	def press_key(self, key_name, hold_seconds=0.05):
		key_object = self.resolve_key(key_name)
		self.controller.press(key_object)
		time.sleep(hold_seconds)
		self.controller.release(key_object)

	def check_new_shift(self, text):
		lower_text = text.lower()
		if (
			("new" in lower_text and "shift" in lower_text)
			or ("take" in lower_text and "another" in lower_text and "delivery" in lower_text)
			or "enabling" in lower_text
			or "continue" in lower_text
			or ("yes" in lower_text and "no" in lower_text)
			or "select" in lower_text
		):
			self.add_log("Confirm prompt detected. Pressing confirm.")
			self.press_key(self.settings["confirm_key"])

	def check_auto_drive(self, text):
		lower_text = text.lower()
		if "auto" not in lower_text and "drive" not in lower_text and "anna" in lower_text:
			self.add_log("Auto-drive not detected. Triggering auto-drive keys.")
			self.press_key(self.settings["ask_anna_key"])
			self.sleep_interruptible(2)
			self.press_key(self.settings["auto_drive_toggle_key"])

	def check_stuck(self, text):
		lower_text = text.lower()
		if "press" in lower_text and "express" not in lower_text:
			self.press_detected_count += 1
			self.add_log(f"Stuck prompt detected ({self.press_detected_count}/5).")
			if self.press_detected_count >= 5:
				self.add_log("Stuck prompt repeated 5 times. Resetting job.")
				self.press_detected_count = 0
				self.reset_job()
		else:
			self.press_detected_count = 0

	def check_bad_phrases(self, text):
		lower_text = text.lower()
		matched_phrase = next((phrase for phrase in BAD_PHRASES if phrase in lower_text), None)
		if matched_phrase:
			self.add_log(f"Bad phrase detected: {matched_phrase}. Resetting job.")
			self.reset_job()

	def reset_job(self):
		if self.resetting or self.stop_event.is_set():
			return

		self.resetting = True
		self.add_log("Reset sequence started.")

		try:
			for delay in (15, 2, 2, 1, 30):
				self.sleep_interruptible(delay)
				if self.stop_event.is_set():
					return

			self.press_key(self.settings["menu_exit_key"])
			self.sleep_interruptible(2)
			self.press_key(self.settings["menu_right_key"])
			self.sleep_interruptible(2)
			self.press_key(self.settings["confirm_key"])
			self.sleep_interruptible(1)
			self.press_key(self.settings["confirm_key"])
			self.sleep_interruptible(30)

			self.press_key(self.settings["map_key"])
			self.sleep_interruptible(2)
			self.press_key(self.settings["move_left_key"])
			self.press_key(self.settings["move_down_key"])
			self.sleep_interruptible(3)
			self.press_key(self.settings["move_up_key"])
			self.sleep_interruptible(2)
			self.press_key(self.settings["move_forward_key"])
			self.sleep_interruptible(5.41)
			self.press_key(self.settings["map_action_key"])
			self.sleep_interruptible(2)
			self.press_key(self.settings["confirm_key"])
			self.add_log("Reset sequence finished.")
		finally:
			self.resetting = False

	def screen_scanning(self):
		if self.stop_event.is_set() or self.resetting:
			return

		screen_width, screen_height = pyautogui.size()
		screenshot = pyautogui.screenshot(region=(0, 0, int(screen_width * 0.4), screen_height))
		image = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_RGB2BGR)
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
		gray = cv2.GaussianBlur(gray, (3, 3), 0)
		_, threshold = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
		text = pytesseract.image_to_string(threshold, config="--psm 6")

		if text.strip():
			self.check_new_shift(text)
			self.check_auto_drive(text)
			self.check_bad_phrases(text)
			self.check_stuck(text)


def load_settings_from_file():
	settings = dict(DEFAULT_SETTINGS)
	if not os.path.exists(SETTINGS_FILE):
		return settings

	try:
		with open(SETTINGS_FILE, "r", encoding="utf-8") as settings_file:
			loaded_settings = json.load(settings_file)
		if isinstance(loaded_settings, dict):
			for key, value in loaded_settings.items():
				if key in settings:
					settings[key] = value
	except Exception:
			pass
	return settings


def save_settings_to_file(settings):
	with open(SETTINGS_FILE, "w", encoding="utf-8") as settings_file:
		json.dump(settings, settings_file, indent=2, ensure_ascii=False)
