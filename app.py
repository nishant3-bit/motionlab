import io, math, tempfile, os
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="MotionLab | Movement, understood.", page_icon="◒", layout="wide")

# ---------- Visual system ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#202923; --muted:#748078; --paper:#ffffff; --line:#e4e8df; --green:#315b46; --pale:#e8eee7; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
.stApp { background:var(--paper); }
.block-container { max-width:1400px; padding-top:2rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.045em; color:var(--ink); }
h1 { font-size:2.45rem !important; font-weight:800 !important; }
h2 { font-size:1.55rem !important; font-weight:750 !important; }
h3 { font-size:1.08rem !important; font-weight:700 !important; }
p, label { color:var(--ink); }
[data-testid="stSidebar"] { background:#202923; }
[data-testid="stSidebar"] * { color:#f4f5ef !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#c5d0c7 !important; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); padding:17px 18px; border-radius:14px; box-shadow:0 2px 8px rgba(30,45,35,.025); }
[data-testid="stMetricLabel"] { color:#748078 !important; font-size:.82rem; }
[data-testid="stMetricValue"] { color:#202923 !important; font-family:'Manrope',sans-serif; }
.stButton > button, .stDownloadButton > button { border-radius:9px; border:1px solid #315b46; background:#315b46; color:white; font-weight:600; min-height:2.65rem; }
.stButton > button:hover, .stDownloadButton > button:hover { background:#254735; border-color:#254735; color:white; }
.stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextArea textarea { border-radius:9px; }
[data-testid="stTabs"] button { font-weight:600; }
.ml-card { background:white; border:1px solid var(--line); border-radius:16px; padding:20px 22px; }
.ml-eyebrow { text-transform:uppercase; letter-spacing:.12em; font-size:.68rem; font-weight:700; color:#748078; }
.ml-muted { color:#748078; font-size:.9rem; }
.ml-pill { display:inline-block; background:#e8eee7; color:#315b46; border-radius:99px; padding:5px 10px; font-size:.75rem; font-weight:700; }
.ml-rule { border-top:1px solid var(--line); margin:18px 0; }
footer {visibility:hidden;}

/* MotionLab public-facing landing page */
.ml-site {background:#fff;color:#17231c}
.ml-nav {display:flex;align-items:center;justify-content:space-between;padding:10px 0 24px;border-bottom:1px solid #e9eee9;margin-bottom:46px}
.ml-brand {font-family:'Manrope',sans-serif;font-size:1.25rem;font-weight:800;letter-spacing:-.06em;color:#17231c}
.ml-brand span {color:#52765e}
.ml-navlinks {font-size:.86rem;color:#536258;letter-spacing:.01em}
.ml-kicker {font-size:.68rem;letter-spacing:.17em;text-transform:uppercase;font-weight:800;color:#52765e}
.ml-hero-title {font-family:'Manrope',sans-serif;font-size:clamp(2.8rem,6vw,5.7rem);line-height:.99;letter-spacing:-.075em;font-weight:800;color:#15221a;margin:18px 0 20px}
.ml-hero-copy {font-size:1.08rem;line-height:1.75;color:#66736a;max-width:560px}
.ml-hero-panel {background:#f2f5f0;border:1px solid #e4eae3;padding:14px;border-radius:4px}
.ml-photo-caption {font-size:.72rem;color:#68756c;letter-spacing:.04em;text-transform:uppercase;margin-top:9px}
.ml-section-title {font-family:'Manrope',sans-serif;font-size:2.1rem;letter-spacing:-.06em;font-weight:750;color:#17231c}
.ml-feature {border-top:1px solid #e5ebe5;padding:22px 0 18px}
.ml-feature-no {font-size:.72rem;color:#6b8a70;letter-spacing:.12em;font-weight:800}
.ml-feature-title {font-size:1.06rem;font-weight:750;color:#17231c;margin:7px 0}
.ml-feature-copy {font-size:.88rem;line-height:1.65;color:#718077}
.ml-cta {background:#193d2b;color:white;padding:32px 34px;border-radius:3px}
.ml-cta h2 {color:white!important}
.ml-small {font-size:.78rem;color:#748078}


/* MotionLab full product design system */
:root { --ml-forest:#244b36; --ml-leaf:#6f8d72; --ml-cream:#f7f8f5; --ml-ink:#17231c; }
[data-testid="stAppViewContainer"] { background:#fff; }
[data-testid="stSidebar"] { background:#17251d; border-right:1px solid #26392d; }
[data-testid="stSidebar"] > div:first-child { padding-top:1.5rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {font-size:1.55rem!important;letter-spacing:-.06em;color:#fff}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:9px 12px;border-radius:7px;margin:2px 0;font-size:.9rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:#26392d}
.block-container {max-width:1440px;padding-top:2.4rem;padding-bottom:4rem}
h1 {font-size:2.65rem!important;line-height:1.08!important;letter-spacing:-.065em!important}
h2 {font-size:1.55rem!important;letter-spacing:-.05em!important}
h3 {font-size:1.05rem!important;letter-spacing:-.025em!important}
.ml-page-intro {padding:4px 0 22px;border-bottom:1px solid #e8ece7;margin-bottom:26px}
.ml-page-intro .ml-eyebrow {color:#64816a}
.ml-panel {background:#fff;border:1px solid #e6ebe5;border-radius:12px;padding:22px;box-shadow:0 5px 20px rgba(20,40,25,.035)}
.ml-panel-soft {background:#f6f8f5;border:1px solid #e9eee8;border-radius:12px;padding:22px}
.ml-section-kicker {font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;color:#6d8871;font-weight:800}
[data-testid="stMetric"] {border-radius:10px!important;border:1px solid #e6ebe5!important;box-shadow:0 3px 12px rgba(20,40,25,.025)!important}
[data-testid="stDataFrame"] {border:1px solid #e6ebe5;border-radius:10px;overflow:hidden}
.stForm {border:1px solid #e7ece6;border-radius:12px;padding:20px;background:#fbfcfa}
.stButton>button,.stDownloadButton>button {border-radius:7px;min-height:2.8rem;letter-spacing:.005em}
hr {border-color:#e8ece7!important}

</style>
""", unsafe_allow_html=True)

# ---------- Optional Supabase ----------
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase()

def db_enabled():
    return supabase is not None

def set_profile(user, role, display_name):
    if not db_enabled(): return
    try:
        supabase.table("profiles").upsert({
            "id": user.id, "email": user.email, "display_name": display_name,
            "role": role, "updated_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Could not save profile: {e}")

def current_profile():
    if not db_enabled() or not st.session_state.get("user"): return None
    try:
        res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).maybe_single().execute()
        return res.data
    except Exception:
        return None




@st.cache_data(show_spinner=False)
def build_homepage_pose_demo(video_path):
    """Create a genuine MediaPipe pose-overlay version of the supplied demo clip."""
    import cv2
    import mediapipe as mp
    import tempfile, os
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("The demonstration video could not be opened.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = tmp.name
    tmp.close()
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    pose_api = mp.solutions.pose
    drawing = mp.solutions.drawing_utils
    detected = total = 0
    try:
        with pose_api.Pose(static_image_mode=False, model_complexity=1,
                           smooth_landmarks=True, min_detection_confidence=.5,
                           min_tracking_confidence=.5) as pose:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                total += 1
                if result.pose_landmarks:
                    detected += 1
                    drawing.draw_landmarks(
                        frame, result.pose_landmarks, pose_api.POSE_CONNECTIONS,
                        drawing.DrawingSpec(color=(80, 210, 145), thickness=3, circle_radius=3),
                        drawing.DrawingSpec(color=(40, 130, 85), thickness=2, circle_radius=2)
                    )
                cv2.putText(frame, "MOTIONLAB  |  2D POSE TRACKING", (18, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, .72, (245, 255, 248), 2, cv2.LINE_AA)
                writer.write(frame)
    finally:
        cap.release()
        writer.release()
    with open(output_path, "rb") as f:
        rendered = f.read()
    try:
        os.unlink(output_path)
    except OSError:
        pass
    return rendered, (100.0 * detected / total if total else 0.0), total


def landing_page():
    """Public marketing homepage shown before account sign-in."""
    st.markdown("""
    <div class="ml-nav">
      <div class="ml-brand">MOTION<span>LAB</span></div>
      <div class="ml-navlinks">PLATFORM &nbsp;&nbsp;&nbsp; BIOMECHANICS &nbsp;&nbsp;&nbsp; PERFORMANCE &nbsp;&nbsp;&nbsp; FOR COACHES</div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
    with left:
        st.markdown('<div class="ml-kicker">SPORTS BIOMECHANICS · PERFORMANCE ANALYSIS</div>', unsafe_allow_html=True)
        st.markdown('<div class="ml-hero-title">Understand<br>movement.<br><span style="color:#52765e">Build performance.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="ml-hero-copy">Video-based movement analysis for athletes, coaches and performance programmes. Review technique, examine movement patterns and make better-informed training decisions.</div>', unsafe_allow_html=True)
        st.write("")
        cta1, cta2 = st.columns([1,1])
        with cta1:
            if st.button("Explore the platform  →", use_container_width=True, key="landing_explore"):
                st.session_state["show_auth"] = True
                st.session_state["auth_mode"] = "Create account"
                st.rerun()
        with cta2:
            if st.button("Sign in", use_container_width=True, key="landing_signin"):
                st.session_state["show_auth"] = True
                st.session_state["auth_mode"] = "Sign in"
                st.rerun()
        st.markdown('<div class="ml-small" style="margin-top:14px">BUILT FOR ATHLETES · COACHES · ACADEMIES · TEAMS</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="ml-hero-panel">', unsafe_allow_html=True)
        st.image("https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=1500&q=85",
                 use_container_width=True, caption="Performance happens in the details.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="ml-photo-caption">MOVEMENT REVIEW · TECHNIQUE · PERFORMANCE DEVELOPMENT</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:55px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="ml-kicker">THE MOTIONLAB PLATFORM</div>', unsafe_allow_html=True)
    st.markdown('<div class="ml-section-title">From video to a clearer view of movement.</div>', unsafe_allow_html=True)
    st.markdown('<p class="ml-hero-copy" style="font-size:.98rem">A practical workspace that brings video review and accessible biomechanical measurements into one place.</p>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3, gap="large")
    features = [
        ("01", "Biomechanical review", "Inspect 2D joint-angle estimates, body positions and movement patterns across sampled video frames."),
        ("02", "Video-based analysis", "Upload a movement clip, review pose tracking and follow selected measurements over time."),
        ("03", "Performance development", "Keep athlete sessions organised and use consistent video review to inform coaching decisions.")
    ]
    for col, item in zip([f1,f2,f3], features):
        with col:
            st.markdown(f'<div class="ml-feature"><div class="ml-feature-no">{item[0]}</div><div class="ml-feature-title">{item[1]}</div><div class="ml-feature-copy">{item[2]}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="ml-kicker">MOTIONLAB IN ACTION</div>', unsafe_allow_html=True)
    st.markdown('<div class="ml-section-title">From bowling footage to visible movement patterns.</div>', unsafe_allow_html=True)
    st.markdown('<p class="ml-hero-copy" style="font-size:.98rem">Explore the supplied bowling demonstration in its original form and with MotionLab’s 2D pose-tracking overlay.</p>', unsafe_allow_html=True)

    demo_path = os.path.join(os.path.dirname(__file__), "demo_bowling.mp4")
    if os.path.exists(demo_path):
        raw_col, tracked_col = st.columns(2, gap="large")
        with raw_col:
            st.markdown("**01 / ORIGINAL FOOTAGE**")
            with open(demo_path, "rb") as video_file:
                st.video(video_file.read(), autoplay=True, loop=True, muted=True)
            st.caption("Original supplied bowling footage.")
        with tracked_col:
            st.markdown("**02 / 2D POSE-TRACKING OVERLAY**")
            try:
                with st.spinner("Preparing the real pose-tracking preview…"):
                    overlay_bytes, detection_rate, frame_count = build_homepage_pose_demo(demo_path)
                st.video(overlay_bytes, autoplay=True, loop=True, muted=True)
                st.caption(f"MediaPipe pose landmarks rendered across {frame_count} frames · detection on {detection_rate:.0f}% of frames.")
            except Exception as exc:
                st.warning("The original footage is available. The pose-overlay preview could not be generated in this deployment. The full analysis workspace remains available after sign-in.")
                st.caption(f"Technical detail: {exc}")
        st.markdown('<div class="ml-small">The overlay is generated by MotionLab’s current 2D pose-estimation pipeline. It is an image-based visualisation, not a 3D biomechanical assessment or a measurement of force, joint loading or ball-release speed.</div>', unsafe_allow_html=True)
    else:
        st.warning("The demonstration video asset is missing. Add assets/demo_bowling.mp4 to the GitHub repository to display it here.")
    st.markdown("<div style='height:38px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="ml-cta">
      <div class="ml-kicker" style="color:#c1d5c4">FOR THE PEOPLE WHO DEVELOP PERFORMANCE</div>
      <h2 style="font-size:2rem;letter-spacing:-.05em;margin:10px 0">Make every review more purposeful.</h2>
      <p style="color:#e1e9e2;max-width:650px;line-height:1.7">Bring movement footage into a considered workspace for athletes and coaches. Start with a video, examine the details and build a more consistent review process.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Enter MotionLab  →", use_container_width=True, key="landing_bottom_enter"):
        st.session_state["show_auth"] = True
        st.session_state["auth_mode"] = "Create account"
        st.rerun()
    st.markdown("<div style='border-top:1px solid #e5ebe5;margin-top:44px;padding-top:18px;color:#7c887f;font-size:.75rem'>MOTIONLAB · SPORTS BIOMECHANICS & PERFORMANCE ANALYSIS</div>", unsafe_allow_html=True)


def auth_screen():
    if st.session_state.get("show_auth") and st.button("← Back to MotionLab homepage"):
        st.session_state["show_auth"] = False
        st.rerun()
    st.markdown("<div style='max-width:560px;margin:5vh auto 0'>", unsafe_allow_html=True)
    st.markdown("<div class='ml-eyebrow'>SPORTS SCIENCE, MADE PRACTICAL</div>", unsafe_allow_html=True)
    st.title("MotionLab")
    st.markdown("### Better movement starts with better observation.")
    st.write("A considered workspace for athletes and coaches to review movement, track sessions and make training decisions with more context.")
    if not db_enabled():
        st.warning("Account sign-in is not connected yet. Add your Supabase keys during deployment to enable real registration and persistent accounts.")
        st.info("You can still explore the analysis workspace in local preview mode. Preview data is stored only for this browser session.")
        with st.form("preview_login"):
            name = st.text_input("Your name", "Demo user")
            role = st.selectbox("I am a", ["Athlete", "Coach"])
            go = st.form_submit_button("Enter preview workspace", use_container_width=True)
        if go:
            st.session_state.user = type("PreviewUser", (), {"id":"preview", "email":"preview@motionlab.local"})()
            st.session_state.role = role.lower()
            st.session_state.display_name = name
            st.session_state.preview = True
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Sign in", "Create account"])
        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign in", use_container_width=True)
            if submit:
                try:
                    res = supabase.auth.sign_in_with_password({"email":email, "password":password})
                    st.session_state.user = res.user
                    st.session_state.preview = False
                    prof = current_profile()
                    st.session_state.role = (prof or {}).get("role", "athlete")
                    st.session_state.display_name = (prof or {}).get("display_name", email.split("@")[0])
                    st.rerun()
                except Exception as e: st.error(f"Sign-in failed: {e}")
        with tab2:
            with st.form("signup"):
                name = st.text_input("Full name")
                email = st.text_input("Email address")
                password = st.text_input("Password (at least 8 characters)", type="password")
                role = st.selectbox("Create account as", ["Athlete", "Coach"])
                submit = st.form_submit_button("Create account", use_container_width=True)
            if submit:
                if len(password) < 8: st.error("Please use a password with at least 8 characters.")
                elif not name.strip() or not email.strip(): st.error("Please complete all fields.")
                else:
                    try:
                        res = supabase.auth.sign_up({"email":email, "password":password,
                            "options":{"data":{"display_name":name,"role":role.lower()}}})
                        if res.user:
                            set_profile(res.user, role.lower(), name.strip())
                            st.success("Account created. If email confirmation is enabled, verify your email before signing in.")
                    except Exception as e: st.error(f"Registration failed: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

if "user" not in st.session_state:
    if st.session_state.get("show_auth"):
        auth_screen()
    else:
        landing_page()
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("# ◒ MotionLab")
    st.markdown("<div style='font-size:.62rem;letter-spacing:.16em;color:#9eb3a2;font-weight:800;margin-top:-8px'>BIOMECHANICS / PERFORMANCE</div>", unsafe_allow_html=True)
    st.markdown("---")
    role = st.session_state.get("role","athlete")
    name = st.session_state.get("display_name","Member")
    st.markdown(f"**{name}**")
    st.caption(role.title() + " workspace")
    page = st.radio("WORKSPACE", ["Overview", "Analyse movement", "Athletes", "Session history", "Account"], label_visibility="visible")
    st.markdown("---")
    st.caption("Built for thoughtful coaching.")
    if st.button("Sign out", use_container_width=True):
        if db_enabled():
            try: supabase.auth.sign_out()
            except Exception: pass
        for k in ["user","role","display_name","preview","last_result"]:
            st.session_state.pop(k, None)
        st.rerun()

# ---------- Data access ----------
def save_session(row):
    st.session_state.setdefault("sessions", [])
    st.session_state.sessions.insert(0, row)
    if db_enabled() and not st.session_state.get("preview"):
        try:
            supabase.table("analysis_sessions").insert({
                "user_id": st.session_state.user.id,
                "athlete_name": row["athlete"],
                "sport": row["sport"], "movement": row["movement"],
                "video_name": row["video"], "analysis_date": row["date"],
                "frames_analysed": row["frames"], "detection_rate": row["detection_rate"],
                "summary": row["summary"]
            }).execute()
        except Exception as e:
            st.warning(f"Analysis completed, but cloud session history could not be saved: {e}")

def load_sessions():
    rows = list(st.session_state.get("sessions", []))
    if db_enabled() and not st.session_state.get("preview"):
        try:
            res = supabase.table("analysis_sessions").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).limit(100).execute()
            rows = [{
                "athlete":r.get("athlete_name",""), "sport":r.get("sport",""),
                "movement":r.get("movement",""), "video":r.get("video_name",""),
                "date":r.get("analysis_date",""), "frames":r.get("frames_analysed",0),
                "detection_rate":r.get("detection_rate",0), "summary":r.get("summary",{})
            } for r in (res.data or [])]
        except Exception:
            pass
    return rows

def page_header(kicker, title, subtitle):
    st.markdown(
        f"<div class='ml-page-intro'><div class='ml-eyebrow'>{kicker}</div>"
        f"<h1 style='margin:.55rem 0 .35rem'>{title}</h1>"
        f"<div class='ml-muted'>{subtitle}</div></div>",
        unsafe_allow_html=True
    )

# ---------- Pages ----------
if page == "Overview":
    sessions = load_sessions()
    total = len(sessions)
    athletes = len(set(x.get("athlete","") for x in sessions if x.get("athlete")))
    avg = np.mean([x.get("detection_rate",0) for x in sessions]) if sessions else 0
    page_header("PERFORMANCE WORKSPACE", f"Welcome back, {name.split()[0]}.", "Your workspace for reviewing movement, tracking sessions and developing performance.")
    a,b,c = st.columns(3)
    a.metric("Analysis sessions", total)
    b.metric("Athletes reviewed", athletes)
    c.metric("Average pose detection", f"{avg:.0f}%" if sessions else "—")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    left,right = st.columns([1.35,1], gap="large")
    with left:
        st.markdown("<div class='ml-panel'><div class='ml-section-kicker'>START A REVIEW</div><h2 style='margin:.6rem 0'>Turn footage into a movement review.</h2><p class='ml-muted'>Bring a training clip into MotionLab. Track visible body landmarks, inspect 2D joint-angle estimates and review how selected measurements change through the action.</p></div>", unsafe_allow_html=True)
        if st.button("Open movement analysis  →", use_container_width=True):
            st.session_state.nav_override="Analyse movement"; st.rerun()
    with right:
        st.markdown("<div class='ml-panel-soft'><div class='ml-section-kicker'>BUILT AROUND THE DETAILS</div><h3>Observe. Measure. Interpret.</h3><p class='ml-muted'>Use consistent camera positions, clear event labels and coach expertise. Measurements are only as reliable as the footage and calibration behind them.</p></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div><div class='ml-panel-soft'><div class='ml-section-kicker'>YOUR WORKSPACE</div><h3>"+("Cloud connected" if db_enabled() and not st.session_state.get("preview") else "Local preview")+"</h3><p class='ml-muted'>"+("Your account is connected to cloud session storage." if db_enabled() else "Connect Supabase to enable persistent cloud records across devices.")+"</p></div>", unsafe_allow_html=True)
    st.markdown("## Recent analysis")
    if sessions:
        table = pd.DataFrame([{"Date":x["date"],"Athlete":x["athlete"],"Sport":x["sport"],"Movement":x["movement"],"Pose detection":f'{x["detection_rate"]:.0f}%'} for x in sessions[:8]])
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        st.markdown("<div class='ml-panel'><h3>Your first analysis starts here.</h3><p class='ml-muted'>Upload a short, well-lit clip with the athlete fully visible. A side-on camera view is useful for many movement reviews.</p></div>", unsafe_allow_html=True)

elif page == "Analyse movement":
    page_header("BIOMECHANICAL VIDEO REVIEW", "Analyse movement.", "Upload a clip to review visible body positions, 2D joint-angle estimates and movement patterns. Use calibrated footage and manual event labels for timing metrics.")
    with st.form("analysis_setup"):
        c1,c2,c3 = st.columns(3)
        athlete = c1.text_input("Athlete name or ID", value="")
        sport = c2.selectbox("Sport", ["Cricket / Fast bowling","Baseball / Pitching","Football","Basketball","Tennis","Sprint / Running","General movement"])
        movement = c3.selectbox("Movement", ["Whole action","Bowling / pitching","Sprint / running","Jump / landing","Squat","Lunge","Overhead / serving"])
        d1,d2,d3 = st.columns(3)
        view = d1.selectbox("Camera view", ["Side view","Front view","Rear view","Oblique / unsure"])
        sample_step = d2.select_slider("Frame sampling", options=[2,3,4,5,6,8,10], value=4, help="Analyse every Nth frame.")
        max_frames = d3.select_slider("Maximum analysed frames", options=[150,300,450,600,900,1200], value=600)
        uploaded = st.file_uploader("Choose video", type=["mp4","mov","avi","m4v"])
        run = st.form_submit_button("Run biomechanics analysis  →", use_container_width=True)
    if run:
        if not athlete.strip(): st.error("Add an athlete name or ID before running the analysis.")
        elif uploaded is None: st.error("Upload a video first.")
        else:
            try:
                import cv2, mediapipe as mp
                video = uploaded.getvalue()
                suffix = "." + uploaded.name.split(".")[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(video); path = tmp.name
                cap = cv2.VideoCapture(path)
                if not cap.isOpened(): raise ValueError("Could not read this video. Try an MP4 encoded with H.264.")
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                duration = total_frames / fps if fps else 0
                pose_model = mp.solutions.pose
                drawing = mp.solutions.drawing_utils
                records, snapshots = [], []
                idx, count = 0, 0
                progress = st.progress(0, text="Preparing analysis…")
                pose = pose_model.Pose(static_image_mode=False, model_complexity=1, smooth_landmarks=True, min_detection_confidence=.5, min_tracking_confidence=.5)
                def point(lm, i, w, h):
                    p=lm[i]
                    return (p.x*w,p.y*h) if getattr(p,"visibility",1) >= .35 else None
                def angle(a,b,c):
                    if any(p is None for p in (a,b,c)): return np.nan
                    v1=np.array(a)-np.array(b); v2=np.array(c)-np.array(b)
                    den=np.linalg.norm(v1)*np.linalg.norm(v2)
                    if den < 1e-8: return np.nan
                    return float(np.degrees(np.arccos(np.clip(np.dot(v1,v2)/den,-1,1))))
                while cap.isOpened() and count < max_frames:
                    ok, frame = cap.read()
                    if not ok: break
                    if idx % sample_step == 0:
                        h,w=frame.shape[:2]
                        result=pose.process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
                        row={"frame":idx,"time_s":idx/fps,"pose_detected":bool(result.pose_landmarks)}
                        if result.pose_landmarks:
                            lm=result.pose_landmarks.landmark
                            P=pose_model.PoseLandmark
                            row["left_knee_angle_deg"]=angle(point(lm,P.LEFT_HIP.value,w,h),point(lm,P.LEFT_KNEE.value,w,h),point(lm,P.LEFT_ANKLE.value,w,h))
                            row["right_knee_angle_deg"]=angle(point(lm,P.RIGHT_HIP.value,w,h),point(lm,P.RIGHT_KNEE.value,w,h),point(lm,P.RIGHT_ANKLE.value,w,h))
                            row["left_elbow_angle_deg"]=angle(point(lm,P.LEFT_SHOULDER.value,w,h),point(lm,P.LEFT_ELBOW.value,w,h),point(lm,P.LEFT_WRIST.value,w,h))
                            row["right_elbow_angle_deg"]=angle(point(lm,P.RIGHT_SHOULDER.value,w,h),point(lm,P.RIGHT_ELBOW.value,w,h),point(lm,P.RIGHT_WRIST.value,w,h))
                            row["left_hip_angle_deg"]=angle(point(lm,P.LEFT_SHOULDER.value,w,h),point(lm,P.LEFT_HIP.value,w,h),point(lm,P.LEFT_KNEE.value,w,h))
                            row["right_hip_angle_deg"]=angle(point(lm,P.RIGHT_SHOULDER.value,w,h),point(lm,P.RIGHT_HIP.value,w,h),point(lm,P.RIGHT_KNEE.value,w,h))
                            ls,rs=point(lm,P.LEFT_SHOULDER.value,w,h),point(lm,P.RIGHT_SHOULDER.value,w,h)
                            lh,rh=point(lm,P.LEFT_HIP.value,w,h),point(lm,P.RIGHT_HIP.value,w,h)
                            if all(p is not None for p in (ls,rs,lh,rh)):
                                sm=(np.array(ls)+np.array(rs))/2; hm=(np.array(lh)+np.array(rh))/2; v=sm-hm
                                row["trunk_inclination_deg"]=float(np.degrees(np.arctan2(abs(v[0]),abs(v[1]))))
                            row["mean_landmark_visibility"]=float(np.mean([x.visibility for x in lm]))
                            annotated=frame.copy()
                            drawing.draw_landmarks(annotated,result.pose_landmarks,pose_model.POSE_CONNECTIONS)
                            cv2.putText(annotated,f'{idx/fps:.2f}s',(18,30),cv2.FONT_HERSHEY_SIMPLEX,.65,(50,170,110),2,cv2.LINE_AA)
                            if len(snapshots)<8: snapshots.append(cv2.cvtColor(annotated,cv2.COLOR_BGR2RGB))
                        else: row["mean_landmark_visibility"]=0.0
                        records.append(row); count += 1
                        if total_frames: progress.progress(min(idx/total_frames,1.0),text=f"Reviewing frame {idx} of {total_frames}")
                    idx += 1
                pose.close(); cap.release()
                try:
                    import os; os.unlink(path)
                except Exception: pass
                progress.empty()
                df=pd.DataFrame(records)
                if df.empty: raise ValueError("No frames could be analysed.")
                rate=float(df.pose_detected.mean()*100)
                st.session_state.last_result={"df":df,"athlete":athlete,"sport":sport,"movement":movement,"view":view,"video":uploaded.name,"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"frames":len(df),"detection_rate":rate,"duration":duration,"snapshots":snapshots}
                metrics=[c for c in df.columns if c.endswith("_deg")]
                summary={}
                for col in metrics:
                    vals=df[col].dropna()
                    if len(vals): summary[col]={"mean":round(float(vals.mean()),1),"min":round(float(vals.min()),1),"max":round(float(vals.max()),1)}
                save_session({"athlete":athlete,"sport":sport,"movement":movement,"video":uploaded.name,"date":st.session_state.last_result["date"],"frames":len(df),"detection_rate":rate,"summary":summary})
                st.success("Analysis complete. Review the measurements below.")
            except Exception as e:
                st.error(f"Analysis could not be completed: {e}")
    result=st.session_state.get("last_result")
    if result:
        st.markdown("---")
        st.markdown("## Analysis results")
        x1,x2,x3,x4=st.columns(4)
        x1.metric("Duration",f'{result["duration"]:.1f} s')
        x2.metric("Frames reviewed",result["frames"])
        x3.metric("Pose detection",f'{result["detection_rate"]:.1f}%')
        x4.metric("Camera view",result["view"])
        df=result["df"]
        angle_cols=[c for c in df.columns if c.endswith("_deg") and df[c].notna().sum()>1]
        if angle_cols:
            selected=st.selectbox("Measurement timeline",angle_cols,format_func=lambda s:s.replace("_deg","").replace("_"," ").title())
            fig=px.line(df.dropna(subset=[selected]),x="time_s",y=selected,markers=True,labels={"time_s":"Time (seconds)",selected:"2D angle estimate (degrees)"})
            fig.update_layout(template="plotly_white",height=350,margin=dict(l=10,r=10,t=20,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="white")
            st.plotly_chart(fig,use_container_width=True)
            vals=df[selected].dropna()
            m1,m2,m3=st.columns(3); m1.metric("Mean",f"{vals.mean():.1f}°"); m2.metric("Minimum",f"{vals.min():.1f}°"); m3.metric("Maximum",f"{vals.max():.1f}°")
        if result["snapshots"]:
            st.markdown("### Selected pose frames")
            cols=st.columns(min(4,len(result["snapshots"])))
            for i,im in enumerate(result["snapshots"]):
                cols[i%len(cols)].image(im,use_container_width=True,caption=f"Sample {i+1}")
        st.download_button("Download frame-by-frame CSV",df.to_csv(index=False).encode(),file_name="motionlab_analysis.csv",mime="text/csv")
        st.caption("Interpretation: these are 2D projected estimates from a single camera view. This release does not automatically identify sport-specific events such as back-foot contact, front-foot contact, take-off or release, and therefore does not claim validated GCT, stride length or force measurements. Those require calibrated video, validated event detection or manual event annotation.")

elif page == "Athletes":
    page_header("ATHLETE DIRECTORY", "People behind the performance.", "A considered space for coaches to organise the athletes whose movement they review.")
    if role == "coach":
        with st.form("athlete_add"):
            st.markdown("### Add an athlete")
            a,b,c = st.columns(3)
            athlete_name = a.text_input("Athlete name")
            athlete_sport = b.selectbox("Primary sport",["Cricket","Baseball","Football","Basketball","Tennis","Athletics","Other"])
            athlete_level = c.selectbox("Level",["Development","Club","Academy","University","Professional","Recreational"])
            notes = st.text_input("Coaching notes (optional)")
            add = st.form_submit_button("Add athlete  +", use_container_width=True)
        if add and athlete_name.strip():
            st.session_state.setdefault("athlete_records",[])
            st.session_state.athlete_records.append({"Name":athlete_name,"Sport":athlete_sport,"Level":athlete_level,"Notes":notes})
            st.success("Athlete added to this browser session.")
    records=st.session_state.get("athlete_records",[])
    if records:
        st.markdown("## Athlete roster")
        st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True)
    else:
        st.markdown("<div class='ml-panel'><div class='ml-section-kicker'>ROSTER</div><h2 style='margin:.6rem 0'>Build your athlete directory.</h2><p class='ml-muted'>Add athlete profiles to organise sport, development level and coaching notes. Persistent team management and shared coach-athlete access are planned for a later release.</p></div>",unsafe_allow_html=True)
    if role=="athlete":
        st.info("Your athlete workspace is ready. Coach invitations and shared team spaces are not enabled in this release.")

elif page == "Session history":
    page_header("ANALYSIS ARCHIVE", "Every review, in one place.", "Return to previous movement reviews and export your session log.")
    sessions=load_sessions()
    if sessions:
        table=pd.DataFrame([{"Date":x["date"],"Athlete":x["athlete"],"Sport":x["sport"],"Movement":x["movement"],"Video":x["video"],"Frames":x["frames"],"Pose detection":f'{x["detection_rate"]:.1f}%'} for x in sessions])
        c1,c2=st.columns([1,3])
        c1.metric("Saved sessions",len(sessions))
        c2.download_button("Export session history  ↓",table.to_csv(index=False).encode(),file_name="motionlab_session_history.csv",mime="text/csv",use_container_width=True)
        st.markdown("## Session log")
        st.dataframe(table,use_container_width=True,hide_index=True)
    else:
        st.markdown("<div class='ml-panel'><div class='ml-section-kicker'>YOUR ARCHIVE</div><h2 style='margin:.6rem 0'>Your session history will build here.</h2><p class='ml-muted'>Once you complete an analysis, its summary will appear in this archive.</p></div>",unsafe_allow_html=True)

elif page == "Account":
    page_header("ACCOUNT & PREFERENCES", "Your MotionLab account.", "Profile and workspace information.")
    c1,c2=st.columns(2,gap="large")
    with c1:
        st.markdown("<div class='ml-panel'><div class='ml-section-kicker'>PROFILE</div><h2 style='margin:.7rem 0'>"+str(name)+"</h2><p class='ml-muted'>"+str(st.session_state.user.email)+"</p><span class='ml-pill'>"+role.title()+"</span></div>",unsafe_allow_html=True)
    with c2:
        connected = db_enabled() and not st.session_state.get("preview")
        st.markdown("<div class='ml-panel'><div class='ml-section-kicker'>WORKSPACE STATUS</div><h2 style='margin:.7rem 0'>"+("Cloud connected" if connected else "Preview mode")+"</h2><p class='ml-muted'>"+("Supabase authentication and cloud session storage are configured." if connected else "Connect Supabase to enable persistent accounts and session history across devices.")+"</p></div>",unsafe_allow_html=True)
    st.markdown("## About MotionLab")
    st.markdown("<div class='ml-panel-soft'><p class='ml-muted'>MotionLab is a sports biomechanics and performance-analysis workspace. The current release provides video-based 2D pose estimation and projected joint-angle measurements. It does not directly measure ground-contact forces, 3D joint rotations, joint moments, tissue loading or injury risk.</p></div>",unsafe_allow_html=True)

st.markdown("<div style='margin-top:42px;border-top:1px solid #e4e8df;padding-top:16px;color:#879188;font-size:.78rem'>MOTIONLAB · Movement, understood. &nbsp; This product supports coaching review and does not replace qualified clinical or biomechanical assessment.</div>",unsafe_allow_html=True)
