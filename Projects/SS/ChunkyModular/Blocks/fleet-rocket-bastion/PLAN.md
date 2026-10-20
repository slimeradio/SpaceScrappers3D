# Fleet Rocket Bastion — production plan

Catalog: fleet-rocket-bastion, Turret, 3x3 cells; 4 SeekMissile channels. Cell size is not assumed to be meters. Coordinate convention: +Z up, -Y forward, design units.

Silhouette: squat heavy rotary plinth supporting two separated vertical twin-cell pods, central spine and stepped slab armor. Four dark open launch channels, no visible missile props and no typography.

| Required part | Existing comparison | Decision | Reason |
| --- | --- | --- | --- |
| Broad octagonal base | cm-deck 2.0.0 | New cm-bastion-plinth | Distinct broad missile recoil platform |
| Turntable | cm-bearing 2.0.0 | Reuse uniform scale 0.86 | Same rotary role and axis |
| Pivot cradle | cm-yoke 2.0.0 | New cm-bastion-cradle | Support wide launch pods and central elevation axis |
| Twin launch pod | cm-barrel 2.0.0 | New cm-bastion-pod | Rectangular two-channel shell is not a cannon |
| Missile cell | cm-barrel 2.0.0 | New cm-bastion-cell | Hollow square launch throat with thermal lining |
| Side shields | cm-armor-slab 2.0.0 | New cm-bastion-shield | Dedicated stepped silhouette |
| Spine/targeting housing | cm-receiver 2.0.0 | New cm-bastion-spine | Narrow center spine between pods |
| Diagnostic lamp | cm-lamp 2.0.0 | Reuse uniform scale 0.7 | Existing signal module is compatible |
| Vent | cm-vent-cassette 2.0.0 | Reuse uniform scale 0.7 | Existing cooling cassette fits rear deck |

All new parts must be saved individually with completed shared PBR materials and logical sockets before assembly. Source + GLB only; no intermediate previews/renders/GIF. Sockets are invisible metadata. Small 8-segment bevels and 96-sided round geometry. No game integration or balance changes.

Reused instances in final build: cm-bearing 2.0.0 at scale 0.86; cm-lamp 2.0.0 at 0.7; cm-vent-cassette 2.0.0 at 0.7. Each new part has version 1.0.0, a packed Blender source and separate GLB. Catalog linking describes authoring only; cell size, collider and LOD contract remain undefined.
