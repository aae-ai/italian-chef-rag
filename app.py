from flask import Flask, render_template, request, jsonify
from rag_engine import ChefBot

app = Flask(__name__)
bot = ChefBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')

    if not user_input:
        return jsonify({"error": "No message"}), 400

    try:
        response = bot.ask(user_input)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True, use_reloader=False)
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
if __name__ == "__main__":
    app.run(debug=False)