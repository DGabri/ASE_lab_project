import sqlite3
import typing

class PiecesDAO:
    def __init__(self, database, scheme):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

        with open(scheme, 'r') as sql_file:
            sql_script = sql_file.read()

        try:
            with self.connection:
                self.cursor.executescript(sql_script)
        except sqlite3.Error:
            pass # handle exception
    
    def get_piece_by_id(self, piece_id) -> Any:
        try:
            self.cursor.execute('SELECT * FROM pieces WHERE id = ?', (piece_id))
            return cursor.fetchone()
        except sqlite3.Error:
            self.connection.rollback()
            return None # check structure of return data
    
    def get_all_pieces(self) -> Any:
        try:
            self.cursor.execute('SELECT * FROM pieces')
            return cursor.fetchall()
        except sqlite3.Error:
            self.connection.rollback()
            return None # check structure of return data
    
    def insert_piece(self, piece) -> int:
        try:
            self.cursor.execute('INSERT INTO pieces (name, grade, pic_url, description) VALUES (?, ?, ?, ?)', (piece.name, piece.grade, piece.pic_url, piece.description))
            self.connection.commit()
            return 0 # id of the created piece
        except sqlite3.Error:
            self.connection.rollback()
            return 0
    
    def update_piece(self, piece) -> bool:
        try:
            self.cursor.execute('UPDATE pieces SET name = ?, grade = ?,  pic_url = ?,  description = ?WHERE id = ?', (piece.name, piece.grade, piece.pic_url, piece.description))
            self.connection.commit()
            return True
        except sqlite3.Error:
            self.connection.rollback()
            return False
    
    def delete_piece(self, piece_id) -> bool:
        try:
            self.cursor.execute('DELETE FROM pieces WHERE id = ?', (piece_id))
            self.connection.commit()
            return True
        except sqlite3.Error:
            self.connection.rollback()
            return False

    def close(self):
        self.connection.close()