import streamlit as st
import datetime
from firebase_admin import firestore
from course_manager import render_course_manager

try:
    from email_service import send_welcome_credentials
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False

# Yahan apni application ka live link daal dijiye
APP_URL = "https://attendance-app.streamlit.app" 

def get_db():
    return firestore.client()

TIME_SLOTS = [
    "07:00 AM - 08:00 AM", "08:00 AM - 09:00 AM", "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM"
]

def render_superadmin_panel(current_user_email):
    db = get_db()

    # 1. TIME-BASED GREETING LOGIC
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        greeting = "Good Morning"
    elif 12 <= current_hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    # 2. FETCH ADMIN NAME FROM DATABASE
    admin_doc = db.collection("users").document(current_user_email).get()
    admin_name = "SUPER ADMIN"
    if admin_doc.exists:
        admin_data = admin_doc.to_dict()
        admin_name = admin_data.get("name", "SUPER ADMIN").upper()

    # Custom High-Contrast & Modern Styling
    st.markdown("""
        <style>
        .super-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #38bdf8;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .super-title { font-size: 28px; font-weight: 800; color: #38bdf8; margin: 0 0 5px 0; text-transform: uppercase; }
        .super-sub { font-size: 14px; color: #94a3b8; font-weight: 500; }
        .user-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .bright-txt { color: #f8fafc; font-weight: 600; }
        .accent-txt { color: #38bdf8; font-size: 13px; }
        </style>
    """, unsafe_allow_html=True)

    # 3. GRAND WELCOME UI
    st.markdown(f"""
        <div class="super-header">
            <div class="super-title">👋 {greeting}, {admin_name}!</div>
            <div class="super-sub">🛡️ Super Admin Control Hub | ID: <b style="color:#00E676;">{current_user_email}</b></div>
        </div>
    """, unsafe_allow_html=True)

    # Fetch live users from Firestore
    all_users_ref = db.collection("users")
    all_users_docs = [doc.to_dict() | {"id": doc.id} for doc in all_users_ref.stream()]
    
    pending_users = [u for u in all_users_docs if not u.get("is_deleted", False) and u.get("status") == "pending"]
    archived_users = [u for u in all_users_docs if u.get("is_deleted", False)]

    # Fetch courses from Firestore (Dynamic, no hardcoding)
    courses_ref = db.collection("courses")
    course_docs = {doc.id: doc.to_dict() for doc in courses_ref.stream()}
    course_list = list(course_docs.keys()) if course_docs else ["Please Add A Course"]

    # Top Level Menu Tabs
    tab_pending, tab_add, tab_users, tab_courses, tab_att, tab_trash = st.tabs([
        f"⏳ Pending Requests ({len(pending_users)})" if pending_users else "⏳ Pending Requests",
        "⚡ Direct Add User",
        "👥 Organized User Directory",
        "📚 Course & Topic Manager",
        "📋 Global Attendance",
        "🗑️ Soft-Deleted Trash"
    ])

    # =========================================================================
    # TAB 1: REAL-TIME PENDING APPROVALS
    # =========================================================================
    with tab_pending:
        st.subheader("⏳ Pending Registrations")
        st.caption("Self-registered ya OAuth users ko yahan se approve karein.")
        
        if not pending_users:
            st.info("🎉 Koi bhi user approval ke liye pending nahi hai.")
        else:
            for pu in pending_users:
                u_id = pu["id"]
                u_email = pu.get("email", pu.get("user_id", "N/A"))
                u_name = pu.get("name", "UN-NAMED USER")
                u_phone = pu.get("phone", pu.get("mobile", "N/A"))
                u_role = pu.get("role", "student")

                col_info, col_app, col_rej = st.columns([5, 2, 2])
                col_info.markdown(f"**👤 {u_name}** (`{u_email}`)\n📞 `{u_phone}` | Requested Role: `<b style='color:#fbbf24;'>{u_role.upper()}</b>`", unsafe_allow_html=True)
                
                if col_app.button("✅ Approve & Send Email", key=f"app_{u_id}", type="primary", use_container_width=True):
                    db.collection("users").document(u_id).update({
                        "status": "approved",
                        "is_approved": True,
                        "is_deleted": False
                    })

                    if u_role.lower() == "student":
                        st_ref = db.collection("students").where("email", "==", u_email).stream()
                        st_found = False
                        for st_doc in st_ref:
                            db.collection("students").document(st_doc.id).update({"status": "approved", "is_approved": True, "is_deleted": False})
                            st_found = True
                        if not st_found:
                            db.collection("students").add(pu | {"status": "approved", "is_approved": True, "is_deleted": False})

                    email_msg = ""
                    if EMAIL_ENABLED:
                        # Email Service me app_url send kar rahe hain
                        sent_ok, msg = send_welcome_credentials(u_email, u_name, u_email, u_phone, role=u_role.capitalize(), app_url=APP_URL)
                        email_msg = " | 📩 Email Dispatched with App Link!" if sent_ok else f" | ⚠️ Email skipped ({msg})"

                    st.toast(f"✅ Approved {u_name}!{email_msg}")
                    st.rerun()

                if col_rej.button("❌ Reject", key=f"rej_{u_id}", use_container_width=True):
                    db.collection("users").document(u_id).update({"status": "rejected", "is_deleted": True})
                    st.toast(f"🚫 Rejected {u_name}.")
                    st.rerun()

    # =========================================================================
    # TAB 2: DIRECT ADD USER (FORM AUTO-CLEAR)
    # =========================================================================
    with tab_add:
        st.subheader("⚡ Direct Instant User Registration")

        if "super_add_success" in st.session_state:
            st.success(st.session_state["super_add_success"], icon="🎉")
            if st.button("✖️ Clear Notification", key="clr_super_notif"):
                del st.session_state["super_add_success"]
                st.rerun()

        with st.form("super_add_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            raw_name = c1.text_input("Full Name *", placeholder="E.G. MOHAMMAD EJAZ KHAN")
            u_email = c2.text_input("Email ID (User ID) *", placeholder="user@gmail.com")
            
            c3, c4 = st.columns(2)
            u_phone = c3.text_input("Mobile Number (Default Password) *", placeholder="10-digit number")
            target_role = c4.selectbox("Select Role *", ["Student", "Teacher", "Admin", "Superadmin"])

            c5, c6 = st.columns(2)
            selected_c = c5.selectbox("Assign Course (If Student)", course_list)
            slot_choice = c6.selectbox("Batch Timing Slot", TIME_SLOTS)

            submit_btn = st.form_submit_button("🚀 Direct Add & Approve User", type="primary", use_container_width=True)

            if submit_btn:
                clean_email = u_email.strip().lower()
                clean_phone = u_phone.strip()
                formatted_name = raw_name.strip().upper()

                if not formatted_name or not clean_email or not clean_phone:
                    st.error("⚠️ Name, Email ID aur Mobile Number required hain!")
                else:
                    user_payload = {
                        "username": clean_email,
                        "user_id": clean_email,
                        "email": clean_email,
                        "password": clean_phone,
                        "name": formatted_name,
                        "phone": clean_phone,
                        "mobile": clean_phone,
                        "course": selected_c if target_role == "Student" else "N/A",
                        "batch_timing": slot_choice if target_role == "Student" else "N/A",
                        "role": target_role.lower(),
                        "status": "approved",
                        "is_approved": True,
                        "is_deleted": False,
                        "created_at": firestore.SERVER_TIMESTAMP
                    }

                    db.collection("users").document(clean_email).set(user_payload, merge=True)
                    if target_role.lower() == "student":
                        db.collection("students").add(user_payload)

                    email_status = ""
                    if EMAIL_ENABLED:
                        # Pass app_url to email service
                        sent_ok, msg = send_welcome_credentials(clean_email, formatted_name, clean_email, clean_phone, role=target_role, app_url=APP_URL)
                        email_status = " | 📩 Credentials & App Link Sent!" if sent_ok else f" | ⚠️ Email skipped ({msg})"

                    st.session_state["super_add_success"] = f"🎉 User **{clean_email}** ({target_role}) created & approved!{email_status}"
                    st.rerun()

    # =========================================================================
    # TAB 3: ORGANIZED USER DIRECTORY
    # =========================================================================
    with tab_users:
        st.subheader("👥 Categorized User Directory")
        st.caption("Admins, Teachers, aur Students ki alag-alag structured lists:")

        search_q = st.text_input("🔍 Quick Search User by Name / Email / Phone...", key="super_search_dir").lower()

        active_users = [u for u in all_users_docs if not u.get("is_deleted", False)]
        if search_q:
            active_users = [u for u in active_users if search_q in u.get("name", "").lower() or search_q in u.get("email", "").lower() or search_q in u.get("phone", "")]

        u_tab_super, u_tab_admin, u_tab_teacher, u_tab_student = st.tabs([
            f"👑 Super Admins ({len([u for u in active_users if u.get('role') == 'superadmin'])})",
            f"🛠️ Admins ({len([u for u in active_users if u.get('role') == 'admin'])})",
            f"👨‍🏫 Teachers ({len([u for u in active_users if u.get('role') == 'teacher'])})",
            f"🎓 Students ({len([u for u in active_users if u.get('role') == 'student'])})"
        ])

        def render_user_category_list(user_sub_list):
            if not user_sub_list:
                st.info("Koi user nahi mila.")
                return

            for u in user_sub_list:
                u_id = u["id"]
                u_name = u.get("name", "N/A")
                u_email = u.get("email", "N/A")
                u_role = u.get("role", "student")
                u_phone = u.get("phone", u.get("mobile", "N/A"))

                with st.expander(f"👤 {u_name} | `{u_email}` | 📞 {u_phone}"):
                    with st.form(key=f"edit_usr_{u_id}"):
                        c_a, c_b = st.columns(2)
                        edit_name = c_a.text_input("Full Name", value=u_name)
                        edit_phone = c_b.text_input("Mobile / Password", value=u_phone)

                        c_c, c_d = st.columns(2)
                        role_options = ["student", "teacher", "admin", "superadmin"]
                        edit_role = c_c.selectbox("Role", role_options, index=role_options.index(u_role) if u_role in role_options else 0)
                        
                        edit_course = c_d.selectbox("Assigned Course", course_list, index=course_list.index(u.get("course")) if u.get("course") in course_list else 0) if u_role == "student" else "N/A"

                        if st.form_submit_button("✏️ Update Profile Details", type="primary"):
                            db.collection("users").document(u_id).update({
                                "name": edit_name.strip().upper(),
                                "phone": edit_phone.strip(),
                                "mobile": edit_phone.strip(),
                                "password": edit_phone.strip(),
                                "role": edit_role,
                                "course": edit_course
                            })
                            st.success(f"{edit_name} ka record update ho gaya!")
                            st.rerun()

                    col_s_del, col_p_del = st.columns(2)
                    if col_s_del.button("⚠️ Soft Delete (Archive)", key=f"soft_usr_{u_id}"):
                        db.collection("users").document(u_id).update({"is_deleted": True, "status": "deactivated"})
                        st.warning(f"{u_name} deactivated.")
                        st.rerun()

                    if col_p_del.button("🗑️ Delete Permanently", key=f"perm_usr_{u_id}"):
                        if u_email.lower() == current_user_email.lower():
                            st.error("⚠️ Aap khud ki active session ID delete nahi kar sakte!")
                        else:
                            db.collection("users").document(u_id).delete()
                            st.error(f"{u_name} deleted permanently!")
                            st.rerun()

        with u_tab_super:
            render_user_category_list([u for u in active_users if u.get("role") == "superadmin"])
        with u_tab_admin:
            render_user_category_list([u for u in active_users if u.get("role") == "admin"])
        with u_tab_teacher:
            render_user_category_list([u for u in active_users if u.get("role") == "teacher"])
        with u_tab_student:
            render_user_category_list([u for u in active_users if u.get("role") == "student"])

    # =========================================================================
    # TAB 4: DEDICATED COURSE & TOPIC MANAGER 
    # =========================================================================
    with tab_courses:
        render_course_manager()

    # =========================================================================
    # TAB 5: GLOBAL ATTENDANCE MANAGEMENT
    # =========================================================================
    with tab_att:
        st.subheader("📋 Global Attendance Records & Override")
        st.info("Super Admin attendance record check kar sakta hai aur zarurat padne par slot clean kar sakta hai.")
        
        c1, c2 = st.columns(2)
        att_date = c1.date_input("Select Attendance Date", value=datetime.date.today(), key="sa_att_d")
        att_slot = c2.selectbox("Select Batch Timing Slot", TIME_SLOTS, key="sa_att_s")

        doc_key = f"{att_slot.replace(' ', '_')}_{att_date.strftime('%Y-%m-%d')}"
        att_doc = db.collection("attendance").document(doc_key).get()

        if att_doc.exists:
            att_data = att_doc.to_dict()
            st.success(f"Attendance Record Found for **{att_slot}** on **{att_date}**")
            st.json(att_data.get("records", {}))

            if st.button("🗑️ Clear / Delete Attendance for this Slot", type="primary"):
                db.collection("attendance").document(doc_key).delete()
                st.warning("Attendance record removed.")
                st.rerun()
        else:
            st.info("Is date aur slot ke liye abhi koi attendance record nahi hai.")

    # =========================================================================
    # TAB 6: SOFT-DELETED / TRASH PROFILES
    # =========================================================================
    with tab_trash:
        st.subheader("🗑️ Soft-Deleted / Archived User Profiles")
        if not archived_users:
            st.info("Trash empty hai.")
        else:
            for au in archived_users:
                ca, cb, cc = st.columns([4, 2, 2])
                ca.write(f"❌ **{au.get('name')}** (`{au.get('email', 'N/A')}`) - Role: `{au.get('role')}`")
                if cb.button("🔄 Restore", key=f"r_sa_{au['id']}"):
                    db.collection("users").document(au['id']).update({"is_deleted": False, "status": "approved"})
                    st.rerun()
                if cc.button("🔥 Permanent Delete", key=f"d_sa_{au['id']}"):
                    db.collection("users").document(au['id']).delete()
                    st.rerun()