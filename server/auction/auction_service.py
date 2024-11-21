import logging
from datetime import datetime
import time
from flask import app
from auctions_DAO import AuctionDAO

class AuctionService:
    def __init__(self, auction_dao):
        self.auction_dao = auction_dao

    def create_auction(self, piece_id, creator_id,start_price, end_date):
        """Creates a new auction with the given piece, start price, and end time."""
        try:
            self.auction_dao.create_auction(piece_id, creator_id,start_price, end_date)
            return {"message": "Auction created successfully."}
        except Exception as e:
            logging.error("Error in create_auction: %s", e)
            return {"error": "Failed to create auction due to an internal error."}

    def place_bid(self, auction_id, user_id, bid_amount):
        """Places a bid on an auction, ensuring it is higher than the current highest bid."""
        try:
            if not auction_id or not user_id or not bid_amount:
                raise ValueError("Auction ID, User ID, and Bid Amount are required.")

            if bid_amount <= 0:
                raise ValueError("Bid amount must be greater than zero.")

            highest_bid = self.auction_dao.get_highest_bid(auction_id)

            if highest_bid is not None:
                highest_bid_amount = highest_bid  
            else:
                highest_bid_amount = 0  

            if bid_amount <= highest_bid_amount:
                logging.warning("Invalid bid for auction %s: Bid amount must be greater than the current price of %s", auction_id, highest_bid_amount)
                return {"error": f"Bid amount must be greater than the current price of {highest_bid_amount}."}

            success = self.auction_dao.add_bid(auction_id, user_id, bid_amount)

            if not success:
                return {"error": "Failed to place bid due to internal auction system error."}

            success = self.auction_dao.update_current_price(auction_id, bid_amount)

            if not success:
                return {"error": "Failed to update current price after placing bid."}

            return {"message": "Bid placed successfully."}

        except ValueError as ve:
            logging.warning("Validation error placing bid for auction %s: %s", auction_id, ve)
            return {"error": str(ve)}
        except Exception as e:
            logging.error("Error placing bid for auction %s: %s", auction_id, e)
            return {"error": "Failed to place bid due to an internal error."}

    def close_auction(self, auction_id):
        """Closes an auction and awards the item to the highest bidder, if any."""
        try:
            highest_bid = self.auction_dao.get_highest_bid(auction_id)
            if highest_bid:
                winner_id = highest_bid[0]['user_id']
                piece_id = self.auction_dao.get_piece_id(auction_id)
                
                self.award_piece_to_winner(winner_id, piece_id)

            self.auction_dao.close_auction(auction_id)
            return {"message": "Auction closed and winner awarded."}
        except Exception as e:
            logging.error("Error closing auction %s: %s", auction_id, e)
            return {"error": "Failed to close auction due to an internal error."}

    #to implement
    def award_piece_to_winner(self, user_id, piece_id):
        """Awards the auction piece to the winning user (to be implemented based on system)."""
        try:
            logging.info("Awarding piece %s to user %s", piece_id, user_id)
        except Exception as e:
            logging.error("Error awarding piece %s to user %s: %s", piece_id, user_id, e)
            raise Exception("Failed to award piece to winner.")
        
    def close_expired_auctions(self):
        try:
            self.auction_dao.close_expired_auctions()
            return {"message": "Expired auctions closed successfully."}
        except Exception as e:
            logging.error("Error in closing expired auctions: %s", e)
            return {"error": "Failed to close expired auctions due to an internal error."}
        
    def get_active_auctions(self):
        current_timestamp = int(time.time())
        query = """
        SELECT auction_id, piece_id, creator_id, current_price, 
            start_date, status
        FROM auctions 
        WHERE status = 'running'
        """
        
        try:
            connection = self.auction_dao.connection
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            auctions = []
            for row in rows:
                auction = {
                    "auction_id": row[0],
                    "piece_id": row[1],
                    "creator_id": row[2],
                    "current_price": row[3],
                    "start_date": row[4],
                    "status": row[5],
                }
                auctions.append(auction)
            
            return auctions
        except Exception as e:
            app.logger.error(f"Error fetching active auctions: {str(e)}")
            return None
        
    def get_auction_info(self, auction_id):
        try:
            query = """
                SELECT auction_id, piece_id, creator_id, start_price, end_date, current_price 
                FROM auctions WHERE auction_id = ?
            """
            result = self.auction_dao.execute_query(query, (auction_id,))

            if not result:
                logging.error(f"No auction found for auction_id {auction_id}")
                return None

            if len(result) < 1 or len(result[0]) < 6:
                logging.error(f"Unexpected result format for auction_id {auction_id}: {result}")
                return None

            auction_info = {
                'auction_id': result[0][0],       
                'piece_id': result[0][1],        
                'creator_id': result[0][2],       
                'start_price': result[0][3],      
                'end_date': result[0][4],         
                'current_price': result[0][5]     
            }

            return auction_info

        except Exception as e:
            logging.error("Error retrieving auction info for auction_id %s: %s", auction_id, e)
            return None

    def get_past_auctions(self):
        current_timestamp = int(time.time())
        query = """
        SELECT auction_id, piece_id, creator_id, current_price, 
            start_date, status
        FROM auctions 
        WHERE status = 'ended' || status= 'cancelled'
        """
        
        try:
            connection = self.auction_dao.connection 
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            auctions = []
            for row in rows:
                auction = {
                    "auction_id": row[0],
                    "piece_id": row[1],
                    "creator_id": row[2],
                    "current_price": row[3],
                    "start_date": row[4],
                    "status": row[5],
                }
                auctions.append(auction)
            
            return auctions
        except Exception as e:
            app.logger.error(f"Error fetching active auctions: {str(e)}")
            return None



    def get_active_auctions_by_piece_id(self,piece_id):
        current_timestamp = int(time.time())
        query = """
        SELECT auction_id, piece_id, creator_id, current_price, 
            start_date, status
        FROM auctions 
        WHERE status = 'running' AND piece_id=?
        """
        
        try:
            connection = self.auction_dao.connection 
            cursor = connection.cursor()
            cursor.execute(query, (piece_id,))
            rows = cursor.fetchall()
            
            auctions = []
            for row in rows:
                auction = {
                    "auction_id": row[0],
                    "piece_id": row[1],
                    "creator_id": row[2],
                    "current_price": row[3],
                    "start_date": row[4],
                    "status": row[5],
                }
                auctions.append(auction)
            
            return auctions
        except Exception as e:
            app.logger.error(f"Error fetching active auctions: {str(e)}")
            return None
        
