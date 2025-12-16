"""User management endpoints for PIN-based recovery."""

from flask import Blueprint, request, jsonify
import json
import hashlib
from pathlib import Path

user_bp = Blueprint("user", __name__, url_prefix="/api/user")

# Simple file-based storage for PIN->UUID mappings
PIN_STORAGE_FILE = Path("data/pin_mappings.json")
PIN_STORAGE_FILE.parent.mkdir(exist_ok=True)

def load_pin_mappings():
    """Load PIN mappings from file."""
    if PIN_STORAGE_FILE.exists():
        try:
            with open(PIN_STORAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pin_mappings(mappings):
    """Save PIN mappings to file."""
    with open(PIN_STORAGE_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)

def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA-256."""
    return hashlib.sha256(pin.encode()).hexdigest()


@user_bp.route("/register-pin", methods=["POST"])
def register_pin():
    """
    Register a PIN for a user ID.

    Request body:
        {"pin": "1234", "userId": "uuid-here"}

    Response:
        {"success": true} or {"error": "message"}
    """
    data = request.get_json()

    if not data or "pin" not in data or "userId" not in data:
        return jsonify({"error": "Missing 'pin' or 'userId' in request body"}), 400

    pin = data["pin"].strip()
    user_id = data["userId"].strip()

    # Validate PIN (4-8 digits)
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 8:
        return jsonify({"error": "PIN must be 4-8 digits"}), 400

    if not user_id:
        return jsonify({"error": "User ID cannot be empty"}), 400

    # Hash the PIN
    pin_hash = hash_pin(pin)

    # Load existing mappings
    mappings = load_pin_mappings()

    # Store the mapping
    mappings[pin_hash] = user_id
    save_pin_mappings(mappings)

    return jsonify({"success": True})


@user_bp.route("/recover-user", methods=["POST"])
def recover_user():
    """
    Recover a user ID from a PIN.

    Request body:
        {"pin": "1234"}

    Response:
        {"userId": "uuid-here"} or {"error": "message"}
    """
    data = request.get_json()

    if not data or "pin" not in data:
        return jsonify({"error": "Missing 'pin' in request body"}), 400

    pin = data["pin"].strip()

    # Validate PIN format
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 8:
        return jsonify({"error": "Invalid PIN format"}), 400

    # Hash the PIN
    pin_hash = hash_pin(pin)

    # Load mappings
    mappings = load_pin_mappings()

    # Look up the user ID
    user_id = mappings.get(pin_hash)

    if user_id:
        return jsonify({"userId": user_id})
    else:
        return jsonify({"error": "PIN not found. Please check your PIN or start fresh."}), 404


@user_bp.route("/check-pin", methods=["POST"])
def check_pin():
    """
    Check if a user has a PIN registered.

    Request body:
        {"userId": "uuid-here"}

    Response:
        {"hasPin": true/false}
    """
    data = request.get_json()

    if not data or "userId" not in data:
        return jsonify({"error": "Missing 'userId' in request body"}), 400

    user_id = data["userId"].strip()

    # Load mappings
    mappings = load_pin_mappings()

    # Check if this user ID exists in any mapping
    has_pin = user_id in mappings.values()

    return jsonify({"hasPin": has_pin})
