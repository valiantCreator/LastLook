# LastLook: Developer Handoff & Technical Bible

**Version:** 1.0 (Gold Master)
**Date:** December 4, 2025
**Architecture:** Python / CustomTkinter / Threaded / Async
**Maintainer:** [Your Name]

---

## 1. Executive Summary

**LastLook** is a specialized desktop application designed for Digital Imaging Technicians (DITs) and filmmakers. It addresses the critical risk of data loss during on-set offloading by providing a "Paranoia-First" file transfer environment.

Unlike standard OS file managers (Finder/Explorer), LastLook treats file transfer as a verified transaction. It uses a **"Call and Response"** interface to visually reconcile the Source media with the Destination backup, ensuring bit-for-bit accuracy via MD5 checksums.

### Core Value Proposition

1.  **Visual Verification:** Instant "Traffic Light" feedback (Green=Synced, Red=Missing, Amber=Verifying).
2.  **Data Integrity:** Mandatory MD5 content verification (not just file size).
3.  **Safety:** Capacity guardrails prevent transfers to full drives.
4.  **Audit Trail:** Generates a text-based Transfer Manifest for client delivery.

---

## 2. Tech Stack & Dependencies

### Core Frameworks

- **Language:** Python 3.10+ (Developed on 3.13.5)
- **GUI:** `customtkinter` (v5.2.2) - Wraps Tkinter for modern, High-DPI, Dark Mode UI.
- **Image Engine:** `Pillow` (PIL) - Handles icon rendering and video thumbnail processing.
- **Packaging:** `PyInstaller` - Compiles the Python environment into a standalone `.exe` or `.app`.

### Embedded Engines (Critical)

- **FFmpeg:** A standalone binary (`ffmpeg.exe`) is embedded in the `assets/` folder. It is invoked via `subprocess` to generate video thumbnails.
  - _Note:_ The binary is platform-specific. Current build includes Windows `ffmpeg.exe`.

### Standard Libraries (Key Usage)

- `threading`: Handles the long-running `TransferEngine` (IO Bound).
- `concurrent.futures`: Handles `ThreadPoolExecutor` for the `Scanner` and `ThumbnailGenerator`.
- `shutil`: Used for disk usage statistics and metadata cloning (`copystat`).
- `hashlib`: Used for streaming MD5 calculation.
- `tkinter`: The underlying event loop and widget system.

---

## 3. Project Architecture & File Tree

The project uses a strict separation of concerns: **Model** (Data), **Core** (Logic), **UI** (Presentation), and **Utils** (Helpers).

```text
LastLook/
├── main.py                  # Entry Point. Bootstraps AppWindow.
├── assets/                  # Runtime Resources (Bundled into EXE)
│   ├── check.png            # Green Check Icon
│   ├── error.png            # Red X Icon
│   ├── folder.png           # Source Button Icon
│   ├── disk.png             # Dest Button Icon
│   ├── hourglass.png        # Transferring Icon
│   ├── magnify.png          # Verifying Icon
│   ├── warning.png          # Error/Warning Icon
│   └── ffmpeg.exe           # Video Processing Engine (100MB)
├── src/
│   ├── model/
│   │   ├── types.py         # Enums: SyncStatus, FileType
│   │   └── file_obj.py      # Dataclass: Represents a physical file
│   ├── core/
│   │   ├── scanner.py       # Directory Traversal & Comparison Logic
│   │   ├── hashing.py       # Chunked MD5 Calculation
│   │   ├── thumbnails.py    # FFmpeg Subprocess Interface
│   │   └── engine.py        # The Transfer Logic (Manual Read/Write Loop)
│   ├── ui/
│   │   ├── app_window.py    # Main Controller (State Management)
│   │   ├── panels.py        # Heavy UI (Source/Dest Lists, Inspector)
│   │   └── widgets.py       # Atomic UI (FileRow Component)
│   └── utils/
│       └── assets.py        # Resource Path Resolver (Dev vs Prod)
└── DEVELOPER_HANDOFF.md     # You are here.
```

---

## 4. Component Deep Dive

### 4.1 `src/core/engine.py` (The Transfer Engine)

- **Role:** The "Heart" of the application.
- **Architecture:** Runs on a dedicated `threading.Thread` to prevent UI freezing during I/O.
- **Key Logic:**
  - **Manual Copy Loop:** We do _not_ use `shutil.copy2`. Instead, we open the file stream and read/write in **1MB chunks**.
  - **Why?** This allows us to calculate **Real-Time Speed (MB/s)** and **ETA** by measuring throughput per second.
  - **Verification:** After copying, it runs a "Paranoia Phase":
    1.  Check File Size.
    2.  Calculate Source MD5.
    3.  Calculate Destination MD5.
    4.  Compare. If mismatch -> Throw Error.
  - **Logging:** Maintains an internal list of transaction results and writes `Transfer_Log_YYYYMMDD.txt` upon completion.

### 4.2 `src/ui/panels.py` (The Rendering Engine)

