import requests
import json
import logging
import snowflake.connector
import random
import datetime

GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Snowflake setup
conn = snowflake.connector.connect(
    user="raghavg332",
    password="Qa29Kh4MptfGHEW",
    account="KXCIVVH-LL27432",
    warehouse="COMPUTE_WH",
    database="PR_DASHBOARD",
    schema="PUBLIC"
)
cur = conn.cursor()

def update_documentation_with_rag(pr_description: str, code_diff: str, docs_path="backend/project_docs.txt"):
    """
    Performs a simple RAG-based call to Groq to update documentation.
    """
    # Step 1: Load the existing documentation
    try:
        with open(docs_path, "r") as f:
            existing_docs = f.read()
    except FileNotFoundError:
        logging.error(f"[❌] Documentation file not found at {docs_path}")
        return {"error": "Documentation file not found."}

    # Step 2: Very basic RAG - extract top paragraphs that contain overlap
    paragraphs = existing_docs.split("\n\n")
    keywords = pr_description.lower().split()
    ranked_paragraphs = sorted(paragraphs, key=lambda para: sum(word in para.lower() for word in keywords), reverse=True)
    context = "\n\n".join(ranked_paragraphs[:3])  # Top 3 paragraphs as "retrieved context"

    # Step 3: Build the prompt
    doc_prompt = f"""
You are an expert technical writer and code documentation assistant.

A developer has made the following changes to the codebase:

## PR Description:
{pr_description}

## Code Diff:
{code_diff}

## Relevant Existing Documentation:
{context}

Please provide additions or updates to the documentation based on the above code change. 
Format your response in **Markdown**, and only include sections that should be added or updated. 
If the change doesn't require doc updates, say so.
"""

    # Step 4: Call Groq API
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": doc_prompt}]
    }

    try:
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return {
            "doc_update": result["choices"][0]["message"]["content"].strip()
        }

    except Exception as e:
        logging.exception("Groq API call for documentation update failed")
        return {"error": str(e)}


def build_full_prompt(pr_description: str, code_diff: str) -> str:
    return f"""
You are an AI code reviewer and documentation assistant.

A developer submitted the following pull request. Please do the following:
1. 🔍 Summarize the overall purpose of the PR.
2. 🧠 Rate the merge confidence as: High / Medium / Low.
3. ✅ Review the code for:
   - Syntax issues
   - Style (PEP8)
   - Functionality correctness (does it match the description?)
4. 📝 Extract or suggest updated docstrings for any changed or added functions/classes.

## PR Description:
{pr_description}

## Code Diff:
{code_diff}

Respond ONLY in this JSON format:

{{
  "ai_summary": "...",
  "merge_confidence": "1-10",
  "code_quality": {{
    "syntax_check": "...",
    "style_check": "...",
    "functionality_check": "...",
    "final_rating": "Excellent / Good / Needs Work / Critical Issues"
  }}
}}
"""

def review_and_store_pr(pr_description: str, code_diff: str, pr_title: str, pr_author: str, pr_status: str):
    docstring = update_documentation_with_rag(pr_description, code_diff)
    print(docstring)
    print('\n\n')
    pr_id = random.randint(1000, 9999)
    prompt = build_full_prompt(pr_description, code_diff)

    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        try:
            content = result["choices"][0]["message"]["content"].strip()
            review_data = json.loads(content)

            # Flatten the code quality object for easier insert
            code_quality_str = (
                f"Syntax: {review_data['code_quality']['syntax_check']}\n"
                f"Style: {review_data['code_quality']['style_check']}\n"
                f"Functionality: {review_data['code_quality']['functionality_check']}\n"
                f"Rating: {review_data['code_quality']['final_rating']}"
            )
            cur.execute(f"""
                INSERT INTO PULL_REQUESTS (
                    ID, TITLE, AUTHOR, STATUS, CREATED_AT, UPDATED_AT
                )
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                pr_id,
                pr_title,
                pr_author,
                pr_status,
                datetime.datetime.now(),
                datetime.datetime.now()
            ))
            conn.commit()

            # Insert into Snowflake
            cur.execute(f"""
                INSERT INTO PR_ANALYSIS (
                    PR_ID, AI_SUMMARY, MERGE_CONFIDENCE, CODE_QUALITY,
                    PR_DESCRIPTION, DOCSTRINGS, DIFF
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                pr_id,
                review_data["ai_summary"],
                review_data["merge_confidence"],
                code_quality_str,
                pr_description,
                docstring['doc_update'],
                code_diff
            ))

            conn.commit()

            logging.info(f"[✅] PR #{pr_id} analysis saved to Snowflake.")
            return review_data

        except json.JSONDecodeError:
            logging.error("[❌] Groq returned non-JSON output.")
            return {"error": "Invalid JSON from Groq"}

    except Exception as e:
        logging.exception("Groq API or Snowflake insert failed")
        return {"error": str(e)}

# # 🧪 Example test
# if __name__ == "__main__":
#     code_diff = """
# diff --git a/app/main.py b/app/main.py
# index a1b2c3d..d4e5f6g 100644
# --- a/app/main.py
# +++ b/app/main.py
# @@ def main():
# -    print("Hello")
# +    log_greeting("Hello, world!")
# +    print("Execution completed.")

# +def log_greeting(message):
# +    \"\"\"Logs the greeting message to a file\"\"\"
# +    with open("logs.txt", "a") as log_file:
# +        log_file.write(f"Greeting logged: {message}\\n")
# """
#     pr_description = "Update main function to greet the world."
#     pr_title = "Update main function"
#     pr_author = "johndoe"
#     pr_status = "OPEN"

#     result = review_and_store_pr(pr_description, code_diff, pr_title, pr_author, pr_status)
#     print(json.dumps(result, indent=2))