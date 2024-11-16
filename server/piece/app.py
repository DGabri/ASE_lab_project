from flask import Flask, request, make_response, jsonify
from DAOs.pieces_DAO import PiecesDAO
from db_result import DBResultCode
from classes.piece import Piece
import sqlite3
import json

GRADES = ['C', 'R', 'SR']

with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
piece_dao = PiecesDAO(config['db']['name'], config['db']['scheme'])

def piece_is_valid(piece, to_check):
    if to_check['name'] and (not 'name' in piece or not isinstance(piece['name'], str) or not piece['name']):
        return False

    if to_check['grade'] and (not 'grade' in piece or not piece['grade'] in GRADES):
        return False

    if to_check['pic'] and (not 'pic' in piece or not isinstance(piece['pic'], str) or not piece['pic']):
        return False

    if to_check['point'] and (not 'point' in piece or not isinstance(piece['point'], int) or piece['point'] <= 0 or piece['point'] > 10):
        return False

    if to_check['description'] and (not 'description' in piece or not isinstance(piece['description'], str) or not piece['description']):
        return False

    return True

# Get a list of pieces
@app.route('/piece', methods = ['GET'])
def get_pieces():
    data = request.get_json()

    if 'pieces_id' in data or not all(isinstance(piece_id, int) for piece_id in data['pieces_id']):
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

    if not piece_is_valid(piece, {
        'name': True,
        'grade': True,
        'pic': True,
        'point': True,
        'description': True
    }):
        return make_response(jsonify(message = "Attributes not found or invalid"), 400)

    new_piece = Piece(None, piece['name'], piece['grade'], piece['pic'], piece['point'], piece['description'])
    result = piece_dao.insert_piece(new_piece)

    if result.code == DBResultCode.OK:
        return make_response(jsonify(piece_id = result.content), 201)
    else:
        return make_response(jsonify(message = result.message), 500)

# Update a piece
@app.route('/piece/<int:piece_id>', methods = ['PUT'])
def update_piece(piece_id):
    piece = request.get_json()

    if not piece_is_valid(piece,  {
        'name': 'name' in piece,
        'grade': 'grade' in piece,
        'pic': 'pic' in piece,
        'point': 'point' in piece,
        'description': 'description' in piece
    }):
        return make_response(jsonify(message = "Attributes invalid"), 400)

    piece = Piece(
        piece_id,
        piece['name'] if 'name' in piece else None,
        piece['grade'] if 'grade' in piece else None,
        piece['pic'] if 'pic' in piece else None,
        piece['point'] if 'point' in piece else None,
        piece['description'] if 'description' in piece else None
    )

    if not vars(piece):
        return make_response(jsonify(message = "No attribute found"), 400)

    result = piece_dao.update_piece(piece)

    if result.code == DBResultCode.OK:
        return make_response(jsonify(message = result.message), 200)
    elif result.code == DBResultCode.NOT_FOUND:
        return make_response(jsonify(message = result.message), 404)
    else:
        return make_response(jsonify(message = result.message), 500)

# Get all the pieces in the database
@app.route('/piece/all', methods = ['GET'])
def get_all_pieces():
    result = piece_dao.get_all_pieces()

    if result.code == DBResultCode.OK:
        return make_response(jsonify(pieces = result.content), 200)
    else:
        return make_response(jsonify(message = result.message), 200)

if __name__ == '__main__':
    app.run(debug = True)