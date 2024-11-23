import sqlite3
import bcrypt

class AuthDAO:
    def __init__(self, database):
        self.database = database
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def create_user(self, user_data):
        try:
           
            self.cursor.execute("""
                INSERT INTO users (username, email, hashed_password, user_type)
                VALUES (?, ?, ?, ?) """, 
            (user_data["username"], user_data["email"], user_data["password"], user_data["user_type"]))

            return self.cursor.lastrowid, None
        
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return None, "Username already present"
            elif "email" in str(e):
                return None, "Email already present"
            return None, str(e)
        
        except Exception as e:
            return None, str(e)

    def revoke_user_refresh_token(self, user_id):
        try:
            self.cursor.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id))

            return True
        
        except Exception as e:
            return False
    
    def verify_credentials(self, user_id, password):
        try:
            self.cursor.execute(
                "SELECT id, username, hashed_password, user_type, status FROM users WHERE id= = ?",
                (user_id)
            )
            user = self.cursor.fetchone()
            
            if not user:
                return None, "Invalid credentials"
            
            user_id, username, db_password_hash, user_type, status = user
            
            # user is banned
            if status == 0:
                return None, "Banned account"
                
            # check if provided password and db password coincide
            if bcrypt.checkpw(password.encode("utf-8"), db_password_hash.encode("utf-8")):
                return {
                    "user_id": user_id,
                    "username": username,
                    "user_type": user_type
                }, None
                
            return None, "Invalid credentials"
        except Exception as e:
            return None, str(e)

    def store_refresh_token(self, token, user_id, expires_at):
        self.cursor.execute(
            "INSERT INTO refresh_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at)
        )

    def verify_refresh_token(self, token):
        self.cursor.execute(
            """SELECT user_id FROM refresh_tokens 
               WHERE token = ? AND expires_at > CURRENT_TIMESTAMP""",
            (token)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None