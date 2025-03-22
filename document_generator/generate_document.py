import psycopg2
import faiss
import numpy as np
import pickle
import requests
from sentence_transformers import SentenceTransformer

def generate_pr_documentation(data: dict) -> str:
    # --- Step 1: Load vector index + doc chunks ---
    model = SentenceTransformer("all-MiniLM-L6-v2")
    faiss_index = faiss.read_index("docs_index.faiss")

    with open("docs_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)

    # --- Step 2: Fetch repo-level documentation from PostgreSQL ---
    def fetch_repo_doc(repo_name):
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            user="postgres",
            password="Witcher4",
            dbname="doc_db"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT documentation FROM repo_docs WHERE repo_name = %s", (repo_name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else "No documentation found."

    repo_doc = fetch_repo_doc(data["repo_name"])

    # --- Step 3: Retrieve similar doc chunks using RAG (FAISS) ---
    rag_query = data["diff_code"] + " " + repo_doc
    query_embedding = model.encode([rag_query])
    distances, indices = faiss_index.search(np.array(query_embedding).astype("float32"), 5)
    valid_indices = [i for i in indices[0] if i != -1]
    retrieved_docs = [chunks[i] for i in valid_indices]

    # --- Step 4: Build prompt for Groq LLM ---
    rag_context = "\n---\n".join(retrieved_docs)
    prompt = f"""
# Pull Request Review
## PR Title: {data["pr_title"]}
## Author: @{data["author"]}
## PR Description:
{data["pr_description"]}

## PR Link: {data["pr_url"]}

---

## 🔄 Code Diff (Changed Lines)
{data["diff_code"]}

---

## 🧠 Full Code Context
{data["code_context"]}

---

## 📚 Relevant Documentation (from retrieval)
{rag_context}

---

## 📝 TASK:
Write a detailed markdown report that includes:
- Summary of what this PR changes
- Analysis of the diffed code (syntax, functionality, efficiency)
- How this fits into the existing codebase
- Suggestions or improvements
- Final verdict on quality

Respond in markdown format.
"""

    # --- Step 5: Call Groq LLM ---
    GROQ_API_KEY = "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"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                             headers=headers, json=payload)

    return response.json()['choices'][0]['message']['content']

test_data = {
    "pr_title": "Add login handler",
    "pr_description": "Implements secure login using OAuth2",
    "pr_url": "https://github.com/your/repo/pull/42",
    "author": "kaustubh",
    "code_context": "def login():\n    # handle login flow",
    "diff_code": "+def login():\n+    print('Logging in...')",
    "changed_files": ["auth.py"],
    "repo_name": "your_org/your_repo"
}

markdown = generate_pr_documentation(test_data)
print(markdown)

