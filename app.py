import streamlit as st
import urllib.parse
import requests
from login import render_login_page
from student_panel import render_student_panel
from admin_panel import render_admin_panel
from database import (
    authenticate_user,
    get_user_by_email,
    get_pending_users,
    get_all_approved_users,
    approve_user_in_db
)
from register import show_registration_page
from teacher_panel import render_teacher_panel

# Page Config
st.set_page_config(page_title="AIM Computer Institute Shahjahanpur", page_icon="🎓", layout="wide")

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_email = None
    st.session_state.user_status = None

# Google Auth URL Helper
def get_google_auth_url():
    try:
        client_id = st.secrets["google"]["client_id"]
        redirect_uri = st.secrets["google"]["redirect_uri"]
        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    except Exception:
        return "#"

# Handle OAuth Callback
def handle_google_callback(code):
    try:
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": st.secrets["google"]["client_id"],
            "client_secret": st.secrets["google"]["client_secret"],
            "redirect_uri": st.secrets["google"]["redirect_uri"],
            "grant_type": "authorization_code"
        }
        res = requests.post(token_url, data=payload)
        access_token = res.json().get("access_token")
        if access_token:
            user_info = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"}).json()
            email = user_info.get("email")
            if email:
                st.session_state.user_email = email
                user_data = get_user_by_email(email)
                if user_data:
                    st.session_state.user_status = user_data.get("status", "pending")
                    st.session_state.role = user_data.get("role", "student")
                    if st.session_state.user_status == "approved":
                        st.session_state.logged_in = True
                else:
                    st.session_state.user_status = "unregistered"
                st.query_params.clear()
                st.rerun()
    except Exception as e:
        st.error(f"Auth Error: {str(e)}")

if "code" in st.query_params and not st.session_state.logged_in:
    handle_google_callback(st.query_params["code"])

# Main Header Banner
st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #1E1E1E; border-radius: 12px; margin-bottom: 25px;'>
        <h1 style='color: #4CAF50; margin: 0; font-size: 30px;'>Welcome to AIM Computer Institute Shahjahanpur</h1>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigation (When Not Logged In)
if not st.session_state.logged_in:
    st.sidebar.title("📌 Navigation")
    menu_choice = st.sidebar.radio("Go to:", ["🏠 Home", "🔑 Login Yourself", "📝 Register Yourself"])

    if menu_choice == "🏠 Home":
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 Institute details and announcements will be added here soon.")

    elif menu_choice == "🔑 Login Yourself":
        if st.session_state.user_status in ["pending", "rejected"]:
            st.warning(f"⏳ Status: Pending approval for **{st.session_state.user_email}**")
            st.info("Admin approval milne ke baad aap login kar sakenge.")
            if st.button("Refresh / Reset"):
                st.session_state.clear()
                st.rerun()
        else:
            render_login_page()

    elif menu_choice == "📝 Register Yourself":
        show_registration_page(st.session_state.user_email)

# Logged-In User Interface
else:
    col1, col2 = st.columns([3, 1])
    col1.write(f"Logged in as: **{st.session_state.user_email}** ({st.session_state.role.upper() if st.session_state.role else 'USER'})")
    if col2.button("Logout", type="secondary"):
        st.session_state.clear()
        st.rerun()
        
    st.divider()

    # Role ke hisab se panels render karna
    user_role = (st.session_state.role or "").lower()

    if user_role in ["admin", "superadmin"]:
        # Aapka naya advanced admin panel yahan render hoga
        render_admin_panel(st.session_state.user_email)

    elif user_role == "teacher":
        render_teacher_panel()
        
    elif user_role == "student":
        render_student_panel(st.session_state.user_email)
    else:
        st.warning("⚠️ Aapka role assigned nahi hai. Kripya Admin se sampark karein.")

# Permanent Custom Footer
st.markdown("""
    <br><hr><br>
    <div style='text-align: center;'>
        <h4 style='color: #00E676; font-size: 18px; font-weight: bold; margin: 0;'>
            Designed and Developed by Mohammad Ejaz Khan
        </h4>
    </div>
""", unsafe_allow_html=True)