# Attribute Table Functions — QGIS Plugin

Adds buttons to the toolbar of every QGIS **attribute table** window:

- **Area** — enabled only for polygon layers. Click → pick a unit (m² / km²) → adds a virtual field to the layer.
- **Length** — enabled only for line layers. Click → pick a unit (m / km) → adds a virtual field to the layer.
- **X / Y** — enabled only for point layers. Adds virtual coordinate fields in the chosen CRS.
- **Export CSV** — exports the attribute table (all or selected features) to CSV, geometry included as WKT.

Buttons auto enable/disable based on the layer's geometry type.

Fields are QGIS **virtual fields**: they auto-update when geometry changes and are stored inside the QGIS project (not written to the .shp/.dbf, so the original shapefile is untouched).

Measurements are **ellipsoidal** (WGS84 by default) so layers in geographic CRSs (e.g. EPSG:4326) still return correct m²/km² / m/km values.

## Install

1. Copy this folder into your QGIS plugin directory:
   ```
   %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\attribute_table_functions\
   ```
2. Restart QGIS.
3. `Plugins → Manage and Install Plugins…` → enable **Attribute Table Functions**.

## Use

1. Load a vector layer.
2. Open its attribute table (`F6` or the toolbar icon).
3. On the right end of the attribute-table toolbar you'll see the new buttons.
4. Click the appropriate one, choose a unit / CRS / decimals, click **OK**.
5. A new column appears in the attribute table.

## Field names

Auto-generated: `area_m2`, `area_km2`, `length_m`, `length_km`, `x`, `y`. If a name is already taken, `_2`, `_3`… is appended.

## Notes

- Because the field is virtual, it disappears if you remove the layer from the project. Save the project to keep it.
- To make it a permanent shapefile column: right-click the field in the attribute table → *Field Calculator* → *Update existing field* / *Create new field*, using the same expression (`$area`, `$area / 1000000`, `$length`, or `$length / 1000`).
