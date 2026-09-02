import streamlit as st
from database import init_firebase

def render_update_profile(user_email):
    db = init_firebase()
    
    st.title("⚙️ Update Profile")
    st.caption("Manage your personal details and security.")

    # 1. Fetch current user data from 'users' collection
    user_ref = db.collection("users").document(user_email)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        st.error("⚠️ User profile nahi mili. Kripya admin se contact karein.")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state["current_view"] = "dashboard" # Aapke app ke routing state ka naam yahan dalein
            st.rerun()
        return

    user_data = user_doc.to_dict()
    current_name = user_data.get("name", "")
    current_phone = user_data.get("phone", "")
    current_password = user_data.get("password", "")
    role = user_data.get("role", "student")

    # 2. Render Update Form
    with st.form("update_profile_form"):
        st.subheader("Personal Information")
        
        c1, c2 = st.columns(2)
        # Read-only fields
        c1.text_input("Email ID (User ID)", value=user_email, disabled=True)
        c2.text_input("Account Role", value=role.upper(), disabled=True)

        # Editable fields
        new_name = st.text_input("Full Name", value=current_name)
        new_phone = st.text_input("Mobile Number", value=current_phone)
        
        st.subheader("Security")
        new_password = st.text_input("Password", value=current_password, type="password")

        submit_btn = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)

        if submit_btn:
            if not new_name.strip() or not new_phone.strip() or not new_password.strip():
                st.error("⚠️ Sabhi editable fields fill karna zaroori hai!")
            else:
                updated_payload = {
                    "name": new_name.strip().upper(),
                    "phone": new_phone.strip(),
                    "mobile": new_phone.strip(), # Maintaining dual-keys if used elsewhere
                    "password": new_password.strip()
                }
                
                try:
                    # Update in 'users' collection
                    user_ref.update(updated_payload)

                    # Dual-Sync: Agar student hai toh 'students' collection me bhi update karein
                    if role.lower() == "student":
                        student_query = db.collection("students").where("email", "==", user_email).stream()
                        for doc in student_query:
                            db.collection("students").document(doc.id).update(updated_payload)
                    
                    st.success("🎉 Profile successfully updated!")
                    
                    # Update current session variables to reflect changes instantly
                    st.session_state["user_name"] = updated_payload["name"]
                    
                except Exception as e:
                    st.error(f"⚠️ Error updating profile: {e}")

    # 3. Navigation - Back to main panel
    st.markdown("---")
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        # Update this state key based on how your app.py handles page routing
        st.session_state["show_profile_update"] = False 
        st.rerun()