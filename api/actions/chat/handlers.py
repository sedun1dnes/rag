from flask import request, jsonify
from shared.rag.pipeline import RagPipeline

def post_message():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data["message"]
        rag = RagPipeline()
        response_text = rag.retrieve_and_generate(user_message)

        return jsonify({"response": response_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500