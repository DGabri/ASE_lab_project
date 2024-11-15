import threading
import time
import logging
from datetime import datetime
from auction_service import AuctionService
from auctions_DAO import AuctionDAO

# Set up logging for the worker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class AuctionWorker:
    def __init__(self, check_interval=60):
        """
        Worker that periodically checks for auctions to close.
        
        Args:
            check_interval (int): Time interval in seconds between checks for expired auctions.
        """
        self.check_interval = check_interval  # Interval for checking auctions (default: 60 seconds)
        self.running = False  # Worker state flag
        self.auction_service = AuctionService(AuctionDAO())  # Initialize AuctionService with DAO

    def start(self):
        """Start the auction worker thread."""
        self.running = True
        self.worker_thread = threading.Thread(target=self.run, daemon=True)
        self.worker_thread.start()
        logging.info("Auction worker started.")

    def stop(self):
        """Stop the auction worker."""
        self.running = False
        logging.info("Stopping auction worker...")

    def run(self):
        """Main worker loop that periodically checks for auctions to close."""
        while self.running:
            try:
                logging.info("Checking for expired auctions...")
                expired_auctions = self.auction_service.auction_dao.get_expired_auctions()

                for auction in expired_auctions:
                    auction_id = auction['auction_id']
                    logging.info("Closing auction ID %s", auction_id)
                    result = self.auction_service.close_auction(auction_id)

                    if "error" in result:
                        logging.error("Error closing auction %s: %s", auction_id, result["error"])
                    else:
                        logging.info("Auction %s closed successfully", auction_id)

            except Exception as e:
                logging.error("Error in auction worker loop: %s", e)

            # Wait for the specified interval before the next check
            time.sleep(self.check_interval)

if __name__ == "__main__":
    # Start the auction worker
    worker = AuctionWorker(check_interval=60)  # Adjust interval as needed
    worker.start()

    # Keep the main thread alive to allow the worker to run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()
        logging.info("Auction worker has been stopped.")
