import streamlit as st
import urllib.parse
import requests

from session_manager import SessionManager
from login import render_login_page
from student_panel import render_student_panel
from admin_panel import render_admin_panel
from superadmin_panel import render_superadmin_panel
from teacher_panel import render_teacher_panel

from database import (
    get_user_by_email,
    get_pending_users,
    get_all_approved_users,
    approve_user_in_db
)

from register import show_registration_page


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AIM Computer Institute Shahjahanpur",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# SESSION RESTORE
# ============================================================
# Persistent cookie se login restore karne ki koshish

SessionManager.restore_session(get_user_by_email)


# ============================================================
# GOOGLE AUTH URL HELPER
# ============================================================

def get_google_auth_url():
    try:
        client_id = st.secrets["google"]["client_id"]
        redirect_uri = st.secrets["google"]["redirect_uri"]

        scope = (
            "https://www.googleapis.com/auth/userinfo.email "
            "https://www.googleapis.com/auth/userinfo.profile"
        )

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent"
        }

        return (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"{urllib.parse.urlencode(params)}"
        )

    except Exception:
        return "#"


# ============================================================
# GOOGLE OAUTH CALLBACK
# ============================================================

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

        res = requests.post(
            token_url,
            data=payload,
            timeout=15
        )

        token_data = res.json()
        access_token = token_data.get("access_token")

        if not access_token:
            st.error("❌ Google authentication failed.")
            return

        user_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=15
        )

        user_info = user_response.json()
        email = user_info.get("email")

        if not email:
            st.error("❌ Google account email nahi mila.")
            return

        email = email.strip().lower()

        user_data = get_user_by_email(email)

        if user_data:
            status = user_data.get("status", "pending")
            role = user_data.get("role", "student")

            is_approved = status == "approved"

            SessionManager.set_user_session(
                email=email,
                role=role,
                status=status,
                logged_in=is_approved
            )

        else:
            SessionManager.set_user_session(
                email=email,
                status="unregistered",
                logged_in=False
            )

        # OAuth code ko URL se remove karo
        st.query_params.clear()

        # Fresh run with clean URL + hydrated session
        st.rerun()

    except Exception as e:
        st.error(f"Auth Error: {str(e)}")


# ============================================================
# GOOGLE OAUTH TRIGGER
# ============================================================

if "code" in st.query_params and not SessionManager.is_logged_in():
    handle_google_callback(st.query_params["code"])


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div style="
        text-align: center; 
        padding: 20px;
        background-color: #1E1E1E;
        border-radius: 12px;
        margin-bottom: 25px;
    ">
        <h1 style="
            color: #4CAF50; 
            margin: 0; 
            font-size: 30px;
        ">
            Welcome to AIM Computer Institute Shahjahanpur
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# NOT LOGGED-IN USER INTERFACE
# ============================================================

if not SessionManager.is_logged_in():

    st.sidebar.title("📌 Navigation")

    menu_choice = st.sidebar.radio(
        "Go to:",
        [
            "🏠 Home",
            "🔑 Login Yourself",
            "📝 Register Yourself"
        ]
    )

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if menu_choice == "🏠 Home":

        st.markdown("<br>", unsafe_allow_html=True)

        st.info(
            "💡 Institute details and announcements "
            "will be added here soon."
        )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    elif menu_choice == "🔑 Login Yourself":

        user_status = st.session_state.get("user_status")
        user_email = st.session_state.get("user_email")

        if user_status in ["pending", "rejected"]:

            st.warning(
                f"⏳ Status: Pending approval for "
                f"**{user_email}**"
            )

            st.info(
                "Admin approval milne ke baad "
                "aap login kar sakenge."
            )

            if st.button("Refresh / Reset"):
                SessionManager.logout()

        else:
            render_login_page()

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    elif menu_choice == "📝 Register Yourself":

        show_registration_page()


# ============================================================
# LOGGED-IN USER INTERFACE
# ============================================================

else:

    col1, col2 = st.columns([3, 1])
    
    current_role = st.session_state.get("role")
    current_email = st.session_state.get("user_email")

    display_role = current_role.upper() if current_role else "USER"

    col1.write(
        f"Logged in as: **{current_email}** "
        f"({display_role})"
    )
    
    if col2.button("Logout", type="secondary"):
        SessionManager.logout()

    st.divider()


    # ========================================================
    # ROLE BASED PANEL
    # ========================================================

    user_role = (current_role or "").lower()

    if user_role == "superadmin":
        render_superadmin_panel(current_email)

    elif user_role == "admin":
        render_admin_panel(current_email)

    elif user_role == "teacher":
        #render_teacher_panel()
        render_teacher_panel(st.session_state["user_email"])

    elif user_role == "student":
        render_student_panel(current_email)

    else:
        st.warning(
            "⚠️ Aapka role assigned nahi hai. "
            "Kripya Admin se sampark karein."
        )


# Permanent Custom Footer
st.markdown("""
    <br><hr><br>
    <div style='text-align: center;'>
        <h4 style='color: #00E676; font-size: 18px; font-weight: bold; margin: 0;'>
            Designed and Developed by Mohammad Ejaz Khan
        </h4>
    </div>
""", unsafe_allow_html=True)