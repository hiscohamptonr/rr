/*
  BSCR EDM raw/source export.

  Run this script in an approved SQL client and save the six resultsets, in
  order, as manifest.csv, schema.csv, accgrp.csv, policy.csv, loc.csv, and
  loccvg.csv.  The four data CSVs are full source exports at their stated
  grain: no joins, aggregation, DISTINCT, entity filtering, or Excel
  round-tripping.  Values are emitted as text; NULL is the reserved literal
  \N and an empty string remains empty.  Preserve the headers exactly.

  Run this with the same source parameters and immutable snapshot used for the
  BSCR reconciliation queries.  This script never enables database settings,
  uses NOLOCK, or changes source data.  It accepts an already SNAPSHOT-enabled
  database, or an immutable read-only database/database snapshot.
  It refuses dirty/nonrepeatable reads on mutable databases.
*/
IF @@TRANCOUNT <> 0
BEGIN
    RAISERROR(N'BSCR raw export requires a standalone connection without an ambient transaction.', 16, 1);
    RETURN;
END;

SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @export_run_id uniqueidentifier = NEWID();
DECLARE @export_started_utc datetime2(7) = SYSUTCDATETIME();
DECLARE @source_server nvarchar(128) = CONVERT(nvarchar(128), SERVERPROPERTY(N'ServerName'));
DECLARE @source_database sysname = DB_NAME();
DECLARE @prior_isolation tinyint =
(
    SELECT transaction_isolation_level
    FROM sys.dm_exec_sessions
    WHERE session_id = @@SPID
);
DECLARE @is_snapshot_database bit =
(
    SELECT CONVERT(bit, CASE WHEN source_database_id IS NULL THEN 0 ELSE 1 END)
    FROM sys.databases
    WHERE database_id = DB_ID()
);
DECLARE @snapshot_isolation_on bit =
(
    SELECT CONVERT(bit, CASE WHEN snapshot_isolation_state = 1 THEN 1 ELSE 0 END)
    FROM sys.databases WHERE database_id = DB_ID()
);
DECLARE @is_read_only bit =
(
    SELECT is_read_only FROM sys.databases WHERE database_id = DB_ID()
);
DECLARE @changed_isolation bit = 0;
DECLARE @isolation_mode nvarchar(32);
DECLARE @accgrp_count bigint;
DECLARE @policy_count bigint;
DECLARE @loc_count bigint;
DECLARE @loccvg_count bigint;

