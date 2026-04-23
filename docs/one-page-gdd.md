# One-Page GDD — **Neon Flow** (Working Title)

## High Concept
An endless urban night-driving arcade game where players chain speed, drifts, and near-misses through a procedurally streamed city to maintain momentum and maximize score.

## Pillars
1. **Flow over simulation** — responsive arcade handling, readable risk/reward.
2. **Endless city illusion** — modular district chunk streaming.
3. **Stylish survival** — score is tied to dangerous-but-clean driving.

## Core Player Fantasy
“Thread impossible traffic gaps at high speed and stay in the zone until the city breaks you.”

## Core Loop (30–120s cycle)
1. Spawn into streamed district with starter momentum.
2. Drive, drift, and near-miss traffic to build combo + score.
3. Complete micro-objectives (courier pickup, time gate, intersection clear).
4. Select one perk at interval gate (~90s).
5. Survive escalating density/hazards/police pressure.
6. Crash out or lose momentum, then cash out rewards for meta unlocks.

## Inputs / Verbs
- Accelerate / Brake
- Steer + lane-threading
- Handbrake drift
- Boost (limited)
- Event trigger/collection
- Recovery from spins/impacts

## Failure Model
- **Minor impact:** speed loss + combo damage.
- **Major impact:** heavy speed loss + spin + damage spike.
- **Run end:** total wreck, immobilized timeout, or momentum fully depleted.

## Scoring & Combo
Primary score contributors:
- Distance traveled
- Near-miss streaks
- Drift duration/quality
- Clean intersection clears
- High-speed uptime
- Objective completions
- Police escape streaks

Combo decays when speed drops below threshold, on collisions, or when chain windows are missed.

## Progression
### Run Progression
- Current score, combo, multiplier
- District intensity tier
- Live perks (handling, speed, boost, threading bonus)

### Meta Progression
- Vehicle unlocks (muscle, tuner, van, interceptor)
- District themes
- New events, weather, police tiers
- Passive account modifiers

## Endless City Structure
Streamed seeded chunk types:
- Straightaways
- Curved blocks
- Four-way intersections
- Overpasses / tunnels
- Market streets
- Highway connectors

Each chunk includes lane metadata + spawn sockets for traffic, hazards, pickups, and scenery.

## Difficulty Escalation
- **0–2 min:** low traffic, readable routes, onboarding flow.
- **2–5 min:** denser traffic, tighter turns, richer scoring opportunities.
- **5–8 min:** police pressure, roadworks, weather modifiers.
- **8+ min:** high-speed chaos, rare set pieces, survival emphasis.

## HUD / UX
- Top-left: score, combo, multiplier
- Top-right: speed, boost, damage
- Edge chip: active objective/event
- Center-low transient callouts only
- Menus/garage/pause in lightweight DOM overlays

## Technical Direction
- **Engine stack:** Three.js + TypeScript + Vite
- **Physics:** Rapier (simplified vehicle/traffic collision model)
- **UI:** DOM HUD overlay
- **Assets:** GLB modular cars + environment kits
- **Rule:** simulation state is source of truth; render layer mirrors state

## MVP “Fun Prototype” Scope
- 1 player car
- 1 district tileset with chunk streaming
- AI traffic
- Distance + combo scoring
- Drift + near-miss bonuses
- Crash/reset run loop
- Basic chase camera
- 1 perk choice every ~90 seconds

## Success Criteria (Prototype)
- First 3 minutes feel fast, readable, and replayable.
- Players understand risk/reward without tutorial walls.
- Average run length naturally varies by skill (not randomness).
- 60 FPS target on mid-range desktop browser at MVP content density.
