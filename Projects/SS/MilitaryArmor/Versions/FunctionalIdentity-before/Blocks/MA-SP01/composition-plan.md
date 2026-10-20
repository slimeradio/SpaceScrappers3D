# MA-SP01 — composition plan

MilitaryArmor 1.3; catalog solar-1x2, 1×2, visual concept without game XML. BU conditional; +Z up, -Y forward, right handed. Static protected photovoltaic field, no invented output values or deployment.

| Need | Existing candidate | Decision | Compatibility |
| --- | --- | --- | --- |
| Armoured 1×2 carrier | MA-H01-P01 v1.0 | Reuse unchanged | 1.8×3.6 BU bounds; eight seats at x ±0.34, y ±0.93/±0.31, z 0.20. Unit scale. Closed protected conduits can serve PV interconnect routing. radiator.tile is reused as a mechanical cassette seat, not a heat-transfer gameplay claim. |
| Light collecting surface | MA-H01-P02 | New MA-SP01-P01 v1.0 | Existing plain ceramic radiative tile has no photovoltaic cell lattice or collector tracks. New cassette fits same 0.60×0.56 BU footprint and socket pose, 3×3 discrete cells and visible fine busbars. |
| Side thermal panels | MA-E01-P04 | Omit | Radiator-specific thermal fins are unnecessary for a solar collecting surface. Frame's unused thermal sockets remain unused. |

Only new cassette source is built and gated before assembly. Eight unit-scale saved cassette instances and one unchanged saved carrier instance. Uniform procedural PBR; graphite/cold blue nonemissive cells, pale raised rim, titanium contacts. No file textures, no animation, no GLB. Existing sources are never saved or rebuilt.
