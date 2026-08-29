import streamlit as st
from firebase_admin import firestore
from gemini_service import generate_ai_learning_content

def get_db():
    return firestore.client()

def render_student_panel(user_email):
    db = get_db()
    
    # Student details fetch
    students_ref = db.collection("students").where("email", "==", user_email).stream()
    student_data = {}
    for doc in students_ref:
        student_data = doc.to_dict()
        break
        
    if not student_data:
        users_ref = db.collection("users").where("email", "==", user_email).stream()
        for doc in users_ref:
            student_data = doc.to_dict()
            break

    name = student_data.get("name") or st.session_state.get("user_name") or "Student"
    assigned_course = student_data.get("course", "")
    batch_timing = student_data.get("batch_timing", "09:00 AM - 10:00 AM")
    profile_pic = st.session_state.get("user_picture", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png")

    # Custom CSS for Glassmorphism & UI Enhancements
    st.markdown("""
        <style>
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        }
        .student-title { font-size: 24px; font-weight: bold; color: #38bdf8; margin: 0; }
        .attendance-badge { float: right; background: #00E676; color: #000; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 12px; }
        </style>
    """, unsafe_allow_html=True)

    # Top Bar: Profile & Update Profile Button
    col_img, col_txt, col_btn = st.columns([1, 5, 2])
    with col_img:
        st.image(profile_pic, width=60)
    with col_txt:
        st.markdown(f"<p class='student-title'>Welcome, {name}! 👋</p>", unsafe_allow_html=True)
    with col_btn:
        if st.button("✏️ Update Profile", use_container_width=True):
            st.toast("Redirecting to profile update...")

    # Hero Card (Glassmorphism)
    st.markdown(f"""
        <div class="glass-card">
            <span class="attendance-badge">Live Attendance: 85%</span>
            <h4 style="margin-top:0;">🎓 Course: {assigned_course if assigned_course else 'Not Assigned'}</h4>
            <p style="margin-bottom:0; color:#94a3b8;">🕒 Batch: {batch_timing}</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation - Dynamic DB Fetch
    st.sidebar.markdown("### 🧭 Learning Navigator")
    
    selected_concept = None
    if assigned_course:
        course_doc = db.collection("courses").document(assigned_course).get()
        if course_doc.exists:
            c_data = course_doc.to_dict()
            papers = c_data.get("papers", {})
            
            if papers:
                selected_paper = st.sidebar.selectbox("📂 Select Paper:", list(papers.keys()))
                subtopics = papers.get(selected_paper, {})
                
                if subtopics:
                    selected_subtopic = st.sidebar.selectbox("📂 Select Sub-topic:", list(subtopics.keys()))
                    concepts = subtopics.get(selected_subtopic, [])
                    
                    if concepts:
                        selected_concept = st.sidebar.selectbox("📂 Select Concept:", concepts)
                    else:
                        st.sidebar.info("No concepts added yet.")
                else:
                    st.sidebar.info("No sub-topics added yet.")
            else:
                st.sidebar.info("No papers configured for this course.")
        else:
            st.sidebar.error("Assigned course details not found in database.")
    else:
        st.sidebar.warning("You are not enrolled in any active course.")

    # Main Learning Hub
    if selected_concept:
        st.subheader(f"✨ Concept: {selected_concept}")
        
        if st.button("🚀 Generate AI Magic Notes & Quiz", type="primary", use_container_width=True):
            with st.spinner("✨ Generating the learning content..."):
                success, ai_output = generate_ai_learning_content(selected_concept, assigned_course, selected_subtopic)
                if success:
                    st.session_state[f"ai_content_{selected_concept}"] = ai_output
                else:
                    st.error(ai_output)

        # 4-Tabbed UI Rendering
        if f"ai_content_{selected_concept}" in st.session_state:
            st.markdown("---")
            raw_text = st.session_state[f"ai_content_{selected_concept}"]
            
            # Robust Array Splitting Logic
            raw_sections = raw_text.split("---SECTION---")
            clean_sections = [sec.strip() for sec in raw_sections if sec.strip()]
            
            # Agar AI ne introductory text add kiya hai (5 ya zyada items), toh last 4 items ko hi tabs maano
            if len(clean_sections) >= 5:
                clean_sections = clean_sections[-4:]
            # Agar output incomplete hai, blanks ko pad kar do taaki index out of range error na aaye
            elif len(clean_sections) < 4:
                clean_sections.extend(["Content is missing or failed to generate."] * (4 - len(clean_sections)))
            
            tab_theory, tab_prac, tab_mcq, tab_sol = st.tabs(["📖 Theory", "💻 Practical", "🎯 MCQ Quiz", "✅ Solutions"])
            
            with tab_theory:
                st.markdown(clean_sections[0])
            with tab_prac:
                st.markdown(clean_sections[1])
            with tab_mcq:
                st.markdown(clean_sections[2])
            with tab_sol:
                st.markdown(clean_sections[3])
        else:
            st.info("💡 Generate button par click karein aur instantly AI-powered detailed notes hasil karein.")