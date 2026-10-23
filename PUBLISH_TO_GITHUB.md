# Publish SecPulse SIEM to GitHub (Windows PowerShell)

This guide assumes a fresh extraction of the clean source archive. Keep your previous audit folder and its local SQLite database as a backup; do not copy `.venv` or `backend/secpulse.db` into this repository.

## 1. Extract and test

Extract the release ZIP so the project root is:

```text
C:\Users\<your-user>\secpulse-siem-release\secpulse-siem
```

Then run the following in PowerShell:

```powershell
$project = "$env:USERPROFILE\secpulse-siem-release\secpulse-siem"
Set-Location $project
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -v
```

Expected: all 13 tests pass. The API integration test uses a temporary database. The regular application database is `backend\secpulse.db` and is ignored by Git.

## 2. Optional local application check

Start the API in the first PowerShell window:

```powershell
Set-Location $project
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. In a second PowerShell window, run the synthetic-event simulator:

```powershell
Set-Location $project
.\.venv\Scripts\python.exe .\simulator.py
```

Stop the simulator with `Ctrl+C`. If running the Docker dashboard instead, use `docker compose up --build` and open `http://127.0.0.1:3000`. A manual browser/Compose check remains important before claiming that deployment route is verified.

## 3. Review what will be published

From the repository root:

```powershell
git status --short
git check-ignore -v .venv/ backend/secpulse.db
git diff --check
```

Do not publish local databases, `.env` files, credentials, real logs, or personal information. If a real secret was ever committed, revoke/rotate it rather than just deleting the file.

## 4. Create the local Git history

If this clean folder is not already a Git repository:

```powershell
git init -b main
git add .
git status --short
git diff --cached --stat
git diff --cached
```

Review the staged files and diff. Verify that `.venv`, `.db`, `.sqlite`, `.env`, and other private/generated files are absent. Then create the first commit:

```powershell
git commit -m "Prepare SecPulse SIEM portfolio release"
git status
```

## 5. Create the GitHub repository and push

1. Sign in to GitHub and choose **New repository**.
2. Name it `secpulse-siem`.
3. Select Public only if you want the code visible to everyone.
4. Create it as an **empty repository**: do not pre-create a README, `.gitignore`, or license, because those are already in this local repository.
5. Copy the HTTPS clone URL shown by GitHub, then run (replace the URL with your actual repository URL):

```powershell
git remote add origin https://github.com/YOUR_USERNAME/secpulse-siem.git
git remote -v
git push -u origin main
```

Git may open a browser for authentication. Never paste a GitHub token into source code or commit it.

## 6. Verify the published repository

Open the new repository page and confirm the README renders and the expected source/tests/docs are present. The `Tests` workflow under `.github/workflows/tests.yml` should run on the push. If it fails, fix the issue and push another commit. Before describing the project as fully verified, also complete the manual dashboard, Docker, and persistence checks listed in `docs/testing.md`.
