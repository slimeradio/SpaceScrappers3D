# Cyclone — final twin rotary battery

Catalog ID fleet-minigun-cyclone, 2x2 reference cells. Two independent six-tube rotary assemblies, two large ammunition drums, paired ribbed drive motors and a low armored body. Six physical tubes per rotor are visual geometry; the two logical firing-group origins match the two existing catalog barrel IDs.

Six new finished reusable parts: cm-cyclone-deck, cm-cyclone-receiver, cm-cyclone-rotor, cm-cyclone-motor, cm-cyclone-drum, cm-cyclone-cheek. Reuses cm-bearing and cm-lamp version 2.0.0 without changing their source. All new parts have separate .blend sources, packed existing CM-T01 material textures, part.json metadata and standalone GLB in Exports/Parts. Emission is provided by the reused recessed status lamp; new nonemissive parts explicitly report no emissive regions.

Final source: fleet-minigun-cyclone.blend. Reproducible build: build.py, shared ../../Tools/weapon_asset_runtime.py. Assembly metadata: assembly.json. Kit: ../../Kits/fleet-minigun-cyclone/kit.json. Final GLB and validation: ../../Exports/fleet-minigun-cyclone/.

239 mesh objects, 620036 evaluated triangles, 12 part instances, 12 embedded texture images. Body, drums and armor follow yaw; paired gun groups elevate independently from the fixed armored body and rotate around their own longitudinal axes. Logical muzzle points follow the rotor hierarchy. Dense fillets use 8 segments, round primitives 96 segments. No typography or presentation renders.

Validation: actual Blender GLB reimport, mesh count and rest bounding box equality, self-contained textures, catalog barrel references, normalized orientation vectors and 7 sampled animation poses. +Z up, -Y forward, right-handed design units. No assumption that a catalog cell equals a meter. Metadata is for authoring; no game integration, LOD or collision setup has been performed.