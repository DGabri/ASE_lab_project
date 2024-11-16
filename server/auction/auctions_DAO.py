import logging
import sqlite3

class AuctionDAO:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def get_running_auctions(self):
        try:
            query = "SELECT * FROM auctions WHERE end_time > NOW() AND is_closed = FALSE"
            return self.execute_query(query)
        except Exception as e:
            logging.error("Error fetching running auctions: %s", e)
            return None

    def create_auction(self, piece_id, start_price, end_time):
        try:
            query = """
            INSERT INTO auctions (piece_id, start_price, end_time, is_closed)
            VALUES (%s, %s, %s, FALSE)
            """
            self.execute_query(query, (piece_id, start_price, end_time))
        except Exception as e:
            logging.error("Error creating auction: %s", e)

    def add_bid(self, auction_id, user_id, bid_amount):
        try:
            query = """
            INSERT INTO bids (auction_id, user_id, bid_amount)
            VALUES (%s, %s, %s)
            """
            self.execute_query(query, (auction_id, user_id, bid_amount))
        except Exception as e:
            logging.error("Error adding bid for auction %s: %s", auction_id, e)

    def close_auction(self, auction_id):
        try:
            query = "UPDATE auctions SET is_closed = TRUE WHERE auction_id = %s"
            self.execute_query(query, (auction_id,))
        except Exception as e:
            logging.error("Error closing auction %s: %s", auction_id, e)

    def get_highest_bid(self, auction_id):
        try:
            query = "SELECT * FROM bids WHERE auction_id = %s ORDER BY bid_amount DESC LIMIT 1"
            return self.execute_query(query, (auction_id,))
        except Exception as e:
            logging.error("Error fetching highest bid for auction %s: %s", auction_id, e)
            return None

    def execute_query(self, query, params=None):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logging.error("Database execution error: %s", e)
            return None
