import sqlite3


def init_db(app, database):
    with app.app_context():
        db = get_db(database)
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """
        )
        db.commit()


def get_db(database):
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row  # Allows us to access columns by name
    return db
