# Modernized Opening Story Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modernized playable browser slice from New Game through the complete Chatsubo/PAX/payment sequence and into the original first destination.

**Architecture:** Preserve verified game state and a 320x200 logical evidence space while rendering player-facing scenes at 1280x800 through replaceable 4x assets. Canvas owns scene composition; responsive DOM panels own dialogue, PAX, controls, saves, and accessibility.

**Tech Stack:** Python 3 extraction and VICE probes, TypeScript, Canvas 2D, DOM/CSS, Vite, Pillow, PixelPerfectV4 ESRGAN, NCNN Vulkan with deterministic PyTorch CPU fallback, GitHub Pages.

**Spec:** `docs/architecture_web.md`

## Global Constraints

- Keep supplied D64 images immutable and retain source hashes and disk provenance.
- Treat verified C64 behavior as authoritative for state, progression, dialogue, and transitions.
- Use 320x200 logical coordinates and 1280x800 replacement-art assets.
- PixelPerfectV4 is mandatory; Vulkan is preferred and CPU is the approved fallback.
- Implement test-first and commit, push, deploy, and publicly verify every milestone.

---

### Task 1: Native frame fidelity

- [x] Normalize the VICE active-display crop and export the browser compositor buffer.
- [x] Correct palette, sprite mode, sprite workspace, and VIC coordinate mapping.
- [x] Retain reference, candidate, diff, hashes, and a zero-mismatch report.
- [x] Commit, push, deploy, and verify the milestone.

### Task 2: Opening-route evidence

- [x] Trace Ratz dialogue, PAX activation, transfer, optional Armitage branch, payment, exit, teardown, and the selector boundary (no destination auto-load exists).
- [x] Export machine-readable golden traces and confirm all promoted state/entity fields in VICE.
- [x] Commit, push, deploy, and verify the milestone.

### Task 3: Destination and asset extraction

- [x] Generalize room extraction around the traced destination ID.
- [x] Export native room, sprite, terminal, hit-region, and provenance assets plus a visual catalog.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 4: Four-times placeholder pipeline

- [ ] Pin PixelPerfectV4 by URL and hash; implement Vulkan conversion/inference and CPU fallback.
- [ ] Validate dimensions, alpha, stable asset IDs, and deterministic manifests.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 5: Multi-room runtime and schema v2

- [ ] Introduce serializable `GameState`, transactional room loading, immutable `SceneSnapshot`, and generated room/dialogue/PAX records.
- [ ] Preserve the checked room-0 trace after migration and fail visibly on unsupported records.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 6: Hybrid 1280x800 interface

- [ ] Render replaceable 4x scene assets in Canvas and accessible responsive controls in DOM layers.
- [ ] Support keyboard, mouse, touch, focus restoration, reduced motion, and a development comparison mode.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 7: Chatsubo interactions

- [ ] Implement traced Ratz dialogue, inspection, hotspots, animation, payment gating, and exit gating.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 8: Full opening PAX

- [ ] Implement login, inbox, reading, composition, transfer, logoff, and the optional Armitage/BAMA deposit branch.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 9: First verified transition

- [ ] Pay Ratz, execute teardown/load/init transaction, enter the traced destination, and expose one verified interaction.
- [ ] Commit, push, deploy, and verify the milestone.

### Task 10: Persistence and release hardening

- [ ] Add versioned autosave, New Game, Continue, Reset, recovery states, responsive route tests, and documentation.
- [ ] Complete the opening route on the public Pages build without console errors.
- [ ] Commit, push, deploy, and verify the milestone.
