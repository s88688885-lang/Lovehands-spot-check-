LOVEHANDS SPOT CHECK: NAVIGATION DROPDOWN UPDATE

This is a small overlay update for the existing Lovehands two-form website.
It is NOT a full replacement website package.

1. Open the EXISTING GitHub repository connected to the live Render service.
2. Replace only templates/base.html with the base.html in this package.
3. Add the new file static/nav-dropdown.css from this package.
4. Commit changes and deploy normally.

The new navigation shows:
New Assessment ▾ -> Spot Check, Medication Assessment
Records ▾ -> Spot Check Records, Medication Records

The two questionnaires, admin setup/login, passwords, existing routes, database,
logo file and user records are unaffected. Do not change any environment variables.
The existing application must already include routes named new_medication and
medication_records (as in the prior two-form website package).

Note: No login credentials or data are included in this update.
