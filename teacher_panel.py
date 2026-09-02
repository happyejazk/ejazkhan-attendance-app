import streamlit as st
import datetime
from firebase_admin import firestore

try:
    from email_service import send_welcome_credentials
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False

def get_db():
    return firestore.client()

BASE_TIME_SLOTS = [
    "07:00 AM - 08:00 AM", "08:00 AM - 09:00 AM", "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM"
]

def get_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12: return "Good Morning"
    elif hour < 17: return "Good Afternoon"
    else: return "Good Evening"

def fetch_dynamic_courses(db):
    """Firestore se courses aur unke papers/modules dynamically fetch karta hai."""
    catalog = {}
    try:
        courses_ref = db.collection("courses").stream()
        for doc in courses_ref:
            data = doc.to_dict()
            papers = data.get("papers", {})
            if isinstance(papers, dict) and papers:
                catalog[doc.id] = list(papers.keys())
            else:
                catalog[doc.id] = ["GENERAL"]
        
        if not catalog:
            catalog = {"No Courses Configured": ["N/A"]}
    except Exception:
        catalog = {"Database Error": ["Error"]}
    return catalog

def render_teacher_panel(user_email):
    st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
        }
        .metric-value { font-size: 24px; font-weight: bold; color: #38bdf8; }
        .metric-label { font-size: 12px; color: #94a3b8; }
        div[data-baseweb="input"] input { text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    db = get_db()
    clean_email = str(user_email).strip().lower() if user_email else ""
    
    # 1. Multi-layer Name Lookup Logic
    teacher_name = st.session_state.get("user_name", "")
    
    if not teacher_name and clean_email:
        # Layer 1: Check document where ID == email
        doc_snap = db.collection("users").document(clean_email).get()
        if doc_snap.exists:
            teacher_name = doc_snap.to_dict().get("name", "")
            
        # Layer 2: Query where 'email' field == clean_email
        if not teacher_name:
            user_query = db.collection("users").where("email", "==", clean_email).stream()
            for doc in user_query:
                teacher_name = doc.to_dict().get("name", "")
                break
                
        # Layer 3: Query by 'user_id'
        if not teacher_name:
            user_id_query = db.collection("users").where("user_id", "==", clean_email).stream()
            for doc in user_id_query:
                teacher_name = doc.to_dict().get("name", "")
                break

    if not teacher_name:
        teacher_name = "Teacher"

    st.title(f"👨‍🏫 {get_greeting()}, {teacher_name}!")
    st.caption("AIM ERP - Teacher Control Center")

    COURSE_CATALOG = fetch_dynamic_courses(db)

    # Stream Firestore Collections
    students_ref = db.collection("students")
    all_docs = [doc.to_dict() | {"id": doc.id} for doc in students_ref.stream()]
    
    active_students = [s for s in all_docs if not s.get("is_deleted", False) and s.get("is_approved", True)]
    pending_students = [s for s in all_docs if not s.get("is_deleted", False) and not s.get("is_approved", True)]
    archived_students = [s for s in all_docs if s.get("is_deleted", False)]

    pending_count_label = f"⏳ Pending ({len(pending_students)})" if pending_students else "⏳ Pending Approvals"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Live Attendance", 
        "➕ Add Student", 
        pending_count_label,
        "🔄 Batch Re-Allocator", 
        "🗑️ Trash & Restore"
    ])

    # ------------------ TAB 1: LIVE ATTENDANCE ------------------
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(active_students)}</div><div class="metric-label">Active Students</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{len(set([s.get("batch_timing") for s in active_students if s.get("batch_timing")]))}</div><div class="metric-label">Batches</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value">{len(pending_students)}</div><div class="metric-label">Pending Approval</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value">{len(archived_students)}</div><div class="metric-label">Archived</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        available_courses = sorted(list(set([s.get("course") for s in active_students if s.get("course")])))
        available_batches = sorted(list(set([s.get("batch_timing") for s in active_students if s.get("batch_timing")])))
        
        f1, f2, f3, f4 = st.columns(4)
        selected_course = f1.selectbox("Course", ["All Courses"] + available_courses, key="f_c")
        selected_module = f2.selectbox("Module", ["All Modules"] + sorted(list(set([s.get("module") for s in active_students if s.get("module")]))), key="f_m")
        
        batch_options = ["🛑 Select Your Batch"] + available_batches + ["➕ Add Custom Slot"]
        selected_batch = f3.selectbox("Batch Slot", batch_options, key="f_b")
        
        if selected_batch == "➕ Add Custom Slot":
            custom_batch = f3.text_input("Enter New Batch Time (e.g., 01:00 PM - 02:00 PM)")
            if custom_batch: selected_batch = custom_batch
            
        selected_date = f4.date_input("Date", value=datetime.date.today(), max_value=datetime.date.today(), key="f_d")

        search_q = st.text_input("🔍 Quick Search Name / Phone / Email ID", "")
        
        is_holiday = st.toggle("🌴 Mark as Public Holiday (No attendance deduction)")
        st.divider()

        if selected_batch == "🛑 Select Your Batch":
            st.warning("⚠️ Kripya attendance mark karne ke liye upar apna Batch select karein.")
        else:
            filtered = active_students
            if selected_course != "All Courses": filtered = [s for s in filtered if s.get("course") == selected_course]
            if selected_module != "All Modules": filtered = [s for s in filtered if s.get("module") == selected_module]
            if selected_batch and selected_batch != "➕ Add Custom Slot": 
                filtered = [s for s in filtered if s.get("batch_timing") == selected_batch]
            if search_q: 
                filtered = [s for s in filtered if search_q.lower() in s.get("name", "").lower() or search_q in s.get("phone", "") or search_q.lower() in s.get("email", "").lower()]

            if filtered or is_holiday:
                date_str = selected_date.strftime("%Y-%m-%d")
                topic = st.text_input("📖 Today's Syllabus / Topic", placeholder="E.G. PYTHON CONDITIONALS", disabled=is_holiday)
                records = {}
                
                if not is_holiday:
                    b1, b2, _ = st.columns([2, 2, 4])
                    if b1.button("✅ Mark All Present", use_container_width=True):
                        for s in filtered: st.session_state[f"att_{s['id']}"] = True
                        st.rerun()
                    if b2.button("❌ Mark All Absent", use_container_width=True):
                        for s in filtered: st.session_state[f"att_{s['id']}"] = False
                        st.rerun()

                    for s in filtered:
                        s_id = s["id"]
                        val = st.session_state.get(f"att_{s_id}", True)
                        ca, cb, cc, cd = st.columns([4, 2, 2, 1])
                        ca.markdown(f"**👤 {s.get('name')}** | `ID: {s.get('email', 'N/A')}` | 📞 `{s.get('phone', 'N/A')}`\n<small>{s.get('course')} | {s.get('batch_timing')}</small>", unsafe_allow_html=True)
                        cb.markdown("🟩 **Active**")
                        records[s_id] = "Present" if cc.toggle("Present", value=val, key=f"att_{s_id}") else "Absent"
                        if cd.button("🗑️", key=f"del_{s_id}"):
                            db.collection("students").document(s_id).update({"is_deleted": True})
                            st.rerun()

                if st.button("💾 Save Attendance", type="primary", use_container_width=True):
                    safe_batch = selected_batch.replace(' ', '_')
                    db.collection("attendance").document(f"{safe_batch}_{date_str}").set({
                        "course": selected_course, 
                        "batch": selected_batch, 
                        "date": date_str,
                        "topic": "PUBLIC HOLIDAY" if is_holiday else topic.upper(), 
                        "records": records,
                        "is_holiday": is_holiday 
                    }, merge=True)
                    st.toast(f"✅ {'Holiday' if is_holiday else 'Attendance'} Saved Successfully!")
            else:
                st.info("Koi active student nahi mila is batch ke liye.")

    # ------------------ TAB 2: ADD STUDENT ------------------
    with tab2:
        st.subheader("➕ Direct Student Registration")
        col1, col2 = st.columns(2)
        raw_name = col1.text_input("Full Name *", placeholder="E.G. MOHAMMAD EJAZ KHAN", key="s_name")
        s_email = col2.text_input("Student Email ID (User ID) *", placeholder="student@gmail.com", key="s_email")
        s_phone = col1.text_input("Mobile Number (Default Password) *", placeholder="10-digit number", key="s_phone")

        c_course, c_module = st.columns(2)
        selected_c = c_course.selectbox("Course *", list(COURSE_CATALOG.keys()), key="s_course")
        final_module = c_module.selectbox("Module *", COURSE_CATALOG.get(selected_c, ["GENERAL"]), key=f"s_mod_{selected_c}")

        c_time, c_custom = st.columns(2)
        reg_batch_opts = BASE_TIME_SLOTS + ["➕ Add Custom Slot"]
        slot_choice = c_time.selectbox("Batch Timing Slot *", reg_batch_opts, key="s_slot")
        if slot_choice == "➕ Add Custom Slot":
            slot_choice = c_custom.text_input("Custom Batch Time", key="s_cust_slot")

        if st.button("🚀 Add Student", type="primary", use_container_width=True):
            clean_s_email = s_email.strip().lower()
            clean_s_phone = s_phone.strip()
            formatted_name = raw_name.strip().upper()

            if not formatted_name or not clean_s_email or not clean_s_phone or not slot_choice:
                st.error("⚠️ Sabhi zaroori fields fill karein!")
            else:
                duplicate = [s for s in active_students if s.get("email") == clean_s_email or s.get("phone") == clean_s_phone]
                if duplicate:
                    st.warning("⚠️ Student pehle se register hai!")
                else:
                    student_payload = {
                        "username": clean_s_email, "user_id": clean_s_email, "email": clean_s_email,
                        "password": clean_s_phone, "name": formatted_name, "phone": clean_s_phone,
                        "course": selected_c, "module": final_module, "batch_timing": slot_choice,
                        "role": "student", "status": "approved", "is_approved": True, "is_deleted": False,
                        "created_at": firestore.SERVER_TIMESTAMP
                    }
                    db.collection("students").add(student_payload)
                    db.collection("users").document(clean_s_email).set(student_payload, merge=True)
                    st.success("🎉 Student Added Successfully!")
                    st.rerun()

    # ------------------ TAB 3: PENDING APPROVALS ------------------
    with tab3:
        if not pending_students:
            st.info("🎉 Koi pending student request nahi hai.")
        else:
            for ps in pending_students:
                p_id = ps["id"]
                p_email = ps.get("email", ps.get("user_id", "N/A"))
                col_info, col_app, col_rej = st.columns([5, 2, 2])
                col_info.markdown(f"**👤 {ps.get('name', 'N/A')}** (`{p_email}`)\n📞 `{ps.get('phone', 'N/A')}`", unsafe_allow_html=True)
                
                if col_app.button("✅ Approve", key=f"app_{p_id}", type="primary"):
                    db.collection("students").document(p_id).update({"status": "approved", "is_approved": True})
                    db.collection("users").document(p_email).set({"status": "approved", "is_approved": True}, merge=True)
                    st.rerun()

                if col_rej.button("❌ Reject", key=f"rej_{p_id}"):
                    db.collection("students").document(p_id).update({"is_deleted": True, "status": "rejected"})
                    st.rerun()

    # ------------------ TAB 4: BATCH RE-ALLOCATOR ------------------
    with tab4:
        if not active_students:
            st.info("Koi active student nahi mila.")
        else:
            student_opts = {f"{s.get('name')} | ({s.get('batch_timing')})": s for s in active_students}
            target_student = student_opts[st.selectbox("🎯 Select Student", list(student_opts.keys()))]

            u_col1, u_col2, u_col3 = st.columns(3)
            new_c = u_col1.selectbox("New Course", list(COURSE_CATALOG.keys()), key="re_c")
            new_m = u_col2.selectbox("New Module", COURSE_CATALOG.get(new_c, ["GENERAL"]), key="re_m")
            
            re_batch_opts = BASE_TIME_SLOTS + ["➕ Add Custom Slot"]
            new_slot = u_col3.selectbox("New Batch Slot", re_batch_opts, key="re_s")
            if new_slot == "➕ Add Custom Slot":
                new_slot = u_col3.text_input("Enter Custom Slot", key="re_cust_slot")

            if st.button("💾 Apply Update", type="primary"):
                db.collection("students").document(target_student["id"]).update({
                    "course": new_c, "module": new_m, "batch_timing": new_slot
                })
                st.rerun()

    # ------------------ TAB 5: TRASH ------------------
    with tab5:
        if not archived_students:
            st.info("Trash empty hai.")
        else:
            for s in archived_students:
                ca, cb, cc = st.columns([4, 2, 2])
                ca.write(f"❌ **{s.get('name')}** (`{s.get('email', 'N/A')}`)")
                if cb.button("🔄 Restore", key=f"r_{s['id']}"):
                    db.collection("students").document(s['id']).update({"is_deleted": False})
                    st.rerun()
                if cc.button("🔥 Delete Permanently", key=f"d_{s['id']}"):
                    db.collection("students").document(s['id']).delete()
                    st.rerun()