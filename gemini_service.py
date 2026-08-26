import streamlit as st
from google import genai

# Modern Gemini Models Priority List
MODEL_PRIORITY_LIST = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite"
    "gemini-2.0-pro",
    "gemini-2.5-pro",
]

def get_gemini_keys():
    """
    Automatic API Key Catch Logic:
    KEY_1, KEY_2, KEY_3, GEMINI_API_KEY sabhi ko automatically detect karta hai.
    """
    keys = []
    
    # 1. KEY_1, KEY_2, KEY_3, KEY_4, KEY_5 ko catch karein
    for i in range(1, 10):
        key_name = f"KEY_{i}"
        if key_name in st.secrets and st.secrets[key_name] and st.secrets[key_name] != "xxx":
            keys.append(st.secrets[key_name])
            
    # 2. GEMINI_API_KEY ko catch karein
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        keys.append(st.secrets["GEMINI_API_KEY"])
        
    # 3. [gemini][keys] list fallback
    try:
        if "gemini" in st.secrets and "keys" in st.secrets["gemini"]:
            keys.extend(st.secrets["gemini"]["keys"])
    except Exception:
        pass

    # Unique keys remove duplicates
    return list(dict.fromkeys(keys))


def generate_ai_learning_content(topic_name, course_name, module_name):
    """
    Latest google-genai SDK ke sath Dual-Language (Hinglish) content generate karta hai.
    """
    keys = get_gemini_keys()
    
    if not keys:
        return False, "⚠️ Gemini API Keys secrets.toml me nahi milin! Please check KEY_1, KEY_2 in secrets.toml."

    # Dual Language Hinglish Prompt
    prompt = f"""
    You are an expert computer teacher for institute students in Shahjahanpur.
    Course: {course_name}
    Module: {module_name}
    Topic: {topic_name}
    
    Please generate comprehensive educational content strictly in easy HINGLISH (A blend of Hindi & English for easy understanding, keeping technical terms in clear English).
    
    Format the response using exact section dividers '---SECTION---' as follows:
    
    SECTION 1 (NOTES):
    ### 📖 Smart Notes: {topic_name}
    Explain concepts clearly in simple Hinglish with bullet points and real-world examples.
    
    ---SECTION---
    SECTION 2 (QUESTIONS):
    ### 🎯 Practice MCQs & Question Bank
    Provide 2 Multiple Choice Questions (MCQs) with 4 options each, and 1 conceptual short question based on {topic_name}.
    
    ---SECTION---
    SECTION 3 (SOLVER):
    ### 💡 Answers & Step-by-Step Solver
    Provide clear answers and step-by-step explanations for the questions above.
    """

    # Rotation Logic using modern google-genai SDK
    for api_key in keys:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in MODEL_PRIORITY_LIST:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        return True, response.text
                except Exception:
                    continue
        except Exception:
            continue

    return False, "⚠️ Sabhi Gemini API Keys ya Models temporarly fail ho gaye hain. Kripya baad me try karein."