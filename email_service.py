import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_welcome_credentials(recipient_email, user_name, user_id, password, role="Student"):
    """
    Sends Welcome Email with User ID, Default Password & Login Link
    """
    try:
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = int(st.secrets["email"].get("smtp_port", 587))
        sender_email = st.secrets["email"].get("sender_email", "")
        sender_password = st.secrets["email"].get("sender_password", "")

        if not sender_email or not sender_password:
            return False, "Email credentials secrets me configured nahi hain!"

        subject = f"🎉 Welcome to AIM Computer Institute - Your {role} Credentials"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="background: #0f172a; padding: 20px; border-radius: 10px; color: #fff;">
                <h2>Welcome to AIM ERP, {user_name}!</h2>
                <p>Aapka <b>{role} Profile</b> successfully create kar diya gaya hai.</p>
                <hr style="border: 1px solid #334155;">
                <h3>🔑 Login Credentials:</h3>
                <p><b>User ID / Email:</b> <span style="color: #38bdf8;">{user_id}</span></p>
                <p><b>Default Password:</b> <span style="color: #38bdf8;">{password}</span> (Aapka Mobile Number)</p>
                <br>
                <p>⚠️ In credentials ka use karke aap portal par direct login kar sakte hain.</p>
                <p>Regards,<br><b>AIM Computer Institute Shahjahanpur</b></p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AIM ERP Portal <{sender_email}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return True, "Email Sent Successfully!"
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"