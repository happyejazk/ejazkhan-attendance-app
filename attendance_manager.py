import datetime
from database import init_firebase

def get_student_attendance_stats(student_id, course, batch):
    """
    Student ka real-time attendance percentage calculate karta hai.
    Public holidays aur future dates ko ignore karta hai.
    """
    db = init_firebase()
    
    try:
        # Student ke course aur batch ke hisaab se attendance fetch karein
        attendance_ref = db.collection("attendance")
        query = attendance_ref.where("course", "==", course).where("batch", "==", batch).stream()
        
        total_classes = 0
        present_count = 0
        holiday_count = 0
        
        # Aaj ki date string format me (YYYY-MM-DD)
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        for doc in query:
            data = doc.to_dict()
            record_date = data.get("date", "")
            
            # 1. Future date protection (agar DB me galti se koi future date aa gayi ho)
            if record_date > today_str:
                continue
                
            # 2. Public Holiday Check
            if data.get("is_holiday", False) == True:
                holiday_count += 1
                continue  # Holiday ko total classes me count nahi karna hai
                
            # 3. Regular Class Calculation
            total_classes += 1
            records = data.get("records", {})
            
            # Student ki ID records dictionary me check karein
            student_status = records.get(student_id, "Absent")
            if student_status == "Present":
                present_count += 1
                
        # Percentage Calculation
        if total_classes == 0:
            percentage = 0.0
        else:
            percentage = (present_count / total_classes) * 100
            
        return {
            "success": True,
            "total_classes": total_classes,
            "present_count": present_count,
            "holiday_count": holiday_count,
            "percentage": round(percentage, 2)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "percentage": 0.0
        }