BEGIN TRY
    IF @is_snapshot_database = 1
    BEGIN
        SET @isolation_mode = N'DATABASE_SNAPSHOT';
    END
    ELSE IF @is_read_only = 1
    BEGIN
        SET @isolation_mode = N'READ_ONLY_DATABASE';
    END
    ELSE IF @snapshot_isolation_on = 1
    BEGIN
        SET @isolation_mode = N'SNAPSHOT';
        IF @prior_isolation <> 5
        BEGIN
            SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
            SET @changed_isolation = 1;
        END;
    END
    ELSE
    BEGIN
        THROW 51001, N'BSCR raw export requires SNAPSHOT isolation already enabled, or a read-only database/database snapshot. Ask the database owner for a consistent source; no dirty/nonrepeatable fallback is allowed.', 1;
    END;

    BEGIN TRANSACTION;

    /* A literal \N in an exported source value is ambiguous with NULL. */
    IF EXISTS (
        SELECT 1 FROM dbo.accgrp AS a
        WHERE a.userid1 = N'\N' OR a.branchname = N'\N' OR a.uwritrname = N'\N'
    )
    BEGIN
        THROW 51002, N'Export aborted: an accgrp text field contains the reserved NULL sentinel \N.', 1;
    END;
    IF EXISTS (
        SELECT 1 FROM dbo.loc AS l
        WHERE l.locnum = N'\N' OR l.state = N'\N' OR l.cntrycode = N'\N' OR l.country = N'\N'
    )
    BEGIN
        THROW 51003, N'Export aborted: a loc text field contains the reserved NULL sentinel \N.', 1;
    END;
    IF EXISTS (
        SELECT 1 FROM dbo.loccvg AS c
        WHERE c.peril IN (1, 2)
          AND (c.deductcur = N'\N' OR c.valuecur = N'\N' OR c.limitcur = N'\N')
    )
    BEGIN
        THROW 51004, N'Export aborted: a loccvg currency field contains the reserved NULL sentinel \N.', 1;
    END;

    SELECT @accgrp_count = COUNT_BIG(*) FROM dbo.accgrp;
    SELECT @policy_count = COUNT_BIG(*) FROM dbo.policy WHERE policytype IN (1, 2);
    SELECT @loc_count = COUNT_BIG(*) FROM dbo.loc;
    SELECT @loccvg_count = COUNT_BIG(*) FROM dbo.loccvg WHERE peril IN (1, 2);

    /* Resultset 1: manifest.csv (exactly four rows, one per exported table). */
    SELECT
        CONVERT(varchar(36), @export_run_id) AS export_run_id,
        CONVERT(nvarchar(128), @source_server) AS source_server,
        CONVERT(nvarchar(128), @source_database) AS source_database,
        CONVERT(varchar(33), @export_started_utc, 126) AS export_started_utc,
        @isolation_mode AS isolation_mode,
        v.table_name,
        CONVERT(varchar(30), v.row_count) AS row_count,
        v.scope
    FROM (VALUES
        (N'accgrp', @accgrp_count, N'ALL rows'),
        (N'policy', @policy_count, N'policytype IN (1,2)'),
        (N'loc', @loc_count, N'ALL rows'),
        (N'loccvg', @loccvg_count, N'peril IN (1,2)')
    ) AS v(table_name, row_count, scope);

    /* Resultset 2: schema.csv, actual dbo source columns from sys metadata. */
    SELECT
        CONVERT(nvarchar(128), t.name) AS table_name,
        CONVERT(nvarchar(128), c.name) AS column_name,
        CONVERT(nvarchar(128), ty.name) AS data_type,
        CONVERT(varchar(10), c.precision) AS [precision],
        CONVERT(varchar(10), c.scale) AS [scale],
        CONVERT(varchar(1), c.is_nullable) AS is_nullable
    FROM sys.tables AS t
    INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
    INNER JOIN sys.columns AS c ON c.object_id = t.object_id
    INNER JOIN sys.types AS ty ON ty.user_type_id = c.user_type_id
    WHERE s.name = N'dbo'
      AND t.name IN (N'accgrp', N'policy', N'loc', N'loccvg')
    ORDER BY t.name, c.column_id;

    /* Resultset 3: accgrp.csv. */
    SELECT
        CONVERT(varchar(36), @export_run_id) AS _export_run_id,
        CASE WHEN a.accgrpid IS NULL THEN N'\N' ELSE CONVERT(varchar(128), a.accgrpid, 3) END AS accgrpid,
        CASE WHEN a.userid1 IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), a.userid1) END AS userid1,
        CASE WHEN a.branchname IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), a.branchname) END AS branchname,
        CASE WHEN a.uwritrname IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), a.uwritrname) END AS uwritrname
    FROM dbo.accgrp AS a;

    /* Resultset 4: policy.csv; retain every qualifying policy, including orphans. */
    SELECT
        CONVERT(varchar(36), @export_run_id) AS _export_run_id,
        CASE WHEN p.policyid IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.policyid, 3) END AS policyid,
        CASE WHEN p.accgrpid IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.accgrpid, 3) END AS accgrpid,
        CASE WHEN p.policytype IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.policytype, 3) END AS policytype,
        CASE WHEN p.partof IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.partof, 3) END AS partof,
        CASE WHEN p.blanlimamt IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.blanlimamt, 3) END AS blanlimamt,
        CASE WHEN p.undcovamt IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.undcovamt, 3) END AS undcovamt,
        CASE WHEN p.blandedamt IS NULL THEN N'\N' ELSE CONVERT(varchar(128), p.blandedamt, 3) END AS blandedamt
    FROM dbo.policy AS p
    WHERE p.policytype IN (1, 2);

    /* Resultset 5: loc.csv; retain every location, including unmapped accounts. */
    SELECT
        CONVERT(varchar(36), @export_run_id) AS _export_run_id,
        CASE WHEN l.locid IS NULL THEN N'\N' ELSE CONVERT(varchar(128), l.locid, 3) END AS locid,
        CASE WHEN l.accgrpid IS NULL THEN N'\N' ELSE CONVERT(varchar(128), l.accgrpid, 3) END AS accgrpid,
        CASE WHEN l.locnum IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), l.locnum) END AS locnum,
        CASE WHEN l.addrmatch IS NULL THEN N'\N' ELSE CONVERT(varchar(128), l.addrmatch, 3) END AS addrmatch,
        CASE WHEN l.state IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), l.state) END AS state,
        CASE WHEN l.cntrycode IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), l.cntrycode) END AS cntrycode,
        CASE WHEN l.country IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), l.country) END AS country,
        CASE WHEN l.latitude IS NULL THEN N'\N' ELSE CONVERT(varchar(128), l.latitude, 3) END AS latitude,
        CASE WHEN l.longitude IS NULL THEN N'\N' ELSE CONVERT(varchar(128), l.longitude, 3) END AS longitude
    FROM dbo.loc AS l;

    /* Resultset 6: loccvg.csv; preserve duplicate source coverage rows. */
    SELECT
        CONVERT(varchar(36), @export_run_id) AS _export_run_id,
        CASE WHEN c.locid IS NULL THEN N'\N' ELSE CONVERT(varchar(128), c.locid, 3) END AS locid,
        CASE WHEN c.peril IS NULL THEN N'\N' ELSE CONVERT(varchar(128), c.peril, 3) END AS peril,
        CASE WHEN c.deductamt IS NULL THEN N'\N' ELSE CONVERT(varchar(128), c.deductamt, 3) END AS deductamt,
        CASE WHEN c.deductcur IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), c.deductcur) END AS deductcur,
        CASE WHEN c.valueamt IS NULL THEN N'\N' ELSE CONVERT(varchar(128), c.valueamt, 3) END AS valueamt,
        CASE WHEN c.valuecur IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), c.valuecur) END AS valuecur,
        CASE WHEN c.limitamt IS NULL THEN N'\N' ELSE CONVERT(varchar(128), c.limitamt, 3) END AS limitamt,
        CASE WHEN c.limitcur IS NULL THEN N'\N' ELSE CONVERT(nvarchar(max), c.limitcur) END AS limitcur
    FROM dbo.loccvg AS c
    WHERE c.peril IN (1, 2);

    COMMIT TRANSACTION;

    IF @changed_isolation = 1
    BEGIN
        IF @prior_isolation = 1 SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
        ELSE IF @prior_isolation = 2 SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
        ELSE IF @prior_isolation = 3 SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
        ELSE IF @prior_isolation = 4 SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
        ELSE IF @prior_isolation = 5 SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
    END;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    IF @changed_isolation = 1
    BEGIN
        IF @prior_isolation = 1 SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
        ELSE IF @prior_isolation = 2 SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
        ELSE IF @prior_isolation = 3 SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
        ELSE IF @prior_isolation = 4 SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
        ELSE IF @prior_isolation = 5 SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
    END;
    THROW;
END CATCH;
