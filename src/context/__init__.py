class ClickContext(object):
    def __init__(self):
        from src.authentication.authentication import TokenAuthentication
        from src.cache.cache import Cache
        from src.context.context import Context
        from src.local.providers.manager import K8sClusterManager

        cache = Cache()
        self.user_id = cache.userId

        self.auth = TokenAuthentication(cache=cache)
        self.context: Context = Context(user_id=self.user_id, auth=self.auth)
        self.cluster_manager = K8sClusterManager()


1
