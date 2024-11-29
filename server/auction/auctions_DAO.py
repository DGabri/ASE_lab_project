import sqlite3
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AuctionsDAO:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self._create_tables()
    
    def _create_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS auctions (
                auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                piece_id INTEGER NOT NULL,
                start_price REAL NOT NULL,
                current_price REAL NOT NULL,
                end_time INTEGER NOT NULL,
                status TEXT CHECK(status IN ('active', 'completed', 'cancelled')) NOT NULL,
                winner_id INTEGER,
                created_at INTEGER NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS bids (
                bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER NOT NULL,
                bidder_id INTEGER NOT NULL,
                bid_amount REAL NOT NULL,
                bid_time INTEGER NOT NULL,
                FOREIGN KEY (auction_id) REFERENCES auctions (auction_id)
            );
        """)
        self.connection.commit()
    
    def create_auction(self, seller_id, piece_id, start_price, duration_hours):
        """Create a new auction"""
        try:
            end_time = int(time.time()) + (duration_hours * 3600)
            self.cursor.execute("""
                INSERT INTO auctions (seller_id, piece_id, start_price, current_price, end_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?)
            """, (seller_id, piece_id, start_price, start_price, end_time, int(time.time())))
            self.connection.commit()
            
            return self.cursor.lastrowid, None
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error creating auction: {str(e)}")
            return None, str(e)

    def get_auction(self, auction_id):
        """Get auction details"""
        self.cursor.execute("""
            SELECT a.*, COUNT(b.bid_id) as bid_count FROM auctions a LEFT JOIN bids b ON a.auction_id = b.auction_id WHERE a.auction_id = ? GROUP BY a.auction_id
        """, (auction_id,))
        
        return self.cursor.fetchone()

    def place_bid(self, auction_id, bidder_id, bid_amount):
        """Place a bid on an auction"""
        try:
            # Check if auction exists and is active
            auction = self.get_auction(auction_id)
            if not auction:
                return None, "Auction not found"
            if auction[6] != 'active':
                return None, "Auction is not active"
            if auction[5] < time.time():
                return None, "Auction has ended"
            if bid_amount <= auction[4]:  # current_price
                return None, "Bid amount must be higher than current price"
            
            # Place bid
            self.cursor.execute("""
                INSERT INTO bids (auction_id, bidder_id, bid_amount, bid_time) VALUES (?, ?, ?, ?)
            """, (auction_id, bidder_id, bid_amount, int(time.time())))
            
            # Update auction current price
            self.cursor.execute("""
                UPDATE auctions SET current_price = ? WHERE auction_id = ?
            """, (bid_amount, auction_id))
            
            self.connection.commit()
            return True, None
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error placing bid: {str(e)}")
            return None, str(e)

    def get_active_auctions(self):
        query = """
            SELECT a.*, COUNT(b.bid_id) as bid_count 
            FROM auctions a 
            LEFT JOIN bids b ON a.auction_id = b.auction_id 
            WHERE a.status = 'active' AND a.end_time > ?
        """
        params = [int(time.time())]
        
        query += " GROUP BY a.auction_id"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def get_active_auctions_by_piece_id(self, piece_id):
        query = """
            SELECT a.*, COUNT(b.bid_id) as bid_count 
            FROM auctions a 
            LEFT JOIN bids b ON a.auction_id = b.auction_id 
            WHERE a.status = 'active' AND a.end_time > ? AND a.piece_id = ?
        """
        params = [int(time.time()), piece_id]
        
        query += " GROUP BY a.auction_id"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_auction_history(self):
        """Get completed auctions history"""
        query = """
            SELECT a.*, COUNT(b.bid_id) as bid_count 
            FROM auctions a 
            LEFT JOIN bids b ON a.auction_id = b.auction_id
            WHERE a.status = 'completed'
            GROUP BY a.auction_id
        """
        self.cursor.execute(query)
        data = self.cursor.fetchall()

        return data

    def modify_auction(self, auction_id, seller_id, updates):
        """Modify auction end time"""
        try:
            auction = self.get_auction(auction_id)
            if not auction:
                return None, "Auction not found"
            if auction[1] != seller_id:
                return None, "Not authorized to modify this auction"
            if auction[6] != 'active':
                return None, "Cannot modify completed or cancelled auction"
            
            if 'end_time' not in updates:
                return None, "End time must be provided"
                
            self.cursor.execute("""
                UPDATE auctions 
                SET end_time = ?
                WHERE auction_id = ?
            """, (updates['end_time'], auction_id))
            
            self.connection.commit()
            return True, None
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error modifying auction: {str(e)}")
            return None, str(e)
        
    # ended auctions that have to be processed    
    def get_ended_auctions(self):
        
        query = """
            SELECT 
                a.auction_id, a.seller_id, a.piece_id, a.start_price,
                a.current_price, a.end_time, a.status, a.winner_id, 
                a.created_at, COUNT(b.bid_id) as bid_count
            FROM auctions a
            LEFT JOIN bids b ON a.auction_id = b.auction_id
            WHERE a.status = 'active' 
            AND a.end_time < ?
            GROUP BY 
                a.auction_id, a.seller_id, a.piece_id,
                a.start_price, a.current_price, a.end_time, a.status,
                a.winner_id, a.created_at
        """
        
        current_time = int(time.time())
        self.cursor.execute(query, (current_time,))
        raw_data = self.cursor.fetchall()
        
        formatted_auctions = []
        for auction in raw_data:
            formatted_auction = {
                'auction_id': auction[0],
                'seller_id': auction[1],
                'piece_id': auction[2],
                'start_price': auction[3],
                'final_price': auction[4],
                'end_time': auction[5],
                'status': auction[6],
                'winner_id': auction[7],
                'created_at': auction[8],
                'bid_count': auction[9]
            }
            formatted_auctions.append(formatted_auction)

        logger.info(f"[AUCTION HISTORY] Retrieved {len(formatted_auctions)} ended auctions pending completion")
        return formatted_auctions

    # get closed auctions    
    def get_completed_auctions(self):

        query = """
            SELECT 
                a.auction_id, a.seller_id, a.piece_id, a.start_price,
                a.current_price, a.end_time, a.status, a.winner_id, 
                a.created_at, COUNT(b.bid_id) as bid_count
            FROM auctions a
            LEFT JOIN bids b ON a.auction_id = b.auction_id
            WHERE a.status = 'completed'
            GROUP BY 
                a.auction_id, a.seller_id, a.piece_id,
                a.start_price, a.current_price, a.end_time, a.status,
                a.winner_id, a.created_at
        """
        
        self.cursor.execute(query)
        raw_data = self.cursor.fetchall()
        
        formatted_auctions = []
        for auction in raw_data:
            formatted_auction = {
                'auction_id': auction[0],
                'seller_id': auction[1],
                'piece_id': auction[2],
                'start_price': auction[3],
                'final_price': auction[4],
                'end_time': auction[5],
                'status': auction[6],
                'winner_id': auction[7],
                'created_at': auction[8],
                'bid_count': auction[9]
            }
            formatted_auctions.append(formatted_auction)

        logger.info(f"[AUCTION HISTORY] Retrieved {len(formatted_auctions)} completed auctions")
        return formatted_auctions

    def complete_auction(self, auction_id):
        '''Complete an auction and handle winner determination'''
        try:
            self.cursor.execute('''
                SELECT piece_id, seller_id 
                FROM auctions 
                WHERE auction_id = ?
            ''', (auction_id,))
            auction_details = self.cursor.fetchone()
            
            if not auction_details:
                return None, "Auction not found"
                
            piece_id, seller_id = auction_details
            logging.info(f"[COMPLETED AUCTION] Piece_id: {piece_id} seller_id: {seller_id}")

            # Get highest bid
            self.cursor.execute('''
                SELECT bidder_id, bid_amount
                FROM bids 
                WHERE auction_id = ? 
                ORDER BY bid_amount DESC 
                LIMIT 1
            ''', (auction_id,))
            
            highest_bid = self.cursor.fetchone()
            logging.info(f"[COMPLETED AUCTION] highest bid: {highest_bid}")
            
            if highest_bid:
                # Update auction with winner
                winner_id, final_price = highest_bid
                self.cursor.execute('''
                    UPDATE auctions 
                    SET status = 'completed',
                        winner_id = ?,
                        current_price = ?
                    WHERE auction_id = ?
                ''', (winner_id, final_price, auction_id))
                
                result = {
                    'winner_id': winner_id,
                    'piece_id': piece_id,
                    'final_price': final_price,
                    'seller_id': seller_id
                }
            else:
                # Delete auction with no bids
                self.cursor.execute('DELETE FROM auctions WHERE auction_id = ?', (auction_id,))
                result = {
                    'winner_id': None,
                    'piece_id': piece_id,
                    'final_price': None,
                    'seller_id': seller_id
                }
            
            self.connection.commit()
            return result, None
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error completing auction: {str(e)}")
            return None, str(e)