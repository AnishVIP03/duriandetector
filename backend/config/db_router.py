"""
Database router for multi-tier demo setup.
Routes queries to the correct PostgreSQL database based on the authenticated
user's subscription tier, using a thread-local variable set by middleware.
"""
import threading

_thread_local = threading.local()

ROLE_TO_DB = {
    'free': 'free_db',
    'premium': 'premium_db',
    'exclusive': 'exclusive_db',
    'admin': 'free_db',
}

ALL_DBS = ['default', 'free_db', 'premium_db', 'exclusive_db']


def set_db_for_role(role):
    """Set the active database for the current thread based on user role."""
    _thread_local.db_alias = ROLE_TO_DB.get(role, 'default')


def get_current_db():
    """Get the active database alias for the current thread."""
    return getattr(_thread_local, 'db_alias', 'default')


def reset_db():
    """Reset to default database."""
    _thread_local.db_alias = 'default'


class TierDatabaseRouter:
    """
    Routes all model reads/writes to the database assigned to the current
    user's subscription tier. Falls back to 'default' when no tier is set.
    """

    def db_for_read(self, model, **hints):
        return get_current_db()

    def db_for_write(self, model, **hints):
        return get_current_db()

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Allow all models to migrate to all databases so each DB
        # has the full schema.
        return True
