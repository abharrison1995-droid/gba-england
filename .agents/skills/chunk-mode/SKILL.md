---
name: chunk-mode
description: >-
  Interactive step-by-step World Architect & Chunk Designer mode for GBH: England.
  Use whenever the user asks to enter Chunk Mode, design, create, or modify a 220x220
  world chunk, generate tileable ground textures, road overlays, boundary walls,
  triggers, and wire bidirectional map adjacencies relative to Home_London.
---

# Chunk Mode — Interactive World Architect Runbook

When activated, you become the **Lead World Architect** for *GBH: England*. You guide the developer through an interactive, step-by-step session to author, generate, texture, and wire a playable $220 \times 220$ world chunk.

---

## The 5-Phase Chunk Creation Workflow

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Concept & Topology (Name, Coords, Neighbors)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: Ground Art & Tileable Material Generation      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: World-Building Layout (Roads, Overlays, Props) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 4: Automated Assembly & Adjacency Wiring         │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 5: Verification & In-Editor Playtest Route       │
└────────────────────────────────────────────────────────┘
```

---

## Phase 1: Concept & Topology Interview

Engage the user with structured prompts to define the chunk's identity and position:

1. **Chunk Name:**
   - Enforce clean alphanumeric names with underscores (e.g. `East_York`, `West_Docklands`, `North_Canal`).
   - *Save Key Rule:* Remind the user that `ChunkName` is a permanent save key.

2. **World Coordinates (Relative to `Home_London` at `0, 0`):**
   - Identify the $(X, Y)$ grid coordinate.
   - Reference existing grid anchors:
     - `Home_London`: $(0, 0)$
     - `North_Wasteland`: $(0, 1)$
     - `South_Slums`: $(0, -1)$
     - `East_RetailPark`: $(1, 0)$
     - `West_Canal`: $(-1, 0)$

3. **City & Consequence Flag (`IsCity`):**
   - `IsCity = true`: Police patrol spawns, knife lockout timers active, magic casting drains concealment (for urban hubs).
   - `IsCity = false`: Outskirts, wastelands, slums, rural roads.

4. **Adjacency & Neighbor Connections:**
   - Confirm which existing chunk(s) will connect to the North, South, East, or West edges.

---

## Phase 2: Ground Art & Tileable Material Generation

1. **Texture Theme & Vibe:**
   - Clarify the ground aesthetic (e.g., weathered Victorian flagstones, dirty cracked asphalt, muddy churned grass, cobbled alleyway, gravel trainyard).
2. **Material Creation (`Assets/Materials/[ChunkName]_Ground.mat`):**
   - Author a Standard Shader material configured with:
     - Diffuse color & smoothness calibrated to the British isometric palette.
     - `_MainTex` UV tiling set to **$60 \times 60$** or **$80 \times 80$** (spanning $2.75 - 3.6\text{m}$ per tile repeat) to eliminate stretching over the $220\text{m}$ plane.
3. **Texture Asset Generation:**
   - If generating bespoke ground texture maps, save them in `Assets/Textures/Ground/` or `art_incoming/` following the project pipeline.

---

## Phase 3: World-Building Layout & Overlays

1. **Road & Detail Layout Style:**
   - `NorthSouth_Road`: Continuous 10m wide thoroughfare from $Z = -110$ to $+110$.
   - `EastWest_Road`: Continuous 10m wide thoroughfare from $X = -110$ to $+110$.
   - `Crossroad_Intersection`: Full 4-way crossroads with an elevated intersection center.
   - `Central_Plaza`: 40x40m paved town square or courtyard.
   - `Wasteland_Dirt_Track`: 6m winding or dirt overlay path.
2. **Z-Fighting Mitigation:**
   - Road overlays must sit at $Y = 0.04\text{m}$ (height scale $0.04\text{m}$).
   - Secondary detail patches (manholes, intersection centers) sit at $Y = 0.06\text{m}$.
3. **Unscaled Container Hierarchy:**
   - All landmark structures, kiosks, trees, and props must be parented under unscaled containers (`Environment/Props`, `Scale: (1, 1, 1)`), **never directly to `Ground`**.

---

## Phase 4: Automated Assembly & Adjacency Wiring

Use [`ChunkPrefabGeneratorTool.cs`](file:///c:/Users/P50/Desktop/gba-england/Assets/Editor/ChunkPrefabGeneratorTool.cs) to assemble the full stack:

1. **Prefab Construction (`Assets/Prefabs/Chunks/[ChunkName]_Prefab.prefab`):**
   - Ground plane ($220 \times 220\text{m}$) with `MeshFilter`, `MeshRenderer`, `MeshCollider`, and static flags 12.
   - 4x `ChunkEdge` triggers at $\pm 109.8$ inner face ($\pm 110.2$ center, size $220 \times 4 \times 0.8$).
   - 4x `BoundaryWall_*` colliders at $\pm 110.0$ inner face ($\pm 110.5$ center, size $230 \times 6 \times 1$).
   - `RuntimeNavMeshBaker` (`AgentRadius = 0.3`, `AgentHeight = 1.55`, `AgentClimb = 0.5`, `AgentSlope = 45`).
   - Default `PlayerSpawnPoint`.
2. **Data Asset Generation (`Assets/Data/Chunks/[ChunkName]_Data.asset`):**
   - Creates `MapChunkData` ScriptableObject.
   - Sets `ChunkName`, `Coordinates`, `IsCity`, and links `ChunkPrefab`.
   - Wires bidirectional N/S/E/W adjacency and cleans up stale reciprocal links.
3. **Registry Injection:**
   - Injects the new chunk into [`Assets/Resources/MapChunkRegistry.asset`](file:///c:/Users/P50/Desktop/gba-england/Assets/Resources/MapChunkRegistry.asset).

---

## Phase 5: Verification & Playtest Guide

Present a concise summary to the user with:
1. **The Traversal Path:** Step-by-step navigation instructions from `Home_London` to the new chunk.
2. **Integrity Check:** Run `python Tools/asset_reachability.py --check-dangling`.
3. **Next Creative Steps:** Recommend specific props from `Assets/3DModels/` or `WorldPalette` to stamp into the new area.
