# Lovehands: protect accounts and records on Render

## Before deploying this update

1. **Do not create a new Render database.** Open Render -> the EXISTING Lovehands web service -> Environment. Confirm `DATABASE_URL` points to the ORIGINAL persistent Render PostgreSQL database containing your users and records. Do not disclose this secret publicly.
2. In the same Environment page confirm `SECRET_KEY` is present and is a stable random string of at least 32 characters. **Do not replace it if it is already set and valid**: rotating it logs users out. Never regenerate it at startup.
3. Take a verified PostgreSQL backup/snapshot first (check your Render database plan for backup availability; otherwise use `pg_dump` from a secure trusted machine). Keep the backup secure and confirm that it can be restored. Do not place care data or database URLs in GitHub.
4. Check your PostgreSQL database plan, storage capacity and retention settings. For a business-critical care system, use a persistent database with automated backup and recovery testing.
5. Deploy to the EXISTING web service rather than creating a second Render service/Blueprint with a new database. Leave `DATABASE_URL` and `SECRET_KEY` unchanged.
6. Test that existing admin and assessor accounts log in, then confirm sample records and draft counts. Restart/redeploy and check they are still present.

## New startup safeguards

- On Render, an absent or non-PostgreSQL `DATABASE_URL` causes a **startup error**, not a new SQLite database.
- On Render, an absent/short `SECRET_KEY` causes a **startup error**, not random session signing keys. Retain your existing secret key when it already meets the requirement.
- Database connections are checked before use (`pool_pre_ping`), helping recovery from transient PostgreSQL disconnects.
- An `installation_state` marker is added for installations after their admin account exists. If a previously initialized database no longer has an admin, the first-time setup route refuses registration; it does not silently create another administrator. It cannot detect switching to an entirely different valid PostgreSQL database, so database configuration and backups still matter.
- The application's 5-minute inactivity logout still applies by design. Logging out is **not** record deletion.

## If users or records appear missing again

Do **not** recreate the administrator or make new assessments until checking whether the application is connected to the original database. In Render, inspect service logs around the restart, check `DATABASE_URL` configuration without revealing its value, and verify PostgreSQL availability and data counts using authorised database administration. Restore a backup only after identifying the correct database and the recovery point, ideally through an experienced administrator. A code update cannot reconstruct data already lost from an ephemeral SQLite filesystem.

## Recovery gaps that still need operational controls

This patch prevents two major misconfigurations, but **does not itself make backups** or guarantee recovery from database deletion/corruption, account deletion, a provider outage or a mistaken database switch to another valid PostgreSQL instance. Establish automated backups, periodic restore testing, retention safeguards, database monitoring, and appropriate UK GDPR controls before relying on this service for care records.
