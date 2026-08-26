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

COURSE_CATALOG = {
    "O Level": ["M1-R5: IT Tools", "M2-R5: Web Designing", "M3-R5: Python", "M4-R5: IoT"],
    "ADCA": ["Module 1: Office", "Module 2: Graphic", "Module 3: Web", "Module 4: Tally"],
    "DCA": ["Office Automation", "Database Management", "Tally Essentials"],
    "CCC": ["Computer Basics", "Cyber Security"],
    "Tally Prime": ["Basic Accounting", "Advanced Inventory"],
    "Other / Custom Course": ["Custom Module"]
}

TIME_SLOTS = [
    "07:00 AM - 08:00 AM", "08:00 AM - 09:00 AM", "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM"
]

def render_teacher_panel():
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

    st.title("👨‍🏫 AIM ERP - Teacher Control Center")
    db = get_db()

    # Stream Firestore Collections
    students_ref = db.collection("students")
    all_docs = [doc.to_dict() | {"id": doc.id} for doc in students_ref.stream()]
    
    # Filter Active, Archived & Pending
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
        f1, f2, f3, f4 = st.columns(4)
        selected_course = f1.selectbox("Course", ["All Courses"] + sorted(list(set([s.get("course") for s in active_students if s.get("course")]))), key="f_c")
        selected_module = f2.selectbox("Module", ["All Modules"] + sorted(list(set([s.get("module") for s in active_students if s.get("module")]))), key="f_m")
        selected_batch = f3.selectbox("Batch Slot", ["All Timings"] + sorted(list(set([s.get("batch_timing") for s in active_students if s.get("batch_timing")]))), key="f_b")
        selected_date = f4.date_input("Date", value=datetime.date.today(), key="f_d")

        search_q = st.text_input("🔍 Quick Search Name / Phone / Email ID", "")

        filtered = active_students
        if selected_course != "All Courses": filtered = [s for s in filtered if s.get("course") == selected_course]
        if selected_module != "All Modules": filtered = [s for s in filtered if s.get("module") == selected_module]
        if selected_batch != "All Timings": filtered = [s for s in filtered if s.get("batch_timing") == selected_batch]
        if search_q: filtered = [s for s in filtered if search_q.lower() in s.get("name", "").lower() or search_q in s.get("phone", "") or search_q.lower() in s.get("email", "").lower()]

        st.divider()

        if filtered:
            date_str = selected_date.strftime("%Y-%m-%d")
            topic = st.text_input("📖 Today's Syllabus / Topic", placeholder="E.G. PYTHON CONDITIONALS")

            b1, b2, _ = st.columns([2, 2, 4])
            if b1.button("✅ Mark All Present", use_container_width=True):
                for s in filtered: st.session_state[f"att_{s['id']}"] = True
                st.rerun()
            if b2.button("❌ Mark All Absent", use_container_width=True):
                for s in filtered: st.session_state[f"att_{s['id']}"] = False
                st.rerun()

            records = {}
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
                db.collection("attendance").document(f"{selected_batch.replace(' ', '_')}_{date_str}").set({
                    "course": selected_course, "batch": selected_batch, "date": date_str,
                    "topic": topic.upper(), "records": records
                }, merge=True)
                st.toast("✅ Attendance Saved Successfully!")
        else:
            st.info("Koi active student nahi mila.")

    # ------------------ TAB 2: ADD STUDENT (USER ID = EMAIL) ------------------
    with tab2:
        st.subheader("➕ Direct Student Registration")

        if "recent_success_msg" in st.session_state:
            st.success(st.session_state["recent_success_msg"], icon="🎉")
            if st.button("✖️ Clear Notification"):
                del st.session_state["recent_success_msg"]
                st.rerun()

        col1, col2 = st.columns(2)
        raw_name = col1.text_input("Full Name *", placeholder="E.G. MOHAMMAD EJAZ KHAN", key="s_name")
        s_email = col2.text_input("Student Email ID (User ID) *", placeholder="student@gmail.com", key="s_email")
        s_phone = col1.text_input("Mobile Number (Default Password) *", placeholder="10-digit number", key="s_phone")

        c_course, c_module = st.columns(2)
        selected_c = c_course.selectbox("Course *", list(COURSE_CATALOG.keys()), key="s_course")
        final_course = selected_c
        final_module = c_module.selectbox("Module *", COURSE_CATALOG[selected_c], key=f"s_mod_{selected_c}") if selected_c != "Other / Custom Course" else "GENERAL"

        c_time, c_custom = st.columns(2)
        slot_choice = c_time.selectbox("Batch Timing Slot *", TIME_SLOTS, key="s_slot")

        if st.button("🚀 Add Student", type="primary", use_container_width=True):
            clean_email = s_email.strip().lower()
            clean_phone = s_phone.strip()
            formatted_name = raw_name.strip().upper()

            if not formatted_name or not clean_email or not clean_phone:
                st.error("⚠️ Name, Email ID (User ID) aur Mobile Number fill karna zaroori hai!")
            else:
                duplicate = [s for s in active_students if s.get("email") == clean_email or s.get("phone") == clean_phone]
                if duplicate:
                    st.warning(f"⚠️ Student with Email '{clean_email}' or Phone '{clean_phone}' pehle se register hai!")
                else:
                    student_payload = {
                        "username": clean_email,
                        "user_id": clean_email,      # USER ID = EMAIL ID
                        "email": clean_email,
                        "password": clean_phone,     # DEFAULT PASSWORD = MOBILE
                        "name": formatted_name,
                        "phone": clean_phone,
                        "course": final_course,
                        "module": final_module,
                        "batch_timing": slot_choice,
                        "role": "student",
                        "status": "approved",        # Teacher created = Auto approved
                        "is_approved": True,         # Fixed Login Access
                        "is_deleted": False,
                        "created_at": firestore.SERVER_TIMESTAMP
                    }

                    # Sync in both 'students' and 'users' collections
                    db.collection("students").add(student_payload)
                    db.collection("users").document(clean_email).set(student_payload, merge=True)

                    email_status = ""
                    if EMAIL_ENABLED:
                        sent_ok, msg = send_welcome_credentials(clean_email, formatted_name, clean_email, clean_phone, role="Student")
                        email_status = " | 📩 Email Sent!" if sent_ok else f" | ⚠️ Email skipped ({msg})"

                    st.session_state["recent_success_msg"] = (
                        f"🎉 **Student Created & Approved Successfully!**\n\n"
                        f"• **User ID**: `{clean_email}`\n"
                        f"• **Password**: `{clean_phone}`\n"
                        f"• **Batch Slot**: {slot_choice}{email_status}"
                    )
                    st.rerun()

    # ------------------ TAB 3: PENDING APPROVALS ------------------
    with tab3:
        st.subheader("⏳ Pending Student Approval Requests")
        st.caption("Self-registered ya Google OAuth wale students ko yahan se Approve karein taaki wo login kar sakein.")

        if not pending_students:
            st.info("🎉 Koi pending student request nahi hai.")
        else:
            for ps in pending_students:
                p_id = ps["id"]
                p_email = ps.get("email", ps.get("user_id", "N/A"))
                p_name = ps.get("name", "UN-NAMED STUDENT")
                p_phone = ps.get("phone", "N/A")

                col_info, col_app, col_rej = st.columns([5, 2, 2])
                col_info.markdown(f"**👤 {p_name}** (`{p_email}`)\n📞 `{p_phone}` | Course: {ps.get('course', 'Unassigned')}", unsafe_allow_html=True)
                
                if col_app.button("✅ Approve", key=f"app_{p_id}", type="primary", use_container_width=True):
                    # Update in 'students'
                    db.collection("students").document(p_id).update({"status": "approved", "is_approved": True})
                    # Update in 'users'
                    db.collection("users").document(p_email).set({"status": "approved", "is_approved": True}, merge=True)
                    st.toast(f"✅ {p_name} Approved for Login!")
                    st.rerun()

                if col_rej.button("❌ Reject", key=f"rej_{p_id}", use_container_width=True):
                    db.collection("students").document(p_id).update({"is_deleted": True, "status": "rejected"})
                    st.toast(f"🚫 {p_name} Rejected.")
                    st.rerun()

    # ------------------ TAB 4: BATCH & COURSE RE-ALLOCATOR ------------------
    with tab4:
        st.subheader("🔄 Dynamic Batch & Course Re-Allocator")
        st.caption("Kisi bhi student ka Batch Slot, Course, ya Module 1-Click me Update karein.")

        if not active_students:
            st.info("Koi active student nahi mila.")
        else:
            student_opts = {f"{s.get('name')} | {s.get('email', 'N/A')} | ({s.get('batch_timing')})": s for s in active_students}
            selected_st_key = st.selectbox("🎯 Select Student to Re-Assign", list(student_opts.keys()))
            target_student = student_opts[selected_st_key]

            st.info(f"Currently Assigned: **{target_student.get('course')}** ({target_student.get('module')}) | Slot: **{target_student.get('batch_timing')}**")

            u_col1, u_col2, u_col3 = st.columns(3)
            new_c = u_col1.selectbox("New Course", list(COURSE_CATALOG.keys()), key="re_c")
            new_m = u_col2.selectbox("New Module", COURSE_CATALOG[new_c], key="re_m")
            new_slot = u_col3.selectbox("New Batch Slot", TIME_SLOTS, key="re_s")

            if st.button("💾 Apply & Update Batch Allocation", type="primary", use_container_width=True):
                db.collection("students").document(target_student["id"]).update({
                    "course": new_c,
                    "module": new_m,
                    "batch_timing": new_slot
                })
                st.success(f"✅ {target_student.get('name')} ka batch successfully change karke '{new_slot}' kar diya gaya!")
                st.rerun()

    # ------------------ TAB 5: TRASH & RESTORE ------------------
    with tab5:
        st.subheader("🗑️ Trash & Archived Profiles")
        if not archived_students:
            st.info("Trash empty hai.")
        else:
            for s in archived_students:
                ca, cb, cc = st.columns([4, 2, 2])
                ca.write(f"❌ **{s.get('name')}** (`{s.get('email', 'N/A')}`) - {s.get('course')}")
                if cb.button("🔄 Restore", key=f"r_{s['id']}"):
                    db.collection("students").document(s['id']).update({"is_deleted": False})
                    st.rerun()
                if cc.button("🔥 Delete Permanently", key=f"d_{s['id']}"):
                    db.collection("students").document(s['id']).delete()
                    st.rerun()