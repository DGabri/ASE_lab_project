from flask import Flask, request, make_response, jsonify
from pieces_DAO import PiecesDAO
from db_result import DBResultCode
from piece import Piece
import sqlite3
import json

GRADES = ['C', 'R', 'SR']

with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
piece_dao = PiecesDAO(config['db']['name'], config['db']['scheme'])

def piece_is_valid(piece):
    if not 'name' in piece or not isinstance(piece['name'], str) or not piece['name']:
        return False

    if not 'grade' in piece or not piece['grade'] in GRADES:
        return False

    if not 'pic_url' in piece or not isinstance(piece['pic_url'], str) or not piece['pic_url']:
        return False

    if not 'description' in piece or not isinstance(piece['description'], str) or not piece['description']:
        return False

    return True

# Get a list of pieces
@app.route('/piece', methods = ['GET'])
def get_pieces():
    data = request.get_json()

    if not 'pieces_id' in data or not all(isinstance(piece_id, int) for piece_id in data['pieces_id']):
        return make_response(jsonify(message = "Attribute 'piece_id' not found or invalid"), 400)

    result = piece_dao.get_pieces_by_id(data['pieces_id'])

    if result.code == DBResultCode.OK:
        return make_response(jsonify(pieces = result.content), 200)
    else:
        return make_response(jsonify(message = str(result.message)), 500)

# Create a piece
@app.route('/piece', methods = ['POST'])
def add_piece():
    piece = request.get_json()

    if not piece_is_valid(piece):
        return make_response(jsonify(message = "Attributes not found or invalid"), 400)

    new_piece = Piece(None, piece['name'], piece['grade'], piece['pic_url'], piece['description'])
    result = piece_dao.insert_piece(new_piece)

    if result.code == DBResultCode.OK:
        return make_response(jsonify(piece_id = result.content), 201)
    else:
        return make_response(jsonify(message = result.message), 500)

# Update a piece
@app.route('/piece/<int:piece_id>', methods = ['PUT'])
def update_piece(piece_id):
    piece = request.get_json()

    if not piece_is_valid(piece):
        return make_response(jsonify(message = "Attributes not found or invalid"), 400)

    updated_piece = Piece(piece_id, piece['name'], piece['grade'], piece['pic_url'], piece['description'])
    result = piece_dao.update_piece(updated_piece)

    if result.code == DBResultCode.OK:
        return make_response(jsonify(message = result.message), 200)
    elif result.code == DBResultCode.NOT_FOUND:
        return make_response(jsonify(message = result.message), 404)
    else:
        return make_response(jsonify(message = result.message), 500)

# Get all pieces in the database
@app.route('/piece/all', methods = ['GET'])
def get_all_pieces():
    result = piece_dao.get_all_pieces()

    if result.code == DBResultCode.OK:
        return make_response(jsonify(pieces = result.content), 200)
    else:
        return make_response(jsonify(message = result.message), 200)

if __name__ == '__main__':
    app.run(debug=True)