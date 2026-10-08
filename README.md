# Lovehands Care Services – Spot Check Portal

A Flask website for assessor logins, authenticated questionnaire submissions, and administrator review of spot checks. The fields and questions follow the supplied Spot Check Form. The original document's **Section One** has a heading but no questions; this project leaves that section empty rather than inventing requirements.

## Features
- Individual assessor and administrator accounts; hashed passwords and role-based access.
- Assessor-only creation (admins can also submit) with recorded responses, comments, visit details, action plan and typed signature.
- Admin dashboard, search/filter, per-record details, browser print-to-PDF and CSV export.
- Admin creation/deactivation of accounts. Login activity, views and exports recorded in an audit log.
- CSRF protection, secure cookie settings, basic throttling and security headers.

## Start locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# IMPORTANT: edit .env; for localhost use SESSION_COOKIE_SECURE=0
python -m flask --app app init-db
python -m flask --app app create-admin
python -m flask --app app run
```
Open http://127.0.0.1:5000 and sign in as the admin you created. Create assessor accounts under **Users**.

To create a production secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Put that value in `SECRET_KEY` in your hosting provider's secrets/environment configuration, **not** in a public repository.

## Hosting & production requirements
- Deploy on a Python hosting service with HTTPS, persistent private disk for SQLite, and secure backups. Example run command: `gunicorn --workers 2 --bind 0.0.0.0:$PORT app:app`.
- Run `flask --app app init-db` on first deployment and `flask --app app create-admin` securely via console/SSH. Do not create a public default account.
- Keep `SESSION_COOKIE_SECURE=1` when accessed over HTTPS. Use a stable strong `SECRET_KEY`. Set `TRUST_PROXY=1` only with a trusted single proxy and configured forwarded headers.
- **SQLite is intended for small-scale single-instance deployment.** For multiple app instances or high traffic, migrate to a managed PostgreSQL database with a migration plan and database-backed/shared login rate limiting.
- Do not deploy real service-user data without a data-protection review, encrypted backups, access-review process, documented retention/deletion policy, vendor data-processing terms, and appropriate UK GDPR security measures.
- Login rate limiting uses process memory; use Redis/shared storage for multi-worker production enforcement.
- No self-service password reset is provided: account recovery currently needs administrator maintenance through a secure server console. Add MFA and secure password reset before broad rollout.
- The typed signature is a declaration, **not** a cryptographically verified e-signature.
- Exported CSVs contain sensitive care information and require secure handling. Exercise caution opening CSV in spreadsheet software; protect against formula injection before allowing unrestricted external input.

## File map
`app.py`: backend and database models; `templates/`: pages; `static/style.css`: design; `instance/`: local database (keep private).
