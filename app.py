import io, os, math, tempfile, subprocess, json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="MotionLab | Sports Biomechanics", page_icon="◒", layout="wide")

# -------------------- Visual system --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#17231c;--muted:#69766d;--line:#e4eae3;--green:#28583e;--sage:#dce9dc;--paper:#fff;--soft:#f5f7f3}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:var(--paper)}
.block-container{max-width:1460px;padding-top:1.3rem;padding-bottom:3rem}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.045em;color:var(--ink)}
h1{font-size:2.35rem!important;font-weight:800!important}
h2{font-size:1.55rem!important;font-weight:800!important}
p,label{color:var(--ink)}
[data-testid="stSidebar"]{background:#17231c}
[data-testid="stSidebar"] *{color:#f7faf6!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#cbd7cd!important}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:15px 17px;border-radius:13px}
[data-testid="stMetricLabel"]{color:#68766c!important;font-size:.8rem}
[data-testid="stMetricValue"]{color:#17231c!important;font-family:'Manrope',sans-serif;font-weight:800}
.stButton>button,.stDownloadButton>button{border-radius:9px;border:1px solid var(--green);background:var(--green);color:#fff!important;font-weight:700;min-height:2.7rem}
.stButton>button:hover,.stDownloadButton>button:hover{background:#1d452f;border-color:#1d452f;color:#fff!important}
.stTextInput input,.stSelectbox div[data-baseweb="select"],.stNumberInput input,.stTextArea textarea{border-radius:9px}
[data-testid="stTabs"] button{font-weight:700}
.ml-card{background:#fff;border:1px solid var(--line);border-radius:15px;padding:20px 22px}
.ml-kicker{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#426c50}
.ml-muted{color:#6e7b71;font-size:.92rem;line-height:1.65}
.ml-brand{font-family:'Manrope',sans-serif;font-size:1.25rem;font-weight:800;letter-spacing:-.06em;color:#17231c}
.ml-brand span{color:#527b5c}
.ml-hero{font-family:'Manrope',sans-serif;font-size:clamp(3rem,6vw,5.6rem);line-height:.96;letter-spacing:-.075em;font-weight:800;color:#15221a;margin:.8rem 0 1.1rem}
.ml-section{font-family:'Manrope',sans-serif;font-size:2rem;letter-spacing:-.06em;font-weight:800;color:#17231c}
.ml-pill{display:inline-block;background:#e7efe6;color:#28583e;border-radius:99px;padding:5px 10px;font-size:.73rem;font-weight:800}
div[data-testid="stAlert"]{border-radius:12px}
footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

SPORTS = ["Cricket / Fast bowling","Baseball / Pitching","Football / Soccer","Basketball","Tennis","Sprint / Running","General movement"]
MOVEMENTS = {
"Cricket / Fast bowling":["Full bowling action","Run-up","Gather / bound","Back-foot contact (BFC)","Delivery stride / front-foot contact (FFC)","Ball release","Follow-through"],
"Baseball / Pitching":["Full pitching action","Wind-up","Stride / lead-foot contact","Arm-cocking","Ball release","Follow-through"],
"Football / Soccer":["Sprint","Acceleration","Deceleration","Change of direction","Kicking","Jump / landing"],
"Basketball":["Jump","Landing","Sprint","Change of direction","Shooting"],
"Tennis":["Serve","Forehand","Backhand","Split-step / movement","Sprint"],
"Sprint / Running":["Acceleration","Maximum velocity","Running gait","Start","Finish"],
"General movement":["Whole movement","Squat","Lunge","Jump / landing","Overhead movement"]
}
PHASE_GUIDES = {
"Cricket / Fast bowling":"Run-up → gather/bound → back-foot contact → delivery stride → front-foot contact → release → follow-through",
"Baseball / Pitching":"Wind-up → stride → lead-foot contact → arm-cocking → release → follow-through",
"Football / Soccer":"Approach → plant / contact → execution → recovery",
"Basketball":"Preparation → take-off → flight → landing / deceleration",
"Tennis":"Preparation → loading → acceleration → contact → recovery",
"Sprint / Running":"Start → acceleration → transition → maximum velocity → deceleration",
"General movement":"Set-up → loading → execution → completion"
}

# -------------------- Optional cloud persistence --------------------
def get_supabase():
    try:
        from supabase import create_client
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
    except Exception:
        return None
supabase = get_supabase()

def save_cloud_session(row):
    if not supabase or st.session_state.get("preview") or not st.session_state.get("user"):
        return False
    try:
        supabase.table("analysis_sessions").insert({
            "user_id": st.session_state.user.id,
            "athlete_name": row["athlete"], "sport": row["sport"],
            "movement": row["movement"], "video_name": row["video"],
            "analysis_date": row["date"], "frames_analysed": row["frames"],
            "detection_rate": row["detection_rate"], "summary": row["summary"]
        }).execute()
        return True
    except Exception as e:
        st.warning(f"Cloud save unavailable: {e}")
        return False

def load_cloud_sessions():
    if not supabase or st.session_state.get("preview") or not st.session_state.get("user"):
        return []
    try:
        r=supabase.table("analysis_sessions").select("*").eq("user_id",st.session_state.user.id).order("created_at",desc=True).limit(100).execute()
        return [{"athlete":x.get("athlete_name",""),"sport":x.get("sport",""),"movement":x.get("movement",""),
                 "video":x.get("video_name",""),"date":x.get("analysis_date",""),"frames":x.get("frames_analysed",0),
                 "detection_rate":x.get("detection_rate",0),"summary":x.get("summary",{})} for x in (r.data or [])]
    except Exception:
        return []

# -------------------- Geometry / analysis --------------------
def angle_3pt(a,b,c):
    if any(p is None for p in (a,b,c)): return np.nan
    u=np.asarray(a)-np.asarray(b); v=np.asarray(c)-np.asarray(b)
    d=np.linalg.norm(u)*np.linalg.norm(v)
    if d<1e-8:return np.nan
    return float(np.degrees(np.arccos(np.clip(np.dot(u,v)/d,-1,1))))

def mid(a,b):
    return None if a is None or b is None else ((a[0]+b[0])/2,(a[1]+b[1])/2)

def extract_video(uploaded, step, max_samples, complexity, visibility_cutoff):
    import cv2, mediapipe as mp
    raw=uploaded.getvalue()
    suffix=os.path.splitext(uploaded.name)[1].lower() or ".mp4"
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=suffix)
    tmp.write(raw); tmp.close()
    cap=cv2.VideoCapture(tmp.name)
    if not cap.isOpened():
        os.unlink(tmp.name)
        raise ValueError("Could not decode this file. Export as MP4 (H.264) and try again.")
    fps=float(cap.get(cv2.CAP_PROP_FPS) or 30)
    total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0); height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    pose_api=mp.solutions.pose; draw=mp.solutions.drawing_utils
    records=[]; thumbs=[]; annotated_frames=[]
    pose=pose_api.Pose(static_image_mode=False,model_complexity=complexity,smooth_landmarks=True,
                       min_detection_confidence=.5,min_tracking_confidence=.5)
    idx=0; samples=0
    prog=st.progress(0,text="Reading video and tracking landmarks…")
    try:
        while cap.isOpened() and samples<max_samples:
            ok,frame=cap.read()
            if not ok:break
            if idx%step==0:
                h,w=frame.shape[:2]
                res=pose.process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
                row={"frame":idx,"time_s":idx/fps,"pose_detected":bool(res.pose_landmarks)}
                if res.pose_landmarks:
                    lm=res.pose_landmarks.landmark; P=pose_api.PoseLandmark
                    def p(name):
                        q=lm[getattr(P,name).value]
                        if float(q.visibility)<visibility_cutoff:return None
                        return (float(q.x*w),float(q.y*h))
                    # Core bilateral joint angles, projected in image plane
                    for side in ["LEFT","RIGHT"]:
                        row[f"{side.lower()}_knee_angle_deg"]=angle_3pt(p(side+"_HIP"),p(side+"_KNEE"),p(side+"_ANKLE"))
                        row[f"{side.lower()}_hip_angle_deg"]=angle_3pt(p(side+"_SHOULDER"),p(side+"_HIP"),p(side+"_KNEE"))
                        row[f"{side.lower()}_ankle_angle_deg"]=angle_3pt(p(side+"_KNEE"),p(side+"_ANKLE"),p(side+"_FOOT_INDEX"))
                        row[f"{side.lower()}_elbow_angle_deg"]=angle_3pt(p(side+"_SHOULDER"),p(side+"_ELBOW"),p(side+"_WRIST"))
                        row[f"{side.lower()}_shoulder_angle_deg"]=angle_3pt(p(side+"_ELBOW"),p(side+"_SHOULDER"),p(side+"_HIP"))
                    shoulder=mid(p("LEFT_SHOULDER"),p("RIGHT_SHOULDER"))
                    hip=mid(p("LEFT_HIP"),p("RIGHT_HIP"))
                    ankle=mid(p("LEFT_ANKLE"),p("RIGHT_ANKLE"))
                    wrist=mid(p("LEFT_WRIST"),p("RIGHT_WRIST"))
                    row["trunk_lean_deg"]=np.nan if shoulder is None or hip is None else float(np.degrees(np.arctan2(abs(shoulder[0]-hip[0]),abs(shoulder[1]-hip[1]))))
                    row["shoulder_line_deg"]=np.nan if p("LEFT_SHOULDER") is None or p("RIGHT_SHOULDER") is None else float(np.degrees(np.arctan2(p("RIGHT_SHOULDER")[1]-p("LEFT_SHOULDER")[1],p("RIGHT_SHOULDER")[0]-p("LEFT_SHOULDER")[0])))
                    row["hip_line_deg"]=np.nan if p("LEFT_HIP") is None or p("RIGHT_HIP") is None else float(np.degrees(np.arctan2(p("RIGHT_HIP")[1]-p("LEFT_HIP")[1],p("RIGHT_HIP")[0]-p("LEFT_HIP")[0])))
                    row["projected_shoulder_hip_separation_deg"]=abs(row["shoulder_line_deg"]-row["hip_line_deg"]) if pd.notna(row["shoulder_line_deg"]) and pd.notna(row["hip_line_deg"]) else np.nan
                    row["body_centre_x_px"]=np.nan if hip is None else hip[0]
                    row["body_centre_y_px"]=np.nan if hip is None else hip[1]
                    row["left_ankle_x_px"]=np.nan if p("LEFT_ANKLE") is None else p("LEFT_ANKLE")[0]
                    row["right_ankle_x_px"]=np.nan if p("RIGHT_ANKLE") is None else p("RIGHT_ANKLE")[0]
                    row["left_wrist_x_px"]=np.nan if p("LEFT_WRIST") is None else p("LEFT_WRIST")[0]
                    row["right_wrist_x_px"]=np.nan if p("RIGHT_WRIST") is None else p("RIGHT_WRIST")[0]
                    row["mean_landmark_visibility"]=float(np.mean([q.visibility for q in lm]))
                    annotated=frame.copy()
                    draw.draw_landmarks(annotated,res.pose_landmarks,pose_api.POSE_CONNECTIONS)
                    cv2.putText(annotated,f'{idx/fps:.3f}s',(18,32),cv2.FONT_HERSHEY_SIMPLEX,.8,(70,180,115),2,cv2.LINE_AA)
                    annotated_frames.append((idx/fps,cv2.cvtColor(annotated,cv2.COLOR_BGR2RGB)))
                    if len(thumbs)<12:thumbs.append(cv2.cvtColor(annotated,cv2.COLOR_BGR2RGB))
                else:
                    row["mean_landmark_visibility"]=0.0
                records.append(row); samples+=1
                if total:prog.progress(min(idx/total,1),text=f"Tracking frame {idx}/{total}")
            idx+=1
    finally:
        pose.close();cap.release()
        try:os.unlink(tmp.name)
        except OSError:pass
    prog.empty()
    if not records:raise ValueError("No video frames were analysed.")
    df=pd.DataFrame(records)
    # Differentiation only describes image-plane motion; scale calibration is optional.
    dt=df["time_s"].diff()
    for col in ["body_centre_x_px","body_centre_y_px","left_ankle_x_px","right_ankle_x_px","left_wrist_x_px","right_wrist_x_px"]:
        if col in df:
            df[col.replace("_px","_px_s")]=df[col].diff()/dt
    return {"df":df,"fps":fps,"total_frames":total,"duration":total/fps if fps else 0,
            "width":width,"height":height,"thumbnails":thumbs,"annotated":annotated_frames}

def add_manual_event_metrics(df, fps, event_frames, px_per_m=None):
    out=df.copy()
    for name,frame in event_frames.items():
        if frame is not None:
            out[f"event_{name}"]=(out["frame"]-int(frame)).abs().le(0)
    # event intervals in seconds, derived only from user-entered event frames and original fps
    def interval(a,b):
        if a is None or b is None or int(b)<=int(a):return np.nan
        return (int(b)-int(a))/fps
    intervals={}
    for a,b,label in [
        ("bfc_start","bfc_end","BFC contact time"),
        ("ffc_start","ffc_end","FFC contact time"),
        ("runup_start","bfc_start","Run-up duration"),
        ("bfc_start","release","BFC to release"),
        ("ffc_start","release","FFC to release")
    ]: intervals[label]=interval(event_frames.get(a),event_frames.get(b))
    # stride length from selected ankle coordinates at event frames, calibrated scale only
    stride=np.nan
    if px_per_m and event_frames.get("bfc_start") is not None and event_frames.get("ffc_start") is not None:
        a=out.iloc[(out.frame-int(event_frames["bfc_start"])).abs().argmin()]
        b=out.iloc[(out.frame-int(event_frames["ffc_start"])).abs().argmin()]
        # Side-view horizontal displacement between the best-visible ankle centres; use user-selected side if known
        vals=[]
        for col in ["left_ankle_x_px","right_ankle_x_px"]:
            if pd.notna(a.get(col)) and pd.notna(b.get(col)):vals.append(abs(float(b[col])-float(a[col]))/float(px_per_m))
        if vals:stride=max(vals)
    return out,intervals,stride

# -------------------- Marketing / auth --------------------
def landing():
    st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e6ebe5;padding:8px 0 22px"><div class="ml-brand">MOTION<span>LAB</span></div><div style="color:#59675d;font-size:.82rem;font-weight:700">PLATFORM　 BIOMECHANICS　 PERFORMANCE　 FOR COACHES</div></div>',unsafe_allow_html=True)
    l,r=st.columns([1.02,1],gap="large",vertical_alignment="center")
    with l:
        st.markdown('<div class="ml-kicker" style="font-size:.82rem">SPORTS BIOMECHANICS · PERFORMANCE ANALYSIS</div>',unsafe_allow_html=True)
        st.markdown('<div class="ml-hero">Understand<br>movement.<br><span style="color:#527b5c">Build performance.</span></div>',unsafe_allow_html=True)
        st.markdown('<div class="ml-muted" style="font-size:1.08rem;max-width:580px">A video-first workspace for athletes, coaches and performance teams. Break movement into phases, inspect mechanics and build a clearer picture of performance.</div>',unsafe_allow_html=True)
        a,b=st.columns(2)
        with a:
            if st.button("Explore the platform →",use_container_width=True,key="hero_explore"):
                st.session_state.show_auth=True;st.session_state.auth_mode="Create account";st.rerun()
        with b:
            if st.button("Sign in",use_container_width=True,key="hero_signin"):
                st.session_state.show_auth=True;st.session_state.auth_mode="Sign in";st.rerun()
        st.caption("BUILT FOR ATHLETES · COACHES · ACADEMIES · TEAMS")
    with r:
        demo_path="demo_bowling.mp4"
        if os.path.exists(demo_path):
            try:
                # Strip the audio stream from the homepage asset (not merely mute playback).
                import base64
                import imageio_ffmpeg
                source_bytes=open(demo_path,"rb").read()
                cache_key=str(os.path.getsize(demo_path))+"_"+str(int(os.path.getmtime(demo_path)))
                silent_path=os.path.join(tempfile.gettempdir(),"motionlab_home_demo_no_audio.mp4")
                if not os.path.exists(silent_path) or os.path.getsize(silent_path)==0:
                    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
                    subprocess.run([ffmpeg,"-y","-i",demo_path,"-an","-c:v","libx264","-preset","veryfast","-crf","25","-movflags","+faststart",silent_path],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
                data=open(silent_path,"rb").read()
                encoded=base64.b64encode(data).decode("ascii")
                st.markdown(f"""<div style="border:1px solid #e3e9e2;border-radius:14px;overflow:hidden;background:#111"><video autoplay muted loop playsinline controls style="width:100%;display:block"><source src="data:video/mp4;base64,{encoded}" type="video/mp4"></video></div><div style="font-size:.7rem;letter-spacing:.12em;color:#6b796f;margin-top:9px">MOTIONLAB VIDEO REVIEW · AUDIO TRACK REMOVED</div>""",unsafe_allow_html=True)
            except Exception as e:st.info(f"Could not prepare the homepage demo. Check that demo_bowling.mp4 is a valid MP4. Details: {e}")
        else:
            st.markdown("<div class='ml-card' style='background:#f4f7f2;padding:48px 25px;text-align:center'><div class='ml-kicker'>VIDEO-BASED ANALYSIS</div><h2>From footage<br>to movement data.</h2><p class='ml-muted'>Upload your licensed demonstration clip as demo_bowling.mp4.</p></div>",unsafe_allow_html=True)
    st.markdown("<div style='height:48px'></div>",unsafe_allow_html=True)
    st.markdown('<div class="ml-kicker">THE MOTIONLAB PLATFORM</div><div class="ml-section">Everything around the movement.</div>',unsafe_allow_html=True)
    features=[("01","Biomechanical analysis","Joint angles, body positions, phase timing and calibrated distance estimates."),
              ("02","Video intelligence","Slow review, pose overlay, frame timeline and event tagging."),
              ("03","Performance monitoring","Session history, athlete profiles, comparisons and coach workflows."),
              ("04","Multi-sport workflows","Cricket, baseball, football, basketball, tennis, sprinting and general movement.")]
    cols=st.columns(4)
    for c,(n,t,d) in zip(cols,features):
        with c:st.markdown(f"<div class='ml-card' style='height:190px'><div class='ml-kicker'>{n}</div><h3>{t}</h3><p class='ml-muted'>{d}</p></div>",unsafe_allow_html=True)
    st.markdown("<div style='height:42px'></div>",unsafe_allow_html=True)
    x,y=st.columns([1.2,1])
    with x:
        st.markdown('<div class="ml-kicker">ANALYSIS THAT SHOWS ITS WORK</div><div class="ml-section">Every phase. Every frame we can measure.</div><p class="ml-muted">Review detected landmarks, inspect joint-angle timelines, mark key events and export the underlying data. Measurements are labelled by how they are obtained.</p>',unsafe_allow_html=True)
    with y:
        st.markdown("<div class='ml-card'><b>VIDEO-DERIVED</b><p class='ml-muted'>Projected joint angles, landmark positions and image-plane movement.</p><hr><b>EVENT-BASED</b><p class='ml-muted'>Contact times and phase intervals from frame markers you confirm.</p><hr><b>CALIBRATED</b><p class='ml-muted'>Distance and speed estimates only after you enter a known scale reference.</p></div>",unsafe_allow_html=True)
    st.markdown("<div style='margin-top:45px;border-top:1px solid #e4eae3;padding-top:18px;color:#778379;font-size:.75rem'>MOTIONLAB · SPORTS BIOMECHANICS & PERFORMANCE INTELLIGENCE</div>",unsafe_allow_html=True)

def auth():
    st.markdown('<div class="ml-kicker">ATHLETE & COACH WORKSPACE</div>',unsafe_allow_html=True)
    st.title("Welcome to MotionLab.")
    st.markdown('<p class="ml-muted">Sign in to your workspace or create an account to begin reviewing movement.</p>',unsafe_allow_html=True)
    if st.button("← Back to homepage"):st.session_state.show_auth=False;st.rerun()
    if supabase:
        t1,t2=st.tabs(["Sign in","Create account"])
        with t1:
            with st.form("signin"):
                email=st.text_input("Email");password=st.text_input("Password",type="password")
                go=st.form_submit_button("Sign in",use_container_width=True)
            if go:
                try:
                    res=supabase.auth.sign_in_with_password({"email":email,"password":password})
                    st.session_state.user=res.user;st.session_state.preview=False
                    st.session_state.role="athlete";st.session_state.display_name=email.split("@")[0]
                    st.rerun()
                except Exception as e:st.error(f"Sign in failed: {e}")
        with t2:
            with st.form("signup"):
                name=st.text_input("Full name");email=st.text_input("Email");pw=st.text_input("Password (8+ characters)",type="password")
                role=st.selectbox("Account type",["Athlete","Coach","Academy / Team"])
                go=st.form_submit_button("Create account",use_container_width=True)
            if go:
                if len(pw)<8:st.error("Use at least 8 characters.")
                elif not name.strip() or not email.strip():st.error("Complete all fields.")
                else:
                    try:
                        res=supabase.auth.sign_up({"email":email,"password":pw,"options":{"data":{"display_name":name,"role":role.lower()}}})
                        if res.user:st.success("Account created. Check your email if verification is enabled.")
                    except Exception as e:st.error(f"Registration failed: {e}")
    else:
        st.warning("Cloud authentication is not configured. You can explore the workspace in preview mode; preview data is not persistent.")
        with st.form("preview_login"):
            name=st.text_input("Your name",value="Demo user");role=st.selectbox("I am a",["Athlete","Coach","Academy / Team"])
            go=st.form_submit_button("Enter preview workspace",use_container_width=True)
        if go:
            st.session_state.user=type("PreviewUser",(),{"id":"preview","email":"preview@motionlab.local"})()
            st.session_state.role=role.lower();st.session_state.display_name=name;st.session_state.preview=True;st.rerun()

if "user" not in st.session_state:
    if st.session_state.get("show_auth"):auth()
    else:landing()
    st.stop()

# -------------------- Workspace navigation --------------------
with st.sidebar:
    st.markdown("# MOTIONLAB")
    st.caption("SPORTS BIOMECHANICS & PERFORMANCE")
    st.markdown("---")
    display=st.session_state.get("display_name","Member")
    role=st.session_state.get("role","athlete")
    st.markdown(f"**{display}**")
    st.caption(role.title()+" workspace")
    page=st.radio("WORKSPACE",["Overview","Video analysis","Athletes","Session history","Reports","Team workspace","Account"])
    st.markdown("---")
    if st.button("Sign out",use_container_width=True):
        if supabase and not st.session_state.get("preview"):
            try:supabase.auth.sign_out()
            except Exception:pass
        for k in ["user","role","display_name","preview","last_result"]:st.session_state.pop(k,None)
        st.rerun()

def header(kicker,title,subtitle):
    st.markdown(f'<div class="ml-kicker">{kicker}</div>',unsafe_allow_html=True)
    st.title(title);st.markdown(f'<div class="ml-muted">{subtitle}</div>',unsafe_allow_html=True)

st.session_state.setdefault("sessions",[])
st.session_state.setdefault("athlete_records",[])
sessions=list(st.session_state.sessions)
if not st.session_state.get("preview"):sessions=load_cloud_sessions()+sessions

if page=="Overview":
    header("PERFORMANCE WORKSPACE","Movement, understood.","Your central workspace for video reviews, athlete records and performance observations.")
    a,b,c,d=st.columns(4)
    a.metric("Sessions reviewed",len(sessions))
    b.metric("Athletes tracked",len(st.session_state.athlete_records))
    c.metric("Sports covered",len(set(x.get("sport","") for x in sessions)) if sessions else "—")
    d.metric("Latest review",sessions[0]["date"][:10] if sessions else "—")
    st.markdown("### Your next review")
    l,r=st.columns([1.15,1])
    with l:
        st.markdown("<div class='ml-card'><div class='ml-kicker'>VIDEO LAB</div><h2>Start with the footage.</h2><p class='ml-muted'>Upload a clip, select the sport and movement, inspect the pose overlay and mark important events such as BFC, FFC or release.</p></div>",unsafe_allow_html=True)
        if st.button("Open video analysis →",use_container_width=True):st.session_state.goto_analysis=True;st.rerun()
    with r:
        st.markdown("<div class='ml-card'><div class='ml-kicker'>MEASUREMENT STANDARD</div><h3>Know what the number means.</h3><p class='ml-muted'>Video-derived estimates, manually marked event timings and calibrated distances are kept separate. No force or 3D data is fabricated from a 2D clip.</p></div>",unsafe_allow_html=True)
    if sessions:
        st.markdown("### Recent sessions")
        st.dataframe(pd.DataFrame([{"Date":x["date"],"Athlete":x["athlete"],"Sport":x["sport"],"Movement":x["movement"],"Detection":f'{x["detection_rate"]:.1f}%'} for x in sessions[:8]]),use_container_width=True,hide_index=True)
    else:st.info("No completed analyses yet. Your first video review will appear here.")

elif page=="Video analysis":
    header("VIDEO LAB","Analyse movement.","Upload a video, track the athlete's 2D pose, review movement metrics and confirm key event frames.")
    with st.form("analysis_form"):
        a,b,c=st.columns(3)
        athlete=a.text_input("Athlete name / ID",value="")
        sport=b.selectbox("Sport",SPORTS)
        movement=st.selectbox("Movement phase / action",MOVEMENTS[sport],key="movement_select")
        d,e,f=st.columns(3)
        camera=d.selectbox("Camera view",["Side-on","Front-on","Rear","Oblique"])
        step=e.select_slider("Frame sampling",options=[1,2,3,4,5,6,8,10],value=2)
        max_samples=f.select_slider("Max samples",options=[150,300,450,600,900,1200],value=600)
        complexity=st.select_slider("Pose model detail",options=[0,1,2],value=1,help="Higher complexity can be slower.")
        cutoff=st.slider("Minimum landmark visibility",.1,.9,.35,.05)
        uploaded=st.file_uploader("Upload video (MP4, MOV, AVI)",type=["mp4","mov","avi","m4v"])
        run=st.form_submit_button("Run pose analysis",use_container_width=True)
    if run:
        if not athlete.strip():st.error("Enter an athlete name or ID.")
        elif uploaded is None:st.error("Upload a video first.")
        else:
            try:
                with st.spinner("Analysing video…"):
                    result=extract_video(uploaded,step,max_samples,complexity,cutoff)
                result.update({"video_bytes":uploaded.getvalue(),"athlete":athlete.strip(),"sport":sport,"movement":movement,"camera":camera,"video":uploaded.name,
                               "date":datetime.now().strftime("%Y-%m-%d %H:%M")})
                st.session_state.last_result=result
                st.success("Pose tracking complete. Add event markers below for contact and phase timing.")
            except Exception as ex:st.error(f"Analysis failed: {ex}")
    result=st.session_state.get("last_result")
    if result:
        df=result["df"]
        st.markdown("---")
        st.markdown("### Session overview")
        rate=float(df.pose_detected.mean()*100)
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Clip duration",f'{result["duration"]:.2f} s')
        m2.metric("Frames sampled",len(df))
        m3.metric("Pose detection",f"{rate:.1f}%")
        m4.metric("Frame rate",f'{result["fps"]:.1f} fps')
        tabs=st.tabs(["Video & pose","Biomechanics","Events & timing","Export"])
        with tabs[0]:
            left,right=st.columns([1.2,1])
            with left:
                st.markdown("#### Source video")
                # Streamlit video player. Source audio muted by browser player setting where supported.
                st.video(result["video_bytes"])
                st.caption("Source footage is shown for review. Annotated sample frames display the pose model output.")
            with right:
                st.markdown("#### Pose tracking samples")
                if result["thumbnails"]:
                    ix=st.slider("Sample frame",0,len(result["thumbnails"])-1,0,key="thumb_ix")
                    st.image(result["thumbnails"][ix],use_container_width=True)
                else:st.warning("No pose landmarks were detected in the sampled frames.")
            if result["thumbnails"]:
                st.markdown("#### Frame gallery")
                cols=st.columns(min(4,len(result["thumbnails"])))
                for i,img in enumerate(result["thumbnails"]):cols[i%len(cols)].image(img,caption=f"Sample {i+1}")
        with tabs[1]:
            st.markdown("#### Joint and segment measurements")
            desc={
              "knee_angle_deg":"2D included angle at the knee (degrees).",
              "hip_angle_deg":"2D included angle at the hip (degrees).",
              "ankle_angle_deg":"2D included angle at the ankle (degrees).",
              "elbow_angle_deg":"2D included angle at the elbow (degrees).",
              "shoulder_angle_deg":"2D included angle at the shoulder (degrees).",
              "trunk_lean_deg":"Projected trunk inclination relative to image vertical.",
              "projected_shoulder_hip_separation_deg":"Difference between projected shoulder and hip line orientations; not true 3D hip-shoulder separation."
            }
            metric_cols=[x for x in df.columns if x.endswith("_deg") and df[x].notna().sum()>1]
            if metric_cols:
                selected=st.selectbox("Metric timeline",metric_cols,format_func=lambda x:x.replace("_deg","").replace("_"," ").title())
                chart=px.line(df,x="time_s",y=selected,labels={"time_s":"Time (s)",selected:"Angle estimate (°)"},markers=False)
                chart.update_layout(template="plotly_white",height=350,margin=dict(l=10,r=10,t=20,b=10))
                st.plotly_chart(chart,use_container_width=True)
                vals=df[selected].dropna()
                aa,bb,cc=st.columns(3);aa.metric("Mean",f"{vals.mean():.1f}°");bb.metric("Minimum",f"{vals.min():.1f}°");cc.metric("Maximum",f"{vals.max():.1f}°")
                st.caption(desc.get("_".join(selected.split("_")[:-1])+"_deg","Projected 2D measurement; interpret in camera context."))
            with st.expander("All available metrics and definitions",expanded=True):
                definitions=[
                ("Bilateral knee / hip / ankle / elbow / shoulder angles","2D projected included angles from visible pose landmarks."),
                ("Trunk lean","Projected angle of shoulder midpoint to hip midpoint relative to vertical."),
                ("Shoulder–hip line separation","Difference between projected shoulder and hip line angles; not axial 3D rotation."),
                ("Landmark visibility","Pose model confidence proxy; not a measure of measurement accuracy."),
                ("Image-plane landmark velocity","Change in landmark pixel position per second; needs scale calibration for physical speed.")]
                for title,definition in definitions:st.markdown(f"**{title}** — {definition}")
            st.dataframe(df.head(500),use_container_width=True,hide_index=True)
        with tabs[2]:
            st.markdown("#### Mark key movement events")
            st.write("Enter the original video frame number for each event. These markers are user-confirmed; MotionLab does not silently guess foot contacts.")
            max_frame=max(0,result["total_frames"]-1)
            with st.form("events_form"):
                if sport.startswith("Cricket"):
                    keys=[("runup_start","Run-up start"),("bfc_start","Back-foot contact start"),("bfc_end","Back-foot contact end"),("ffc_start","Front-foot contact start"),("ffc_end","Front-foot contact end"),("release","Ball release"),("followthrough","Follow-through event")]
                elif sport.startswith("Baseball"):
                    keys=[("runup_start","Wind-up start"),("bfc_start","Lead-foot contact start"),("bfc_end","Lead-foot contact end"),("ffc_start","Stride/plant end"),("release","Ball release"),("followthrough","Follow-through")]
                else:
                    keys=[("runup_start","Movement start"),("bfc_start","Loading / contact start"),("bfc_end","Loading / contact end"),("ffc_start","Execution / contact start"),("ffc_end","Execution / contact end"),("release","Peak / release event"),("followthrough","Recovery event")]
                event_frames={}
                cols=st.columns(3)
                for i,(key,label) in enumerate(keys):
                    value=cols[i%3].number_input(label,min_value=0,max_value=max_frame,value=0,step=1,key="ev_"+key)
                    event_frames[key]=None if value==0 else int(value)
                px_per_m=st.number_input("Calibration: pixels per metre (optional)",min_value=0.0,value=0.0,step=1.0,help="Measure a known distance in the same plane as the athlete. Enter pixels per metre. Leave 0 if unknown.")
                apply=st.form_submit_button("Calculate event metrics",use_container_width=True)
            if apply:
                pxm=px_per_m if px_per_m>0 else None
                enriched,intervals,stride=add_manual_event_metrics(df,result["fps"],event_frames,pxm)
                result["event_frames"]=event_frames;result["event_metrics"]=intervals;result["stride_length_m"]=stride
                result["df"]=enriched;st.session_state.last_result=result
            if result.get("event_metrics"):
                x1,x2,x3=st.columns(3)
                x1.metric("BFC / lead contact",f'{result["event_metrics"].get("BFC contact time",np.nan):.3f} s' if pd.notna(result["event_metrics"].get("BFC contact time",np.nan)) else "Not marked")
                x2.metric("FFC / execution contact",f'{result["event_metrics"].get("FFC contact time",np.nan):.3f} s' if pd.notna(result["event_metrics"].get("FFC contact time",np.nan)) else "Not marked")
                x3.metric("Stride length",f'{result.get("stride_length_m",np.nan):.2f} m' if pd.notna(result.get("stride_length_m",np.nan)) else "Needs scale + markers")
                st.dataframe(pd.DataFrame([{"Metric":k,"Value (s)":v} for k,v in result["event_metrics"].items()]),use_container_width=True,hide_index=True)
                st.caption("Contact durations are frame-marker intervals divided by source FPS. Stride length is a 2D ankle displacement estimate and requires a same-plane scale reference.")
            else:st.info("No event metrics yet. Add frame markers and select Calculate event metrics.")
            st.markdown("**Phase sequence**")
            st.write(PHASE_GUIDES.get(sport,"Mark the events relevant to this movement."))
        with tabs[3]:
            st.markdown("#### Export your review")
            csv=df.to_csv(index=False).encode("utf-8")
            st.download_button("Download frame-by-frame CSV",csv,file_name="motionlab_frame_analysis.csv",mime="text/csv")
            summary={"athlete":result["athlete"],"sport":result["sport"],"movement":result["movement"],"video":result["video"],
                     "date":result["date"],"frames":len(df),"detection_rate":rate,"summary":{}}
            for col in [x for x in df.columns if x.endswith("_deg")]:
                vals=df[col].dropna()
                if len(vals):summary["summary"][col]={"mean":round(float(vals.mean()),2),"min":round(float(vals.min()),2),"max":round(float(vals.max()),2)}
            if st.button("Save session to workspace"):
                st.session_state.sessions.insert(0,summary)
                save_cloud_session(summary)
                st.success("Session saved to your workspace.")
            st.download_button("Download session summary JSON",json.dumps(summary,indent=2,default=str).encode(),file_name="motionlab_session_summary.json",mime="application/json")
        st.info("Measurement limits: a single 2D camera view cannot directly measure ground reaction force, joint moments, tissue loading, true 3D rotations, ball speed or injury risk. GCT and phase durations require reliable event markers; stride length and speed require calibration. Treat all outputs as coaching review aids, not medical decisions.")

elif page=="Athletes":
    header("ATHLETE MANAGEMENT","Athlete library.","Create a working roster and keep athlete details together.")
    with st.form("athlete_form"):
        a,b,c=st.columns(3)
        nm=a.text_input("Athlete name");sp=b.selectbox("Primary sport",["Cricket","Baseball","Football","Basketball","Tennis","Athletics","Other"])
        level=c.selectbox("Level",["Development","Club","Academy","University","Professional","Recreational"])
        note=st.text_input("Notes / goals")
        go=st.form_submit_button("Add athlete")
    if go and nm.strip():
        st.session_state.athlete_records.append({"Name":nm.strip(),"Sport":sp,"Level":level,"Notes":note})
        st.success("Athlete added to this browser session.")
    if st.session_state.athlete_records:st.dataframe(pd.DataFrame(st.session_state.athlete_records),use_container_width=True,hide_index=True)
    else:st.info("No athletes added yet. Add an athlete above to start a roster.")
    st.caption("Roster persistence and coach-to-athlete invitations require the cloud database setup in the deployment guide.")

elif page=="Session history":
    header("TRAINING LOG","Session history.","Review saved sessions and export a record of your work.")
    rows=st.session_state.sessions+([] if st.session_state.get("preview") else load_cloud_sessions())
    if rows:
        tab=pd.DataFrame([{"Date":x["date"],"Athlete":x["athlete"],"Sport":x["sport"],"Movement":x["movement"],"Video":x["video"],"Frames":x["frames"],"Detection":f'{x["detection_rate"]:.1f}%'} for x in rows])
        st.dataframe(tab,use_container_width=True,hide_index=True)
        st.download_button("Export session history CSV",tab.to_csv(index=False).encode(),file_name="motionlab_history.csv",mime="text/csv")
    else:st.info("Completed analyses that you save will appear here.")

elif page=="Reports":
    header("REPORTING","Performance reports.","Build a portable session summary from the latest video analysis.")
    res=st.session_state.get("last_result")
    if not res:st.info("Run a video analysis first. The latest session will be available here.")
    else:
        df=res["df"];st.markdown(f"### {res['athlete']} · {res['sport']}")
        st.write(f"**Movement:** {res['movement']}  \n**Video:** {res['video']}  \n**Date:** {res['date']}")
        st.metric("Pose detection rate",f'{df.pose_detected.mean()*100:.1f}%')
        metrics=[]
        for col in [x for x in df.columns if x.endswith("_deg")]:
            vals=df[col].dropna()
            if len(vals):metrics.append({"Metric":col.replace("_"," ").title(),"Mean":round(vals.mean(),1),"Min":round(vals.min(),1),"Max":round(vals.max(),1)})
        if metrics:st.dataframe(pd.DataFrame(metrics),use_container_width=True,hide_index=True)
        st.caption("Report values are projected 2D estimates. Interpretation should be reviewed by a qualified coach or sports scientist.")

elif page=="Team workspace":
    header("COACHING","Team workspace.","A starting point for academy and team workflows.")
    st.markdown("<div class='ml-card'><h3>Team operations</h3><p class='ml-muted'>The current build includes athlete roster entry, individual video reviews, saved session history and exportable reports. Multi-user invitations, role permissions, team-level analytics and shared media storage are not activated until Supabase policies and storage are configured.</p></div>",unsafe_allow_html=True)
    st.markdown("### Team-ready workflows")
    st.write("- Athlete roster and sport / level tags\n- Session review and coach notes\n- Frame-level CSV and session summary exports\n- Cloud authentication and session history when Supabase is configured")

elif page=="Account":
    header("ACCOUNT","Your workspace settings.","Account status and data handling.")
    a,b=st.columns(2)
    a.markdown(f"<div class='ml-card'><div class='ml-kicker'>PROFILE</div><h3>{display}</h3><p class='ml-muted'>{getattr(st.session_state.user,'email','Preview account')}</p><span class='ml-pill'>{role.title()}</span></div>",unsafe_allow_html=True)
    b.markdown(f"<div class='ml-card'><div class='ml-kicker'>CONNECTION</div><h3>{'Cloud authentication connected' if supabase and not st.session_state.get('preview') else 'Preview mode'}</h3><p class='ml-muted'>{'Supabase credentials detected.' if supabase else 'Configure Supabase to enable real account registration and persistent session history.'}</p></div>",unsafe_allow_html=True)
    st.markdown("### Data handling")
    st.write("Video files are processed for the current analysis and are not automatically saved to cloud storage in this build. Session summaries may be saved to Supabase when configured. Obtain athlete consent before uploading identifiable footage.")

st.markdown("<div style='margin-top:45px;border-top:1px solid #e4eae3;padding-top:16px;color:#778379;font-size:.76rem'>MOTIONLAB · Sports biomechanics & performance intelligence · Coaching support, not medical diagnosis.</div>",unsafe_allow_html=True)
