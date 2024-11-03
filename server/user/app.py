from flask import Flask, make_response, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return make_response(jsonify(s="res"), 200)

if __name__ == '__main__':
    app.run(debug=True)