from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
from DAOs.pieces_DAO import PiecesDAO
from classes.db_result import DBResultCode
from classes.piece import Piece
import sqlite3
import json
import logging

GRADES = ['C', 'R', 'SR']

try:
    with open('config.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("File 'config' not found.")
except ValueError:
    print("Decoding JSON 'config' file has failed.")

logging.basicConfig(filename='piece.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
app = Flask(__name__)
CORS(app)
pieces_dao = PiecesDAO(config['db']['name'], config['db']['scheme'])
app.config['WTF_CSRF_ENABLED'] = False

def piece_is_valid(piece, to_check):
    if to_check['name'] and (not 'name' in piece or not isinstance(piece['name'], str) or not piece['name']):
        return False

    if to_check['grade'] and (not 'grade' in piece or not piece['grade'] in GRADES):
        return False

    if to_check['pic'] and (not 'pic' in piece or not isinstance(piece['pic'], str) or not piece['pic']):
        return False

    if to_check['value'] and (not 'value' in piece or not isinstance(piece['value'], int) or piece['value'] < 0 or piece['value'] > 10):
        return False

    if to_check['description'] and (not 'description' in piece or not isinstance(piece['description'], str) or not piece['description']):
        return False

    return True

# Get a list of pieces
@app.route('/piece', methods = ['GET'])
def get_pieces():
    pieces_id = request.args.getlist('id')

    if len(pieces_id) == 0 or not all(int(piece_id) > 0 for piece_id in pieces_id):
        return jsonify(message = "Attribute 'piece_id' not found or invalid"), 400

    result = pieces_dao.get_pieces(pieces_id)

    if result.code == DBResultCode.NOT_FOUND:
        return jsonify(message = result.message), 404

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500
    
    return jsonify(pieces = [piece.to_dict() for piece in result.content]), 200
        

# Add a new piece
@app.route('/piece', methods = ['POST'])
def add_piece():
    piece = request.get_json()

    if not piece_is_valid(piece, {
        'name': True,
        'grade': True,
        'pic': True,
        'value': True,
        'description': True
    }):
        return jsonify(message = "Attributes not found or invalid"), 400

    new_piece = Piece(None, piece['name'], piece['grade'], piece['pic'], piece['value'], piece['description'])
    result = pieces_dao.insert_piece(new_piece)

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500
    
    return jsonify(piece_id = result.content), 201
        
# Update a piece
@app.route('/piece/<int:piece_id>', methods = ['PUT'])
def update_piece(piece_id):
    piece = request.get_json()

    if not piece_is_valid(piece,  {
        'name': 'name' in piece,
        'grade': 'grade' in piece,
        'pic': 'pic' in piece,
        'value': 'value' in piece,
        'description': 'description' in piece
    }):
        return jsonify(message = "Attributes invalid"), 400

    piece = Piece(
        piece_id,
        piece['name'] if 'name' in piece else None,
        piece['grade'] if 'grade' in piece else None,
        piece['pic'] if 'pic' in piece else None,
        piece['value'] if 'value' in piece else None,
        piece['description'] if 'description' in piece else None
    )

    if not piece.to_dict():
        return jsonify(message = "No attribute found"), 400

    result = pieces_dao.update_piece(piece)

    if result.code == DBResultCode.NOT_FOUND:
            return jsonify(message = result.message), 404

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500
    
    return jsonify(message = result.message), 200  

# Get all the pieces in the database
@app.route('/piece/all', methods = ['GET'])
def get_all_pieces():
    result = pieces_dao.get_all_pieces()

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500

    return jsonify(pieces = [piece.to_dict() for piece in result.content]), 200

if __name__ == '__main__':
    app.run(debug = True) # nosec