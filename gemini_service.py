import streamlit as st
import random
import time
from google import genai
from google.genai import types

# Modern Gemini Models Priority List
MODEL_PRIORITY_LIST = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
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
    Latest google-genai SDK ke sath Dual-Language (English + Pure Hindi) content generate karta hai.
    """
    keys = get_gemini_keys()
    
    if not keys:
        return False, "⚠️ Gemini API Keys secrets.toml me nahi milin! Please check KEY_1, KEY_2 in secrets.toml."

    # Dynamic seed to force absolute uniqueness every time the button is clicked
    dynamic_seed = time.time() + random.randint(1000, 9999)

    prompt = f"""
    You are an expert, professional computer educator.
    Course: {course_name}
    Module: {module_name}
    Topic: {topic_name}
    Variation Seed: {dynamic_seed}
    
    CRITICAL INSTRUCTIONS:
    1. DUAL-LANGUAGE (PROFESSIONAL): Do use informal "Hinglish". Use clean, professional English for technical definitions, ALWAYS start the exact Hindi translation (in Devanagari) on a NEW PARAGRAPH (using double line breaks) immediately after the English text.
    2. ABSOLUTE UNIQUENESS: You must generate completely new real-world examples, fresh analogies, and brand-new MCQs that you have never used before. Do not repeat standard textbook examples.
    3. EXAM & NOTES FOCUSED: Make the content structured, point-wise, and highly readable for students making notes.
    
    Format the response using exact section dividers '---SECTION---' as follows:
    
    SECTION 1 (THEORY):
    ### 📖 Theory & Concepts
    Explain fundamental concepts of {topic_name}. Write point-wise in Professional English, Leave a blank line, and then provide its exact Hindi translation/explanation.
    
    ---SECTION---
    SECTION 2 (PRACTICAL & EXAMPLES):
    ### 💻 Practical Implementation
    Provide 2-3 completely unique real-world examples or code snippets showing how this works practically. Explain the logic clearly in English followed by a blank line, and then the Hindi explanation.
    
    ---SECTION---
    SECTION 3 (QUESTIONS):
    ### 🎯 Practice MCQs
    Provide 3 completely NEW Multiple Choice Questions (MCQs) with 4 options each to test the concept. (DO NOT provide answers here).
    
    ---SECTION---
    SECTION 4 (SOLVER):
    ### ✅ Solutions & Explanations
    Provide the correct answers for the above MCQs with detailed step-by-step reasoning in English and Hindi.
    """

    # High temperature for maximum creativity and uniqueness
    generation_config = types.GenerateContentConfig(
        temperature=0.9,
    )

    # Rotation Logic using modern google-genai SDK
    for api_key in keys:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in MODEL_PRIORITY_LIST:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=generation_config
                    )
                    if response and response.text:
                        return True, response.text
                except Exception:
                    continue
        except Exception:
            continue

    return False, "⚠️ Sabhi Gemini API Keys ya Models temporarly fail ho gaye hain. Kripya baad me try karein."