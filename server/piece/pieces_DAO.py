import sqlite3
from db_result import DBResult, DBResultCode

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
    
    def get_pieces_by_id(self, pieces_id):
        try:
            with self.connection:
                self.cursor.execute('SELECT * FROM pieces WHERE id IN (%s)' % ','.join('?' * len(pieces_id)), pieces_id)

            return DBResult(self.cursor.fetchall(), DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))
    
    def get_all_pieces(self):
        try:
            with self.connection:
                self.cursor.execute('SELECT * FROM pieces')

            return DBResult(self.cursor.fetchall(), DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))
    
    def insert_piece(self, piece):
        try:
            with self.connection:
                self.cursor.execute('INSERT INTO pieces (name, grade, pic_url, description) VALUES (?, ?, ?, ?) RETURNING id', (piece.name, piece.grade, piece.pic_url, piece.description))
                [piece_id] = self.cursor.fetchone()
    
            return DBResult(piece_id, DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))

    def update_piece(self, piece):
        try:
            with self.connection:
                self.cursor.execute('UPDATE pieces SET name = ?, grade = ?,  pic_url = ?,  description = ? WHERE id = ? RETURNING id', (piece.name, piece.grade, piece.pic_url, piece.description, piece.id))
                row = self.cursor.fetchone()

            if row:
                return DBResult(True, DBResultCode.OK, "Piece updated")
            else:
                return DBResult(True, DBResultCode.NOT_FOUND, "No piece founded")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))
    
    def delete_piece(self, piece_id):
        try:
            with self.connection:
                self.cursor.execute('DELETE FROM pieces WHERE id = ?', (piece_id))

            return DBResult(True, DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))

    def close(self):
        self.connection.close()