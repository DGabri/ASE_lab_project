import sqlite3

class PieceDAOSQLite:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
    
    def get_piece_by_id(self, piece_id):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM pieces WHERE id = ?', (piece_id))
        return cursor.fetchone()
    
    def get_all_pieces(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM pieces')
        return cursor.fetchall()
    
    def insert_piece(self, piece):
        cursor = self.connection.cursor()
        cursor.execute('INSERT INTO pieces (name, grade, pic_url, description) VALUES (?, ?, ?, ?)', (piece.name, piece.grade, piece.pic_url, piece.description))
        self.connection.commit()
    
    def update_piece(self, piece):
        cursor = self.connection.cursor()
        cursor.execute('UPDATE pieces SET name = ?, grade = ?,  pic_url = ?,  description = ?WHERE id = ?', (piece.name, piece.grade, piece.pic_url, piece.description))
        self.connection.commit()
    
    def delete_piece(self, piece_id):
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM pieces WHERE id = ?', (piece_id))
        self.connection.commit()