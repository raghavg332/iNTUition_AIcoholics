from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import snowflake.connector
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

app = FastAPI()

# Snowflake credentials
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "raghavg332")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "Qa29Kh4MptfGHEW")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "KXCIVVH-LL27432")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "PR_DASHBOARD")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    """Establish connection to Snowflake database"""
    try:
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        raise e

@app.get("/api/prs")
def fetch_all_prs():
    try:
        conn = get_conn()
        cursor = conn.cursor(snowflake.connector.DictCursor)
        
        # Using cursor to get results as dictionaries
        cursor.execute("SELECT id, title, author, status, created_at, updated_at FROM pull_requests ORDER BY updated_at DESC")
        results = cursor.fetchall()
        
        # Format the data to match frontend expectations
        formatted_results = []
        for row in results:
            # Capitalize the status to match frontend expectations
            status = row['STATUS'].capitalize() if row['STATUS'] else 'Unknown'
            
            formatted_results.append({
                "id": row['ID'],
                "title": row['TITLE'],
                "author": row['AUTHOR'],
                "status": status,
                "created_at": row['CREATED_AT'].strftime("%Y-%m-%d") if row['CREATED_AT'] else None,
                "updated_at": row['UPDATED_AT'].strftime("%Y-%m-%d") if row['UPDATED_AT'] else None
            })
        
        cursor.close()
        conn.close()
        return formatted_results
    except Exception as e:
        print(f"Error fetching PRs: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/prs/{pr_id}")
def fetch_pr_analysis(pr_id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor(snowflake.connector.DictCursor)
        
        # Fetch the analysis data
        cursor.execute(f"SELECT * FROM pr_analysis WHERE pr_id = {pr_id}")
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="PR analysis not found")
        
        # Format the data to match frontend expectations
        formatted_result = {
            "pr_id": result['PR_ID'],
            "ai_summary": result['AI_SUMMARY'],
            "merge_confidence": result['MERGE_CONFIDENCE'].capitalize(),  # Capitalize for frontend
            "code_quality": result['CODE_QUALITY'],
            "diff": result['DIFF']
        }
        
        cursor.close()
        conn.close()
        return formatted_result
    except Exception as e:
        print(f"Error fetching PR analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
'''
@app.get("/api/prs")
def fetch_all_prs():
    # Test data
    test_data = [
        {
            "id": 1,
            "title": "Add new feature",
            "author": "johndoe",
            "status": "Open",
            "created_at": "2023-01-01",
            "updated_at": "2023-01-02"
        },
        {
            "id": 2,
            "title": "Fix bug in login",
            "author": "janedoe",
            "status": "Merged",
            "created_at": "2023-01-03",
            "updated_at": "2023-01-04"
        }
    ]
    return test_data

@app.get("/api/prs/{pr_id}")
def fetch_pr_analysis(pr_id: int):
    # Test data
    test_data = {
        "pr_id": pr_id,
        "ai_summary": "This PR adds a new feature that improves user experience",
        "merge_confidence": "High",
        "code_quality": "Good code quality. No major issues found.",
        "diff": "```\n+ def new_function():\n+     return 'new feature'\n```"
    }
    return test_data'
'''