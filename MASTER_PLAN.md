# LastLook: Master Project Documentation

**Version:** 1.0 (Gold Master)
**Tagline:** "AYO SOMEBODY CHECK HIS HARD DRIVE."
**Status:** Production Ready

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

### 2.1 System Architecture

The application is structured into distinct layers to separate UI, Logic, and Assets:

- **`src/model/`**: Data definitions (`file_obj.py`, `types.py`).
- **`src/core/`**: The Heavy Lifting.
  - `scanner.py`: Handles `os.scandir` operations and the Source vs. Dest comparison loop.
  - `engine.py`: The `TransferEngine` that uses a manual read/write loop to enable real-time Speed/ETA monitoring, MD5 Verification, and Manifest generation.
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
  - `VERIFYING` (Amber/Magnify): Active MD5 Hash Calculation.
  - `ERROR` (Red/Warning): Checksum mismatch or I/O failure.
- **FileType**: Derived from extension for icon rendering logic.

---

## 3. Functional Requirements

### 3.1 The "Traffic Light" UI

- **Green Row (Synced):** Background `#1c3a1c` with Green Check Icon.
- **Red Row (Missing):** Background `#3a1c1c` with Red X Icon.
- **Selection:** Checkbox + Blue Row Highlight.

### 3.2 The Interaction Model

- **Mirror Logic:** Clicking Source highlights Dest. Clicking Dest highlights Source.
- **Focus Management:** Clicking background deselects. Clicking active row toggles focus off.
- **Batch Selection:** Checkboxes allow additive selection. "Select All Missing" utility button grabs all Red rows.

### 3.3 The Secure Transfer Engine

- **Threading:** MUST run on `threading.Thread` to prevent GUI freeze.
- **Logic:**
  1.  **Capacity Check:** If `Selection Size > Dest Free Space`, lock Transfer button and alert user.
  2.  **Iterate:**
      - Update UI -> `TRANSFERRING` (Spinner).
      - **Manual Copy:** Read/Write file in 1MB chunks to calculate Throughput (MB/s) and ETA.
      - **Metadata:** Explicitly restore file timestamps via `shutil.copystat`.
      - **Verification:** Calculate MD5 Hash of Source vs. Destination.
      - **Logging:** Append details to internal transaction log.
      - Update UI -> `SYNCED` (if Hash matches) or `ERROR` (if mismatch).
- **Finalization:** Write `Transfer_Log.txt` to destination folder upon completion.

### 3.4 The Inspector Pane

- **Smart Preview:** Uses embedded `ffmpeg` (Async Threaded) to show video frames.
- **Capacity Alert:** If `Selection > Free Space`, displays Red Warning text showing exactly how much space needs to be freed.

---

## 4. Roadmap (Implementation Stages)

### Phase 1: The Skeleton (v0.1 - v0.2) - [COMPLETED]

- [x] Basic 3-Pane Layout & File Scanning.
- [x] Threaded Transfer Engine.
- [x] Batch Selection (Checkboxes).

### Phase 2: The Intelligence (v0.3 - v0.6) - [COMPLETED]

- [x] **Bidirectional Sync:** Dest -> Source highlighting.
- [x] **Asset Injection:** PNG Icons via `assets` folder.
- [x] **Video Thumbnails:** Embedded FFmpeg with Async Threading.
- [x] **Stability Hardening:** Fixed Garbage Collection and Race Condition crashes.

### Phase 3: The Polish (v0.7 - v0.9) - [COMPLETED]

- [x] **MD5 Checksums:** Deep content verification (The "Paranoia" Engine).
- [x] **Drive Capacity Bar:** Visual storage indicators with "Insufficient Space" locking.
- [x] **Job Monitor:** Speed/ETA readout using manual chunked transfer logic.

### Phase 4: Final Release (v1.0) - [COMPLETED]

- [x] **Transfer Receipt:** Generate Audit Log Manifest.
- [ ] **Cross-Platform:** Validation for macOS paths (Future v1.1).
