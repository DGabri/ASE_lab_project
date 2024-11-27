CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    token_balance FLOAT
);

CREATE TABLE IF NOT EXISTS collection (
    user_id INTEGER NOT NULL,
    gacha_id INTEGER NOT NULL,
    added_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    user_id INTEGER,
    action TEXT NOT NULL,
    message TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    type TEXT NOT NULL,  -- 'purchase', 'reward', 'auction'
    ts INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);