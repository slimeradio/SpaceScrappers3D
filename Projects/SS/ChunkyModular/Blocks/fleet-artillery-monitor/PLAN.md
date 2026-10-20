# Monitor production plan
Catalog: fleet-artillery-monitor, 3x3 grid, three logical barrels. Model units are design units, +Z up, -Y forward; grid is not a metric size. Distinct design: broad naval battery, three long large-caliber cannons, deep tapered armored turret, large recoil sleeves and counterweight.

| Component | Existing comparison | Decision |
|---|---|---|
| Bearing | cm-bearing 2.0.0: compatible origin; uniform scale | Reuse |
| Signal lamp | cm-lamp 2.0.0: finished compatible emissive part | Reuse |
| Foundation | cm-deck differs in footprint and braced naval foundation | New cm-monitor-deck |
| Casemate | cm-receiver is a smaller dual-weapon receiver; cannot cover triple large recoil cradles | New cm-monitor-casemate |
| Heavy gun | cm-barrel has short twin-gun proportions; extended triple artillery needs own geometry and metadata | New cm-monitor-gun |
| Recoil sleeve | cm-breech-collar insufficient for long sliding artillery carriage | New cm-monitor-sleeve |
| Roof armor | cm-armor-slab shape does not match tapered casemate top | New cm-monitor-roof |
| Counterweight | No matching broad slotted aft recoil balance module | New cm-monitor-counterweight |

Finish all parts with shared existing textures and machine-readable local metadata before assembly. Independent recoil for three guns, elevation and yaw hierarchy. Logical mount sockets, vectors and permitted regions remain invisible. No typography. No previews, renders, GIFs or intermediate deliverables requested. Final source, GLB, metadata and structural validation only. Authoring metadata is not a game import contract.