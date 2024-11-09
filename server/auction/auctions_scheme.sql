CREATE TABLE IF NOT EXISTS auctions (
    auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    piece_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    start_price DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2),
    start_date INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),  
    end_date INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'ended', 'cancelled')) DEFAULT 'running',
    winner_id INTEGER,
    FOREIGN KEY (piece_id) REFERENCES pieces(piece_id),
    FOREIGN KEY (creator_id) REFERENCES users(id),
    FOREIGN KEY (winner_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bids (
    bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    bid_amount DECIMAL(10, 2) NOT NULL,
    bid_date INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),  
    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);