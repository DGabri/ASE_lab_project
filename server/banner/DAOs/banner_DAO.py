import sqlite3
from db_result import DBResult, DBResultCode

class BannersDAO:
    def __init__(self, database, scheme):
        self.connection = sqlite3.connect(database, check_same_thread = False)
        self.cursor = self.connection.cursor()

        with open(scheme, 'r') as sql_file:
            sql_script = sql_file.read()

        try:
            with self.connection:
                self.cursor.executescript(sql_script)
        except sqlite3.Error as e:
            print(f"Cannot initialize banners DAO: {e}")
    
    def get_banner_by_id(self, banner_id):
        try:
            with self.connection:
                self.cursor.execute('SELECT * FROM banners WHERE id = ?',
                banner_id
            )

            return DBResult(self.cursor.fetchall(), DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))
    
    def insert_banner(self, banner):
        try:
            with self.connection:
                self.cursor.execute(
                    'INSERT INTO banners (name, cost, pic, piece_num, common_rate, rare_rate, super_rare_rate) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id',
                    (banner.name, banner.cost, banner.pic, banner.pieces_num, banner.rates.common, banner.rates.rare, banner.rates.super_rare)
                )

                [piece_id] = self.cursor.fetchone()
    
            return DBResult(piece_id, DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))

    def update_banner(self, banner_id):
        try:
            with self.connection:
                self.cursor.execute(
                    'UPDATE banners SET name = ?, cost = ?,  pic = ?, piece_num = ?, common_rate = ?, rare_rate = ?, super_rare_rate = ? WHERE id = ? RETURNING id',
                    (banner.name, banner.cost, banner.pic, banner.pieces_num, banner.rates.common, banner.rates.rare, banner.rates.super_rare, banner_id)
                )

                row = self.cursor.fetchone()

            if row:
                return DBResult(True, DBResultCode.OK, "Banner updated")
            else:
                return DBResult(True, DBResultCode.NOT_FOUND, "No banner founded")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))
    
    def delete_banner(self, banner_id):
        try:
            with self.connection:
                self.cursor.execute(
                    'DELETE FROM banners WHERE id = ?',
                    banner_id
                )

            return DBResult(True, DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))

    def close(self):
        self.connection.close()