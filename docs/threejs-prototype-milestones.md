# Three.js Prototype Milestone Plan — Endless Urban Driving Runner

## Milestone 0 — Project Foundation (2–3 days)
**Goal:** bootable technical skeleton with clean boundaries.

### Deliverables
- Vite + TypeScript + Three.js project scaffold
- Module boundaries:
  - `simulation/`
  - `physics/`
  - `render/`
  - `ui/`
  - `content/`
- Deterministic game loop (`fixedUpdate` + `renderUpdate`)
- Basic input abstraction (keyboard + controller-ready mapping)
- Minimal debug overlay (FPS, speed, chunk index)

### Exit Criteria
- Blank scene runs stable with loop separation and input polling.

---

## Milestone 1 — First Driveable Slice (4–6 days)
**Goal:** car feels controllable and fun in a single repeated test road.

### Deliverables
- Arcade vehicle controller (accelerate, brake, steer, handbrake, boost)
- Chase camera rig with smoothing and look-ahead
- One road test chunk + barriers
- Collision response (no fancy damage yet)
- Speedometer + simple combo placeholder HUD

### Exit Criteria
- Driving loop is playable for 2+ minutes with no major control bugs.

---

## Milestone 2 — Endless Chunk Streaming (4–6 days)
**Goal:** illusion of continuous city traversal.

### Deliverables
- Chunk definition format in `content/` (connectors, lane metadata, spawn sockets)
- Seeded chunk queue generator
- Runtime chunk mount/unmount pooling
- At least 6 chunk archetypes (straight, curve, 4-way, overpass, tunnel, connector)

### Exit Criteria
- 10+ minute run with stable memory and no visible chunk pop-in at target speed.

---

## Milestone 3 — Traffic + Risk Systems (5–7 days)
**Goal:** create meaningful moment-to-moment tension.

### Deliverables
- AI traffic spawner + despawner tied to lane sockets
- Basic traffic behavior states (cruise, slow, lane block variants)
- Near-miss detector
- Collision severity tiers (minor/major)
- Momentum/heat meter with decay rules

### Exit Criteria
- Players can reliably earn/lose momentum via driving quality.

---

## Milestone 4 — Scoring + Combo + Run End (3–5 days)
**Goal:** complete arcade run logic.

### Deliverables
- Score model (distance, near-miss, drift, high-speed uptime)
- Combo multiplier and break conditions
- Damage accumulation and run-fail conditions
- End-of-run summary screen

### Exit Criteria
- Full run loop from spawn → play → fail → results → restart.

---

## Milestone 5 — Perks + Escalation (4–6 days)
**Goal:** add light systemic depth.

### Deliverables
- Upgrade gate every ~90 seconds with 3 random perk choices
- Perk effects (grip, top speed, boost capacity, threading bonus)
- Intensity director (traffic density, weather toggles, police chance)
- Basic police pressure prototype (spawn + chase timer)

### Exit Criteria
- Distinct run variability from perk/path/intensity differences.

---

## Milestone 6 — Content + Polish Pass (ongoing, 1–2 weeks)
**Goal:** make MVP feel cohesive and replayable.

### Deliverables
- Visual theming pass (night lighting, signage, fog tuning)
- Additional chunk set pieces and hazard props
- Juice pass (VFX/SFX/UI callouts/camera shake tuning)
- Performance optimization (object pools, draw-call and shader budget checks)
- First meta unlocks (at least 2 new vehicles)

### Exit Criteria
- External playtesters can understand and enjoy loop without designer present.

---

## Cross-Cutting Technical Rules
- Simulation is authoritative; render objects are projections.
- Avoid per-frame allocations in critical loops.
- Use object pools for traffic, VFX, and chunk instances.
- Keep HUD mostly DOM; avoid heavy UI framework coupling.
- Instrument performance from Milestone 1 onward.

## KPI Targets for MVP Validation
- Median FPS >= 60 on target desktop class
- Time-to-fun < 30 seconds
- Median first-session run length: 2–4 minutes
- At least 3 “meaningful decisions” per run (routing/perks/risk windows)
