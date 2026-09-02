import streamlit as st
import extra_streamlit_components as stx


class SessionManager:

    COOKIE_NAME = "aim_user_email"
    COOKIE_MAX_AGE = 24 * 60 * 60  # 7 days

    @staticmethod
    def get_cookie_manager():
        """
        CookieManager ko session_state me cache karta hai.
        """
        if "cookie_manager" not in st.session_state:
            st.session_state.cookie_manager = stx.CookieManager(
                key="aim_cookie_mgr_instance"
            )

        return st.session_state.cookie_manager

    @staticmethod
    def init_session():
        """
        Streamlit session state ke required variables initialize karta hai.
        """
        defaults = {
            "logged_in": False,
            "role": None,
            "user_email": None,
            "user_status": None,
            "cookie_fetched": False
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def restore_session(get_user_by_email_fn):
        """
        Browser cookie se user session restore karta hai.
        Async CookieManager readiness lag ko fix karta hai.
        """
        SessionManager.init_session()

        # Agar current Streamlit session already logged-in hai, to lookup avoid karo
        if st.session_state.get("logged_in", False):
            return

        cookie_mgr = SessionManager.get_cookie_manager()

        try:
            cookies = cookie_mgr.get_all()
        except Exception:
            cookies = None

        # Jab tak CookieManager readiness signal/data na de, loop safely handle karo
        if cookies is None:
            return

        saved_email = cookies.get(SessionManager.COOKIE_NAME)

        # Cookie available nahi hai
        if not saved_email:
            return

        saved_email = str(saved_email).strip().lower()

        # Database se user verify karo
        user_data = get_user_by_email_fn(saved_email)

        # User database me nahi mila
        if not user_data:
            try:
                cookie_mgr.delete(SessionManager.COOKIE_NAME)
            except Exception:
                pass
            return

        status = user_data.get("status", "pending")
        role = user_data.get("role", "student")

        # Sirf approved users ko automatic session restore karo
        if status == "approved":
            st.session_state.user_email = saved_email
            st.session_state.role = role
            st.session_state.user_status = status
            st.session_state.logged_in = True
        else:
            st.session_state.user_email = saved_email
            st.session_state.role = role
            st.session_state.user_status = status
            st.session_state.logged_in = False

    @staticmethod
    def set_user_session(
        email,
        role=None,
        status=None,
        logged_in=False
    ):
        """
        Successful login ke baad Session State update karta hai
        aur Browser cookie set karta hai.
        """
        clean_email = str(email).strip().lower() if email else None

        # Session State Update
        st.session_state.user_email = clean_email
        st.session_state.role = role
        st.session_state.user_status = status
        st.session_state.logged_in = logged_in

        # Persistent Browser Cookie Update
        if logged_in and clean_email:
            cookie_mgr = SessionManager.get_cookie_manager()
            cookie_mgr.set(
                SessionManager.COOKIE_NAME,
                clean_email,
                max_age=SessionManager.COOKIE_MAX_AGE
            )

    @staticmethod
    def is_logged_in():
        """
        Current Streamlit session ka login status return karta hai.
        """
        return st.session_state.get("logged_in", False)

    @staticmethod
    def logout():
        """
        Browser cookie + current Streamlit session dono clear karta hai.
        """
        cookie_mgr = SessionManager.get_cookie_manager()

        try:
            cookie_mgr.delete(SessionManager.COOKIE_NAME)
        except Exception:
            pass

        # State reset
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.user_email = None
        st.session_state.user_status = None

        st.rerun()