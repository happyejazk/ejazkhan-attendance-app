import streamlit as st
import random
import time
from google import genai
from google.genai import types

# Modern Gemini Models Priority List
MODEL_PRIORITY_LIST = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-2.0-pro",
    "gemini-2.5-pro"
]

def get_gemini_keys():
    """
    Automatic API Key Catch Logic:
    KEY_1, KEY_2, KEY_3, GEMINI_API_KEY sabhi ko automatically detect karta hai.
    """
    keys = []
    
    # 1. KEY_1 se KEY_9 tak catch karein
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
    Latest google-genai SDK ke sath Student-Friendly content generate karta hai.
    Screen par loader ke sath active model ka naam fixed rehta hai.
    """
    keys = get_gemini_keys()
    
    if not keys:
        return False, "⚠️ Gemini API Keys secrets.toml me nahi milin! Please check KEY_1, KEY_2 in secrets.toml."

    # Status Message Display Placeholder
    status_box = st.empty()

    # Dynamic seed for unique output on every click
    dynamic_seed = time.time() + random.randint(1000, 9999)

    prompt = f"""
    You are an expert, friendly computer educator who explains technical concepts in the absolute simplest, easiest, and most beginner-friendly manner possible.
    Course: {course_name}
    Module: {module_name}
    Topic: {topic_name}
    Variation Seed: {dynamic_seed}
    
    CRITICAL INSTRUCTIONS:
    1. SIMPLE & STUDENT-FRIENDLY LANGUAGE: Use extremely clear, easy, and simple words. Avoid high-level technical jargon so beginner students can grasp everything without confusion.
    2. EASY PRACTICAL EXAMPLES: All practical examples, code snippets, and real-world analogies MUST be super easy and non-complex. Use simple daily-life scenarios.
    3. DUAL-LANGUAGE (EASY ENGLISH + PURE HINDI): Use clean, simple English for technical definitions, and ALWAYS start the exact Hindi translation (in Devanagari) on a NEW PARAGRAPH (using double line breaks) immediately after the English text.
    4. ABSOLUTE UNIQUENESS & NOTES FOCUSED: Generate fresh real-world examples and MCQs each time. Keep the content structured, point-wise, and highly readable for students making notes.
    
    Format the response using exact section dividers '---SECTION---' as follows:
    
    SECTION 1 (THEORY):
    ### 📖 Theory & Concepts
    Explain fundamental concepts of {topic_name} in the simplest possible terms. Write point-wise in Easy English, Leave a blank line, and then provide its exact Hindi translation/explanation.
    
    ---SECTION---
    SECTION 2 (PRACTICAL & EXAMPLES):
    ### 💻 Practical Implementation
    Provide 2-3 super easy, beginner-friendly real-world examples or short code snippets showing how this works practically. Keep logic very clear and non-complex. Explain in Easy English followed by a blank line, and then the Hindi explanation.
    
    ---SECTION---
    SECTION 3 (QUESTIONS):
    ### 🎯 Practice MCQs
    Provide 3 completely NEW, simple Multiple Choice Questions (MCQs) with 4 options each to test the concept. (DO NOT provide answers here).
    
    ---SECTION---
    SECTION 4 (SOLVER):
    ### ✅ Solutions & Explanations
    Provide the correct answers for the above MCQs with clear, step-by-step simple reasoning in English and Hindi.
    """

    # AFC warning disable karne ke liye config set ki gayi hai
    generation_config = types.GenerateContentConfig(
        temperature=0.9,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    # Rotation Logic using modern google-genai SDK
    for api_key in keys:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in MODEL_PRIORITY_LIST:
                try:
                    # Model ka naam screen par 'Generating Learning Content' ke sath fix dikhega
                    status_box.info(f"⏳ Generating learning content using **{model_name}**... Please wait.")
                    
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=generation_config
                    )
                    if response and response.text:
                        status_box.success(f"✅ Content generated successfully using **{model_name}**!")
                        time.sleep(1) # Final message dikhane ke liye halka delay
                        status_box.empty() # Content aane par box clear kar dega
                        return True, response.text
                except Exception:
                    continue
        except Exception:
            continue

    status_box.error("⚠️ Sabhi Gemini API Keys ya Models temporarily fail ho gaye hain.")
    return False, "⚠️ Sabhi Gemini API Keys ya Models temporarily fail ho gaye hain. Kripya baad me try karein."