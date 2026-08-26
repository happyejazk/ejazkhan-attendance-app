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

    # Smart Name & Profile Photo logic
    name = student_data.get("name") or st.session_state.get("user_name") or "Student"
    course = student_data.get("course", "CCC")
    module = student_data.get("module", "Computer Basics")
    profile_pic = st.session_state.get("user_picture", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png")

    # Header Banner
    col_img, col_txt = st.columns([1, 6])
    with col_img:
        st.image(profile_pic, width=80)
    with col_txt:
        st.title(f"Welcome, {name}! 👋")
        st.caption(f"📚 Enrolled Course: **{course}** | Module: **{module}** | Batch Slot: {student_data.get('batch_timing', '09:00 AM - 10:00 AM')}")

    st.divider()

    # Sidebar Navigation
    st.sidebar.markdown("### 🧭 Learning Navigator")
    st.sidebar.markdown(f"**Course:** {course}")
    
    course_topics_map = {
        "O Level": ["Introduction to Computers", "Flowcharts & Algorithms", "Python Conditionals", "Loops in Python", "Web Design Basics (HTML/CSS)"],
        "ADCA": ["Advanced Excel Functions", "Tally Ledger Creation", "Graphic Design Intro", "Database Queries"],
        "CCC": ["Operating System Basics", "Internet & Emailing", "LibreOffice Writer", "Digital Financial Tools"],
        "Tally Prime": ["Company Creation", "Inventory Management", "GST Accounting Reports"]
    }
    
    topics_list = course_topics_map.get(course, ["Operating System Basics", "Internet & Emailing"])
    selected_topic = st.sidebar.selectbox("📂 Select Topic to Learn:", topics_list)

    # Main Learning Hub
    if selected_topic:
        st.subheader(f"📖 Live Study Hub: {selected_topic}")
        
        if st.button("🚀 Generate AI Notes & Solver Panel", type="primary", use_container_width=True):
            with st.spinner("✨ Gemini AI Dual-Language content generate kar raha hai..."):
                success, ai_output = generate_ai_learning_content(selected_topic, course, module)
                if success:
                    st.session_state[f"ai_content_{selected_topic}"] = ai_output
                else:
                    st.error(ai_output)

        # Tabbed UI Rendering
        if f"ai_content_{selected_topic}" in st.session_state:
            st.markdown("---")
            raw_text = st.session_state[f"ai_content_{selected_topic}"]
            
            # Split sections
            sections = raw_text.split("---SECTION---")
            
            tab1, tab2, tab3 = st.tabs(["📖 Hinglish Smart Notes", "🎯 Practice Questions", "💡 Solution & Solver"])
            
            with tab1:
                st.markdown(sections[0] if len(sections) > 0 else raw_text)
            with tab2:
                st.markdown(sections[1] if len(sections) > 1 else "Question section loading error.")
            with tab3:
                st.markdown(sections[2] if len(sections) > 2 else "Solver section loading error.")
        else:
            st.info("💡 Upar diye gaye button par click karke is topic ke instant AI-powered Hinglish Notes, Questions aur Solver generate karein.")