import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json


class Database:
    """База данных для сохранения результатов анализов вакансий"""

    def __init__(self, db_path: str = "hh_analyzer.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    area TEXT,
                    user_id INTEGER,
                    total_vacancies INTEGER,
                    stats TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON analyses(user_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON analyses(created_at)
            """)

            conn.commit()

    def save_analysis(
        self,
        query: str,
        area: Optional[str],
        user_id: int,
        total_vacancies: int,
        stats: Dict
    ) -> int:
        """Сохранить результаты анализа"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analyses (query, area, user_id, total_vacancies, stats)
                VALUES (?, ?, ?, ?, ?)
            """, (query, area, user_id, total_vacancies, json.dumps(stats, ensure_ascii=False)))
            conn.commit()
            return cursor.lastrowid

    def get_user_analyses(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить последние анализы пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analyses
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_stats(self, user_id: Optional[int] = None) -> Dict:
        """Получить статистику использования"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Общее количество анализов
            cursor.execute("SELECT COUNT(*) FROM analyses")
            total_analyses = cursor.fetchone()[0]

            # Анализов за сегодня
            cursor.execute("""
                SELECT COUNT(*) FROM analyses
                WHERE DATE(created_at) = DATE('now')
            """)
            today_analyses = cursor.fetchone()[0]

            # Количество уникальных пользователей
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM analyses")
            unique_users = cursor.fetchone()[0]

            # Топ запросов
            cursor.execute("""
                SELECT query, COUNT(*) as count
                FROM analyses
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            """)
            top_queries = cursor.fetchall()

            return {
                "total_analyses": total_analyses,
                "today_analyses": today_analyses,
                "unique_users": unique_users,
                "top_queries": top_queries
            }
