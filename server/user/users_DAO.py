import sqlite3
import time
import logging 
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
        
    def get_user_account(self, user_info):
        try:
            # initial zero balance for tokens
            self.cursor.execute("""
            INSERT INTO users (email, username, token_balance) VALUES (%s, %s, %s) """,
            (user_info["email"], user_info["username"], 0))
    
            self.connection.commit()
            return self.cursor.lastrowid 

        # rollback errors for consistency
        except sqlite3.Error:
            self.connection.rollback()
            return None
    
    def create_user_account(self, user_info):
        """
        returns a tuple: (user_id, error_message)
        """
        try:            
            # initial zero balance for tokens
            logging.info(f"DAO user INFO: {user_info}")
            
            self.cursor.execute("""
            INSERT INTO users (id, username, email, token_balance) 
            VALUES (?, ?, ?, ?)
            """, (user_info["user_id"], user_info["username"], user_info["email"], 0))
            
            # Important: Commit the transaction
            self.connection.commit()
            
            # Return the user_id we just inserted
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
    
    ## REMOVE, PUT IN AUTH
    def delete_user_account(self, user_id):

        try:
            self.cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "User not found"
            
            # delete user colelction
            self.cursor.execute("DELETE FROM collection WHERE user_id = ? ", (user_id,))
            
            # delete user transactions
            self.cursor.execute("DELETE FROM transactions WHERE user_id = ? ", (user_id,))
            
            # delete user logs
            self.cursor.execute("DELETE FROM logs WHERE user_id = ? ", (user_id,))
            
            # delte user from users db
            self.cursor.execute("DELETE FROM users WHERE id = ? ", (user_id,))
            
            self.connection.commit()
            return True, "User deleted correctly"
        
        except sqlite3.Error as e:
            print(f"DB error: {str(e)}")

            self.connection.rollback()
            return False, e
    
    ## ALSO CALL AUTH FOR CONSISTENCY
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
            print(f"Error updating user: {str(e)}")
            return False, "Internal server error"
    
    def get_user_gacha_collection(self, user_id):

        try:
            # check if user exists
            self.cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, [], "User does not exist"
            
            # get collection
            self.cursor.execute(" SELECT * FROM collection WHERE user_id = ? ", (user_id,))
            return True, [dict(row) for row in self.cursor.fetchall()], "Success"
        
        except sqlite3.Error:
            return False, [], "Error getting user collection"
    
    def update_token_balance(self, user_id, increment_amount, is_refill):
        """
        returns a tuple: (user_balance, error_message)
        """
        logging.info(f"Checking user balance for user_id: {user_id} increment: {increment_amount} is_refill: {is_refill}")
        
        self.cursor.execute("SELECT token_balance FROM users WHERE id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        logging.info(f"Query result: {result}")
        
        try:
            self.cursor.execute(" SELECT token_balance FROM users WHERE id = ?", (user_id,))
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
            self.cursor.execute("UPDATE users SET token_balance = ? WHERE id = ?", (new_token_balance, user_id) )
            
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
            self.cursor.execute("SELECT token_balance FROM users WHERE id = ? ", (user_id,))
            
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
            
            self.cursor.execute("SELECT * FROM users")
            return [dict(row) for row in self.cursor.fetchall()]
        
        except sqlite3.Error:
            return []
    
    # RIVEDERE
    def admin_modify_user(self, user_id, updates):
        pass
        
    def admin_get_user_currency_tx(self, user_id):
        
        try:
            self.cursor.execute(" SELECT * FROM transactions WHERE user_id = ? ORDER BY ts DESC ", (user_id))
            return [dict(row) for row in self.cursor.fetchall()]
        
        except sqlite3.Error:
            return []
    
    def admin_get_user_market_hist(self, user_id):
        
        try:
            self.cursor.execute("SELECT * FROM transactions WHERE user_id = ? AND type = 'auction' ORDER BY ts DESC", (user_id))
            return [dict(row) for row in self.cursor.fetchall()]
        
        except sqlite3.Error:
            return []
    
    def admin_set_user_account_status(self, user_id, user_account_status):
        
        try:
            self.cursor.execute(" SELECT token_balance FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "User not found"
            
            self.cursor.execute(" UPDATE users SET account_status = ? WHERE id = ? ", (user_account_status, user_id))
            
            # log action
            now = int(time.time())
            action = "User ban" if user_account_status == 0 else "User unban"
            action_log = "banned" if user_account_status == 0 else "unbanned"
            
            self.cursor.execute("INSERT INTO logs (ts, user_id, action, message) VALUES (?,?,?,?)", (now, user_id, action, f"User: {user_id} banned"))
            
            self.connection.commit()
            return True, f"User: {user_id} {action_log}"
        
        except sqlite3.Error:
            self.connection.rollback()
            return False

    def log_action(self, user_id, action, message):

        try:
            self.cursor.execute(" UPDATE users SET account_status = 0 WHERE id = ?", (user_id))
            
            # log action
            now = int(time.time())
            
            self.cursor.execute(" INSERT INTO logs (ts, user_id, action, message) VALUES (?, ?, ?, ?)", (now, user_id, action, message))
            
            self.connection.commit()
            return True
        
        except sqlite3.Error:
            self.connection.rollback()
            return False
                
    def admin_get_last_5_min_logs(self):
        
        try:
            five_minutes_ago = int(time.time()) - 60 * 5
            self.cursor.execute(" SELECT * FROM logs WHERE ts >= ?", (five_minutes_ago,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "No logs in the last 5 minutes"
        
            return True, result
        
        except sqlite3.Error:
            self.connection.rollback()
            return False
        
    def close(self):
        self.connection.close()
