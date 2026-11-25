# MotionLab — first deployable web release

A Streamlit web app for athlete and coach accounts, video-based 2D pose analysis, session history and CSV exports.

## Important scope notes
- This release includes open athlete/coach registration when Supabase is configured.
- Supabase stores user profiles and analysis-session metadata. It does **not** store uploaded video files.
- Athlete directory entries are currently session-local. Coach-to-athlete invitations, shared team workspaces, billing, video cloud storage and 3D biomechanics are not included yet.
- The analysis is 2D, camera-dependent and intended for coaching review. It does not calculate force, joint moments, tissue loading, injury risk or medical clearance.
- The app is an early release and must be tested with representative videos before commercial use.

## Deploy
1. Create a free project at https://supabase.com/.
2. In Supabase, open **SQL Editor**, create a query, paste `supabase_schema.sql`, and run it.
3. In Supabase Project Settings → API, copy the Project URL and `anon` public key.
4. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `supabase_schema.sql`.
5. Open https://share.streamlit.io/, sign in with GitHub, choose the repository, branch `main`, main file `app.py`.
6. In Streamlit app settings → **Secrets**, add:

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_PUBLIC_KEY"
```

7. Choose Python 3.11 if the deployment settings offer a Python version selector, then deploy.
8. Open the public Streamlit URL and test registration, sign-in, video analysis and session history.

## Local run (Mac)
Python 3.11 recommended:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Before real customers
Use a private test group first. Add a privacy notice and consent flow before processing identifiable athlete footage. Set upload limits, retention/deletion controls, monitoring, backups and a support contact. Do not use the current app for clinical decisions.
