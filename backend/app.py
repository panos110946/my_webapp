import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)   # επιτρέπει requests από το frontend

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask backend!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)