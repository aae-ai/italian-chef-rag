 from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>Italian Chef RAG - Test Page</h1>
    <p>If you see this, the basic Flask app is working.</p>
    <p><a href="/health">Check Health</a></p>
    """

@app.route('/health')
def health():
    return {"status": "ok", "message": "App is running"}

@app.route('/test')
def test():
    return {"status": "success", "test": "endpoint working"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)