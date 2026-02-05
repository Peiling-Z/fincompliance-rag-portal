import streamlit as st
import requests, os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="FinCompliance RAG", layout="wide")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Statistics"],
    index=0
)

if page == "Statistics":
    # Import and run statistics page
    import importlib.util
    spec = importlib.util.spec_from_file_location("statistics", "ui/pages/statistics.py")
    statistics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(statistics)
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
