import os
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg  # από το psycopg στο requirements.txt

app = Flask(__name__)
CORS(app)   # επιτρέπει requests από το frontend

# Παίρνουμε το DATABASE_URL από τα env vars του Render
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    # autocommit=True για να μην ασχολούμαστε με manual commit
    return psycopg.connect(DATABASE_URL, autocommit=True)



@app.route("/")
def home():
    return {
        "message": "Backend is running!"
    }


@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask backend!"})


@app.route("/api/db-test")
def db_test():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW()")
                (now,) = cur.fetchone()
        return jsonify({"status": "ok", "db_time": now.isoformat()})
    except Exception as e:
        # για debugging
        return jsonify({"status": "error", "error": str(e)}), 500




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)