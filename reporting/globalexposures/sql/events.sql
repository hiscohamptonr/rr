-- Server (original Python default): PR0603-41001-00
-- Database: GlobalExposures
-- Schema: data
-- Source table: data.Events
-- Export with headers as: events.csv
-- Confirm the server/database and event selection before running.
DECLARE @event_id int = NULL;

SELECT
    EventID,
    EventName,
    EventDescription
FROM data.Events
WHERE @event_id IS NULL OR EventID = @event_id
ORDER BY EventID;
