import sqlite3

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

            return self.cursor.fetchall(), ""
        except sqlite3.Error as e:
            return None, e
    
    def get_all_pieces(self):
        try:
            with self.connection:
                self.cursor.execute('SELECT * FROM pieces')

            return self.cursor.fetchall(), ""
        except sqlite3.Error as e:
            return None, e
    
    def insert_piece(self, piece):
        try:
            self.cursor.execute('INSERT INTO pieces (name, grade, pic_url, description) VALUES (?, ?, ?, ?) RETURNING id', (piece.name, piece.grade, piece.pic_url, piece.description))
            row = self.cursor.fetchone()
            piece_id = row if row else None
            self.cursor.commit()
            return piece_id, ""
        except sqlite3.Error as e:
            return None, e

    def update_piece(self, piece):
        try:
            with self.connection:
                self.cursor.execute('UPDATE pieces SET name = ?, grade = ?,  pic_url = ?,  description = ? WHERE id = ?', (piece.name, piece.grade, piece.pic_url, piece.description, piece.id))
            
            return True, ""
        except sqlite3.Error as e:
            return False, e
    
    def delete_piece(self, piece_id):
        try:
            with self.connection:
                self.cursor.execute('DELETE FROM pieces WHERE id = ?', (piece_id))

            return True, ""
        except sqlite3.Error as e:
            return False, e

    def close(self):
        self.connection.close()