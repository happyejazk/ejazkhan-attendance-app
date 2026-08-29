#admin_panel.py
import streamlit as st
from firebase_admin import firestore
from datetime import datetime
import pytz

def get_db():
    return firestore.client()

def get_time_greeting():
    """IST Time ke hisaab se dynamic greeting generate karta hai."""
    ist_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_tz)
    hour = current_time.hour

    if 5 <= hour < 12:
        return "Good Morning 🌅"
    elif 12 <= hour < 17:
        return "Good Afternoon ☀️"
    elif 17 <= hour < 21:
        return "Good Evening 🌇"
    else:
        return "Good Night 🌙"

def render_admin_panel(current_user_email):
    db = get_db()
    
    # 1. Current logged-in user (Admin/Superadmin) ki details fetch karna
    current_user_ref = db.collection("users").where("email", "==", current_user_email).stream()
    current_user_data = {}
    doc_id = None
    for doc in current_user_ref:
        current_user_data = doc.to_dict()
        doc_id = doc.id
        break
        
    if not current_user_data:
        st.error("⚠️ Access Denied: User details not found.")
        return

    admin_name = current_user_data.get("name", "Admin")
    admin_role = current_user_data.get("role", "admin").lower() # 'admin' or 'superadmin'
    
    # 2. Top Welcome Banner with Time Greetings
    greeting = get_time_greeting()
    
    col_img, col_txt = st.columns([1, 8])
    with col_img:
        # Profile pic default
        st.image(st.session_state.get("user_picture", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"), width=80)
    with col_txt:
        st.title(f"{greeting}, {admin_name}! 👋")
        if admin_role == "superadmin":
            st.caption("🛡️ **System Role:** SUPERADMIN (Absolute Powers Enabled) | You can manage all users and admins.")
        else:
            st.caption("🛠️ **System Role:** ADMIN | You can manage students and pending approvals.")

    st.divider()

    # 3. Tabbed UI for neat organization
    tab_pending, tab_manage = st.tabs(["🕒 Pending Approvals", "👥 Manage All Users"])

    # ==========================================
    # TAB 1: PENDING APPROVALS
    # ==========================================
    with tab_pending:
        st.subheader("Action Required: Pending User Approvals")
        
        # Fetch users with status 'pending' or missing status
        pending_users = list(db.collection("users").where("status", "==", "pending").stream())
        
        if not pending_users:
            st.success("🎉 Koi bhi user approval ke liye pending nahi hai!")
        else:
            for doc in pending_users:
                user = doc.to_dict()
                u_id = doc.id
                u_name = user.get("name", "No Name")
                u_email = user.get("email", "No Email")
                u_mobile = user.get("mobile", "N/A")
                
                with st.expander(f"👤 {u_name} ({u_email})"):
                    st.write(f"**Mobile:** {u_mobile}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✅ Approve User", key=f"app_{u_id}", type="primary"):
                            db.collection("users").document(u_id).update({
                                "status": "approved",
                                "role": "student" # Default role on approval
                            })
                            st.success(f"{u_name} approved successfully! Please refresh.")
                            st.rerun()
                            
                    with col2:
                        if st.button("❌ Reject & Delete", key=f"rej_{u_id}"):
                            db.collection("users").document(u_id).delete()
                            st.warning(f"Registration for {u_name} rejected and deleted.")
                            st.rerun()

    # ==========================================
    # TAB 2: MANAGE ALL USERS (Editable Forms)
    # ==========================================
    with tab_manage:
        st.subheader("Complete User Directory")
        
        # Search Box
        search_query = st.text_input("🔍 Search user by Name or Email...").lower()
        
        all_users = list(db.collection("users").stream())
        
        for doc in all_users:
            user = doc.to_dict()
            u_id = doc.id
            u_name = user.get("name", "")
            u_email = user.get("email", "")
            u_role = user.get("role", "student")
            
            # Filtering logic
            if search_query and (search_query not in u_name.lower() and search_query not in u_email.lower()):
                continue
                
            # Badge setup based on role
            role_badge = "👑 Superadmin" if u_role == "superadmin" else "🛠️ Admin" if u_role == "admin" else "🎓 Student"
            
            with st.expander(f"{role_badge} | {u_name} - {u_email}"):
                with st.form(key=f"form_{u_id}"):
                    st.markdown("### Update Details")
                    
                    # Editable fields
                    new_name = st.text_input("Name", value=u_name)
                    new_mobile = st.text_input("Mobile Number", value=user.get("mobile", ""))
                    
                    courses_list = ["None", "CCC", "O Level", "ADCA", "Tally Prime"]
                    user_course = user.get("course", "None")
                    course_index = courses_list.index(user_course) if user_course in courses_list else 0
                    new_course = st.selectbox("Course", courses_list, index=course_index)
                    
                    new_module = st.text_input("Module", value=user.get("module", ""))
                    
                    # Safe Status Selectbox with 'approved' included
                    status_options = ["active", "approved", "pending", "suspended"]
                    current_status = user.get("status", "active")
                    status_index = status_options.index(current_status) if current_status in status_options else 0
                    new_status = st.selectbox("Account Status", status_options, index=status_index)
                    
                    # Role Dropdown (Only Superadmin can assign Superadmin role)
                    role_options = ["student", "admin"]
                    if admin_role == "superadmin":
                        role_options.append("superadmin")
                    
                    current_role_index = role_options.index(u_role) if u_role in role_options else 0
                    new_role = st.selectbox("System Role", role_options, index=current_role_index)

                    col_update, col_del = st.columns(2)
                    
                    with col_update:
                        submit_update = st.form_submit_button("💾 Save Updates", type="primary")
                        if submit_update:
                            db.collection("users").document(u_id).update({
                                "name": new_name,
                                "mobile": new_mobile,
                                "course": new_course,
                                "module": new_module,
                                "status": new_status,
                                "role": new_role
                            })
                            st.success(f"{new_name}'s profile updated successfully!")
                            st.rerun()

                # Delete Button Logic OUTSIDE the form to avoid accidental form submissions
                can_delete = False
                if admin_role == "superadmin":
                    can_delete = True
                elif admin_role == "admin" and u_role not in ["admin", "superadmin"]:
                    can_delete = True
                
                if can_delete:
                    if st.button(f"🗑️ Delete Account ({u_name})", key=f"del_{u_id}"):
                        if u_email == current_user_email:
                            st.error("You cannot delete your own active session account!")
                        else:
                            db.collection("users").document(u_id).delete()
                            st.success(f"User {u_name} has been permanently deleted.")
                            st.rerun()
                else:
                    st.info("🔒 You do not have permission to delete this user.")