- **Role:** Displays the lists of thousands of files.
- **Performance Optimization (The "Hybrid Renderer"):**
  - **Problem:** Tkinter freezes if you try to create 500 widgets in one frame.
  - **Solution:** We use a **Python Generator** to "Time-Slice" the rendering.
    - It processes 20 items.
    - Yields control to the UI loop (`self.after(5)`).
    - Resumes.
  - **Recycling:** We implemented **Widget Recycling**. `render_files` checks if `self.rows` already exist. If yes, it calls `row.update_data()` instead of destroying/recreating the widget. This makes folder switching nearly instant.
  - **Pre-Warmer:** On app launch, it silently builds 200 invisible rows in the background so the first folder load feels instant.

### 4.3 `src/core/thumbnails.py` & `InspectorPanel`

- **Role:** Generating previews for video files.
- **Architecture:**
  - `thumbnails.py` calls `ffmpeg.exe -ss 00:00:01 -vframes 1` to grab a JPEG.
  - `InspectorPanel` uses a `concurrent.futures.ThreadPoolExecutor(max_workers=1)` to run this command off the main thread.
- **Stability Logic:**
  - **Task Cancellation:** Uses `active_file_id` tracking. If the user clicks File A, then immediately File B, the callback for File A discards its result to prevent race conditions.
  - **Zombie Image Fix:** Tkinter crashes if you try to update a Label with an image that Python has garbage-collected. We use a `_rebuild_label()` method that destroys and recreates the label widget if a `TclError` is detected.

### 4.4 `src/utils/assets.py`

- **Role:** Finding files in a frozen exe.
- **Logic:**
  - If running as script: Returns `os.path.abspath("./assets")`.
  - If running as frozen (PyInstaller): Returns `sys._MEIPASS/assets`.
  - _Critical:_ Without this, the app crashes immediately upon launch in Production.

---

## 5. "War Stories" (Common Bugs & Fixes)

_These are the specific issues we encountered during development. Reference this if you plan to refactor._

1.  **The "White Screen of Death" (UI Freeze)**

    - _Symptom:_ Selecting a folder with >500 files froze the app for 3 seconds.
    - _Fix:_ Implemented the **Time-Sliced Generator** in `panels.py`. The loop yields every 20 items to let the UI redraw.

2.  **The "Zombie Image" Crash (`pyimageX doesn't exist`)**

    - _Symptom:_ Rapidly clicking different video files caused a hard crash to desktop.
    - _Cause:_ Python's Garbage Collector deleted the `PhotoImage` reference before Tkinter could paint it.
    - _Fix:_
      1.  **Anchoring:** Assigned images to `self.current_image` to keep a strong reference.
      2.  **Atomic Updates:** Explicitly set `image=None` before changing text.
      3.  **Try/Catch:** Wrapped updates in `try/except tkinter.TclError` and used `_rebuild_label()` to recover from corruption.

3.  **The "Stuck Highlight"**

    - _Symptom:_ Clicking a file highlighted it, but clicking it again didn't deselect it.
    - _Fix:_ Implemented "Toggle Logic" in `on_file_click`. If `clicked_id == active_id`, we call `deselect_all()`.

4.  **The "Ghost Image" Overlap**
    - _Symptom:_ When switching from a Video file to "Batch View" (insufficient space warning), the video thumbnail persisted behind the text.
    - _Cause:_ CTkLabel sometimes fails to clear the image buffer when switching to text-only mode.
    - _Fix:_ `show_batch` and `clear_view` now call `_rebuild_label()` to force a clean slate.

---

## 6. Build & Distribution

### Requirements

- **OS:** Windows 10/11 (due to included `ffmpeg.exe`).
- **Python:** 3.10 or higher.

### Development Setup

```bash
pip install customtkinter Pillow packaging
python main.py
```

### Production Build (The "Gold Master" Command)

**CRITICAL:** You must determine the location of `customtkinter` on your machine using `pip show customtkinter`.

```bash
# Example Path: C:\Users\Dev\AppData\Local\Programs\Python\Python310\Lib\site-packages

python -m PyInstaller --noconfirm --onedir --windowed --icon=NONE --name="LastLook" --add-data "<PATH_TO_CTK>;customtkinter/" --add-data "assets;assets/" main.py
```

- **`--onedir`**: Creates a folder (faster startup than `--onefile`).
- **`--windowed`**: Hides the console.
- **`--add-data`**: Crucial for bundling the UI library and the Assets folder (FFmpeg/Icons).

---

## 7. Roadmap & Future Scope

### v1.1 Updates (Quality of Life)

1.  **MacOS Support:**
    - Requires downloading the macOS binary of FFmpeg.
    - Update `assets.py` to detect `os.name` and select the correct binary.
    - Update PyInstaller command to use `:` separator instead of `;`.
2.  **Sound Alerts:** Implement `winsound` or `playsound` library to trigger an audio cue on `on_transfer_complete`.

### v2.0 Updates (Major Features)

1.  **PDF Receipts:** Integrate `reportlab` to generate branded PDF manifests instead of `.txt` files.
2.  **Multi-Threading (CPU):** Move MD5 hashing to `multiprocessing` to utilize all CPU cores. Currently, it is threaded (IO bound), but MD5 is CPU bound.
3.  **Pause/Resume:** Refactor `TransferEngine` to support pausing the stream, not just stopping it.
