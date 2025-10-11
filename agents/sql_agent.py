# agents/sql_agent.py

import sqlite3
import os
from google.cloud import aiplatform, storage
from dotenv import load_dotenv

# -----------------------------
# Helper function to fetch DB from GCS
# -----------------------------
def download_db_from_gcs(bucket_name, blob_name, local_path="/tmp/loans.db"):
    """Download SQLite DB from Google Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    return local_path


# -----------------------------
# SQLAgent Class
# -----------------------------
class SQLAgent:
    def __init__(self, db_path=None):
        """
        db_path: path to SQLite DB; if None, downloads from GCS
        """
        self.db_path = db_path or download_db_from_gcs(
            bucket_name=os.getenv("LOAN_DB_BUCKET"),
            blob_name=os.getenv("LOAN_DB_BLOB")
        )
        # Initialize Vertex AI
        self.project = os.getenv("GCP_PROJECT")
        self.location = os.getenv("GCP_REGION", "us-central1")
        aiplatform.init(project=self.project, location=self.location)
        self.model = os.getenv("VERTEX_AI_MODEL", "gemini-1.5")

    # -----------------------------
    # Connect to SQLite DB
    # -----------------------------
    def _connect(self):
        return sqlite3.connect(self.db_path)

    # -----------------------------
    # Convert NL -> SQL using Vertex AI Gemini
    # -----------------------------
    def nl_to_sql(self, user_query):
        """
        Calls Vertex AI text-generation model to convert NL query -> SQL
        """
        from google.cloud.aiplatform.gapic.schema import predict
        from google.cloud.aiplatform.gapic import PredictionServiceClient
        from google.protobuf import json_format
        import json

        client = aiplatform.gapic.PredictionServiceClient()

        endpoint = f"projects/{self.project}/locations/{self.location}/models/{self.model}"

        prompt = f"""
        You are a SQL generator. Convert the following natural language question into a 
        parameterized SQL query against a SQLite database with table 'loans' having columns: 
        loan_amount, tenure, interest_rate, topup_eligible.
        Return only the SQL.
        Question: {user_query}
        """

        instance = {"content": prompt}
        instances = [json_format.ParseDict(instance, predict.instance.Instance())]

        response = client.predict(endpoint=endpoint, instances=instances)
        predictions = response.predictions

        if predictions and len(predictions) > 0:
            sql_query = predictions[0].get("content", "").strip()
            return sql_query
        return None

    # -----------------------------
    # Execute SQL safely
    # -----------------------------
    def execute_sql(self, sql_query):
        if not sql_query:
            return {"error": "Cannot convert query to SQL."}

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return {"columns": columns, "rows": rows}
        except Exception as e:
            return {"error": str(e)}

    # -----------------------------
    # Main entry: handle user query
    # -----------------------------
    def handle_query(self, user_query):
        sql_query = self.nl_to_sql(user_query)
        result = self.execute_sql(sql_query)
        return result


if __name__ == "__main__":

    load_dotenv()

    agent = SQLAgent()
    query = "What is my next EMI?"
    result = agent.handle_query(query)
    print(result)
