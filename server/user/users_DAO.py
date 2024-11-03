import sqlite3
import time

class UsersDAO:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
    
    def create_user_account(self, user_info):
        
        try:
            now = int(time.time())
            
            # initial zero balance for tokens
            # account status set to active
            self.cursor.execute(f"""
                INSERT INTO users (email,     username,                type, created_at, token_balance, account_status)
                VALUES ({user_info["email"]}, {user_info["username"]}, 1,    {now},      0,              1)
            """)
            
            self.connection.commit()
            return self.cursor.lastrowid
        
        # rollback errors for consistency
        except sqlite3.Error:
            self.connection.rollback()
            return None
    
    def delete_user_account(self, user_id):

        try:
                    
            # delete user colelction
            self.cursor.execute(f"DELETE FROM collection WHERE user_id = {user_id}")
            
            # delete user transactions
            self.cursor.execute(f"DELETE FROM transactions WHERE user_id = {user_id}")
            
            # delete user logs
            self.cursor.execute(f"DELETE FROM logs WHERE user_id = {user_id}")
            
            # delte user from users db
            self.cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
            
            self.connection.commit()
            return True
        
        except sqlite3.Error:
            self.connection.rollback()
            return False
    
    def modify_user_account(self, new_user_info):
        pass
    
    def get_user_gacha_collection(self, user_id):

        try:
        
            self.cursor.execute(f""" SELECT * FROM collection WHERE user_id = {user_id} """)
            return [dict(row) for row in self.cursor.fetchall()]
        
        except sqlite3.Error:
            return []
    
    def update_token_balance(self, user_id, increment_amount, is_refill):

        try:
           
            # update
            self.cursor.execute(f"""UPDATE users SET token_balance = token_balance + {increment_amount} WHERE id = {user_id} """)
            
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
                
            
            self.cursor.execute(f""" INSERT INTO transactions (user_id, amount, type, ts) VALUES ({user_id}, {increment_amount}, {transaction_type}, {now}) """)
            
            # Get new balance
            self.cursor.execute(f""" SELECT token_balance FROM users WHERE id = {user_id} """)
            
            self.connection.commit()
            result = self.cursor.fetchone()
            
            return result["token_balance"] if result else None
            
        except sqlite3.Error:
            self.connection.rollback()
            return None
    
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
            self.cursor.execute(f""" SELECT * FROM transactions WHERE user_id = {user_id} ORDER BY ts DESC """)
            return [dict(row) for row in self.cursor.fetchall()]
        
        except sqlite3.Error:
            return []
    
    def admin_get_user_market_hist(self, user_id):
        
        try:
            self.cursor.execute(f""" SELECT * FROM transactions WHERE user_id = {user_id} AND type = "auction" ORDER BY ts DESC""")
            return [dict(row) for row in self.cursor.fetchall()]
        
        except sqlite3.Error:
            return []
    
    def admin_ban_user(self, user_id):
        
        try:
            self.cursor.execute(f""" UPDATE users SET account_status = 0 WHERE id = {user_id} """)
            
            # log action
            now = int(time.time())
            
            self.cursor.execute(f""" INSERT INTO logs (ts, user_id, action, message) VALUES ({now}, {user_id}, "user_ban", "User: {user_id} banned") """)
            
            self.connection.commit()
            return True
        
        except sqlite3.Error:
            self.connection.rollback()
            return False

    def log_action(self, user_id, action, message):

        try:
            self.cursor.execute(f""" UPDATE users SET account_status = 0 WHERE id = {user_id} """)
            
            # log action
            now = int(time.time())
            
            self.cursor.execute(f""" INSERT INTO logs (ts, user_id, action, message) VALUES ({now}, {user_id}, "user_ban", "User: {user_id} banned") """)
            
            self.connection.commit()
            return True
        
        except sqlite3.Error:
            self.connection.rollback()
            return False
                
    def close(self):
        self.connection.close()
