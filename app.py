from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Minimal App OK"

@app.route("/health")
def health():
    return "Minimal Health OK"

if __name__ == "__main__":
    app.run(debug=True)
