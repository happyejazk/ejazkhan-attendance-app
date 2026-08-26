import streamlit as st
from firebase_admin import firestore

try:
    from email_service import send_welcome_credentials
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False

def get_db():
    return firestore.client()

def handle_oauth_or_custom_registration(email, name, role="student", phone=""):
    """
    Registers Google OAuth / Custom Users with persistent User ID, Password, Role, and Welcome Email
    """
    db = get_db()
    clean_email = email.strip().lower()
    default_password = phone.strip() if phone else "123456"

    user_data = {
        "user_id": clean_email,         # USER ID = EMAIL ID
        "email": clean_email,
        "name": name.strip().upper(),
        "phone": phone.strip(),
        "role": role.lower(),           # 'student', 'teacher', or 'admin'
        "password": default_password,   # Mobile Number or Default Pass
        "created_at": firestore.SERVER_TIMESTAMP
    }

    # Save/Update in central 'users' collection
    db.collection("users").document(clean_email).set(user_data, merge=True)

    # If role is student, sync with 'students' collection too
    if role.lower() == "student":
        db.collection("students").add(user_data | {"is_deleted": False, "batch_timing": "Unassigned"})

    # Automatic Welcome Email Dispatcher
    email_status = ""
    if EMAIL_ENABLED:
        sent_ok, msg = send_welcome_credentials(clean_email, name.strip().upper(), clean_email, default_password, role=role.capitalize())
        email_status = " | 📩 Email Sent!" if sent_ok else f" | ⚠️ Email skipped ({msg})"

    return True, f"User '{clean_email}' registered as [{role.upper()}]{email_status}"

def show_registration_page():
    st.title("📝 AIM ERP - User Registration")
    st.caption("Register new Student, Teacher, or Admin Profile")

    with st.form("user_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name *", placeholder="E.G. MOHAMMAD EJAZ KHAN")
        email = col2.text_input("Email Address (User ID) *", placeholder="user@gmail.com")
        
        col3, col4 = st.columns(2)
        phone = col3.text_input("Mobile Number (Default Password)", placeholder="10-digit number")
        role = col4.selectbox("User Role *", ["Student", "Teacher", "Admin"])

        submit_btn = st.form_submit_button("🚀 Register User", type="primary", use_container_width=True)

        if submit_btn:
            if not name.strip() or not email.strip():
                st.error("⚠️ Full Name aur Email ID fill karna mandatory hai!")
            else:
                success, msg = handle_oauth_or_custom_registration(email, name, role.lower(), phone)
                if success:
                    st.success(f"🎉 {msg}")
                else:
                    st.error(f"⚠️ {msg}")