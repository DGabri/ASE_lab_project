CREATE TABLE IF NOT EXISTS banners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cost INT NOT NULL,
    pic TEXT NOT NULL,
    pieces_num INTEGER NOT NULL,
    common_rate DECIMAL(5,2) NOT NULL,
    rare_rate DECIMAL(5,2) NOT NULL,
    super_rare_rate DECIMAL(5, 2) NOT NULL
);