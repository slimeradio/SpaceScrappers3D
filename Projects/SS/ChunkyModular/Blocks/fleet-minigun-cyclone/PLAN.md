# Cyclone production plan
Catalog: fleet-minigun-cyclone, 2x2 grid, two logical firing groups. Model units are design units, +Z up, -Y forward; grid is not a metric size. Distinct design: compact wide twin rotary cannons, exposed six-tube clusters, cylindrical motors and low angular body.

| Component | Existing comparison | Decision |
|---|---|---|
| Bearing | cm-bearing 2.0.0: compatible origin, uniform scaling | Reuse at positive uniform scale |
| Signal lamp | cm-lamp 2.0.0: compatible finished materials | Reuse |
| Low armored deck | cm-deck: broad rectangular turret deck differs from compact twin-rotary footing | New cm-cyclone-deck |
| Twin receiver | cm-receiver: separate conventional breeches do not fit shared rotary motor housing | New cm-cyclone-receiver |
| Six-tube rotary cluster | cm-barrel: single cannon bore and muzzle brake | New cm-cyclone-rotor |
| Rotary motor | No compatible geared side motor | New cm-cyclone-motor |
| Ammunition drum | No compatible large round ammunition casing | New cm-cyclone-drum |
| Cheek armor | Existing cheeks enclose conventional breech | New cm-cyclone-cheek |

Finish each new part with shared existing packed textures and metadata before assembly. Two separate logical muzzle references represent two rotary groups; six physical tubes are visual geometry per group, no invented extra gameplay barrels. Yaw, elevation and rotor spinning authoring channels. No typography. No previews, renders, GIFs or intermediate deliverables requested. Final source, GLB, metadata and structural validation only. Authoring metadata is not a game import contract.