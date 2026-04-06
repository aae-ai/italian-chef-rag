import os
import logging
import traceback
from flask import Flask, render_template, request, jsonify
from rag_engine import ChefBot

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# ---------------------------------------------------------------------------
# ChefBot initialisation — wrapped so the app can still start on failure
# ---------------------------------------------------------------------------
bot = None
bot_init_error = None

try:
    logger.info("Initialising ChefBot...")
    bot = ChefBot()
    logger.info("ChefBot initialised successfully.")
except Exception as e:
    bot_init_error = str(e)
    logger.error("ChefBot failed to initialise: %s", bot_init_error)
    logger.error(traceback.format_exc())

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/health')
def health():
    """Lightweight health check that does not depend on the RAG engine."""
    status = {
        "status": "ok",
        "bot_ready": bot is not None,
    }
    if bot_init_error:
        status["bot_init_error"] = bot_init_error
    return jsonify(status), 200


@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error("Error rendering index: %s", e)
        logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to render page", "detail": str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    if bot is None:
        logger.error("Chat request received but ChefBot is not available. Init error: %s", bot_init_error)
        return jsonify({
            "error": "ChefBot is not available.",
            "detail": bot_init_error or "Unknown initialisation error.",
        }), 503

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        user_input = data.get('message')
        if not user_input:
            return jsonify({"error": "No message"}), 400

        logger.info("Received chat message (length=%d)", len(user_input))
        response = bot.ask(user_input)
        logger.info("ChefBot responded successfully.")
        return jsonify({"response": response})

    except Exception as e:
        logger.error("Unhandled error in /chat: %s", e)
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False)