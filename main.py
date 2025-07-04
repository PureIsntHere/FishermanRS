import os
import time
import configparser
import warnings
from collections import deque
from datetime import datetime, timedelta, timezone

import numpy as np
import pyautogui
import soundcard as sc
import pygetwindow as gw
import keyboard
import requests
from rich.console import Console
from rich.live import Live
from rich.text import Text
from soundcard.mediafoundation import SoundcardRuntimeWarning

#Fixes for Deprecations
warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)
if not hasattr(np, "_orig_fromstring"):
    np._orig_fromstring = np.fromstring
    def _safe_fromstring(data, dtype=float, count=-1, sep=""):
        return np.frombuffer(data, dtype=dtype, count=count)
    np.fromstring = _safe_fromstring

#Configuration
CONFIG_FILE = "settings.ini"
DEFAULTS = {
    'threshold':                '0.020',
    'listen_delay':             '0.8',
    'catch_delay':              '1.0',
    'block_duration':           '0.1',
    'cast_offset_x':            '0',
    'cast_offset_y':            '0',
    'reel_offset_x':            '0',
    'reel_offset_y':            '0',
    'stuck_window_seconds':     '30',
    'stuck_threshold':          '20',
    'fish_webhook_threshold':   '50',
    'discord_webhook_url':      '',
    'error_webhook_url':        '',
    'fish_webhook_url':         '',
}
#Create or update config file with missing keys
def ensure_config():
    cfg = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        cfg['Settings'] = DEFAULTS.copy()
    else:
        cfg.read(CONFIG_FILE)
        if 'Settings' not in cfg:
            cfg['Settings'] = {}
        updated = False
        for k, v in DEFAULTS.items():
            if k not in cfg['Settings']:
                cfg['Settings'][k] = v
                updated = True
        if not updated:
            return cfg
    #write with header
    with open(CONFIG_FILE, 'w') as f:
        f.write("# Rune Slayer Fish Bot Configuration\n")
        f.write("# Update thresholds and webhook URLs under [Settings]\n\n")
        cfg.write(f)
    return cfg

config = ensure_config()
s = config['Settings']

#Audio/Fishing params
SAMPLE_RATE    = 44100
BLOCK_DURATION = float(s.get('block_duration'))
THRESHOLD      = float(s.get('threshold'))
LISTEN_DELAY   = float(s.get('listen_delay'))
CATCH_DELAY    = float(s.get('catch_delay'))
CAST_OFFSET    = (int(s.get('cast_offset_x')), int(s.get('cast_offset_y')))
REEL_OFFSET    = (int(s.get('reel_offset_x')), int(s.get('reel_offset_y')))

#Stuck detection
STUCK_WINDOW    = timedelta(seconds=float(s.get('stuck_window_seconds')))
STUCK_THRESHOLD = int(s.get('stuck_threshold'))

#Fish-count webhook
FISH_ALERT_THRESHOLD = int(s.get('fish_webhook_threshold'))

#Webhook URLs
WEBHOOK_ERRORS = s.get('error_webhook_url').strip()
WEBHOOK_FISH   = s.get('fish_webhook_url').strip()
WINDOW_TITLE   = "Roblox"
GUAGE_LEN      = 10

#State vars
running    = False
amplitude  = 0.0
fish_count = 0
cast_times = deque()

#Helper functions

def send_webhook(url: str, content: str):
    if not url:
        return
    try:
        requests.post(url, json={"content": content}, timeout=5)
    except Exception:
        pass


def build_status_line(status: str):
    fill   = min(1.0, amplitude/THRESHOLD) if THRESHOLD>0 else 0
    blocks = int(fill * GUAGE_LEN)
    gauge  = "▉"*blocks + " "*(GUAGE_LEN-blocks)
    return Text(f"[{status}] Thr={THRESHOLD:.3f} Amp={amplitude:.3f} [{gauge}] Delay={CATCH_DELAY:.1f}s Fish={fish_count}")


def toggle_running():
    global running
    running = not running


def choose_loopback_device():
    devices = sc.all_microphones(include_loopback=True)
    print("\nAvailable loopback devices:")
    for i, d in enumerate(devices): print(f"  [{i}] {d.name}")
    while True:
        choice = input("Select device index for Roblox audio: ").strip()
        if choice.isdigit() and 0 <= int(choice) < len(devices):
            print(f"→ Using '{devices[int(choice)].name}'\n")
            return devices[int(choice)]
        print("Invalid—try again.")


def find_roblox_window():
    wins = gw.getWindowsWithTitle(WINDOW_TITLE)
    if not wins:
        raise RuntimeError(f"No window containing '{WINDOW_TITLE}' found.")
    win = wins[0]
    try: win.restore()
    except: pass
    win.activate(); time.sleep(0.2)
    return win

#Main Bot Loop

