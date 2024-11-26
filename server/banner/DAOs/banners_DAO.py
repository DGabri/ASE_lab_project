import sqlite3
from db_result import DBResult, DBResultCode
from classes.banner import Banner

class BannersDAO:
    def __init__(self, database, scheme):
        self.connection = sqlite3.connect(database, check_same_thread = False)
        self.cursor = self.connection.cursor()

        try:
            with open(scheme, 'r') as sql_file:
                sql_script = sql_file.read()
        except FileNotFoundError:
            print("File 'scheme' not found.")
        except ValueError:
            print("File 'scheme' not open.")

        try:
            with self.connection:
                self.cursor.executescript(sql_script)
        except sqlite3.Error as e:
            print(f"Cannot initialize banners DAO: {e}")
    
    def get_banner(self, banner_id):
        try:
            with self.connection:
                self.cursor.execute(
                    'SELECT * FROM banners WHERE id = ?',
                    (banner_id,)
                )

                row = self.cursor.fetchone()

            if not row:
                return DBResult(None, DBResultCode.NOT_FOUND, "No banner found")

            return DBResult(Banner.from_array(list(row[:5]) + [list(row[5:])]), DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))
    
    def insert_banner(self, banner):
        try:
            with self.connection:
                self.cursor.execute(
                    'INSERT INTO banners (name, cost, pic, piece_num, common_rate, rare_rate, super_rare_rate) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id',
                    (banner.name, banner.cost, banner.pic, banner.pieces_num, banner.rates.common, banner.rates.rare, banner.rates.super_rare)
                )

                (piece_id,) = self.cursor.fetchone()
    
            return DBResult(piece_id, DBResultCode.OK, "")
        except sqlite3.Error as e:
            return DBResult(None, DBResultCode.ERROR, str(e))

    def update_banner(self, banner):
        banner = banner.to_dict()
        banner_keys = ()
        banner_values = ()
        
        for key, value in banner.items():
            if key == 'rates':
                if value:
                    for grade, rate in value.items():
                        banner_keys += (grade + '_rate',)
                        banner_values += (rate,)
            elif value != None and key != 'id':
                banner_keys += (key,)
                banner_values += (value,)

        try:
            with self.connection:
                # SQL injection checked
                self.cursor.execute('UPDATE banners SET ' + ', '.join([f"{key} = ?" for key in banner_keys]) + ' WHERE id = ? RETURNING id', banner_values + (banner['id'],)) # nosec
                row = self.cursor.fetchone()

            if not row:
                return DBResult(True, DBResultCode.NOT_FOUND, "No banner founded")
            
            return DBResult(True, DBResultCode.OK, "Banner updated")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))
    
    def delete_banner(self, banner_id):
        try:
            with self.connection:
                self.cursor.execute(
                    'DELETE FROM banners WHERE id = ? RETURNING id',
                    banner_id
                )

                row = self.cursor.fetchone()

            if not row:
                return DBResult(True, DBResultCode.NOT_FOUND, "No banner founded")
            
            return DBResult(True, DBResultCode.OK, "Banner updated")
        except sqlite3.Error as e:
            return DBResult(False, DBResultCode.ERROR, str(e))

    def close(self):
        self.connection.close()