# LastLook (formerly SyncShield)

> **"AYO SOMEBODY CHECK HIS HARD DRIVE."**

**LastLook** is a specialized, "Dark Mode" file transfer verification tool for Filmmakers and DITs. Unlike standard file managers, it prioritizes **visual verification** ("Call and Response") to ensure every bit of footage makes it from the SD Card to the SSD safely.

## 🚦 Status: Alpha Prototype (v0.1)

The core engine is functional. The UI currently supports:

- ✅ **Visual Sync:** Green (Synced) vs. Red (Missing) row highlighting.
- ✅ **Threaded Transfer:** Copies missing files without freezing the UI.
- ✅ **Night Shift:** Amber overlay for eye protection on dark sets.
- ✅ **Metadata Inspection:** View file size and modification dates.

## 🧠 Roadmap & Feature Gaps (v2.1)

### Phase 1: Core Intelligence (The Brain)

- [ ] **Advanced Selection Engine:** Implement `Set<ID>` logic to handle Shift+Click ranges and Ctrl+Click toggles.
- [ ] **Batch Inspector:** When multiple files are selected, the Inspector should calculate and display:
  - Total Size (e.g., "45.2 GB")
  - Status Breakdown (e.g., "4 Synced, 2 Missing")
- [ ] **"Select All Missing":** One-click button to instantly select all Red rows for transfer.

### Phase 2: Visual Confidence (The Eyes)

- [ ] **Video Thumbnails:** Use `ffmpeg` to generate frame grabs for `.mp4`, `.mov`, and `.mxf` files.
- [ ] **True Night Shift:** Investigate using a top-level transparent window overlay for better color accuracy (amber tint) vs. simple theme recoloring.
- [ ] **Bidirectional Sync:** Clicking a file in the Dest pane should auto-scroll to find its match in Source.

### Phase 3: Professional Safety (The Shield)

- [ ] **MD5 Checksum:** Upgrade from File Size verification to Content Hash verification.
- [ ] **Transfer Receipt:** Generate a PDF Manifest at the end of the session.
- [ ] **Capacity Guardrails:** Prevent transfer start if `Batch Size > Dest Free Space`.

## 🛠️ Build Instructions (Dev)

### Prerequisites

- Python 3.10+
- `customtkinter`
- `Pillow`

### Running Locally

```bash
python main.py
```