def main():
    global running, amplitude, fish_count, THRESHOLD, LISTEN_DELAY, CATCH_DELAY
    console = Console()
    mic     = choose_loopback_device()
    console.clear()
    console.print("[bold blue]FishermanRS - Made with <3 by Pure[/bold blue]")
    console.print("[yellow](Hotkeys: Enter=Start/Stop, F1/F2 Threshold, F3/F4 Listen, F5/F6 Catch)[/yellow]\n")

    #Hotkeys
    keyboard.add_hotkey('enter', toggle_running)
    def save_config():
        with open(CONFIG_FILE, 'w') as f:
            f.write("# Rune Slayer Fish Bot Configuration\n")
            f.write("# Update thresholds and webhook URLs under [Settings]\n\n")
            config.write(f)
    def adjust_threshold(delta):
        global THRESHOLD
        THRESHOLD = max(0.0, round(THRESHOLD + delta, 3))
        s['threshold'] = str(THRESHOLD)
        save_config()
        console.log(f"[green]Threshold[/green] set to {THRESHOLD:.3f}")
    def adjust_listen_delay(delta):
        global LISTEN_DELAY
        LISTEN_DELAY = max(0.0, round(LISTEN_DELAY + delta, 2))
        s['listen_delay'] = str(LISTEN_DELAY)
        save_config()
        console.log(f"[green]Listen Delay[/green] set to {LISTEN_DELAY:.2f}s")
    def adjust_catch_delay(delta):
        global CATCH_DELAY
        CATCH_DELAY = max(0.0, round(CATCH_DELAY + delta, 2))
        s['catch_delay'] = str(CATCH_DELAY)
        save_config()
        console.log(f"[green]Catch Delay[/green] set to {CATCH_DELAY:.2f}s")

    keyboard.add_hotkey('f1', lambda: adjust_threshold(-0.005))
    keyboard.add_hotkey('f2', lambda: adjust_threshold(0.005))
    keyboard.add_hotkey('f3', lambda: adjust_listen_delay(-0.1))
    keyboard.add_hotkey('f4', lambda: adjust_listen_delay(0.1))
    keyboard.add_hotkey('f5', lambda: adjust_catch_delay(-0.1))
    keyboard.add_hotkey('f6', lambda: adjust_catch_delay(0.1))

    #Initial window & coords
    win       = find_roblox_window()
    last_geom = (win.left, win.top, win.width, win.height)
    cast_x    = win.left + win.width//2 + CAST_OFFSET[0]
    cast_y    = win.top  + win.height//2 + CAST_OFFSET[1]
    reel_x    = win.left + win.width//2 + REEL_OFFSET[0]
    reel_y    = win.top  + win.height//2 + REEL_OFFSET[1]

    with Live(build_status_line("Idle"), console=console, refresh_per_second=10) as live:
        with mic.recorder(samplerate=SAMPLE_RATE) as recorder:
            try:
                while True:
                    if not running:
                        time.sleep(0.1)
                        live.update(build_status_line("Paused"))
                        continue

                    #Re-acquire window geometry if moved
                    win = find_roblox_window()
                    geom = (win.left, win.top, win.width, win.height)
                    if geom != last_geom:
                        last_geom = geom
                        cast_x    = win.left + win.width//2 + CAST_OFFSET[0]
                        cast_y    = win.top  + win.height//2 + CAST_OFFSET[1]
                        reel_x    = win.left + win.width//2 + REEL_OFFSET[0]
                        reel_y    = win.top  + win.height//2 + REEL_OFFSET[1]
                        console.log("[cyan]Window moved—updated click coords.[/cyan]")

                    #Stuck detection using timezone-aware timestamps
                    now = datetime.now(timezone.utc)
                    cast_times.append(now)
                    while cast_times and now - cast_times[0] > STUCK_WINDOW:
                        cast_times.popleft()
                    if len(cast_times) > STUCK_THRESHOLD:
                        send_webhook(WEBHOOK_ERRORS,
                                     f":warning: Bot appears stuck—{len(cast_times)} casts in " + \
                                     f"last {STUCK_WINDOW.total_seconds():.0f}s.")
                        cast_times.clear()

                    #Cast
                    live.update(build_status_line("Casting"))
                    pyautogui.click(cast_x, cast_y)
                    time.sleep(LISTEN_DELAY)

                    #Listen for bite
                    live.update(build_status_line("Listening"))
                    while running:
                        raw = recorder.record(int(BLOCK_DURATION*SAMPLE_RATE))
                        arr = np.frombuffer(raw, dtype=np.int16) if isinstance(raw,(bytes,bytearray)) else raw
                        norm = np.iinfo(arr.dtype).max if arr.dtype.kind in ('i','u') else 1.0
                        amplitude = np.sqrt((arr.astype(np.float64)**2).mean())/norm
                        live.update(build_status_line("Listening"))
                        if amplitude >= THRESHOLD:
                            break

                    #Reel
                    live.update(build_status_line("Reeling"))
                    pyautogui.click(reel_x, reel_y)
                    time.sleep(CATCH_DELAY)

                    #Count & webhook alert
                    fish_count += 1
                    if FISH_ALERT_THRESHOLD and fish_count % FISH_ALERT_THRESHOLD == 0:
                        send_webhook(WEBHOOK_FISH,
                                     f":fish: Caught {fish_count} fish so far!")

            except KeyboardInterrupt:
                console.log("Exiting on user interrupt.")
            except Exception as e:
                console.log(f"[red]Error:[/red] {e}")
                send_webhook(WEBHOOK_ERRORS, f":x: Bot error: {e}")
                raise

if __name__ == "__main__":
    main()
