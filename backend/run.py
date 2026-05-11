import sys
import os

try:
    from src.app import create_app
    app = create_app()
    print("✅ Flask app created successfully")
except Exception as e:
    print(f"❌ CRITICAL ERROR DURING APP CREATION: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

@app.route('/')
def health():
    return "NeuroPredict API is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)