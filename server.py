from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from nova_ultimate import chat_with_tools

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400
    try:
        response = chat_with_tools(message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=False)
