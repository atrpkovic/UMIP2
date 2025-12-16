"""Quick test script to verify app routes."""
from app.main import app

print("\n=== Testing Flask App Routes ===\n")

# Create a test client
with app.test_client() as client:
    # Test health endpoint
    print("Testing /health endpoint...")
    response = client.get('/health')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")

    # Test index endpoint
    print("\nTesting / endpoint...")
    response = client.get('/')
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.content_type}")
    print(f"Content length: {len(response.data)} bytes")

    if response.status_code == 200:
        print("✓ Index page loads successfully!")
    else:
        print(f"✗ Index page failed with status {response.status_code}")
        print(f"Error: {response.data[:500]}")

print("\n=== All Flask routes registered ===")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} -> {rule.endpoint}")
