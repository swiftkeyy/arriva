"""Global database instance holder."""

# Global database connection
_db_connection = None


def set_db(db):
    """Set the global database connection."""
    global _db_connection
    _db_connection = db


def get_db():
    """Get the global database connection."""
    return _db_connection
