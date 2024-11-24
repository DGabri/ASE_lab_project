CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    user_type INTEGER NOT NULL, -- 0 = admin 1 = player
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    account_status INTEGER  -- 0 = banned 1 = active
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);