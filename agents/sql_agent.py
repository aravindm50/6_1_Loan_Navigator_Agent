# agents/sql_agent.py

import sqlite3
import os
import logging
from google.cloud import storage
from dotenv import load_dotenv
from google import genai
from google.genai.types import HttpOptions
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)

# -----------------------------
# Helper: Download SQLite DB from GCS
# -----------------------------
def download_db_from_gcs(bucket_name, blob_name, local_path="/tmp/loans.db"):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    return local_path

# -----------------------------
# Helper: Clean SQL
# -----------------------------
def clean_sql(sql_query: str) -> str:
    if not sql_query:
        return ""
    fences = ["```sqlite", "```", "```sql"]
    for fence in fences:
        sql_query = sql_query.replace(fence, "")
    return sql_query.strip()

# -----------------------------
# SQLAgent
# -----------------------------
class SQLAgent:
    def __init__(self, db_path=None):
        self.db_path = db_path or download_db_from_gcs(
            bucket_name=os.getenv("LOAN_DB_BUCKET"),
            blob_name=os.getenv("LOAN_DB_BLOB")
        )
        self.client = genai.Client(
            project=os.getenv("GCP_PROJECT"),
            location=os.getenv("GCP_REGION", "us-central1"),
            http_options=HttpOptions(api_version="v1")
        )

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def list_tables(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def get_table_schema(self, table_name):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()
        return schema

    def build_schema_prompt(self):
        tables = self.list_tables()
        prompt_parts = []
        for table in tables:
            schema = self.get_table_schema(table)
            columns_str = ", ".join([f"{col} ({dtype})" for col, dtype in schema.items()])
            prompt_parts.append(f"Table '{table}' with columns: {columns_str}")
        return "\n".join(prompt_parts)

    def nl_to_sql(self, user_query):
        schema_description = self.build_schema_prompt()
        prompt = f"""
        You are a SQL generator with knowledge of the database schema below.
        Identify relevant tables/columns for the user question.

        Database schema:
        {schema_description}

        Question: {user_query}

        Rules:
        1. Only include relevant columns.
        2. Return valid SQLite SQL.
        3. If unanswerable, return: -- no query
        4. Return only SQL, no explanations.
        """
        try:
            predictions = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt],
            )
            return clean_sql(predictions.text)
        except Exception as e:
            logging.error(f"Vertex AI SQL generation failed: {e}")
            return ""

    def execute_sql(self, sql_query):
        if not sql_query or "-- no query" in sql_query.lower():
            return {"error": "Query cannot be generated from the user input."}
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return {"columns": columns, "rows": rows}
        except Exception as e:
            logging.error(f"SQL execution failed: {e}")
            return {"error": str(e)}

    def handle_query(self, user_query):
        sql_query = self.nl_to_sql(user_query)
        logging.info(f"Generated SQL:\n{sql_query}")
        result = self.execute_sql(sql_query)
        # Fallback for empty result
        if not result.get("rows") and "error" not in result:
            result["fallback"] = True
        return result



if __name__ == "__main__":
    agent = SQLAgent()
    print("Tables in DB:", agent.list_tables())
    query = "What is my next EMI?"
    result = agent.handle_query(query)
    print(result)
