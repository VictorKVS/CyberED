# FAS Cinematic Motion Profile — draft v1.1

## Hard gate
Do not animate speech or blink by swapping entire unrelated portraits. A static stable face is preferable to visibly jumping anatomy.

## Pipeline
1. Choose one master frontal pose, with permission to use as character asset.
2. Establish canonical canvas, face bounding box, eye corners, iris centers, nose, lip corners and chin anchors.
3. Separate eye and mouth layers from master; keep hair, glasses, shoulders and background fixed.
4. Generate coherent eyelid positions and mouth visemes from the same master (not crops of differently posed faces).
5. Composite layers using masks and interpolation, avoid full-frame crossfade.
6. Synchronize mouth to TTS phoneme/viseme timestamps; interpolate coarticulation, add smoothing, preserve pauses.
7. For head motion and gestures, use rigged mesh/landmark warp or temporally consistent video segments with matched entry/exit poses.
8. Add subtle idle motion only after validation; honor reduced motion and battery/performance constraints.

## Acceptance criteria
- No perceptible shift of glasses, hairline, background or face scale in blink/speech tests.
- No whole-face flashes; no sudden pose jumps; mouth remains inside lip anchor bounds.
- Blink duration ~120–250 ms; configurable interval, no forced repetition pattern.
- Mouth movement follows speech audio, not a fixed arbitrary loop.
- Test at 30 fps minimum target on typical devices; use 60 fps when practical, measured not assumed.
- A/B visual review at desktop and mobile; QA with audio on/off and slow playback.
- Each asset pack must pass automatic geometry checks and human perceptual QA before marking READY.

## Current status
The uploaded contact sheets are reference poses and facial feature references only. They do not provide a continuous temporal animation. Current ALINA widget uses a stable portrait; true lip sync, rigging, aligned masks, and voice are not implemented yet.
