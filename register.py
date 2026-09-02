import streamlit as st
from firebase_admin import firestore

# Aapki existing database file se safe connection function import kar rahe hain
from database import init_firebase

def fetch_active_courses():
    """
    Firestore ke 'courses' collection se dynamic courses fetch karta hai.
    """
    db = init_firebase()
    try:
        courses_ref = db.collection("courses")
        # Har document ka ID (Course Name) nikal kar list banayega
        course_docs = {doc.id: doc.to_dict() for doc in courses_ref.stream()}
        course_list = list(course_docs.keys())
        return course_list if course_list else []
    except Exception as e:
        st.error(f"Error fetching courses: {e}")
        return []

def handle_student_registration(email, name, phone, course):
    """
    Registers Users strictly as 'student' with 'pending' status. No email logic here.
    """
    db = init_firebase()
    clean_email = email.strip().lower()
    default_password = phone.strip() if phone else "123456"

    user_data = {
        "username": clean_email,
        "user_id": clean_email,         
        "email": clean_email,
        "name": name.strip().upper(),
        "phone": phone.strip(),
        "mobile": phone.strip(),
        "role": "student",              # Explicitly fixed to student
        "course": course,
        "password": default_password,   
        "status": "pending",            # Fixed to pending for Admin approval
        "is_approved": False,           
        "is_deleted": False,
        "created_at": firestore.SERVER_TIMESTAMP
    }

    try:
        # Save securely in 'users' collection
        db.collection("users").document(clean_email).set(user_data, merge=True)
        return True, f"Registration successful for {name.strip().upper()}! Kripya Admin approval ka wait karein."
    except Exception as e:
        return False, f"Error details: {str(e)}"

def show_registration_page():
    st.title("📝 AIM ERP - Student Registration")
    st.caption("Register for a new course at AIM Computer Institute")

    # Dynamic courses fetch karke list me 'Other' option append kar rahe hain
    course_list = fetch_active_courses()
    if "Other" not in course_list:
        course_list.append("Other")

    with st.form("user_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name *", placeholder="E.G. MOHAMMAD EJAZ KHAN")
        email = col2.text_input("Email Address (User ID) *", placeholder="user@gmail.com")
        
        col3, col4 = st.columns(2)
        phone = col3.text_input("Mobile Number (Default Password)", placeholder="10-digit number")
        selected_course = col4.selectbox("Select Course *", course_list)

        submit_btn = st.form_submit_button("🚀 Register", type="primary", use_container_width=True)

        if submit_btn:
            if not name.strip() or not email.strip():
                st.error("⚠️ Full Name aur Email ID fill karna mandatory hai!")
            else:
                success, msg = handle_student_registration(email, name, phone, selected_course)
                if success:
                    st.success(f"🎉 {msg}")
                else:
                    st.error(f"⚠️ {msg}")