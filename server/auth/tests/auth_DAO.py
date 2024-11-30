import requests
import logging
import sqlite3
import bcrypt
import time
import time
logger = logging.getLogger(__name__)

class AuthDAO:
    def __init__(self, database):
        self.database = database
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def create_user(self, user_data):
        try:
            now = time.time()
            user_id = self.get_next_user_id()
            logger.info(f"[AUTH-DAO] [{now}] Creating new user: {user_data} user_id: {user_id}")
            
            self.cursor.execute("""
                INSERT INTO users (id, username, email, hashed_password, user_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?) """, 
            (user_id, user_data["username"], user_data["email"], user_data["password"], user_data["user_type"], now))
            self.connection.commit()

            return self.cursor.lastrowid, None
        
        except sqlite3.IntegrityError as e:
            self.connection.rollback()
            if "username" in str(e):
                return None, "Username already present"
            elif "email" in str(e):
                return None, "Email already present"
            return None, str(e)
        
        except Exception as e:
            self.connection.rollback()
            return None, str(e)
    def modify_user_account(self, new_user_info):
        try:
            self.cursor.execute("SELECT id FROM users WHERE id = ?", (new_user_info["user_id"],))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "User not found"
            
            # update
            self.cursor.execute("UPDATE users SET username = ? WHERE id = ?", (new_user_info["username"], new_user_info["user_id"]) )
            self.connection.commit()
            
            result = self.cursor.fetchone()
            
            return True, "Username updated successfully"
            
        except Exception as e:
            self.connection.rollback()
            print(f"[AUTH-DAO] Error updating user: {str(e)}")
            return False, "Internal server error"
        
    def delete_user(self, user_id):
        try:
            logger.info(f"[AUTH-DAO] Deleting user with ID: {user_id}")
            # transaction for all queries
            self.cursor.execute("BEGIN TRANSACTION")
            
            # delete refresh token
            self.cursor.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id,))
            
            # delete user
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            if self.cursor.rowcount == 0:
                self.connection.rollback()
                return False, "User not found"
            
            self.connection.commit()
            logger.info(f"[AUTH-DAO] Successfully deleted user with ID: {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"[AUTH-DAO] Error deleting user {user_id}: {str(e)}")
            self.connection.rollback()
            return False, f"Error deleting user: {str(e)}"
    
    def revoke_user_refresh_token(self, user_id):
        try:
            # check if token exists
            self.cursor.execute("SELECT COUNT(*) FROM refresh_tokens WHERE user_id = ?", (user_id,))
            count = self.cursor.fetchone()[0]
            logger.info(f"Found {count} tokens for user {user_id}")

            if count == 0:
                return False, "No active sessions found for user"

            # delete
            self.cursor.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id,))
            rows_deleted = self.cursor.rowcount
            logger.info(f"Deleted {rows_deleted} tokens for user {user_id}")
            
            self.connection.commit()
            return True, f"Successfully logged out and deleted {rows_deleted} active sessions"
        
        except Exception as e:
            logger.error(f"Error revoking refresh token for user {user_id}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def verify_credentials(self, username, password):
        try:
            self.cursor.execute(
                """SELECT id, username, hashed_password, user_type
                   FROM users WHERE username = ? """,
                (username,)
            )
            
            user = self.cursor.fetchone()
            
            if not user:
                logger.info(f"[AUTH-DAO] No user found for username: {username}")
                return None, "Invalid credentials"
            
            logger.debug(f"[AUTH-DAO] Found user record: {user}")
            user_id, username, db_password_hash, user_type = user
            
            
            try:
                # password and hash encoded
                password_bytes = password.encode('utf-8')
                hash_bytes = db_password_hash.encode('utf-8') if isinstance(db_password_hash, str) else db_password_hash
                
                # Verify password
                if bcrypt.checkpw(password_bytes, hash_bytes):
                    logger.info(f"[AUTH-DAO] Successful AUTH-DAOentication for user: {username}")
                    return {
                        "user_id": user_id,
                        "username": username,
                        "user_type": user_type
                    }, None
                else:
                    logger.info(f"[AUTH-DAO] Invalid password for user: {username}")
                    return None, "Invalid credentials"
                    
            except ValueError as ve:
                logger.error(f"[AUTH-DAO] Password verification error: {str(ve)}")
                return None, "Invalid password format"
                
        except Exception as e:
            logger.error(f"[AUTH-DAO] AUTH-DAOentication error: {str(e)}", exc_info=True)
            return None, f"AUTH-DAOentication error: {str(e)}"

    def store_refresh_token(self, token, user_id, expires_at):
        self.cursor.execute(
            "INSERT INTO refresh_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at)
        )
        self.connection.commit()

    def verify_refresh_token(self, token):
        self.cursor.execute(
            """SELECT user_id FROM refresh_tokens 
               WHERE token = ? AND expires_at > CURRENT_TIMESTAMP""",
            (token,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        try:
            self.cursor.execute(
                """SELECT id, username, email, user_type, created_at, last_login 
                   FROM users WHERE id = ?""", 
                (user_id,)
            )
            user = self.cursor.fetchone()
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "user_type": user[3],
                    "created_at": user[5],
                    "last_login": user[6]
                }, None
            return None, "User not found"
        except Exception as e:
            return None, str(e)
    
    def get_next_user_id(self):
        """Get next available user ID by checking both local and user service"""
        try:
            # get current user_id
            self.cursor.execute("SELECT MAX(id) FROM users")
            local_max = self.cursor.fetchone()[0] or 0
            
            # get max id from user
            try:
                response = requests.get("https://user:5000/max_user_id", timeout=10, verify=False) # nosec 
                if response.status_code == 200:
                    remote_max = response.json().get('max_id', 0)
                    return max(local_max, remote_max) + 1
            except:
                # to be safe about potential problems with user service
                return local_max + 100
                
        except Exception as e:
            logger.error(f"Error getting next user ID: {str(e)}")
            raise