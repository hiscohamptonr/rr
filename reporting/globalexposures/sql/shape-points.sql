-- Server (original Python default): PR0603-41001-00
-- Database: GlobalExposures
-- Schema: data
-- Source table: data.ShapeFiles
-- Export with headers as: shape-points.csv
-- Confirm the server/database and use the same event selection as events.sql and pml.sql.
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
