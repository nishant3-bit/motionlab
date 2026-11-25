import io, math, tempfile
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
:root { --ink:#202923; --muted:#748078; --paper:#f5f6f1; --line:#e4e8df; --green:#315b46; --pale:#e8eee7; }
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

def auth_screen():
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
    auth_screen()
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("# ◒ MotionLab")
    st.caption("MOVEMENT, UNDERSTOOD.")
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
    st.markdown(f"<div class='ml-eyebrow'>{kicker}</div>", unsafe_allow_html=True)
    st.title(title)
    st.markdown(f"<p class='ml-muted'>{subtitle}</p>", unsafe_allow_html=True)

# ---------- Pages ----------
if page == "Overview":
    page_header("YOUR PERFORMANCE WORKSPACE", f"Good to see you, {name.split()[0]}.", "A clear place to review movement and keep the important details in view.")
    sessions = load_sessions()
    total = len(sessions)
    athletes = len(set(x.get("athlete","") for x in sessions if x.get("athlete")))
    avg = np.mean([x.get("detection_rate",0) for x in sessions]) if sessions else 0
    a,b,c = st.columns(3)
    a.metric("Analysed sessions", total)
    b.metric("Athletes in your records", athletes)
    c.metric("Average pose detection", f"{avg:.0f}%" if sessions else "—")
    st.markdown(" ")
    left,right = st.columns([1.35,1])
    with left:
        st.markdown("<div class='ml-card'><div class='ml-eyebrow'>START HERE</div><h3>Review a movement</h3><p class='ml-muted'>Upload a clip, choose the movement context and inspect the 2D measurements alongside the video.</p></div>", unsafe_allow_html=True)
        if st.button("Open movement analysis →", use_container_width=True): st.session_state.nav_override="Analyse movement"; st.rerun()
    with right:
        st.markdown("<div class='ml-card'><div class='ml-eyebrow'>A NOTE ON THE DATA</div><h3>Evidence before conclusions</h3><p class='ml-muted'>MotionLab reports image-based estimates. Use consistent camera positions and coach judgement when interpreting changes.</p></div>", unsafe_allow_html=True)
    st.markdown("## Recent sessions")
    if sessions:
        st.dataframe(pd.DataFrame([{"Date":x["date"],"Athlete":x["athlete"],"Sport":x["sport"],"Movement":x["movement"],"Detection":f'{x["detection_rate"]:.0f}%'} for x in sessions[:8]]), use_container_width=True, hide_index=True)
    else:
        st.markdown("<div class='ml-card'><h3>No sessions yet</h3><p class='ml-muted'>Your first analysis will appear here. Start with a short, well-lit side-view clip.</p></div>", unsafe_allow_html=True)

elif page == "Analyse movement":
    page_header("VIDEO REVIEW", "Analyse a movement.", "A practical first-pass review using 2D pose estimation. Keep the camera still and the full athlete in frame.")
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
        run = st.form_submit_button("Run movement analysis", use_container_width=True)
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
        st.markdown("## Session findings")
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
        st.caption("Interpretation: these are 2D projected estimates from a single camera view. They are not 3D joint rotations, force, joint moments, tissue loading, injury-risk predictions or medical advice.")

elif page == "Athletes":
    page_header("PEOPLE", "Athletes.", "Keep a simple record of the people whose movement you review.")
    if role == "coach":
        with st.form("athlete_add"):
            a,b,c=st.columns(3)
            athlete_name=a.text_input("Athlete name")
            athlete_sport=b.selectbox("Primary sport",["Cricket","Baseball","Football","Basketball","Tennis","Athletics","Other"])
            athlete_level=c.selectbox("Level",["Development","Club","Academy","University","Professional","Recreational"])
            notes=st.text_input("Coaching notes (optional)")
            add=st.form_submit_button("Add athlete")
        if add and athlete_name.strip():
            st.session_state.setdefault("athlete_records",[])
            st.session_state.athlete_records.append({"Name":athlete_name,"Sport":athlete_sport,"Level":athlete_level,"Notes":notes})
            st.success("Athlete added to this session's workspace.")
    records=st.session_state.get("athlete_records",[])
    if records: st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True)
    else: st.markdown("<div class='ml-card'><h3>Your athlete list starts here</h3><p class='ml-muted'>Coach accounts can add athletes. In this first release, athlete directory entries are held in the current browser session; cloud team relationships are a next build step.</p></div>",unsafe_allow_html=True)
    if role=="athlete":
        st.info("Your athlete account is ready. Analyse your own sessions here; coach invitations and shared team spaces will be added in a later release.")

elif page == "Session history":
    page_header("TRAINING LOG", "Session history.", "A record of the movement reviews saved to your workspace.")
    sessions=load_sessions()
    if sessions:
        table=pd.DataFrame([{"Date":x["date"],"Athlete":x["athlete"],"Sport":x["sport"],"Movement":x["movement"],"Video":x["video"],"Frames":x["frames"],"Detection":f'{x["detection_rate"]:.1f}%'} for x in sessions])
        st.dataframe(table,use_container_width=True,hide_index=True)
        st.download_button("Export session history",table.to_csv(index=False).encode(),file_name="motionlab_session_history.csv",mime="text/csv")
    else:
        st.markdown("<div class='ml-card'><h3>Nothing logged yet</h3><p class='ml-muted'>Completed analyses will show up here.</p></div>",unsafe_allow_html=True)

elif page == "Account":
    page_header("PREFERENCES", "Your account.", "Manage the basics of your MotionLab workspace.")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("<div class='ml-card'><div class='ml-eyebrow'>PROFILE</div><h3>"+str(name)+"</h3><p class='ml-muted'>"+str(st.session_state.user.email)+"</p><span class='ml-pill'>"+role.title()+"</span></div>",unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='ml-card'><div class='ml-eyebrow'>WORKSPACE STATUS</div><h3>"+("Cloud-connected" if db_enabled() and not st.session_state.get("preview") else "Preview mode")+"</h3><p class='ml-muted'>"+("Supabase authentication is configured." if db_enabled() else "Connect Supabase to enable real accounts and persistent cloud session history.")+"</p></div>",unsafe_allow_html=True)

st.markdown("<div style='margin-top:42px;border-top:1px solid #e4e8df;padding-top:16px;color:#879188;font-size:.78rem'>MOTIONLAB · Movement, understood. &nbsp; This product supports coaching review and does not replace qualified clinical or biomechanical assessment.</div>",unsafe_allow_html=True)
