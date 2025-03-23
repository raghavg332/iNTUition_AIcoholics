# 🤖 Code Roast : An AI-Powered Pull Request Review System

> An end-to-end intelligent platform for automated code review, documentation updates, and pull request analysis — powered by LLMs, Tree-sitter, and Snowflake.

---

## 🚀 Overview

This system integrates with GitHub to automatically:
- Analyze pull requests using AI (via [Groq](https://groq.com))
- Parse and understand diffs using [Tree-sitter](https://tree-sitter.github.io/)
- Perform RAG (Retrieval-Augmented Generation) to update project documentation
- Store all insights in **Snowflake** for analytics
- Display all PRs, diffs, AI feedback, and doc suggestions via a beautiful **Web App**

Whether you're an engineering team lead, reviewer, or contributor — you get fast, reliable, and insightful AI-powered review feedback at every step.

---

## 🧠 Features

- ✅ **AI PR Summary**  
  Instant analysis of pull request purpose, syntax/style/functionality, and merge confidence.

- 📝 **Automatic Docstring Suggestions**  
  Extract or generate missing/updated docstrings for new or changed functions.

- 📘 **RAG-based Documentation Updates**  
  Contextual retrieval from `project_docs.txt` with AI-generated Markdown additions.

- 📄 **Code Diff Parsing**  
  Tree-sitter-based code structure diffing to isolate changed functions only.

- 💬 **GitHub Comment Posting**  
  Summaries are posted as comments directly on PRs, no need to open another tool.

- 📊 **Snowflake Integration**  
  All AI-generated insights and PR metadata stored for reporting, audit, and search.

- 🌐 **Web App Dashboard**  
  Browse all PRs, view diffs, AI reviews, and doc updates in a single UI.

---

## 🧱 Tech Stack

| Layer              | Tech Used                                      |
|--------------------|-----------------------------------------------|
| **AI Models**       | [Groq API (LLaMA 3)](https://groq.com)        |
| **Diff Parsing**    | [Tree-sitter](https://tree-sitter.github.io/) |
| **Backend API**     | [FastAPI](https://fastapi.tiangolo.com)       |
| **Git Integration** | GitHub App + `PyGithub`                       |
| **RAG Engine**      | Basic keyword-matching from local docs        |
| **Database**        | [Snowflake](https://www.snowflake.com)        |
| **Frontend**        | HTML, JS, CSS (Markdown + Diff Viewers)       |

---

## ⚙️ How It Works

1. 🔔 **GitHub Webhook Trigger**
   - On PR open/update → sends payload to FastAPI backend

2. 🧠 **AI Review Processing**
   - Extracts code diffs, changed functions
   - Groq generates AI summary, confidence rating, and docstrings

3. 📘 **Documentation Updates**
   - Local project docs indexed via simple RAG
   - Groq suggests Markdown additions

4. 💾 **Data Storage**
   - All results are saved in Snowflake for dashboard & analytics

5. 🌐 **Web App UI**
   - Explore PRs, view diffs, AI reviews, and doc updates
