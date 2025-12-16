from app import create_app
from config import settings

app = create_app()


@app.route("/")
def index():
    """Serve the chat interface."""
    from flask import render_template
    return render_template("chat.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=settings.flask_debug, host="0.0.0.0", port=5000)
