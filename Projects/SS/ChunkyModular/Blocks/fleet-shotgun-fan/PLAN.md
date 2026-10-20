# Fleet Shotgun Fan — production plan

Catalog: fleet-shotgun-fan, Turret, 2x1 cells; exactly 1 Bullet barrel and 12 projectiles per shot. Twelve pellets do not imply twelve barrels. Coordinate convention: +Z up, -Y forward, design units.

Silhouette: low wide wedge with one broad flattened bore, deep stepped breech and paired side ammunition drums. Distinct from twin cannons and missile pods. Short aggressive muzzle, no text.

| Required part | Existing comparison | Decision | Reason |
| Wide low deck | cm-deck 2.0.0 | New cm-fan-plinth | Wide 2x1 aspect, low silhouette |
| Rotary bearing | cm-bearing 2.0.0 | Reuse uniform scale 0.52 | Compatible vertical yaw joint |
| Breech and slide | cm-receiver 2.0.0 | New cm-fan-breech | Wider squat receiver designed around one bore |
| Single fan muzzle | cm-barrel 2.0.0 | New cm-fan-muzzle | Short flattened oval/rectangular throat, no duplicated barrels |
| Recoil guide | cm-hydraulic-actuator 2.0.0 | New cm-fan-slide | Longitudinal rail action without decorative hardware |
| Side drum | cm-radiator 2.0.0 | New cm-fan-drum | Round ammunition storage silhouette |
| Top armor | cm-armor-slab 2.0.0 | New cm-fan-carapace | Stepped wedge armor fitted to breech |
| Diagnostic lamp | cm-lamp 2.0.0 | Reuse uniform scale 0.45 | Existing diagnostic module fits front fascia |
| Vent | cm-vent-cassette 2.0.0 | Reuse uniform scale 0.55 | Compatible cooling insert |

Save all new parts separately with completed shared PBR textures, sockets and animation metadata, then assemble instances. No preview/renders/GIF. Small high-resolution bevels, no typography. No engine-ready claim: collider/LOD/import mapping are not defined.

Additional compatible reuse: cm-trunnion-armored 2.0.0, uniform scale 0.42, supports independent pitch axis. Each new part has version 1.0.0, a packed Blender source and separate GLB. Catalog linking describes authoring only; cell size, collider and LOD contract remain undefined.
