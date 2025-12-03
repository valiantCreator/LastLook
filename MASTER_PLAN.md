# LastLook: Master Project Documentation

**Version:** 0.6 (Beta)
**Tagline:** "AYO SOMEBODY CHECK HIS HARD DRIVE."
**Status:** Stable / Portable Build

---

## 1. Product Vision & Philosophy

**LastLook** is a specialized file transfer verification tool for Digital Imaging Technicians (DITs), filmmakers, and photographers. Unlike standard operating system file managers (Finder/Explorer), which are designed for general-purpose use, LastLook prioritizes **data integrity**, **visual verification**, and **low-light usability**.

### The Core Problem

Operating systems (Finder/Explorer) fail at "high-stakes" data transfer. They lack:

1.  **Visual Confirmation:** Did the file _actually_ arrive?
2.  **Comparison:** Is the destination file identical to the source?
3.  **Safety:** Preventing accidental formatting of cards before backup is confirmed.

### The Solution: "Call and Response"

A 3-pane interface where every action in the Source (Left) triggers a verification lookup in the Destination (Center), providing instant "Traffic Light" feedback.

---

## 2. Technical Specifications & Architecture

### 2.1 System Architecture (New in v0.6)

The application is structured into distinct layers to separate UI, Logic, and Assets:

- **`src/model/`**: Data definitions (`file_obj.py`, `types.py`).
- **`src/core/`**: The Heavy Lifting.
  - `scanner.py`: Handles `os.scandir` operations and the Source vs. Dest comparison loop.
  - `engine.py`: The `TransferEngine` that runs `shutil.copy2` on a background thread (`threading`).
  - `thumbnails.py`: Interface for the embedded `ffmpeg.exe` to generate frame grabs.
- **`src/ui/`**: The Presentation Layer (`app_window.py`, `panels.py`, `widgets.py`).
- **`src/utils/`**: Resource loader (`assets.py`) that locates icons and FFmpeg in both Dev and PyInstaller environments.

### 2.2 File Objects (The Data Structure)

Every file row in the UI maps to this Python Data Class:

- **`id`**: Absolute Path (String).
- **`filename`**: String (e.g., "A001_C001.mp4").
- **`size`**: Integer (Bytes).
- **`mtime`**: Float (Timestamp).
- **`status`**: Enum (Synced, Missing, Transferring).
- **`type`**: Enum (Image, Video, Audio, Other).

### 2.3 The Enums

- **SyncStatus**:
  - `MISSING` (Red): Exists in Source, NOT in Dest (or size mismatch).
  - `SYNCED` (Green): Exists in both, Metadata matches.
  - `TRANSFERRING` (Blue/Spinner): Active copy.
- **FileType**: Derived from extension for icon rendering logic.

---

## 3. Functional Requirements

### 3.1 The "Traffic Light" UI (Grid Layout)

- **Green Row (Synced):** Background `#1c3a1c`. Icon: ✅.
- **Red Row (Missing):** Background `#3a1c1c`. Icon: ❌.
- **Blue Tint (Selected):** User has clicked the row.

### 3.2 The Interaction Model

- **Source Click:** Highlights the row. Immediately searches `DestList`. If found -> Highlight Dest Row Green. If missing -> Flash Dest Row Red.
- **Dest Click (Bidirectional):** Highlights Dest row. Searches `SourceList`. Highlights Source Row Blue.
- **Focus Management:** Clicking background deselects. Clicking active row toggles focus off.
- **Batch Selection:**
  - **Checkboxes:** Additive selection for batch operations.
  - **Shift+Click:** Range Select (Future Scope).
  - **Ctrl+Click:** Toggle Select (Future Scope).
  - **"Select All Missing":** Utility button to select all `Status == MISSING`.

### 3.3 The Secure Transfer Engine

- **Threading:** MUST run on `threading.Thread` to prevent GUI freeze.
- **Logic:**
  1.  Filter `Selection` for files where `Status == MISSING`.
  2.  Check `DestDrive.FreeSpace > Batch.TotalSize`. If false -> **HALT** (Future Scope).
  3.  Iterate:
      - Update UI -> `TRANSFERRING`.
      - `shutil.copy2(src, dst)` (Preserves Metadata).
      - Post-Copy Check: `os.path.getsize(dst) == src.size`.
      - Update UI -> `SYNCED`.
- **Cancellation:** Must support a "Stop" flag to halt the loop safely.

### 3.4 The Inspector Pane

Dynamic content based on selection:

- **0 Items:** "Select a file..."
- **1 Item:** - **Video:** Uses embedded `ffmpeg` to extract a frame at 00:00:01 (Async Threaded).
  - **Logic:** Implements RAM Caching (`self.thumbnail_cache`) for instant reloading.
  - **Metadata:** Filename, Size (MB/GB), Full Path.
- **>1 Items:** "Batch Summary" (Total Size, Count of Missing vs Synced).

### 3.5 Night Shift (Eye Guard)

- **Implementation:** Toggle button.
- **Behavior:** Shifts UI colors to Amber (`#FFB347` Text, `#2e1c05` Backgrounds) to reduce blue light emission in dark environments.

---

## 4. Roadmap (Implementation Stages)

### Phase 1: The Skeleton (v0.1 - v0.2) - [COMPLETED]

- [x] Basic 3-Pane Layout.
- [x] File Scanning & Size Comparison.
- [x] Threaded Transfer.
- [x] Basic Red/Green UI.

### Phase 2: The Intelligence (v0.3 - v0.6) - [COMPLETED]

- [x] **Multi-Select:** Checkboxes and Batch Logic.
- [x] **Batch Inspector:** Calculating total size of selection.
- [x] **"Select All Missing" Button.**
- [x] **Bidirectional Sync:** Dest -> Source highlighting.
- [x] **Smart Inspector:** Toggle-off logic and background deselect.
- [x] **Asset Injection:** PNG Icons via `assets` folder.
- [x] **Video Thumbnails:** Embedded FFmpeg with Async Threading.
- [x] **Stability Hardening:** Fixed Garbage Collection and Race Condition crashes.

### Phase 3: The Polish (Next Priority)

- [ ] **MD5 Checksums:** Deep content verification.
- [ ] **Drive Capacity Bar:** Visual storage indicators.
- [ ] **Transfer Receipt:** Generate PDF Manifest.
- [ ] **Job Monitor:** Speed/ETA readout.
- [ ] **Advanced Inputs:** Implementation of Shift+Click (Range) and Ctrl+Click (Toggle) handlers.
