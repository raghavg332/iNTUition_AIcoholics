import os, re
from github import Auth
from github import Github, GithubIntegration
from github.GithubException import GithubException
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_cpp as tscpp
import requests
import json
import logging
import snowflake.connector
import random
import datetime


GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def authenticate_github(app_id: int, installation_id, private_key: str):
    gi = GithubIntegration(integration_id=app_id, private_key=private_key)
    g = gi.get_github_for_installation(installation_id)
    return g

def get_pull_request(g, repo_name: str, pr_number: int):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return pr

def parse_changed_lines(patch: str):
    added_or_modified_lines = set()
    deleted_lines = set()
    for line in patch.splitlines():
        if line.startswith("@@"):
            match = re.findall(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                old_start, old_count, new_start, new_count = match[0]

                old_start = int(old_start)
                old_count = int(old_count or 1)
                for l in range(old_start, old_start + old_count):
                    deleted_lines.add(l)

                new_start = int(new_start)
                new_count = int(new_count or 1)
                for l in range(new_start, new_start + new_count):
                    added_or_modified_lines.add(l)

    return {
        "added_or_modified_lines": added_or_modified_lines,
        "deleted_lines": deleted_lines
    }

def get_file_contents(g, repo_name: str, file_path: str, commit_sha: str):
    repo = g.get_repo(repo_name)
    try:
        contents = repo.get_contents(file_path, ref=commit_sha)
        return contents.decoded_content.decode()
    except GithubException as e:
        if e.status == 404:
            return ""
        else:
            raise e

def get_lines_changed(pr):
    files = pr.get_files()
    file_changes = {}
    for file in files:
        if file.status == "removed":
            continue
        file_changes[file.filename] = parse_changed_lines(file.patch)

    return file_changes

def get_paraser(language_name):

    PY_LANGUAGE = Language(tspython.language())
    JS_LANGUAGE = Language(tsjavascript.language())
    CPP_LANGUAGE = Language(tscpp.language())

    LANGUAGES = {
        'python': PY_LANGUAGE,
        'javascript': JS_LANGUAGE,
        'cpp': CPP_LANGUAGE,
    }
    parser = Parser(LANGUAGES[language_name])
    return parser

def extract_functions(code, language_name, changed_lines):
    parser = get_paraser(language_name)
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    functions = []

    def node_within_lines(node):
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        return any([start_line <= line <= end_line for line in changed_lines])
    
    def traverse(node):
        if language_name == "python" and node.type == "function_definition":
            if node_within_lines(node):
                func_name_node = node.child_by_field_name('name')
                func_name = func_name_node.text.decode()
                functions.append({'name': func_name, 'code': node.text.decode()})
        elif language_name == 'javascript' and node.type in ['function_declaration', 'method_definition', 'arrow_function']:
            if node_within_lines(node):
                func_name_node = node.child_by_field_name('name')
                func_name = func_name_node.text.decode()
                functions.append({'name': func_name, 'code': node.text.decode()})
        elif language_name == 'cpp' and node.type in ['function_definition']:
            if node_within_lines(node):
                func_name_node = node.child_by_field_name('name')
                func_name = func_name_node.text.decode()
                functions.append({'name': func_name, 'code': node.text.decode()})
        for child in node.children:
            traverse(child)

    traverse(root_node)
    return functions

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


def build_full_prompt(pr_description: str, code_diff_str: str) -> str:
    return f"""
You are an AI code reviewer and documentation assistant.

A developer submitted the following pull request. Please do the following:
1. 🔍 Summarize the overall purpose of the PR. Be a little detailed
2. 🧠 Rate the merge confidence on a scale of 1 - 10
3. ✅ Review the code for:
   - Syntax issues
   - Style (PEP8)
   - Functionality correctness (does it match the description?)
4. 📝 Extract or suggest updated docstrings for any changed or added functions/classes.
5. The Code Diff is made up of the old and new version of the code, if any of the field is empty it means, the function is either added or deleted respectively.

## PR Description:
{pr_description}

## Code Diff:
{code_diff_str}

Respond ONLY in this JSON format without any additional text:

{{
  "ai_summary": "...",
  "merge_confidence": "1 - 10",
  "code_quality": {{
    "syntax_check": "...",
    "style_check": "...",
    "functionality_check": "...",
    "final_rating": "Excellent / Good / Needs Work / Critical Issues"
  }}
}}
"""

def review_and_store_pr(pr_description: str, code_diff: dict, pr_title: str, pr_author: str, pr_status: str):
    code_diff_str = ""
    for file in list(code_diff.keys()):
        code_diff_str += f"File: {file}\n\n"
        diff = code_diff[file]

        for func_name in list(diff.keys()):
            old_code = diff[func_name]['old_code']
            new_code = diff[func_name]['new_code']
            if old_code is None:
                old_code = ""
            if new_code is None:
                new_code = ""
            code_diff_str += f"Function: {func_name}\n\nOld Code:\n{old_code}\n\nNew Code:\n{new_code}"
    docstring = update_documentation_with_rag(pr_description, code_diff)
    pr_id = random.randint(1000, 9999)
    prompt = build_full_prompt(pr_description, code_diff_str)

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
                code_diff_str
            ))

            conn.commit()

            logging.info(f"[✅] PR #{pr_id} analysis saved to Snowflake.")
            print(f"[✅] PR #{pr_id} analysis saved to Snowflake.")
            return review_data

        except json.JSONDecodeError:
            logging.error("[❌] Groq returned non-JSON output.")
            print("[❌] Groq returned non-JSON output.")
            return {"error": "Invalid JSON from Groq"}

    except Exception as e:
        logging.exception("Groq API or Snowflake insert failed")
        return {"error": str(e)}

