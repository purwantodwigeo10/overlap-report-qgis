# Sample data

These small WGS 84 GeoJSON files are provided for a quick functional test.
They contain synthetic geometries and no personal or production data.

## Self Overlap

1. Add `primary.geojson` to QGIS.
2. Select **Self Overlap** and use `parcel_id` as the identifier.
3. Choose a new output Shapefile and run the analysis.
4. Confirm that the overlap-detail output contains one polygon intersection.

## Pair Overlap

1. Add both GeoJSON files to QGIS.
2. Select **Pair Overlap**.
3. Use `primary.geojson` as the primary layer and `secondary.geojson` as the
   secondary layer.
4. Use `parcel_id` and `zone_id` as the respective identifier fields.
5. Choose a new output Shapefile and run the analysis.
6. Confirm that the overlap-detail output contains two polygon intersections.
