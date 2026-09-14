-- Run against the GlobalExposures database and export the result as events.csv.
DECLARE @event_id int = NULL;

SELECT
    EventID,
    EventName,
    EventDescription
FROM data.Events
WHERE @event_id IS NULL OR EventID = @event_id
ORDER BY EventID;
