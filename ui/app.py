import streamlit as st
import requests, os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="FinCompliance RAG", layout="wide")

# Simple navigation using sidebar
# NOTE: For production, consider using Streamlit's native multipage app structure
# by moving pages to a pages/ subdirectory for automatic navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Statistics"], index=0)

if page == "Statistics":
    # Redirect to statistics page using Streamlit's native approach
    st.info("📊 Statistics page selected. In production, this would navigate to the statistics view.")
    st.markdown("### Statistics Dashboard Coming Soon")
    st.markdown("The statistics page has been implemented in `ui/pages/statistics.py`.")
    st.markdown("To use it, run `streamlit run ui/pages/statistics.py` separately, or configure Streamlit multipage apps.")
else:
    # Home page content
    st.title("📑 FinCompliance RAG Portal")

    with st.sidebar:
        st.header("Upload PDF")
        file = st.file_uploader("Choose a file", type=["pdf","txt"])
        if file and st.button("Ingest"):
            res = requests.post(f"{API_URL}/upload", files={"file": (file.name, file.getvalue())})
            st.success(res.json())

    st.subheader("Ask a question")
    q = st.text_input("Enter your question about the docs")
    if st.button("Ask") and q:
        res = requests.post(f"{API_URL}/ask", json={"question": q})
        data = res.json()
        st.write("**Answer**")
        st.code(data.get("answer",""))
        st.write("**Citations**")
        st.json(data.get("citations", []))
