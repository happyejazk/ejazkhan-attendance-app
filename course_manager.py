import streamlit as st
from firebase_admin import firestore

def get_db():
    return firestore.client()

def render_course_manager():
    db = get_db()
    st.subheader("📚 Advanced Course & Syllabus Manager")
    st.caption("Manage Courses, Papers, Sub-topics, and Detailed Concepts in a 4-level hierarchy.")

    # ==========================================
    # 1. ADD NEW MAIN COURSE
    # ==========================================
    with st.expander("➕ **Add New Main Course**"):
        with st.form("add_course_form", clear_on_submit=True):
            new_course_name = st.text_input("Course Name (e.g., O Level, ADCA)")
            new_course_desc = st.text_input("Course Description")
            if st.form_submit_button("Create Course", type="primary"):
                if new_course_name.strip():
                    c_key = new_course_name.strip().title()
                    db.collection("courses").document(c_key).set({
                        "course_name": c_key,
                        "description": new_course_desc.strip(),
                        "papers": {} # Initializing empty dictionary for nested structure
                    }, merge=True)
                    st.success(f"Course '{c_key}' created!")
                    st.rerun()
                else:
                    st.error("Course name is required!")

    st.divider()
    st.markdown("### 📖 Existing Courses & Deep Syllabus")

    # ==========================================
    # 2. FETCH, MIGRATE & DISPLAY NESTED COURSES
    # ==========================================
    courses_ref = db.collection("courses")
    course_docs = {doc.id: doc.to_dict() for doc in courses_ref.stream()}

    if not course_docs:
        st.info("No courses found. Add a course above.")
        return

    for c_id, c_data in course_docs.items():
        # --- AUTO-MIGRATION LOGIC ---
        needs_update = False
        papers_dict = c_data.get("papers")
        
        if papers_dict is None:
            papers_dict = {}
            old_topics = c_data.get("topics", [])
            # Convert old array items to paper keys
            if isinstance(old_topics, list):
                for old_topic in old_topics:
                    papers_dict[old_topic] = {} 
            needs_update = True
        
        if needs_update:
            # Update DB to the new nested format and remove the old 'topics' array
            db.collection("courses").document(c_id).update({
                "papers": papers_dict,
                "topics": firestore.DELETE_FIELD
            })
        # ----------------------------

        with st.expander(f"📘 **Course:** {c_id}", expanded=False):
            # Delete Course Level
            if st.button(f"🗑️ Delete Entire '{c_id}' Course", key=f"del_c_{c_id}", type="secondary"):
                db.collection("courses").document(c_id).delete()
                st.rerun()
            
            st.markdown("---")
            st.markdown("#### 📄 Papers / Main Topics")
            
            # Add New Paper
            p_col1, p_col2 = st.columns([4, 1])
            new_paper = p_col1.text_input(f"New Paper for {c_id}", placeholder="e.g., M3-R5 Python", key=f"inp_p_{c_id}")
            if p_col2.button("➕ Add Paper", key=f"btn_p_{c_id}"):
                if new_paper.strip():
                    papers_dict[new_paper.strip()] = {}
                    db.collection("courses").document(c_id).update({"papers": papers_dict})
                    st.rerun()

            # Iterate through Papers
            for paper_name, subtopics_dict in papers_dict.items():
                st.markdown(f"**📝 Paper:** `{paper_name}`")
                
                # Delete Paper
                if st.button("❌ Remove Paper", key=f"del_p_{c_id}_{paper_name}"):
                    del papers_dict[paper_name]
                    db.collection("courses").document(c_id).update({"papers": papers_dict})
                    st.rerun()

                # Add New Sub-topic
                st_col1, st_col2 = st.columns([4, 1])
                new_subtopic = st_col1.text_input(f"New Sub-topic in {paper_name}", placeholder="e.g., Operators and Expressions", key=f"inp_st_{c_id}_{paper_name}")
                if st_col2.button("➕ Add Sub-topic", key=f"btn_st_{c_id}_{paper_name}"):
                    if new_subtopic.strip():
                        subtopics_dict[new_subtopic.strip()] = []
                        papers_dict[paper_name] = subtopics_dict
                        db.collection("courses").document(c_id).update({"papers": papers_dict})
                        st.rerun()

                # Iterate through Sub-topics
                for subtopic_name, concepts_list in subtopics_dict.items():
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**🔸 Sub-topic:** *{subtopic_name}*")
                    
                    # Delete Sub-topic
                    if st.button("❌ Remove Sub-topic", key=f"del_st_{c_id}_{paper_name}_{subtopic_name}"):
                        del subtopics_dict[subtopic_name]
                        papers_dict[paper_name] = subtopics_dict
                        db.collection("courses").document(c_id).update({"papers": papers_dict})
                        st.rerun()

                    # Render Concepts List
                    if concepts_list:
                        for idx, concept in enumerate(concepts_list):
                            c_col1, c_col2 = st.columns([5, 1])
                            c_col1.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▪️ {concept}")
                            if c_col2.button("🗑️", key=f"del_cpt_{c_id}_{paper_name}_{subtopic_name}_{idx}"):
                                concepts_list.pop(idx)
                                subtopics_dict[subtopic_name] = concepts_list
                                papers_dict[paper_name] = subtopics_dict
                                db.collection("courses").document(c_id).update({"papers": papers_dict})
                                st.rerun()

                    # Add Concept Form
                    with st.form(key=f"form_cpt_{c_id}_{paper_name}_{subtopic_name}", clear_on_submit=True):
                        new_concept = st.text_input("Add specific concept", placeholder="e.g., Types of operator")
                        if st.form_submit_button("Add Concept"):
                            if new_concept.strip():
                                concepts_list.append(new_concept.strip())
                                subtopics_dict[subtopic_name] = concepts_list
                                papers_dict[paper_name] = subtopics_dict
                                db.collection("courses").document(c_id).update({"papers": papers_dict})
                                st.rerun()
                st.markdown("---")
                