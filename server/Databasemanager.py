import sqlite3
from typing import Optional, List, Tuple

class DataBaseManagerC:
    def __init__(self, db_name="data/usersdata.db"):
        self.db_name = db_name
    
    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def setup_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Player (
                    player_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    username        TEXT UNIQUE NOT NULL,
                    password_hash   TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RankingHistory (
                    ranking_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id       INTEGER NOT NULL,
                    ranking         INTEGER NOT NULL,
                    wins            INTEGER NOT NULL DEFAULT 0,
                    number_of_games INTEGER NOT NULL DEFAULT 0,
                    recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES Player(player_id)
                );
            """)
            conn.commit()

    def get_player_id(self, username: str) -> Optional[int]:
        query = "SELECT player_id FROM Player WHERE username = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            return result[0] if result else None

    def username_exists(self, username: str) -> bool:
        query = "SELECT 1 FROM Player WHERE username = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (username,))
            return cursor.fetchone() is not None

    def verify_hash_in_db(self, player_id: int, provided_hash: str) -> bool:
        query = "SELECT 1 FROM Player WHERE player_id = ? AND password_hash = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id, provided_hash))
            return cursor.fetchone() is not None

    def add_ranking_history(self, player_id: int, ranking: int, wins: int, total_games: int):
        query = """
            INSERT INTO RankingHistory (player_id, ranking, wins, number_of_games) 
            VALUES (?, ?, ?, ?);
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id, ranking, wins, total_games))
            conn.commit()

    # --- NEW METHOD ADDED HERE ---
    def get_leaderboard(self) -> List[Tuple[str, int]]:
        query = """
            SELECT username, ranking
            FROM Player
            JOIN RankingHistory USING (player_id)
            WHERE recorded_at = (
                SELECT MAX(recorded_at)
                FROM RankingHistory r2
                WHERE r2.player_id = Player.player_id
            )
            ORDER BY ranking DESC;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def create_player(self, username: str, password_hash: str):
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO Player (username, password_hash) VALUES (?, ?)", 
                    (username, password_hash)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                pass

# =================