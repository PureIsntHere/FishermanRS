# FishermanRS

A minimal, audio-triggered fishing bot for RuneSlayer.

---

## Features

- **Audio-based detection**: Listens for a water-splash sound using RMS amplitude.
- **Single-line live UI**: Compact status bar with current state, threshold, amplitude gauge, and delay.
- **Configurable**: All parameters live in `settings.ini` (auto-generated if missing).
---

## Requirements

- Python 3.8+  
- Windows 10 or newer
---

## Installation

- Clone This Repo: https://github.com/PureIsntHere/FishermanRS.git
- Install Requirements with Pip. (pip install -r requirements.txt)
   
**Or just download a precompiled Release from the Releases Tab**
---

## Configuration

On first run, the bot will create `settings.ini` with commented default values:

```ini
# Rune Slayer Fish Bot Configuration
# Adjust values below to fine-tune bot behavior

[Settings]
threshold       = 0.020   # sensitivity (0.0–1.0)
listen_delay    = 0.8     # seconds after cast before listening
catch_delay     = 1.0     # seconds after reel before next cast
block_duration  = 0.1     # seconds per audio read
cast_offset_x   = 0       # click offset from window center X
cast_offset_y   = 0       # click offset from window center Y
reel_offset_x   = 0       # reel click offset X
reel_offset_y   = 0       # reel click offset Y
```

Feel free to tweak any setting, then save and rerun the bot.

---

## Usage

1. **Run the bot**:
   ```powershell
   python main.py
   ```
2. **Select your audio device** from the numbered list (the one Roblox uses).
3. The console will clear, then display:
   ```
   FishermanRS – Made with ❤️ by Pure
   (This Script is Free. If you paid for it, you were scammed.)

   Press [Enter] to start/stop.
   ```
4. **Press Enter** to begin fishing.  
5. The **live status bar** will update in place:
   ```
   [Listening ▉▉▏ 0.075/0.020] Delay=1.0s
   ```

6. Disable Ambient Noise and Music in the in game settings

7. Find a quiet spot with water somewhere

8. Zoom your camera all the way in while facing the water

9. Press **Enter** to start the bot
---

## Troubleshooting

- **No audio detected**: make sure your loopback device is not muted and Roblox’s sound is playing.
- **Missed splashes**: try lowering `threshold` in `settings.ini`, or increase `block_duration`.

---

## License

This script is provided **Free of Charge**.  
Do **not** sell or redistribute—if someone charged you for it, you were scammed.  

**FishermanRS – Made with ❤️ by Pure**  

