"""
Middleware for multi-database tier routing.
Sets the active database based on the authenticated user's role.
"""
from config.db_router import set_db_for_role, reset_db


class TierDatabaseMiddleware:
    """
    After authentication, sets the thread-local database alias so the
    TierDatabaseRouter directs queries to the correct tier database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set DB context if user is authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_db_for_role(request.user.role)

        response = self.get_response(request)

        # Always reset after request completes
        reset_db()
        return response
