from flask import Blueprint, request, jsonify
from app.agent.sql_agent import SQLAgent

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

# Initialize agent (singleton for the app)
agent = SQLAgent()


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    
    Request body:
        {"message": "user's question"}
    
    Response:
        {
            "answer": "natural language response",
            "sql": "generated SQL query (if any)",
            "data": [...] or null,
            "error": null or "error message"
        }
    """
    data = request.get_json()
    
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400
    
    user_message = data["message"].strip()
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Process the question through the agent
    result = agent.ask(user_message)
    
    return jsonify(result)


@chat_bp.route("/schema", methods=["GET"])
def get_schema():
    """Return the current schema documentation (for debugging)."""
    from app.database.schema import get_schema_documentation
    return jsonify({"schema": get_schema_documentation()})