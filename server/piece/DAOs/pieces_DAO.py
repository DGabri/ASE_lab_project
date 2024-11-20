import sqlite3
from db_result import DBResult, DBResultCode
from classes.piece import Piece

class PiecesDAO:
    def __init__(self, database, scheme):
        self.connection = sqlite3.connect(database, check_same_thread = False)
        self.cursor = self.connection.cursor()

        with open(scheme, 'r') as sql_file:
            sql_script = sql_file.read()

        try:
            with self.connection:
                self.cursor.executescript(sql_script)
        except sqlite3.Error as e:
            print(f"Cannot initialize pieces DAO: {e}")
    
    def get_pieces(self, pieces_id):
        try:
            with self.connection:
                self.cursor.execute(
                    'SELECT * FROM pieces WHERE id IN (%s)' % ','.join('?' * len(pieces_id)),
                    (pieces_id,)
                )

                rows = self.cursor.fetchall()

            if not rows:
                return DBResult(None, DBResultCode.NOT_FOUND, "No pieces found")

            return DBResult([Piece.from_array(list(row)) for row in rows], DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))
    
    def get_all_pieces(self):
        try:
            with self.connection:
                self.cursor.execute('SELECT * FROM pieces')
                rows = self.cursor.fetchall()

            if not rows:
                return DBResult(None, DBResultCode.NOT_FOUND, "No pieces found")

            return DBResult([Piece.from_array(list(row)) for row in rows], DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))
    
    def insert_piece(self, piece):
        try:
            with self.connection:
                self.cursor.execute(
                    'INSERT INTO pieces (name, grade, pic, value, description) VALUES (?, ?, ?, ?, ?) RETURNING id',
                    (piece.name, piece.grade, piece.pic, piece.value, piece.description)
                )

                (piece_id,) = self.cursor.fetchone()
    
            return DBResult(piece_id, DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))

    def update_piece(self, piece):
        piece = vars(piece)
        piece_keys = ()
        piece_values = ()
        
        for key, value in piece.items():
            if value != None and key != 'id':
                piece_keys += (key,)
                piece_values += (value,)

        try:
            with self.connection:
                self.cursor.execute('UPDATE pieces SET ' + ', '.join([f"{key} = ?"  for key in piece_keys]) + ' WHERE id = ? RETURNING id', piece_values + (piece['id'],))
                row = self.cursor.fetchone()

            if not row:
                return DBResult(True, DBResultCode.NOT_FOUND, "No piece founded")
            
            return DBResult(True, DBResultCode.OK, "Piece updated")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))

    def close(self):
        self.connection.close()