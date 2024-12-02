import sqlite3
import time
import logging 
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class UsersDAO:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()
        
    def get_max_user_id(self):
        """Endpoint to support ID synchronization"""
        try:
            self.cursor.execute("SELECT MAX(user_id) FROM users")
            return self.cursor.fetchone()[0] or 0
        except Exception as e:
            raise
        
    # function to create a user account    
    def create_user_account(self, user_info):
        """
        returns a tuple: (user_id, error_message)
        """
        try:            
            # initial zero balance for tokens
            logging.info(f"DAO user INFO: {user_info}")
            
            self.cursor.execute("""
            INSERT INTO users (user_id, username, email, token_balance) 
            VALUES (?, ?, ?, ?)
            """, (user_info["user_id"], user_info["username"], user_info["email"], 0))
            
            self.connection.commit()
            
            # return user id
            logging.info(f"Successfully created user with id: {user_info['user_id']}")
            return user_info["user_id"], None
        
        # rollback errors for consistency
        except sqlite3.IntegrityError as e:
            self.connection.rollback()
            logging.error(f"Integrity error creating user: {str(e)}")
            if "UNIQUE constraint failed" in str(e):
                return None, "Username or email already exists"
            return None, str(e)
        
        except sqlite3.Error as e:
            self.connection.rollback()
            logging.error(f"Database error creating user: {str(e)}")
            return None, str(e)
        
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Unexpected error creating user: {str(e)}")
            return None, "Internal server error"
    
    # delete user, also called auth
    def delete_user_account(self, user_id):
        try:
            # Log initial check
            logger.info(f"[USER-DAO] Checking existence of user {user_id}")
            
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                logger.error(f"[USER-DAO] User {user_id} not found in database")
                return False, "User not found"
            
            logger.info(f"[USER-DAO] User {user_id} found, starting deletion process")
                
            # Begin transaction
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Delete with logging each step
            logger.info(f"[USER-DAO] Deleting from collection")
            self.cursor.execute("DELETE FROM collection WHERE user_id = ?", (user_id,))
            
            logger.info(f"[USER-DAO] Deleting from transactions")
            self.cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            
            logger.info(f"[USER-DAO] Deleting from logs")
            self.cursor.execute("DELETE FROM logs WHERE user_id = ?", (user_id,))
            
            logger.info(f"[USER-DAO] Deleting from users")
            self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            self.connection.commit()
            logger.info(f"[USER-DAO] Successfully deleted all data for user {user_id}")
            return True, "User deleted successfully"
            
        except sqlite3.Error as e:
            error_msg = f"DB error during user deletion: {str(e)}"
            logger.error(f"[USER-DAO] {error_msg}")
            self.connection.rollback()
            return False, error_msg
    
    # modify username
    def modify_user_account(self, new_user_info):
       
        try:
            # check if user exists
            self.cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?", 
                (new_user_info["user_id"],)
            )
            if not self.cursor.fetchone():
                return False, "User not found"
                
            # check if new username is already taken 
            self.cursor.execute(
                "SELECT user_id FROM users WHERE username = ? AND user_id != ?",
                (new_user_info["username"], new_user_info["user_id"])
            )
            if self.cursor.fetchone():
                return False, "Username already taken"
                
            # update
            self.cursor.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (new_user_info["username"], new_user_info["user_id"])
            )
            
            # check if update was made
            if self.cursor.rowcount == 0:
                self.connection.rollback()
                return False, "No changes made"
                
            self.connection.commit()
            return True, "Username updated successfully"
                
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error updating user: {str(e)}")
            return False, str(e) 
        
    def get_user_by_id(self, user_id):
        try:
            self.cursor.execute(
                "SELECT user_id, username, email FROM users WHERE user_id = ?", 
                (user_id,)
            )
            user = self.cursor.fetchone()
            if user:
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    def get_user_by_username(self, username):
        try:
            self.cursor.execute(
                "SELECT user_id, username, email FROM users WHERE username = ?", 
                (username,)
            )
            user = self.cursor.fetchone()
            if user:
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None
    
    ############### COLLECTION ###############    
    def get_user_gacha_collection(self, user_id):
        try:
            # check if user exists
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, [], "User does not exist"
            
            # get collection with explicit columns and JSON structure
            self.cursor.execute("""
                SELECT json_object(
                    'user_id', user_id,
                    'gacha_id', gacha_id,
                    'added_at', added_at
                ) as item
                FROM collection 
                WHERE user_id = ?
            """, (user_id,))
            
            # Convert each JSON string to a Python dict
            collection = [json.loads(row[0]) for row in self.cursor.fetchall()]
            
            return True, collection, "Success"
        
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            return False, [], "Error getting user collection"
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return False, [], "Error parsing collection data"
    
    def update_token_balance(self, user_id, increment_amount, is_refill):
        logging.info(f"Checking user balance for user_id: {user_id} increment: {increment_amount} is_refill: {is_refill}")
        
        self.cursor.execute("SELECT token_balance FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        logging.info(f"Query result: {result}")
        
        try:
            self.cursor.execute(" SELECT token_balance FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                logging.warning(f"User {user_id} not found in database")
                return 0, "User not found"
            
            present_token_balance = float(result[0])
            new_token_balance = present_token_balance + increment_amount
            
            if new_token_balance < 0:
                return 0, "Negative balance"
            
            # prevent game cheat
            if (is_refill and increment_amount > 50):
                return 0, "Refill balance must be below 50 to prevent cheating"
                
            # update
            self.cursor.execute("UPDATE users SET token_balance = ? WHERE user_id = ?", (new_token_balance, user_id) )
            
            # save transaction
            now = int(time.time())
            transaction_type = ""
            
            if (is_refill):
                transaction_type = "Refill"
            
            # user received auction amount
            if (increment_amount > 0):
                transaction_type = "Reward"
            # user won an auction
            else:
                transaction_type = "Purchase"
                
            
            self.cursor.execute("INSERT INTO transactions (user_id, amount, type, ts) VALUES (?,?,?,?)", (user_id, increment_amount, transaction_type, now))
            
            # Get new balance
            self.cursor.execute("SELECT token_balance FROM users WHERE user_id = ? ", (user_id,))
            
            self.connection.commit()
            result = self.cursor.fetchone()
            logging.info(f"Updated result: {result}")
            return new_token_balance, None
            
        except Exception as e:
            self.connection.rollback()
            print(f"Error updating {user_id} balance: {str(e)}")
            return None, "Internal server error"
    
    ##########################################################################################################################################################################
    ## ADMIN FUNCTION
     
    def admin_get_all_users(self):
        try:
            self.cursor.execute("SELECT user_id, username, email, token_balance FROM users")
            rows = self.cursor.fetchall()
            
            # convert to list
            users = []
            for row in rows:
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'token_balance': row[3]
                })
            
            return users, None
        
        except sqlite3.Error as e:
            logging.error(f"Error retrieving players: {str(e)}")
            return [], "Error retrieving players"
        
    def admin_get_user(self, user_id):
        try:
            self.cursor.execute("""
                SELECT user_id, username, email, token_balance FROM users WHERE user_id = ?
            """, (user_id,))
            
            rows = self.cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'token_balance': row[3]
                })
            
            return users, None
            
        except sqlite3.Error as e:
            logging.error(f"Error retrieving user {user_id}: {str(e)}")
            return [], "Error retrieving player"
    
    def admin_modify_user(self, user_id, new_username):
        try:
            user_data = {
                "user_id": user_id,
                "username": new_username
            }
            
            success, message = self.modify_user_account(user_data)
            return success, message
            
        except Exception as e:
            return False, "Failed to modify user"
        
    def admin_get_user_currency_tx(self, user_id):
        try:
            self.cursor.execute("""
                SELECT user_id, amount, type, ts FROM transactions WHERE user_id = ? ORDER BY ts DESC
            """, (user_id,))
            
            transactions = []
            for row in self.cursor.fetchall():
                transactions.append({
                    'user_id': row[0],
                    'amount': row[1],
                    'type': row[2],
                    'timestamp': row[3]
                })
            
            return transactions, None
        
        except sqlite3.Error as e:
            logging.error(f"Error retrieving transactions for user {user_id}: {str(e)}")
            return [], "Error retrieving transactions"

    def admin_get_user_market_hist(self, user_id):
        try:
            self.cursor.execute("""
                SELECT user_id, amount, type, ts FROM transactions WHERE user_id = ? AND type = 'auction' ORDER BY ts DESC
            """, (user_id,))  
            
            transactions = []
            for row in self.cursor.fetchall():
                transactions.append({
                    'user_id': row[0],
                    'amount': row[1],
                    'type': row[2],
                    'timestamp': row[3]
                })
            
            return transactions, None
        
        except sqlite3.Error as e:
            logging.error(f"Error retrieving auction history for user {user_id}: {str(e)}")
            return [], "Error retrieving transactions"
    
    # log action to the database
    def log_action(self, user_id, action, message):

        try:
            # log action
            now = int(time.time())
            
            self.cursor.execute(" INSERT INTO logs (ts, user_id, action, message) VALUES (?, ?, ?, ?)", (now, user_id, action, message))
            
            self.connection.commit()
            logger.info("[USER LOG] LOGGED ACTION")
            return True
        
        except sqlite3.Error:
            self.connection.rollback()
            return False
    
    # get latest logs
    def admin_get_latest_logs(self):
        try:
            # get logs up to 1 hour ago
            one_hour_ago_ts = int(time.time()) - 60 * 60
            #self.cursor.execute(" SELECT * FROM logs WHERE ts >= ?", (one_hour_ago_ts,))
            self.cursor.execute(" SELECT * FROM logs")
            results = self.cursor.fetchall()
            
            if not results:
                return [], "No logs in the last hour"
        
            # convert to dict
            logs = []
            for row in results:
                logs.append({
                    'log_id': row[0],
                    'timestamp': row[1],
                    'user_id': row[2],
                    'action': row[3],
                    'message': row[4]
                })
            
            return logs, None

        except sqlite3.Error:
            self.connection.rollback()
            return [], "Error retrieving logs"

    ################
    # auction
    # handle transaction outcome
    # Deduct money from winner
    # Give money to seller
    # update collection
    def execute_transaction(self, auction_data):
        try:
            winner_id = auction_data["winner_id"]
            final_price = auction_data["final_price"]
            piece_id = auction_data["piece_id"]
            seller_id = auction_data["seller_id"]

            # check if winner has balance
            self.cursor.execute(
                "SELECT token_balance FROM users WHERE user_id = ?",
                (winner_id,)
            )
            
            winner_balance = self.cursor.fetchone()
            if not winner_balance or winner_balance[0] < final_price:
                logger.info(f"[USER DAO] Insufficient winner balance")
                return False, "Insufficient balance"

            # subtract balance from winner
            self.cursor.execute(
                """UPDATE users 
                SET token_balance = token_balance - ? 
                WHERE user_id = ?""",
                (final_price, winner_id)
            )
            
            self.connection.commit()
            logger.info(f"[USER DAO] Deducted winner balance")
            
            # add token to seller
            self.cursor.execute(
                """UPDATE users 
                SET token_balance = token_balance + ? 
                WHERE user_id = ?""",
                (final_price, seller_id)
            )
            
            self.connection.commit()
            logger.info(f"[USER DAO] Added balance to seller")
            
            # add piece to winner collection
            self.cursor.execute(
                """INSERT INTO collection (user_id, gacha_id, added_at) 
                VALUES (?, ?, strftime('%s','now'))""",
                (winner_id, piece_id)
            )
            
            self.connection.commit()
            logger.info(f"[USER DAO] added piece to winner collection")
            
            # subtract piece from seller collection
            self.cursor.execute(
                """DELETE FROM collection 
                WHERE user_id = ? AND gacha_id = ?""",
                (seller_id, piece_id)
            )
            
            self.connection.commit()
            logger.info(f"[USER DAO] Deducted piece from seller")
            
            # log transactions for winner and seller
            # winner
            self.cursor.execute(
                """INSERT INTO transactions 
                (user_id, amount, type, ts) 
                VALUES (?, ?, 'auction', strftime('%s','now'))""",
                (winner_id, -final_price)
            )
            
            self.connection.commit()
            logger.info(f"[USER DAO] Deducted winner balance")
            
            # seller
            self.cursor.execute(
                """INSERT INTO transactions 
                (user_id, amount, type, ts) 
                VALUES (?, ?, 'auction', strftime('%s','now'))""",
                (seller_id, final_price)
            )
            
            # log the action
            self.cursor.execute(
                """INSERT INTO logs (ts, user_id, action, message)
                VALUES (strftime('%s','now'), ?, 'auction_complete', ?)""",
                (winner_id, piece_id, "Winner received gacha, seller deducted")
            )
            
            return True, ""
            
        except sqlite3.Error as e:
            return False, str(e)
    
    def get_user_balance(self, user_id):
        try:
            self.cursor.execute("SELECT token_balance FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return float(result[0]) if result else (0, "User not found")
        
        except Exception as e:
            return 0, str(e)

    # check if user has a piece
    def user_has_piece(self, user_id, piece_id):
        try:
            # check if user has piece
            self.cursor.execute(
                "SELECT added_at FROM collection WHERE user_id = ? AND gacha_id = ? ORDER BY added_at ASC LIMIT 1", 
                (user_id, piece_id)
            )
            result = self.cursor.fetchone()
            
            if not result:
                return False, None
                
            # if there is at least one piece remove the oldest for the auction
            self.cursor.execute(
                "DELETE FROM collection WHERE user_id = ? AND gacha_id = ? AND added_at = ?",
                (user_id, piece_id, result[0])
            )
            self.connection.commit()
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking/removing piece: {str(e)}")
            self.connection.rollback()
            return False, str(e)
        
    def update_user_collection(self, update_info):
        try:
            user_id = update_info.get("user_id")
            pieces_id = update_info.get("pieces_id", [])
            
            # check input validity
            if not user_id or not isinstance(pieces_id, list):
                return False, "Invalid input format"
                
            # check user existance
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not self.cursor.fetchone():
                return False, "User not found"
                
            # atomic transaction
            self.cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Insert new pieces
                current_time = int(time.time())
                
                for piece_id in pieces_id:
                    self.cursor.execute("""
                        INSERT INTO collection (user_id, gacha_id, added_at) 
                        VALUES (?, ?, ?)
                    """, (user_id, piece_id, current_time))
                
                self.connection.commit()
                return True, "Success"
                
            except sqlite3.Error as e:
                self.connection.rollback()
                return False, f"Database error: {str(e)}"
                
        except Exception as e:
            return False, "Internal server error"
        
    def close(self):
        self.connection.close()
        