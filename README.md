# Overlap Report

Overlap Report is a QGIS plugin for detecting polygon overlaps and producing
inspectable area and percentage reports. It supports two analysis modes:

- **Self Overlap** detects intersections between different features in one
  polygon layer.
- **Pair Overlap** detects intersections between a primary and a secondary
  polygon layer, including layers with different coordinate reference systems.

## Compatibility

- QGIS 3.22 through 3.99
- Windows, Linux, and macOS
- No third-party Python packages or bundled binaries

## Installation

1. Open **Plugins > Manage and Install Plugins** in QGIS.
2. For a downloaded package, select **Install from ZIP** and choose the ZIP.
3. After repository publication, search for **Overlap Report** in **All**.
4. Open it from **Vector > RUANG SPASIAL > Overlap Report** or its toolbar icon.

## Inputs

- Analysis mode: Self Overlap or Pair Overlap
- Primary polygon layer, from the QGIS project or a local vector file
- Secondary polygon layer for Pair Overlap
- Optional identifier fields used in overlap descriptions
- Optional primary-layer attributes copied to the detail output
- Output report Shapefile path

## Outputs

The plugin creates two Shapefiles:

1. The requested report output, containing the primary features plus a stable
   source ID, overlap summary, overlap area in square metres, and percentage.
2. A sibling file ending in `_Overlap.shp`, containing each intersection
   geometry, both source feature IDs, area in square metres, description, and
   optional selected attributes.

Area measurement is CRS-aware and converted to square metres. Pair Overlap
temporarily transforms secondary geometries into the primary layer CRS without
modifying either source layer.

The analysis workspace displays live progress from 0 to 100 percent, including
the current processing stage while inputs are copied, indexed, analysed, and
summarised.

## Quick functional test

Synthetic GeoJSON files are included in `sample_data`. See
`sample_data/README.md` for Self Overlap and Pair Overlap test steps and the
expected intersection counts.

## Activation and network access

The plugin includes two successful analysis runs in trial mode. Continued use
requires activation through RUANG SPASIAL License Hub and an internet
connection when an active license is checked.

- Product code: `OVRT`
- Fixed code: `YM`
- Request page: <https://aktivasi.ruangspasial.my.id/request>
- User guide: <https://aktivasi.ruangspasial.my.id/help/overlap-report-qgis>

All License Hub and help traffic uses HTTPS. No HTTP fallback is included.

## Privacy

For license verification, the plugin sends the product identifiers, the
activation code entered by the user, and a Device ID to RUANG SPASIAL License
Hub. The Device ID is a 32-character value derived with SHA-256 from a stable
local machine identifier; the original identifier is not transmitted. The
local license state is stored in the current user's application-data folder.

## License and support

Copyright (C) 2026 Dwi Purwanto (Ruang Spasial).

This plugin is free software licensed under the GNU General Public License,
version 3 or any later version. See `LICENSE` for the complete terms.

- Homepage: <https://aktivasi.ruangspasial.my.id/help/overlap-report-qgis>
- Support: <ruangspasial@gmail.com>
- Source code: <https://github.com/purwantodwigeo10/overlap-report-qgis>
- Issue tracker: <https://github.com/purwantodwigeo10/overlap-report-qgis/issues>
