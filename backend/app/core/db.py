import sqlite3
from pathlib import Path
from threading import Lock


class Database:
    def __init__(self, path: str = "backend/data/app.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self.initialize()

    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self._lock, self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS watchlists (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS watchlist_items (
                    id TEXT PRIMARY KEY,
                    watchlist_id TEXT NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
                    symbol TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (watchlist_id, symbol)
                );
                CREATE TABLE IF NOT EXISTS portfolios (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS portfolio_holdings (
                    id TEXT PRIMARY KEY, portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
                    symbol TEXT NOT NULL, quantity REAL NOT NULL CHECK(quantity > 0),
                    created_at TEXT NOT NULL, UNIQUE(portfolio_id, symbol)
                );
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    symbol TEXT NOT NULL, operator TEXT NOT NULL CHECK(operator IN ('above', 'below')),
                    threshold REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alert_deliveries (
                    id TEXT PRIMARY KEY, alert_id TEXT NOT NULL REFERENCES price_alerts(id) ON DELETE CASCADE,
                    observed_price REAL NOT NULL, delivered_at TEXT NOT NULL,
                    UNIQUE(alert_id, observed_price)
                );
                """
            )


db = Database()
