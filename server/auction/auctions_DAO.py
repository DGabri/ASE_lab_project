import sqlite3
from typing import List, Optional, Dict

class AuctionDAO:
    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def create_auction(self, piece_id: int, creator_id: int, start_price: float, end_date: int) -> Optional[int]:
        """Creates a new auction and returns the auction ID."""
        try:
            query = """
            INSERT INTO auctions (piece_id, creator_id, start_price, current_price, end_date, status)
            VALUES (?, ?, ?, ?, ?, 'running')
            """
            self.cursor.execute(query, (piece_id, creator_id, start_price, start_price, end_date))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating auction: {e}")
            return None

    def add_bid(self, auction_id: int, user_id: int, bid_amount: float) -> bool:
        """Adds a bid to an auction if the bid is valid."""
        try:
            # Check if auction is running and the bid is higher than the current price
            current_price = self.get_current_price(auction_id)
            if current_price is not None and bid_amount > current_price:
                bid_query = """
                INSERT INTO bids (auction_id, user_id, bid_amount)
                VALUES (?, ?, ?)
                """
                self.cursor.execute(bid_query, (auction_id, user_id, bid_amount))
                self.update_current_price(auction_id, bid_amount)
                self.connection.commit()
                return True
            return False
        except sqlite3.Error as e:
            print(f"Error adding bid: {e}")
            return False

    def get_open_auctions(self) -> List[Dict]:
        """Retrieves all auctions that are currently running."""
        try:
            query = "SELECT * FROM auctions WHERE status = 'running'"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error fetching open auctions: {e}")
            return []

    def close_auction(self, auction_id: int, winner_id: Optional[int]) -> bool:
        """Closes an auction and assigns the winner."""
        try:
            query = """
            UPDATE auctions
            SET status = 'ended', winner_id = ?
            WHERE auction_id = ? AND status = 'running'
            """
            self.cursor.execute(query, (winner_id, auction_id))
            self.connection.commit()
            return self.cursor.rowcount > 0  # Returns True if the auction was updated
        except sqlite3.Error as e:
            print(f"Error closing auction: {e}")
            return False

    def get_current_price(self, auction_id: int) -> Optional[float]:
        """Retrieves the current highest bid for the auction."""
        try:
            query = "SELECT current_price FROM auctions WHERE auction_id = ?"
            self.cursor.execute(query, (auction_id,))
            result = self.cursor.fetchone()
            return result['current_price'] if result else None
        except sqlite3.Error as e:
            print(f"Error fetching current price: {e}")
            return None

    def update_current_price(self, auction_id: int, bid_amount: float) -> None:
        """Updates the current price of an auction."""
        try:
            query = """
            UPDATE auctions
            SET current_price = ?
            WHERE auction_id = ?
            """
            self.cursor.execute(query, (bid_amount, auction_id))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error updating current price: {e}")

    def get_auction_bids(self, auction_id: int) -> List[Dict]:
        """Retrieves all bids for a specific auction."""
        try:
            query = "SELECT * FROM bids WHERE auction_id = ? ORDER BY bid_date DESC"
            self.cursor.execute(query, (auction_id,))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error fetching bids for auction: {e}")
            return []

    def __del__(self):
        """Ensures the database connection is closed when the DAO is destroyed."""
        self.connection.close()
