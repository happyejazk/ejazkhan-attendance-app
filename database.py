import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def init_firebase():
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def authenticate_user(email, password):
    try:
        db = init_firebase()
        users_ref = db.collection("users")
        
        # Email ko trim aur lowercase karke check karein
        clean_email = email.strip().lower()
        clean_password = str(password).strip()
        
        query = users_ref.where("email", "==", clean_email).stream()
        
        user_found = False
        for doc in query:
            user_found = True
            user_data = doc.to_dict()
            
            # Direct password check ya fallback phone check
            saved_password = str(user_data.get("password") or user_data.get("phone", "")).strip()
            
            if saved_password == clean_password:
                if user_data.get("status") != "approved":
                    return False, "Your account is pending for approval. Contact Admin!", None
                return True, user_data.get("role", "student"), user_data.get("batch", "N/A")
            else:
                return False, "Incorrect Password!", None
                
        if not user_found:
            return False, "User not found!", None
            
    except Exception as e:
        return False, f"Error: {str(e)}", None

def get_user_by_email(email):
    try:
        db = init_firebase()
        clean_email = email.strip().lower()
        users_ref = db.collection("users").where("email", "==", clean_email).stream()
        for doc in users_ref:
            data = doc.to_dict()
            data["doc_id"] = doc.id
            return data
        return None
    except Exception as e:
        return None

def register_new_user(name, email, requested_role, phone="", batch=""):
    try:
        db = init_firebase()
        user_data = {
            "name": name.strip(),
            "email": email.strip().lower(),
            "role": requested_role,
            "phone": phone.strip(),
            "password": phone.strip(),  # Explicit password field for new users
            "batch": batch,
            "status": "pending"
        }
        db.collection("users").add(user_data)
        return True, "Registration successful! Admin approval ka wait karein."
    except Exception as e:
        return False, str(e)

def get_pending_users():
    try:
        db = init_firebase()
        users_ref = db.collection("users").where("status", "==", "pending").stream()
        pending_list = []
        for doc in users_ref:
            data = doc.to_dict()
            data["doc_id"] = doc.id
            pending_list.append(data)
        return pending_list
    except Exception as e:
        return []

def get_all_approved_users():
    try:
        db = init_firebase()
        users_ref = db.collection("users").where("status", "==", "approved").stream()
        users_list = []
        for doc in users_ref:
            data = doc.to_dict()
            data["doc_id"] = doc.id
            users_list.append(data)
        return users_list
    except Exception as e:
        return []

def approve_user_in_db(doc_id, assigned_role, batch=""):
    try:
        db = init_firebase()
        db.collection("users").document(doc_id).update({
            "status": "approved",
            "role": assigned_role,
            "batch": batch
        })
        return True
    except Exception as e:
        return False

def reject_user_in_db(doc_id):
    try:
        db = init_firebase()
        db.collection("users").document(doc_id).update({
            "status": "rejected"
        })
        return True
    except Exception as e:
        return False

def update_user_details(doc_id, name, role, batch, phone):
    try:
        db = init_firebase()
        db.collection("users").document(doc_id).update({
            "name": name,
            "role": role,
            "batch": batch,
            "phone": phone
        })
        return True
    except Exception as e:
        return False

def delete_user_from_db(doc_id):
    try:
        db = init_firebase()
        db.collection("users").document(doc_id).delete()
        return True
    except Exception as e:
        return False