from app import create_app
from config import settings

app = create_app()

if __name__ == "__main__":
    app.run(debug=settings.flask_debug, host="0.0.0.0", port=5000)
