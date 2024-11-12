from flask import Flask, request, make_response, jsonify
from pieces_DAO import PiecesDAO
from piece import Piece
import sqlite3

GRADES = ['C', 'R', 'SR']

app = Flask(__name__)
piece_dao = PiecesDAO('pieces.db', 'pieces_scheme.sql')

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

@app.route('/piece', methods = ['GET'])
def get_pieces():
    data = request.get_json()

    if not 'pieces_id' in data or not all(isinstance(piece_id, int) for piece_id in data['pieces_id']):
        return make_response(jsonify(message = "Attribute 'piece_id' not found or invalid"), 400)

    pieces, mess = piece_dao.get_pieces_by_id(data['pieces_id'])

    if pieces:
        return make_response(jsonify(list = pieces), 200)
    else:
        return make_response(jsonify(message = str(mess)), 500)
    
@app.route('/piece', methods = ['POST'])
def add_piece():
    piece = request.get_json()

    if not piece_is_valid(piece):
        return make_response(jsonify(message = "Attributes not found or invalid"), 400)

    new_piece = Piece(None, piece['name'], piece['grade'], piece['pic_url'], piece['description'])
    piece_id, mess = piece_dao.insert_piece(new_piece)

    if piece_id:
        return make_response(jsonify(piece_id = piece_id), 201)
    else:
        return make_response(jsonify(message = str(mess)), 500)

@app.route('/piece/<int:piece_id>', methods = ['PUT'])
def update_piece(piece_id):
    piece = request.get_json()

    if not piece_is_valid(piece):
        return make_response(jsonify(message = "Attributes not found or invalid"), 400)

    updated_piece = Piece(piece_id, piece['name'], piece['grade'], piece['pic_url'], piece['description'])
    updated, mess = piece_dao.update_piece(updated_piece)

    if updated:
        return make_response(jsonify(message = "Piece updated successfully"), 200)
    else:
        return make_response(jsonify(message = mess), 500)

@app.route('/piece/all', methods = ['GET'])
def get_all_pieces():
    pieces, mess = piece_dao.get_all_pieces()

    if pieces:
        return make_response(jsonify(list = pieces), 200)
    else:
        return make_response(jsonify(message = mess), 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)