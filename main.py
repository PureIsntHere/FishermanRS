import os
import time
import configparser
import warnings
from soundcard.mediafoundation import SoundcardRuntimeWarning
import numpy as np
import pyautogui
import soundcard as sc
import pygetwindow as gw
import keyboard          # pip install keyboard
from rich.console import Console
from rich.live import Live
from rich.text import Text

#Fixes soundcard warnings spamning the console
warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)

#Fixes numpy deprecation warning for fromstring
if not hasattr(np, "_orig_fromstring"):
    np._orig_fromstring = np.fromstring
    def _safe_fromstring(data, dtype=float, count=-1, sep=""):
        return np.frombuffer(data, dtype=dtype, count=count)
    np.fromstring = _safe_fromstring


#Configuration setup
CONFIG_FILE = "settings.ini"
DEFAULTS = {
    'threshold':      '0.020',   # sensitivity (0.0–1.0)
    'listen_delay':   '0.8',     # seconds after cast before listening
    'catch_delay':    '1.0',     # seconds after reel before next cast
    'block_duration': '0.1',     # seconds per audio read
    'cast_offset_x':  '0',       # click offset from window center X
    'cast_offset_y':  '0',       # click offset from window center Y
    'reel_offset_x':  '0',       # reel click offset X
    'reel_offset_y':  '0',       # reel click offset Y
}
if not os.path.exists(CONFIG_FILE):
    parser = configparser.ConfigParser()
    parser['Settings'] = DEFAULTS
    with open(CONFIG_FILE, 'w') as f:
        f.write("# Rune Slayer Fish Bot Configuration\n")
        f.write("# Adjust values below to fine-tune bot behavior\n\n")
        parser.write(f)
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
settings = config['Settings']

SAMPLE_RATE    = 44100
BLOCK_DURATION = float(settings.get('block_duration', DEFAULTS['block_duration']))
THRESHOLD      = float(settings.get('threshold', DEFAULTS['threshold']))
LISTEN_DELAY   = float(settings.get('listen_delay', DEFAULTS['listen_delay']))
CATCH_DELAY    = float(settings.get('catch_delay', DEFAULTS['catch_delay']))
CAST_OFFSET    = (
    int(settings.get('cast_offset_x', DEFAULTS['cast_offset_x'])),
    int(settings.get('cast_offset_y', DEFAULTS['cast_offset_y']))
)
REEL_OFFSET    = (
    int(settings.get('reel_offset_x', DEFAULTS['reel_offset_x'])),
    int(settings.get('reel_offset_y', DEFAULTS['reel_offset_y']))
)
WINDOW_TITLE = "Roblox"

running   = False
amplitude = 0.0

# Start/stop toggle
def toggle_running():
    global running
    running = not running

# Device selection and UI clear
def choose_loopback_device():
    devices = sc.all_microphones(include_loopback=True)
    print("\nAvailable loopback devices:")
    for i, d in enumerate(devices): print(f"  [{i}] {d.name}")
    while True:
        choice = input("Select device index for Roblox audio: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(devices):
                print(f"→ Using '{devices[idx].name}'\n")
                return devices[idx]
        print("Invalid—try again.")

# Focus Roblox window
def find_roblox_window():
    wins = gw.getWindowsWithTitle(WINDOW_TITLE)
    if not wins: raise RuntimeError(f"No window containing '{WINDOW_TITLE}' found.")
    win = wins[0]
    try: win.restore()
    except: pass
    win.activate(); time.sleep(0.2)
    return win

# Compute click coords
def get_click_coords(win, offset):
    return (win.left + win.width//2 + offset[0], win.top + win.height//2 + offset[1])

# Build a single-line status
GUAGE_LEN = 10

def build_status_line(status: str):
    # gauge blocks
    fill = min(1.0, amplitude/THRESHOLD) if THRESHOLD>0 else 0
    blocks = int(fill * GUAGE_LEN)
    gauge = "▉"*blocks + " "*(GUAGE_LEN-blocks)
    return Text(f"[{status}] Thr={THRESHOLD:.3f} Amp={amplitude:.3f} [{gauge}] Delay={CATCH_DELAY:.1f}s")

# Main loop
def main():
    global running, amplitude
    console = Console()
    mic = choose_loopback_device()
    console.clear()
    console.print("[bold blue]FishermanRS - Made with <3 by Pure[/bold blue]")
    console.print("[yellow](This Script is Free. If you paid for it, you were scammed.)[/yellow]\n")
    keyboard.add_hotkey('enter', toggle_running)
    console.print("Press [green]Enter[/green] to start/stop.\n")

    win = find_roblox_window()
    cast_x, cast_y = get_click_coords(win, CAST_OFFSET)
    reel_x, reel_y = get_click_coords(win, REEL_OFFSET)

    with Live(build_status_line("Idle"), console=console, refresh_per_second=10) as live:
        with mic.recorder(samplerate=SAMPLE_RATE) as recorder:
            while True:
                if not running:
                    time.sleep(0.1)
                    live.update(build_status_line("Paused"))
                    continue

                # Cast
                live.update(build_status_line("Casting"))
                pyautogui.click(cast_x, cast_y); time.sleep(LISTEN_DELAY)

                # Listen
                live.update(build_status_line("Listening"))
                while running:
                    raw = recorder.record(int(BLOCK_DURATION*SAMPLE_RATE))
                    arr = np.frombuffer(raw, dtype=np.int16) if isinstance(raw,(bytes,bytearray)) else raw
                    norm = np.iinfo(arr.dtype).max if arr.dtype.kind in('i','u') else 1.0
                    amplitude = np.sqrt(np.mean(arr.astype(np.float64)**2)) / norm
                    live.update(build_status_line("Listening"))
                    if amplitude>=THRESHOLD: break

                # Reel
                live.update(build_status_line("Reeling"))
                pyautogui.click(reel_x, reel_y); time.sleep(CATCH_DELAY)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nExiting.")
    except Exception as e: print(f"\nError: {e}")
