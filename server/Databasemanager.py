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
            
            # 1. Player Identity Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Player (
                    player_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    username        TEXT UNIQUE NOT NULL,
                    password_hash   TEXT NOT NULL
                );
            """)

            # 2. Current Stats Table (New: Holds the active rating for fast access)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS CurrentRankings (
                    player_id       INTEGER PRIMARY KEY,
                    ranking         INTEGER NOT NULL DEFAULT 1200,
                    wins            INTEGER NOT NULL DEFAULT 0,
                    number_of_games INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (player_id) REFERENCES Player(player_id)
                );
            """)

            # 3. History Table (Logs changes over time)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RankingHistory (
                    history_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id       INTEGER NOT NULL,
                    ranking         INTEGER NOT NULL,
                    wins            INTEGER NOT NULL,
                    number_of_games INTEGER NOT NULL,
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

    def update_ranking(self, player_id: int, new_ranking: int, new_wins: int, new_total_games: int):
        """
        Updates the player's current stats and logs the change in history.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Update (or Insert) the Current Rankings table
            cursor.execute("""
                INSERT OR REPLACE INTO CurrentRankings (player_id, ranking, wins, number_of_games)
                VALUES (?, ?, ?, ?);
            """, (player_id, new_ranking, new_wins, new_total_games))
            
            # 2. Add a log entry to history
            cursor.execute("""
                INSERT INTO RankingHistory (player_id, ranking, wins, number_of_games) 
                VALUES (?, ?, ?, ?);
            """, (player_id, new_ranking, new_wins, new_total_games))
            
            conn.commit()

    def get_leaderboard(self) -> List[Tuple[str, int, int, int]]:
        """
        Returns: List of (username, ranking, wins, games_played)
        """
        query = """
            SELECT p.username, c.ranking, c.wins, c.number_of_games
            FROM Player p
            JOIN CurrentRankings c ON p.player_id = c.player_id
            ORDER BY c.ranking DESC;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def get_player_stats(self, player_id: int) -> Tuple[int, int, int]:
        """
        Returns: (ranking, wins, number_of_games)
        """
        query = "SELECT ranking, wins, number_of_games FROM CurrentRankings WHERE player_id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id,))
            result = cursor.fetchone()
            if result:
                return result
            return (1200, 0, 0) # Default if not found

    def create_player(self, username: str, password_hash: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 1. Create the Player
                cursor.execute(
                    "INSERT INTO Player (username, password_hash) VALUES (?, ?)", 
                    (username, password_hash)
                )
                player_id = cursor.lastrowid
                
                # 2. Initialize their stats in CurrentRankings
                cursor.execute(
                    "INSERT INTO CurrentRankings (player_id, ranking, wins, number_of_games) VALUES (?, ?, ?, ?)",
                    (player_id, 1200, 0, 0)
                )
                
                # 3. Initialize history
                cursor.execute(
                     "INSERT INTO RankingHistory (player_id, ranking, wins, number_of_games) VALUES (?, ?, ?, ?)",
                     (player_id, 1200, 0, 0)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                pass # Username already exists