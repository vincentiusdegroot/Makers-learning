# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file HTML5 canvas game (`index.html`) — a top-down GTA-style courier/driving game with police chases. There is no build step, no package manager, and no bundler: everything (markup, CSS, and one large IIFE of vanilla JS) lives in `index.html`.

## Running it

Open `index.html` directly in a browser (e.g. `firefox index.html`). There is no dev server, no `package.json`, and no Node/npm in this environment.

## Testing

There is no JS test runner available in this environment (no Node/npm, no browser automation like Playwright/Selenium). The one test that exists, `tests/test_render_mini.py`, is a dependency-free Python script that statically parses the inline `<script>` block in `index.html` (stripping comments) rather than executing the JS. Run it with:

```
python3 tests/test_render_mini.py -v
```

When adding tests for other behavior in `index.html`, follow this same pattern (regex/static checks against the extracted script) unless a JS runtime becomes available — don't assume `node`, `npm`, or a browser driver are installed.

All tests must pass after each change to `index.html` before committing.

## Architecture

Everything lives inside one IIFE in `index.html`'s `<script>` block (~1150 lines), organized into clearly marked sections (search for `// ====` banners) in this order:

1. **WORLD** — grid constants (`CELL`, `ROAD`, `COLS`/`ROWS`, `WORLD` size), a seeded PRNG (`mulberry32`) used for deterministic world generation vs. `Math.random()` used for gameplay randomness, and shared math helpers (`clamp`, `dist`, `path`).
2. **STATIC GROUND LAYER** — the city (buildings, parks, canal, streets) is painted once onto an offscreen `ground` canvas and blitted per frame rather than redrawn every frame; the minimap has its own offscreen base (`miniBase`) built the same way.
3. **ENTITIES** — traffic (cars/bikes), parked cars, pedestrians, and police, each with its own `spawnX`/`updateX` pair and stored in a module-level array (`traffic`, `parked`, `peds`, `police`).
4. **PLAYER** — player/vehicle state, the job system (`newJob`, `checkJob`), the wanted/bust mechanic (`crime`, `bust`), toast notifications (`toast`), and movement (`driveVehicle`, `walkPlayer`, `toggleVehicle` for entering/exiting vehicles).
5. **COLLISION CONSEQUENCES** — `checkImpacts` (crashes, being spotted by police, etc.).
6. **RENDER** — `render()` draws the world each frame from the `ctx` (main canvas) and calls `renderMini()` to draw the `mini` canvas overlay (job marker, police blips, player chevron). Collision/solid geometry (`solids`, `hitsSolid`) is built once during world generation and reused by both movement and rendering.
7. **HUD** — DOM text/element updates (cash, stars, job description, street name), driven by a `last` cache so the DOM is only touched when a displayed value actually changes.
8. **LOOP** — `frame(now)` is the single `requestAnimationFrame` loop: it advances game state only when `state === 'play'`, then always calls `render()` and `updateHud()`. `state` is a simple string machine: `title | play | busted`.
9. **INPUT** — a single `keydown`/`keyup` listener pair populates the `keys` map that movement code polls; `BLOCK_KEYS` prevents default browser behavior (scrolling) for arrow keys/space.
10. **BOOT** — populates initial entities and starts the `requestAnimationFrame` loop; runs once at the bottom of the IIFE.

### Key implicit contracts to preserve when editing

- Anything in **RENDER** or **LOOP** that is called unconditionally every frame (e.g. `renderMini()` from `render()`) must stay a live function — commenting out a function body while leaving its call site in place throws at runtime and breaks the entire frame loop, not just that piece of rendering.
- World geometry (`solids`, `cellIdx`) is built once at module load from the same constants used for rendering (`CELL`, `ROAD`, `WORLD`); changing grid constants affects world gen, collision, and the minimap scale (`MINI / WORLD`) together.
- `sr()` (seeded) is for one-time world generation so the map layout is reproducible; `rr()`/`pick()` (unseeded `Math.random()`) are for ongoing gameplay spawns — don't mix them up.
