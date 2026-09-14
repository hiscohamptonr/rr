-- Run against the GlobalExposures database and export the result as pml.csv.
DECLARE @event_id int = NULL;

SELECT
    EventID,
    PolygonID,
    PML
FROM data.PML
WHERE @event_id IS NULL OR EventID = @event_id;
