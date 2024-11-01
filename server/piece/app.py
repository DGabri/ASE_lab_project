from flask import Flask, request, make_response, jsonify
from DAO import PieceDAOSQLite
from model import Piece
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return make_response(jsonify(s = "res"), 200)

@app.route('/piece', methods=['GET', 'POST'])
def piece():
    if request.method == 'POST':
        data = request.get_json()
        piece_dao = PieceDAOSQLite('pieces.db')
        new_piece = Piece(None, 'King', 'SR', '', 'The king (♔, ♚) is the most important piece in the game of chess. It may move to any adjoining square; it may also perform, in tandem with the rook, a special move called castling. If a player\'s king is threatened with capture, it is said to be in check, and the player must remove the threat of capture immediately. If this cannot be done, the king is said to be in checkmate, resulting in a loss for that player. A player cannot make any move that places their own king in check. Despite this, the king can become a strong offensive piece in the endgame or, rarely, the middlegame.')
        piece_dao.insert_piece(new_piece)
        return make_response("Piece created successfully", 201)
            
    if request.method == 'GET':
        piece_id = request.args.get('piece_id')
        piece_dao = PieceDAOSQLite('pieces.db')
        pieces = piece_dao.get_piece_by_id(piece_id)
        return make_response(jsonify(list=pieces), 200)

if __name__ == '__main__':
    connection = sqlite3.connect('pieces.db')
    cur = connection.cursor()
    
    try:
        cur.execute(
            '''CREATE TABLE pieces(
                id integer primary key, 
                name text, 
                grade text, 
                pic_url text,
                description text
            )'''
        )
    except sqlite3.OperationalError:
        print("Error in creation of table pieces")
    
    print("\nDatabase created successfully!")
    connection.commit()
    connection.close()
    app.run(host='0.0.0.0', port='5000', debug=True)