def process_pull_request(g, repo_name, pr_number, sender=None):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr_description = pr.title
    pr_title = pr.title
    pr_author = pr.user.login
    pr_status = pr.state
    code_diff = get_lines_changed(pr)
    file_diff_func = {}
    for file in list(code_diff.keys()):
        diff_func = {}
        new_code = get_file_contents(g, repo_name, file, pr.head.sha)
        old_code = get_file_contents(g, repo_name, file, pr.base.sha)
        added_or_modified_functions_after = extract_functions(new_code, "python", code_diff[file]['added_or_modified_lines'])
        deleted_functions_before = extract_functions(old_code, "python", code_diff[file]['deleted_lines'])
        old_functions_all = extract_functions(old_code, "python", set(range(1, len(old_code.split("\n")))))
        new_functions_all = extract_functions(new_code, "python", set(range(1, len(new_code.split("\n")))))
        for func in added_or_modified_functions_after:
            matched_old_function = next((f for f in old_functions_all if f['name'] ==  func['name']), None)
            diff_func[func['name']] = {
                "new_code": func['code'],
                "old_code": matched_old_function['code'] if matched_old_function else None
            }
        
        for func in deleted_functions_before:
            matched_new_function = next((f for f in new_functions_all if f['name'] ==  func['name']), None)
            diff_func[func['name']] = {
                "new_code": matched_new_function['code'] if matched_new_function else None,
                "old_code": func['code']
            }
        
        file_diff_func[file] = diff_func
    
    # Get the review data and post a comment
    review_data = review_and_store_pr(pr_description, file_diff_func, pr_title, pr_author, pr_status)
    
    # Post the review as a comment on the PR
    post_review_comment(g, repo_name, pr_number, review_data)


def post_review_comment(g, repo_name, pr_number, review_data):
    """
    Posts the AI review as a comment on the pull request.
    
    Args:
        g: Authenticated GitHub instance
        repo_name: Repository name (owner/repo)
        pr_number: Pull request number
        review_data: The AI review data dictionary
    """
    try:
        # Get the repo and PR objects
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Format the comment body
        comment_body = f"""
## 🤖 AI Code Review

### Summary
{review_data.get('ai_summary', 'No summary available')}

### Merge Confidence: **{review_data.get('merge_confidence', 'Unknown')}**

### Code Quality Review
- **Syntax:** {review_data.get('code_quality', {}).get('syntax_check', 'Not analyzed')}
- **Style:** {review_data.get('code_quality', {}).get('style_check', 'Not analyzed')}
- **Functionality:** {review_data.get('code_quality', {}).get('functionality_check', 'Not analyzed')}
- **Overall Rating:** {review_data.get('code_quality', {}).get('final_rating', 'Not rated')}

---
*This review was automatically generated by AI.*
"""
        
        # Create the comment on the PR
        pr.create_issue_comment(comment_body)
        logging.info(f"[✅] Posted AI review comment on PR #{pr_number} in {repo_name}")
        print(f"[✅] Posted AI review comment on PR #{pr_number} in {repo_name}")
        return True
    except Exception as e:
        logging.exception(f"[❌] Failed to post comment on PR #{pr_number}: {str(e)}")
        print(f"[❌] Failed to post comment on PR #{pr_number}: {str(e)}")
        return False