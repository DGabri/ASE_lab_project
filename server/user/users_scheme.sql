CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    type INTEGER NOT NULL,  -- 0 = admin 1 = player
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    token_balance FLOAT,
    account_status INTEGER  -- 0 = banned 1 = active
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