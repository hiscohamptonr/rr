-- Run against the GlobalExposures database and export the result as shape-points.csv.
DECLARE @event_id int = NULL;

SELECT
    ShapefileID,
    EventID,
    PolygonID,
    Lat,
    Long,
    DrawOrder
FROM data.ShapeFiles
WHERE @event_id IS NULL OR EventID = @event_id
ORDER BY EventID, PolygonID, DrawOrder;
