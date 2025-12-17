from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
from app.agent.sql_agent import SQLAgent

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

# Initialize agent (singleton for the app)
agent = SQLAgent()


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint (non-streaming).

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


@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Request body:
        {"message": "user's question"}

    Response:
        Server-Sent Events stream with JSON objects:
        - {"type": "token", "content": "text"}
        - {"type": "sql", "content": "SELECT ..."}
        - {"type": "status", "content": "status message"}
        - {"type": "data_ready", "row_count": 123}
        - {"type": "complete", "sql": "...", "data": [...]}
        - {"type": "error", "content": "error message"}
    """
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_message = data["message"].strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    def generate():
        """Generator function for streaming events."""
        try:
            for event in agent.ask_stream(user_message):
                # Format as SSE: data: {json}\n\n
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            # Send error event
            error_event = {
                "type": "error",
                "content": f"Stream error: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\n\n"

            # Send completion event
            complete_event = {
                "type": "complete",
                "sql": None,
                "data": None,
                "error": str(e)
            }
            yield f"data: {json.dumps(complete_event)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@chat_bp.route("/schema", methods=["GET"])
def get_schema():
    """Return the current schema documentation (for debugging)."""
    from app.database.schema import get_schema_documentation
    return jsonify({"schema": get_schema_documentation()})


@chat_bp.route("/model", methods=["POST"])
def set_model():
    """
    Set the active LLM model.

    Request body:
        {"model": "claude-sonnet" | "llama-3.3-70b" | "deepseek-v3" | "gemini"}

    Response:
        {"success": true, "model": "selected-model-name"}
    """
    data = request.get_json()

    if not data or "model" not in data:
        return jsonify({"error": "Missing 'model' in request body"}), 400

    model_key = data["model"]

    # Map frontend model keys to actual model identifiers
    model_mapping = {
        "claude-sonnet": "claude-sonnet-4-5-20250929",
        "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
        "deepseek-v3": "deepseek-ai/DeepSeek-V3",
        "gemini": "gemini-2.0-flash-exp"
    }

    if model_key not in model_mapping:
        return jsonify({"error": f"Invalid model: {model_key}"}), 400

    # Update the agent's model
    agent.set_model(model_key, model_mapping[model_key])

    return jsonify({"success": True, "model": model_key})