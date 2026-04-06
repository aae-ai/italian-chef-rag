from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>✅ Italian Chef RAG - Test Page</h1>
    <p>The basic Flask app is working on Railway!</p>
    <p>If you see this message, the deployment is successful.</p>
    <hr>
    <p>Next step: We will add your RAG functionality gradually.</p>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "message": "App is running correctly on Railway"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)