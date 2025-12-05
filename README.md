# LastLook

> **"AYO SOMEBODY CHECK HIS HARD DRIVE."**

**LastLook** is a specialized, "Dark Mode" file transfer verification tool for Filmmakers and DITs. Unlike standard file managers, it prioritizes **visual verification** ("Call and Response") to ensure every bit of footage makes it from the SD Card to the SSD safely.

## 🚦 Status: Gold Master (v1.0)

The application is feature-complete, stable, and ready for production use.

### Core Capabilities

- ✅ **Visual Sync:** Traffic Light logic (Green=Synced, Red=Missing) with instant updates.
- ✅ **Secure Transfer:** Threaded, non-blocking copy engine using `shutil` (preserves metadata).
- ✅ **Eye Guard:** Amber-tinted "Night Shift" mode for low-light set environments.
- ✅ **Portable Engine:** Ships with embedded `ffmpeg.exe` for standalone video processing.

### Advanced Features

- ✅ **Smart Selection:** Batch checkboxes, "Select All Missing," and background deselect logic.
- ✅ **Bidirectional Mirroring:** Clicking a file in the Destination highlights the original in Source.
- ✅ **Live Video Thumbnails:** Asynchronous, threaded generation of frame grabs for video files.
- ✅ **Instant Caching:** RAM-based caching for zero-latency previewing.
- ✅ **Paranoia Engine:** MD5 Checksum verification ensures bit-for-bit data integrity.
- ✅ **Job Monitor:** Real-time transfer speed (MB/s) and ETA calculation.
- ✅ **Transfer Receipt:** Automatically generates a text-based Audit Log (`Transfer_Log_[Date].txt`) proving verification.

## 🧠 Roadmap & Feature Gaps

### Phase 1: Core Intelligence (The Brain) - [COMPLETED]

- [x] **Advanced Selection Engine:** `Set<ID>` logic implemented for batch tracking.
- [x] **Batch Inspector:** Calculates Total Size and Item Count dynamically.
- [x] **"Select All Missing":** Utility button implemented.

### Phase 2: Visual Confidence (The Eyes) - [COMPLETED]

- [x] **Video Thumbnails:** `ffmpeg` integration with background threading (`concurrent.futures`).
- [x] **Professional Assets:** Replaced Unicode characters with clean PNG icons.
- [x] **Bidirectional Sync:** Dest -> Source highlighting implemented.

### Phase 3: Professional Safety (The Shield) - [COMPLETED]

- [x] **MD5 Checksum:** Upgrade from File Size verification to bit-for-bit Content Hash verification.
- [x] **Capacity Guardrails:** Prevent transfer start if `Batch Size > Dest Free Space`.

### Phase 4: Polish (The Feel) - [COMPLETED]

- [x] **Job Monitor:** Real-time transfer speed (MB/s) and ETA readout in the footer.
- [x] **Stability Hardening:** Fixed Garbage Collection and Race Condition crashes.

### Phase 5: Final Delivery (v1.0) - [COMPLETED]

- [x] **Transfer Receipt:** Generate a TXT Manifest at the end of the session.
- [ ] **Sound Alerts:** Audio feedback (Moved to v1.1).

## 🛠️ Build Instructions (Dev)

### Prerequisites

- Python 3.10+
- `customtkinter`
- `Pillow`

### Running Locally

```bash
python main.py
```

### Building the Executable (Windows)

**CRITICAL:** You must include the `assets` folder (containing FFmpeg) and the `customtkinter` library path.

```bash
# 1. Get CTk Path
pip show customtkinter

# 2. Build (Replace <PATH_TO_CTK> with the result from above)
python -m PyInstaller --noconfirm --onedir --windowed --icon=NONE --name="LastLook" --add-data "<PATH_TO_CTK>;customtkinter/" --add-data "assets;assets/" main.py
```
