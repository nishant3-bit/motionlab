# MotionLab v2 — Sports Biomechanics & Performance

A Streamlit application for multi-sport video review and first-pass 2D pose analysis.

## What's included
- Premium white / forest-green interface and landing page
- Athlete, coach and academy/team account entry
- Optional Supabase authentication and session-summary persistence
- Multi-sport movement selection: cricket/fast bowling, baseball/pitching, football, basketball, tennis, sprint/running and general movement
- Video upload and MediaPipe Pose landmark tracking
- Bilateral 2D projected knee, hip, ankle, elbow and shoulder angles
- Projected trunk lean and shoulder/hip line orientation
- Frame-by-frame CSV export, pose-frame gallery and metric timelines
- Manual event tagging for run-up, BFC, FFC, release and follow-through
- Contact-time calculations from manually confirmed frame numbers and source FPS
- Optional pixels-per-metre calibration for projected stride-distance estimates
- Athlete roster, session history, reports and team workspace pages
- Muted homepage video demo when `demo_bowling.mp4` exists in the repository root

## Important: measurement boundaries
This build does not infer every event automatically. Contact times are calculated from frame markers entered by the user. Stride distance is only estimated when a same-plane calibration is entered and relevant event frames are marked. Pose angles are 2D projections and depend on camera angle, occlusion, visibility and perspective.

A single ordinary video does NOT directly measure ground reaction force, joint moments, tissue loading, true 3D joint rotations, ball speed, injury risk, or medical readiness. Those require validated methods, suitable sensors or specialist equipment. Do not use this tool for diagnosis or return-to-play decisions.

## Local run (Mac)
Python 3.11 recommended:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## GitHub / Streamlit deployment
1. Replace `app.py`, `requirements.txt`, `README.md`, and `supabase_schema.sql` in the root of your `motionlab` GitHub repository.
2. Keep your `demo_bowling.mp4` in the same repository root. The app plays it muted on the homepage.
3. Streamlit Community Cloud should detect the GitHub commit and redeploy automatically.
4. Open your app URL and check the deployment logs if it fails.

## Enable real accounts
1. Create a Supabase project.
2. Open SQL Editor and run `supabase_schema.sql`.
3. In Streamlit Community Cloud → app → Settings → Secrets, add:
```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR-SUPABASE-ANON-KEY"
```
4. Save and reboot the app. Never put the service-role key in this app.

## Current release scope / not yet production-ready
- The demo is a deployable early product build, not a validated commercial biomechanics system.
- Athlete roster entries are browser-session scoped; coach invitations, academy-wide multi-user permissions, shared video storage, billing, audit logs and team analytics need further backend work.
- The homepage demo is transcoded without its audio stream using imageio-ffmpeg when the app prepares the landing page.
- Use only footage you own or are licensed to display. Do not imply athlete endorsement without permission.
- Before accepting real athlete data commercially, add consent, privacy policy, retention/deletion controls, access controls, monitoring, and independent sports-science validation.
