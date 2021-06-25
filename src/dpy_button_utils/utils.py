from discord.http import Route


class _CustomRoute(Route):
    """
    A route that allows for v9
    """
    BASE = "https://discord.com/api/v9"
