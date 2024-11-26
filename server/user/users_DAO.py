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
    
    # function to create a user account    
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
    
    # delete user, also called auth
    def delete_user_account(self, user_id):
        """
        returns a tuple: (success_boolean, error_message)
        """
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
    
    # modify username
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
            return [dict(row) for row in self.cursor.fetchall()], None
        
        except sqlite3.Error:
            return [], "error retrieving players"
        
    def admin_get_user(self, user_id):
        try:
            self.cursor.execute("SELECT * FROM users where id = ?", (user_id))
            return [dict(row) for row in self.cursor.fetchall()], None
        
        except sqlite3.Error:
            return [], "error retrieving player"
    
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
            self.cursor.execute(" SELECT * FROM transactions WHERE user_id = ? ORDER BY ts DESC ", (user_id))
            return [dict(row) for row in self.cursor.fetchall()], False
        
        except sqlite3.Error:
            return [], "Error retrieving transactions"
    
    def admin_get_user_market_hist(self, user_id):
        
        try:
            self.cursor.execute("SELECT * FROM transactions WHERE user_id = ? AND type = 'auction' ORDER BY ts DESC", (user_id))
            return [dict(row) for row in self.cursor.fetchall()], None
        
        except sqlite3.Error:
            return [], "Error retrieving transactions"
    
    # log action to the database
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
    
    # get latest logs
    def admin_get_latest_logs(self):
        try:
            # get logs up to 1 hour ago
            one_hour_ago_ts = int(time.time()) - 60 * 60
            self.cursor.execute(" SELECT * FROM logs WHERE ts >= ?", (one_hour_ago_ts,))
            result = self.cursor.fetchone()
            
            if not result:
                return [], "No logs in the last 5 minutes"
        
            return result, False
        
        except sqlite3.Error:
            self.connection.rollback()
            return [], "Error retrieving logs"

    def handle_auction_win(self, winner_id, gacha_id, bid_amount, seller_id=None):
        """
        Handle auction win: transfer gacha to winner, deduct bid amount, pay seller
        
        Args:
            winner_id (int): ID of the winning bidder
            gacha_id (int): ID of the gacha being auctioned
            bid_amount (float): Final winning bid amount
            seller_id (int, optional): ID of the seller (None for system auctions)
        
        Returns:
            tuple: (success, error_message)
        """
        try:          
            # add gacha to winner collection
            now = int(time.time())
            self.cursor.execute("""
                INSERT INTO collection (user_id, gacha_id, added_at) VALUES (?, ?, ?)
            """, (winner_id, gacha_id, now))
            
            # remove coin from winner
            winner_balance, err = self.update_token_balance(winner_id, -bid_amount, False)
            if err:

                return False, f"Failed to update winner balance: {err}"
                
            # add token to player if the auction is not a system auction
            if seller_id:
                seller_balance, err = self.update_token_balance(seller_id, bid_amount, False)
                
                if err:
                    return False, f"Failed to update seller balance: {err}"
            
            return True, None
            
        except sqlite3.Error as e:
            return False, "Database error handling auction win"

    def handle_auction_loss(self, bidder_id, bid_amount):
        """
        Refund bid token amount to losing bidder
            
        Args:
            bidder_id (int): ID of the losing bidder
            bid_amount (float): Bid amount to refund
        """
        try:
            # refund bid amount to loser
            new_balance, err = self.update_token_balance(bidder_id, bid_amount, False)
            
            if err:
                return False, f"Failed to refund bid: {err}"
                
            return True, None
            
        except sqlite3.Error as e:
            logging.error(f"Database error in handle_auction_loss: {str(e)}")
            return False, "Database error"

    def process_auction_outcome(self, auction_data):
        """
        handle auction win and loss
        
        auction_data: dict containing:
            winner_id: ID of winning bidder
            gacha_id: ID of auctioned gacha
            winning_bid: Final winning bid amount
            seller_id: ID of seller (optional)
            losing_bids: List of tuples (bidder_id, bid_amount) for losing bids
    
        """
        try:
            # handle winner
            success, error = self.handle_auction_win(
                auction_data['winner_id'],
                auction_data['gacha_id'],
                auction_data['winning_bid'],
                auction_data.get('seller_id')  # optional, could not be defined
            )
            
            if not success:
                return False, f"Failed to process winner: {error}"
                
            # manage all losing bids
            for bidder_id, bid_amount in auction_data['losing_bids']:
                success, error = self.handle_auction_loss(bidder_id, bid_amount)
                if not success:
                    logging.error(f"Failed to process refund for bidder {bidder_id}: {error}")
                    
            return True, None
            
        except Exception as e:
            return False, "Internal error processing auction"
    
    def close(self):
        self.connection.close()