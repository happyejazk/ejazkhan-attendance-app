import streamlit as st
import urllib.parse
import requests
from database import authenticate_user

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

def render_login_page():
    st.subheader("🔑 AIM ERP Portal Login")
    st.caption("Aap apne User ID (Email) & Password se ya phir Google Sign-In se login kar sakte hain.")

    # Tabs for smooth switching between Google Auth and Password Login
    tab_manual, tab_google = st.tabs(["🔑 User ID & Password Login", "🚀 Google Sign-In"])

    # ---------------- TAB 1: MANUAL LOGIN (USER ID & PASSWORD) ----------------
    with tab_manual:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("manual_login_form"):
            user_id_input = st.text_input("User ID / Email Address *", placeholder="student@gmail.com")
            password_input = st.text_input("Password (Mobile Number / Default) *", type="password", placeholder="10-digit mobile number")
            
            login_btn = st.form_submit_button("🔓 Secure Login", type="primary", use_container_width=True)
            
            if login_btn:
                if not user_id_input.strip() or not password_input.strip():
                    st.error("⚠️ Kripya User ID aur Password dono enter karein!")
                else:
                    clean_email = user_id_input.strip().lower()
                    clean_password = password_input.strip()
                    
                    # Database authentication check
                    status, role_or_msg, batch = authenticate_user(clean_email, clean_password)
                    
                    if status:
                        st.session_state.logged_in = True
                        st.session_state.role = role_or_msg
                        st.session_state.user_email = clean_email
                        st.session_state.user_status = "approved"
                        st.success("🎉 Login Successful! Dashboard load ho raha hai...")
                        st.rerun()
                    else:
                        st.error(f"⚠️ {role_or_msg}")

    # ---------------- TAB 2: GOOGLE OAUTH LOGIN ----------------
    with tab_google:
        st.markdown("<br>", unsafe_allow_html=True)
        google_url = get_google_auth_url()
        st.markdown(
            f'<a href="{google_url}" target="_self" style="text-decoration: none;">'
            f'<button style="width: 100%; height: 48px; background-color: #4285F4; color: white; border: none; '
            f'border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px;">🚀 Sign in with Google Account</button></a>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 **Note:** Google OAuth se login karne ke liye wahi email use karein jo institute mein registered hai.")