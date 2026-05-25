from pynput import keyboard
from pynput.keyboard import Key, Controller
import time
import pyautogui
import pytesseract
import cv2
import numpy
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

###
# variables
screen_scanning_timer = 2 # how many iterations need to happen until the program takes a screenshot of the monitor and scans it
bad_phrases = [
	"drift",
	"drift drive",
	"drift score",
	"drift points",
	"wreckage",
	"perform",
	"wrecking",
	"skill points",
	"perform near-miss",
	"near-miss"
]
press_detected_count = 0
resetting = False
stop_program = False
###

# checks if F8 is pressed to stop the program
def on_press(key):
    global stop_program

    if key == keyboard.Key.f8:
        print("F8 pressed → exiting")
        stop_program = True

# checks if auto drive is enabled, if not it enables it by pressing c and then é
def check_auto_drive(text: str):

	if("auto" not in text.lower() and "drive" not in text.lower() and "anna" in text.lower()):
		kb.press('c')
		kb.release('c')
		time.sleep(2)
		kb.press('é')
		kb.release('é')

# checks if the player is stuck by looking for the word "press" in the text, if it finds it 5 times in a row it resets the job
def check_stuck(text):
    global press_detected_count

    lower_text = text.lower()

    if "press" in lower_text and "express" not in lower_text:
        press_detected_count += 1
        print(f"PRESS detected ({press_detected_count}/5)")

        if press_detected_count >= 5:
            print("PRESS detected 5 times in a row, resetting job...")
            reset_job()
            press_detected_count = 0
    else:
        # reset counter if not continuous
        press_detected_count = 0


def check_new_shift(text: str):

	if("new" in text.lower() and "shift" in text.lower()
	or "take" in text.lower() and "another" in text.lower() and "delivery" in text.lower()
	or "enabling" in text.lower()
	or "continue" in text.lower()
	or "yes" in text.lower() and "no" in text.lower()
	or "select" in text.lower()):
		kb.press(Key.enter)
		kb.release(Key.enter)

def reset_job():
	global resetting
	time.sleep(15)

	# exists the job and opens the map
	kb.press(Key.esc)
	kb.release(Key.esc)
	time.sleep(2)
	kb.press(Key.right)
	kb.release(Key.right)
	time.sleep(2)
	kb.press(Key.enter)
	kb.release(Key.enter)
	time.sleep(1)
	kb.press(Key.enter)
	kb.release(Key.enter)

	# load time wait
	time.sleep(30)

	# teleports to the raku raku job location
	kb.press("m")
	kb.release("m")
	time.sleep(2)
	kb.press("a")
	kb.press("s")
	time.sleep(3)
	kb.release("a")
	time.sleep(3)
	kb.release("s")
	kb.press(Key.up)
	time.sleep(2)
	kb.release(Key.up)
	kb.press("w")
	time.sleep(5.41)
	kb.release("w")
	kb.press("x")
	kb.release("x")
	time.sleep(2)
	kb.press(Key.enter)
	kb.release(Key.enter)
	resetting = False

# checks if the text contains any keywords indicating that ANNA doesn't work here, if it does it resets the job
def check_bad_phrases(text):
	lower_text = text.lower()
	global resetting

	if any(phrase in lower_text for phrase in bad_phrases):
		resetting = True
		reset_job()

# takes a screenshot of the monitor and turns it into text, then sends it to other sub functions
def screen_scanning():

	time.sleep(1)

	screen_width, screen_height = pyautogui.size()

	screenshot = pyautogui.screenshot(
		region=(0, 0, int(screen_width * 0.4), screen_height)
	)

	img = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_RGB2BGR)

	# Grayscale
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# Upscale image (VERY important for game text)
	gray = cv2.resize(
		gray,
		None,
		fx=2,
		fy=2,
		interpolation=cv2.INTER_CUBIC
	)

	# Increase contrast
	gray = cv2.GaussianBlur(gray, (3, 3), 0)

	# Threshold
	_, thresh = cv2.threshold(
		gray,
		180,
		255,
		cv2.THRESH_BINARY
	)

	# OCR
	text = pytesseract.image_to_string(
		thresh,
		config='--psm 6'
	)

	print(text)

	check_new_shift(text)
	check_auto_drive(text)
	check_bad_phrases(text)
	check_stuck(text)

if __name__ == "__main__":

	kb = Controller()
	i: int = 0

	listener = keyboard.Listener(on_press=on_press)
	listener.start()

	while not stop_program:
		i = i + 1
		time.sleep(5)
	
		if(i == screen_scanning_timer - 1):
			
			if resetting:
				continue
			screen_scanning()
			
			i = 0