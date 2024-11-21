from datetime import datetime
import logging
import sqlite3
import time

class AuctionDAO:
    def __init__(self, database, scheme):
        self.connection = sqlite3.connect(database, check_same_thread = False)
        self.cursor = self.connection.cursor()

        with open(scheme, 'r') as sql_file:
            sql_script = sql_file.read()

        try:
            with self.connection:
                self.cursor.executescript(sql_script)
        except sqlite3.Error as e:
            print(f"Cannot initialize auction DAO: {e}")

    def get_running_auctions(self):
        try:
            query = "SELECT * FROM auctions WHERE end_date > NOW() AND status = running"
            return self.execute_query(query)
        except Exception as e:
            logging.error("Error fetching running auctions: %s", e)
            return None

    def create_auction(self, piece_id, creator_id, start_price, end_date):

        if start_price <= 0:
            return {"error": "Start price must be greater than zero."}, 400

        try:
            query = """
            INSERT INTO auctions (piece_id, creator_id, start_price, current_price, start_date, end_date, status)
            VALUES (?, ?, ?, ?, strftime('%s', 'now'), ?, 'running')
            """
            self.execute_query(query, (piece_id, creator_id, start_price, None, end_date))

            return {"status": "Auction created successfully"}
        
        except Exception as e:
            logging.error("Error creating auction: %s", e)
            return {"error": "Failed to create auction"}, 500


    def update_current_price(self, auction_id, bid_amount):
        try:
            query = "UPDATE auctions SET current_price = ? WHERE auction_id = ?"
            self.execute_query(query, (bid_amount, auction_id))
            return True
        except Exception as e:
            logging.error(f"Error updating current price for auction {auction_id}: {e}")
            return False


    def add_bid(self, auction_id, user_id, bid_amount):
        try:
            current_price_query = """
            SELECT current_price 
            FROM auctions 
            WHERE auction_id = ?
            """
            connection = self.connection 
            cursor = connection.cursor()
            cursor.execute(current_price_query, (auction_id,))
            result = cursor.fetchone()

            if result is None:
                raise ValueError(f"Auction with ID {auction_id} does not exist.")

            
            current_price = result[0]  

            if current_price is None:
                current_price = 0

            if bid_amount <= current_price:
                logging.warning(f"Bid amount {bid_amount} is not greater than the current price {current_price}")
                return False

            insert_bid_query = """
            INSERT INTO bids (auction_id, user_id, bid_amount)
            VALUES (?, ?, ?)
            """
            cursor.execute(insert_bid_query, (auction_id, user_id, bid_amount))

            update_price_query = """
            UPDATE auctions
            SET current_price = ?
            WHERE auction_id = ?
            """
            cursor.execute(update_price_query, (bid_amount, auction_id))

            connection.commit()

            logging.info(f"Bid added successfully for auction {auction_id} by user {user_id}.")
            return True

        except Exception as e:
            logging.error(f"Error adding bid for auction {auction_id}: {e}")
            return False

    def close_auction(self, auction_id):
        try:
            query = "UPDATE auctions SET status = 'ended' WHERE auction_id = ?"
            self.execute_query(query, (auction_id,))
        except Exception as e:
            logging.error("Error closing auction %s: %s", auction_id, e)

    def get_highest_bid(self, auction_id):
            query = "SELECT bid_amount FROM bids WHERE auction_id = ? ORDER BY bid_amount DESC LIMIT 1"
            result = self.execute_query(query, (auction_id,))

            if result:
                return result[0][0]  
            return None



    def execute_query(self, query, params=None):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()  # Commetti esplicitamente la transazione
                logging.info(f"Executed query: {query} with params {params}")
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error("Database error: %s", e)
            raise


    def get_expired_auctions(self):
        """
        Retrieves all expired auctions where the end date has passed and the status is still 'running'.
        """
        query = """
        SELECT auction_id, piece_id, creator_id, current_price, 
            start_date, end_date, status
        FROM auctions 
        WHERE end_date <= strftime('%s', 'now') AND status = 'running'
        """
        try:
            # Ottieni la connessione al database
            connection = self.connection  
            cursor = connection.cursor()
            
            # Esegui la query
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Costruisci la lista di aste scadute
            expired_auctions = []
            for row in rows:
                auction = {
                    "auction_id": row[0],
                    "piece_id": row[1],
                    "creator_id": row[2],
                    "current_price": row[3],
                    "start_date": row[4],
                    "end_date": row[5],
                    "status": row[6],
                }
                expired_auctions.append(auction)
            
            return expired_auctions

        except Exception as e:
            logging.error("Error fetching expired auctions: %s", e)
            # Puoi decidere di sollevare un'eccezione o restituire un valore vuoto
            raise RuntimeError("Failed to fetch expired auctions") from e



    def close_expired_auctions(self):
        try:
            expired_auctions = self.get_expired_auctions()  # Verifica se ci sono aste scadute
            if expired_auctions is None:
                logging.warning("No expired auctions found.")
                return {"message": "No expired auctions found."}

            for auction in expired_auctions:
                # Gestisci la chiusura dell'asta
                self.close_auction(auction['auction_id'])
            
            return {"message": "Expired auctions closed successfully."}
        except Exception as e:
            logging.error("Error in closing expired auctions: %s", e)
            return {"error": "Failed to close expired auctions due to an internal error."}


    # Funzione per determinare il vincitore
    def determine_winner(self, auction_id):
        query = """
        SELECT user_id, bid_amount FROM bids
        WHERE auction_id = ?
        ORDER BY bid_amount DESC LIMIT 1
        """
        result = self.execute_query(query, (auction_id,))
        if result:
            winner_id, winning_bid = result[0]
            logging.info(f"Vincitore dell'asta {auction_id}: User {winner_id} con un'offerta di {winning_bid}")
        else:
            logging.info(f"Asta {auction_id} chiusa senza offerte.")

    
    def get_active_auctions(self):
        current_timestamp = int(datetime.now().timestamp())
        query = """
        SELECT auction_id, piece_id, creator_id, start_price, current_price, 
               start_date, end_date, status, winner_id 
        FROM auctions 
        WHERE status = 'running'
        """

        try:
            cursor = self.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            auctions = []
            for row in rows:
                auction = {
                    "auction_id": row[0],
                    "piece_id": row[1],
                    "creator_id": row[2],
                    "start_price": row[3],
                    "current_price": row[4],
                    "start_date": row[5],
                    "end_date": row[6],
                    "status": row[7],
                    "winner_id": row[8]
                }
                auctions.append(auction)
            
            
            return auctions
        except Exception as e:
            raise Exception(f"Error fetching active auctions: {str(e)}")
        
    def update_status_to_ended(self, auction_id):
        query = """
        UPDATE auctions 
        SET status = 'ended'
        WHERE auction_id = %s
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (auction_id,))
            connection.commit()
        except Exception as e:
            logging.error("Error updating auction status to ended for auction_id %s: %s", auction_id, e)
            raise

    def get_bidding_history(self, auction_id):
        query = """
        SELECT bid_id, user_id, bid_amount, bid_date
        FROM bids
        WHERE auction_id = ?
        ORDER BY bid_date ASC
        """
        result = self.execute_query(query, (auction_id,))
        
        if result:
            return result
        return []
