import logging
from datetime import datetime
from auctions_DAO import AuctionDAO

class AuctionService:
    def __init__(self, dao: AuctionDAO):
        """
        Service layer that handles business logic for auctions.
        
        Args:
            dao (AuctionDAO): Data Access Object for interacting with the auction database.
        """
        self.auction_dao = dao
        self.logger = logging.getLogger(__name__)

    def create_auction(self, auction_data):
        """
        Creates a new auction.
        
        Args:
            auction_data (dict): Information about the auction (e.g., item_id, starting_bid, end_time).

        Returns:
            dict: Result of the operation or error message.
        """
        try:
            auction_id = self.auction_dao.create_auction(auction_data)
            return {"auction_id": auction_id}
        except Exception as e:
            self.logger.error(f"Error creating auction: {e}")
            return {"error": str(e)}

    def place_bid(self, bid_data):
        """
        Places a bid on an auction.

        Args:
            bid_data (dict): Bid information (e.g., auction_id, bidder_id, bid_amount).

        Returns:
            dict: Result of the operation or error message.
        """
        try:
            success = self.auction_dao.place_bid(bid_data)
            if success:
                return {"status": "Bid placed successfully"}
            else:
                return {"error": "Failed to place bid"}
        except Exception as e:
            self.logger.error(f"Error placing bid: {e}")
            return {"error": str(e)}

    def close_auction(self, auction_id):
        """
        Closes an auction and determines the winner.

        Args:
            auction_id (int): ID of the auction to close.

        Returns:
            dict: Result of the operation or error message.
        """
        try:
            result = self.auction_dao.close_auction(auction_id)
            if result:
                return {"status": "Auction closed successfully"}
            else:
                return {"error": "Failed to close auction"}
        except Exception as e:
            self.logger.error(f"Error closing auction {auction_id}: {e}")
            return {"error": str(e)}

    def get_auction(self, auction_id):
        """
        Retrieves auction details.

        Args:
            auction_id (int): ID of the auction to retrieve.

        Returns:
            dict: Auction details or error message.
        """
        try:
            auction = self.auction_dao.get_auction(auction_id)
            return {"auction": auction}
        except Exception as e:
            self.logger.error(f"Error retrieving auction {auction_id}: {e}")
            return {"error": str(e)}

    def get_active_auctions(self):
        """
        Retrieves all currently active auctions.

        Returns:
            dict: List of active auctions or error message.
        """
        try:
            active_auctions = self.auction_dao.get_active_auctions()
            return {"active_auctions": active_auctions}
        except Exception as e:
            self.logger.error("Error fetching active auctions: %s", e)
            return {"error": str(e)}

    def get_bid_history(self, auction_id):
        """
        Retrieves the bid history for a specific auction.

        Args:
            auction_id (int): ID of the auction.

        Returns:
            dict: Bid history or error message.
        """
        try:
            bid_history = self.auction_dao.get_bid_history(auction_id)
            return {"bid_history": bid_history}
        except Exception as e:
            self.logger.error(f"Error retrieving bid history for auction {auction_id}: {e}")
            return {"error": str(e)}
