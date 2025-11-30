import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg  # PostgreSQL driver

app = Flask(__name__)
CORS(app)   # επιτρέπει requests από το frontend

# Παίρνουμε το DATABASE_URL από τα env vars του Render
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    # autocommit=True για να μην ασχολούμαστε με manual commit
    return psycopg.connect(DATABASE_URL, autocommit=True)


# ---------- BASIC ROUTES ----------

@app.route("/")
def home():
    return {"message": "Backend is running!"}


@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask backend!"})


@app.route("/api/db-test")
def db_test():
    """Απλό test ότι η DB απαντάει."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW()")
                (now,) = cur.fetchone()
        return jsonify({"status": "ok", "db_time": now.isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ---------- 1. INIT DB (CREATE TABLE) ----------

@app.route("/api/init-db")
def init_db():
    """
    Δημιουργεί τον πίνακα notes αν δεν υπάρχει.
    Την καλείς ΜΟΝΟ για setup (π.χ. μια φορά από τον browser).
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
        return jsonify({"status": "ok", "message": "notes table ready"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ---------- 2. CREATE (POST) ----------

@app.route("/api/notes", methods=["POST"])
def create_note():
    """
    Περιμένει JSON:
    {
      "title": "κάτι",
      "content": "προαιρετικό κείμενο"
    }
    """
    data = request.get_json() or {}
    title = data.get("title")
    content = data.get("content", "")

    if not title:
        return jsonify({"error": "title is required"}), 400

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO notes (title, content)
                    VALUES (%s, %s)
                    RETURNING id, title, content, created_at;
                    """,
                    (title, content),
                )
                row = cur.fetchone()

        note = {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        }
        return jsonify(note), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- 3. READ ALL (GET) ----------

@app.route("/api/notes", methods=["GET"])
def list_notes():
    """
    Επιστρέφει όλα τα notes σαν JSON list.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, content, created_at "
                    "FROM notes ORDER BY id;"
                )
                rows = cur.fetchall()

        notes = [
            {
                "id": r[0],
                "title": r[1],
                "content": r[2],
                "created_at": r[3].isoformat() if r[3] else None,
            }
            for r in rows
        ]
        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- 4. READ ONE (GET by id) ----------

@app.route("/api/notes/<int:note_id>", methods=["GET"])
def get_note(note_id):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, content, created_at
                    FROM notes
                    WHERE id = %s;
                    """,
                    (note_id,),
                )
                row = cur.fetchone()

        if row is None:
            return jsonify({"error": "note not found"}), 404

        note = {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        }
        return jsonify(note)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- 5. UPDATE (PUT) ----------

@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    """
    Περιμένει JSON με όποια πεδία θες να αλλάξεις:
    {
      "title": "νέος τίτλος",
      "content": "νέο περιεχόμενο"
    }
    """
    data = request.get_json() or {}
    title = data.get("title")
    content = data.get("content")

    if title is None and content is None:
        return jsonify({"error": "nothing to update"}), 400

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Παίρνουμε το παλιό note
                cur.execute(
                    "SELECT id, title, content, created_at FROM notes WHERE id = %s;",
                    (note_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return jsonify({"error": "note not found"}), 404

                current_title = row[1]
                current_content = row[2]

                new_title = title if title is not None else current_title
                new_content = content if content is not None else current_content

                cur.execute(
                    """
                    UPDATE notes
                    SET title = %s, content = %s
                    WHERE id = %s
                    RETURNING id, title, content, created_at;
                    """,
                    (new_title, new_content, note_id),
                )
                updated = cur.fetchone()

        note = {
            "id": updated[0],
            "title": updated[1],
            "content": updated[2],
            "created_at": updated[3].isoformat() if updated[3] else None,
        }
        return jsonify(note)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- 6. DELETE (DELETE) ----------

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM notes WHERE id = %s RETURNING id;", (note_id,))
                row = cur.fetchone()

        if row is None:
            return jsonify({"error": "note not found"}), 404

        return jsonify({"status": "deleted", "id": note_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- MAIN ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)