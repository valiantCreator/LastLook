# LastLook: Master Project Documentation

**Version:** 2.2 (Python Production)
**Tagline:** "AYO SOMEBODY CHECK HIS HARD DRIVE."

---

## 1. Product Vision & Philosophy

**LastLook** is a specialized file transfer verification tool for Digital Imaging Technicians (DITs) and Filmmakers. It prioritizes **visual verification** over blind copying.

### The Core Problem

Operating systems (Finder/Explorer) fail at "high-stakes" data transfer. They lack:

1.  **Visual Confirmation:** Did the file _actually_ arrive?
2.  **Comparison:** Is the destination file identical to the source?
3.  **Safety:** Preventing accidental formatting of cards before backup is confirmed.

### The Solution: "Call and Response"

A 3-pane interface where every action in the Source (Left) triggers a verification lookup in the Destination (Center), providing instant "Traffic Light" feedback.

---

## 2. Technical Specifications & Data Models

### 2.1 File Objects (The Data Structure)

Every file row in the UI maps to this Python Data Class:

- **`id`**: Absolute Path (String).
- **`filename`**: String (e.g., "A001_C001.mp4").
- **`size`**: Integer (Bytes).
- **`mtime`**: Float (Timestamp).
- **`status`**: Enum (Synced, Missing, Transferring).
- **`type`**: Enum (Image, Video, Audio, Other).

### 2.2 The Enums

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

- **Source Click:** Highlights the row. immediately searches `DestList`. If found -> Highlight Dest Row Green. If missing -> Flash Dest Row Red.
- **Dest Click (Bidirectional):** Highlights Dest row. Searches `SourceList`. Highlights Source Row Blue.
- **Batch Selection:**
  - **Shift+Click:** Range Select.
  - **Ctrl+Click:** Toggle Select.
  - **"Select All Missing":** Utility button to select all `Status == MISSING`.

### 3.3 The Secure Transfer Engine

- **Threading:** MUST run on `threading.Thread` to prevent GUI freeze.
- **Logic:**
  1.  Filter `Selection` for files where `Status == MISSING`.
  2.  Check `DestDrive.FreeSpace > Batch.TotalSize`. If false -> **HALT**.
  3.  Iterate:
      - Update UI -> `TRANSFERRING`.
      - `shutil.copy2(src, dst)` (Preserves Metadata).
      - Post-Copy Check: `os.path.getsize(dst) == src.size`.
      - Update UI -> `SYNCED`.
- **Cancellation:** Must support a "Stop" flag to halt the loop safely.

### 3.4 The Inspector Pane

Dynamic content based on selection:

- **0 Items:** "Select a file..."
- **1 Item:** Thumbnail (FFmpeg/PIL), Filename, Size (MB/GB), Full Path.
- **>1 Items:** "Batch Summary" (Total Size, Count of Missing vs Synced).

### 3.5 Night Shift (Eye Guard)

- **Implementation:** Toggle button.
- **Behavior:** Shifts UI colors to Amber (`#FFB347` Text, `#2e1c05` Backgrounds) to reduce blue light emission in dark environments.

---

## 4. Roadmap (Implementation Stages)

### Phase 1: The Skeleton (Current Status)

- [x] Basic 3-Pane Layout.
- [x] File Scanning & Size Comparison.
- [x] Threaded Transfer.
- [x] Basic Red/Green UI.

### Phase 2: The Logic (Next Priority)

- [ ] **Multi-Select:** Checkboxes and Shift-Click logic.
- [ ] **Batch Inspector:** Calculating total size of selection.
- [ ] **"Select All Missing" Button.**
- [ ] **Bidirectional Sync:** Dest -> Source highlighting.

### Phase 3: The Polish

- [ ] **MD5 Checksums:** Deep content verification.
- [ ] **Video Thumbnails:** FFmpeg integration.
- [ ] **Drive Capacity Bar:** Visual storage indicators.
- [ ] **PDF Manifest:** Transfer receipt generation.
