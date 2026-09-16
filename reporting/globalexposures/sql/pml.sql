-- Server (original Python default): PR0603-41001-00
-- Database: GlobalExposures
-- Schema: data
-- Source table: data.PML
-- Export with headers as: pml.csv
-- Confirm the server/database and use the same event selection as events.sql and shape-points.sql.
DECLARE @event_id int = NULL;

SELECT
    EventID,
    PolygonID,
    PML
FROM data.PML
WHERE @event_id IS NULL OR EventID = @event_id;
