import logging
from datetime import datetime
import time
from flask import app
import requests

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
                    creator_id= highest_bid[0]['creator_id']
                    piece_id = self.auction_dao.get_piece_id(auction_id)

                    # Call the method to award the piece and update balances and collection
                    self.award_piece_to_winner(winner_id, piece_id, highest_bid[0]['bid_amount'],creator_id)

                self.auction_dao.close_auction(auction_id)
                return {"message": "Auction closed and winner awarded."}
            except Exception as e:
                logging.error("Error closing auction %s: %s", auction_id, e)
                return {"error": "Failed to close auction due to an internal error."}

    def award_piece_to_winner(self, user_id, piece_id, highest_bid, creator_id):
        """
        Awards the auction piece to the winning user and updates their balance through the API.
        The creator of the piece receives a percentage of the highest bid.
        """
        try:
            logging.info("Awarding piece %s to user %s", piece_id, user_id)

            cursor = self.db_connection.cursor()         
            self.db_connection.begin()

            current_time = int(time.time())

            # Aggiungi il pezzo alla collezione del vincitore
            cursor.execute(
                "INSERT INTO collection (user_id, gacha_id, added_at) VALUES (?, ?, ?)",
                (user_id, piece_id, current_time)
            )

            # Log dell'azione
            cursor.execute(
                "INSERT INTO logs (ts, user_id, action, message) VALUES (?, ?, ?, ?)",
                (current_time, user_id, 'AWARD_PIECE', f"Awarded piece {piece_id} to user {user_id}")
            )

            # Registra la transazione del vincitore
            cursor.execute(
                "INSERT INTO transactions (user_id, amount, type, ts) VALUES (?, ?, ?, ?)",
                (user_id, highest_bid, 'reward', current_time)
            )

            # Aggiorna il saldo del vincitore (sottrai il costo)
            update_data_winner = {
                "amount": -highest_bid,
                "is_refill": False
            }

            response = requests.put(f"{self.api_base_url}/player/gold/{user_id}", json=update_data_winner, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Error updating winner balance: {response.json().get('rsp', 'Unknown error')}")


            # Aggiorna il saldo del creator (aggiungi la quota)
            update_data_creator = {
                "amount": highest_bid,
                "is_refill": True
            }

            response_creator = requests.put(f"{self.api_base_url}/player/gold/{creator_id}", json=update_data_creator,timeout=10)
            if response_creator.status_code != 200:
                raise Exception(f"Error updating creator balance: {response_creator.json().get('rsp', 'Unknown error')}")

            # Registra la transazione per il creator
            cursor.execute(
                "INSERT INTO transactions (user_id, amount, type, ts) VALUES (?, ?, ?, ?)",
                (creator_id, highest_bid, 'creator_reward', current_time)
            )

            # Commit delle modifiche
            self.db_connection.commit()

            logging.info(
                "Piece %s awarded to user %s successfully. Creator %s received %s gold.",
                piece_id, user_id, creator_id, highest_bid
            )

        except Exception as e:
            logging.error("Error awarding piece %s to user %s: %s", piece_id, user_id, e)
            self.db_connection.rollback()
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
        
    def get_auction_by_id(self, auction_id):
        """
        Retrieves auction information by auction_id from the database.
        
        :param auction_id: The ID of the auction to retrieve.
        :return: Dictionary with auction details if found, None otherwise.
        """
        try:
            # SQL query to get auction details by auction_id
            query = """
                SELECT auction_id, piece_id, creator_id, start_price, end_date, current_price 
                FROM auctions WHERE auction_id = ?
            """
            
            # Execute the query using auction_dao, which should handle DB connections and queries
            result = self.auction_dao.execute_query(query, (auction_id,))

            # If no result is found for the provided auction_id, log and return None
            if not result or len(result) == 0:
                logging.error(f"No auction found for auction_id {auction_id}")
                return None

            # If the result does not contain the expected number of columns (6), log an error and return None
            if len(result[0]) != 6:
                logging.error(f"Unexpected result format for auction_id {auction_id}: {result}")
                return None

            # Assuming the first element in the result contains the auction details
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
            # Log any exception that occurs during the query execution
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
        
    def modify_auction(self, auction_id, status):
        """
        Modifies the details of an auction and performs necessary actions when changing the status.

        Args:
            auction_id (int): The ID of the auction to modify.
            status (str): The new status to set for the auction (e.g., 'running', 'ended', 'cancelled').

        Returns:
            dict: A message indicating success or failure.
        """
        try:
            # Verifica che lo status sia uno stato valido
            valid_statuses = ['running', 'ended', 'cancelled']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status value: {status}. Valid statuses are {valid_statuses}")

            # Esegui la query per aggiornare lo stato dell'asta
            query = "UPDATE auctions SET status = ? WHERE auction_id = ?"
            connection = self.auction_dao.connection
            cursor = connection.cursor()
            cursor.execute(query, (status, auction_id))

            # Se il numero di righe modificate è 0, significa che l'asta non è stata trovata
            if cursor.rowcount == 0:
                return {"error": f"Auction with ID {auction_id} not found."}

            # Se lo stato è 'ended', chiama close_auction per eseguire ulteriori azioni
            if status == 'ended':
                close_result = self.close_auction(auction_id)
                if close_result.get("error"):
                    return close_result  # Restituisce un errore se qualcosa va storto con close_auction

            # Commit delle modifiche
            connection.commit()

            # Restituisci una risposta di successo
            return {"message": f"Auction {auction_id} status updated to '{status}'."}

        except ValueError as ve:
            logging.warning("Validation error in modify_auction for auction %s: %s", auction_id, ve)
            return {"error": str(ve)}
        except Exception as e:
            logging.error("Error modifying auction %s: %s", auction_id, e)
            return {"error": "Failed to modify auction due to an internal error."}

                
