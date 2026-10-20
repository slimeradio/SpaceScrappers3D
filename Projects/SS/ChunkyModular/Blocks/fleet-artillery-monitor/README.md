# Monitor — final triple heavy artillery

Catalog ID fleet-artillery-monitor, 3x3 reference cells. Broad tapered naval casemate, three long large-caliber open-bore guns, individual sliding recoil carriages and a deep aft counterweight. All three functional muzzle origins match the existing catalog barrel IDs.

Six new finished reusable parts: cm-monitor-deck, cm-monitor-casemate, cm-monitor-gun, cm-monitor-sleeve, cm-monitor-roof, cm-monitor-counterweight. Reuses cm-bearing and cm-lamp version 2.0.0 without changing their source. All new parts have separate .blend sources, packed existing CM-T01 material textures, part.json metadata and standalone GLB in Exports/Parts. Two reused recessed lamps supply emission; nonemissive new parts explicitly report no emissive regions.

Final source: fleet-artillery-monitor.blend. Reproducible build: build.py, shared ../../Tools/weapon_asset_runtime.py. Assembly metadata: assembly.json. Kit: ../../Kits/fleet-artillery-monitor/kit.json. Final GLB and validation: ../../Exports/fleet-artillery-monitor/.

173 mesh objects, 377020 evaluated triangles, 13 part instances, 12 embedded texture images. The casemate and roof follow yaw while three guns elevate within their forward openings. Each gun recoils separately along local +Y; muzzle points follow recoil and elevation. Dense fillets use 8 segments, round primitives 96 segments. No typography or presentation renders.

Validation: actual Blender GLB reimport, mesh count and rest bounding box equality, self-contained textures, catalog barrel references, normalized orientation vectors and 7 sampled animation poses. +Z up, -Y forward, right-handed design units. No assumption that a catalog cell equals a meter. Metadata is for authoring; no game integration, LOD or collision setup has been performed.