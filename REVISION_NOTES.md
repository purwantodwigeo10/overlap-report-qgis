# Revision notes — overlap_report_ovrt 26.1.0

Version retained at the author's request.

## Changes

- Use scoped Qt enums, exec(), Qt-compatible QAction imports and explicit Qt5/Qt6 field types.
- Use bounded License Hub HTTPS requests, manual redirect policy, HTTP/network error checks and an already-finished reply guard.
- Give explicit inactive/revoked/expired/pending states priority over conflicting success flags.
- Prevent reentrant Run operations during nested event loops.
- Require new output filenames to protect existing data; partial new output may remain if a later write fails.
- Use union coverage for report area and percentage; retain individual intersection features in the detail layer.
- Use the current streaming vector-writer creation API.
- Require new filenames for both report and overlap outputs.

## Required QGIS test

Self Overlap: sample primary.geojson must produce one detail intersection. Pair Overlap with secondary.geojson must produce two. Add a triple-overlap case: the main report must count the union once, while the detail layer retains each pair. Test different input CRSs.

## Validation limits

Offline regression tests, actual standalone PyQt5/PyQt6 enum checks, and Python lint/syntax checks were run. Full QGIS/GDAL processing, Windows file locking, live activation and the official repository scanners were not run. The package retains QGIS 3.22–3.99 compatibility metadata; no QGIS 4 support is claimed. Standalone Qt tests do not establish complete QGIS compatibility.

## Publishing

Install this ZIP in QGIS without extracting it. For GitHub, extract and upload the contents of this plugin folder at the existing repository root. Do not upload another plugin's files. Check public repository, issue tracker and help URLs before uploading to QGIS. Changing GitHub source or version text does not replace the ZIP stored on the QGIS plugin site. If the version already exists, inspect its Manage/Edit options before replacing it; do not delete the whole plugin.
