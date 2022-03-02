class ClickContext(object):
    def __init__(self):
        from unikube.cache.cache import Cache
        from unikube.cluster.providers.manager import ClusterManager
        from unikube.context.context import Context

        # add cache to the context (loading this cache is required to identify the user)
        cache = Cache()
        self.cache = cache
        self.user_id = cache.userId

        self.context = Context(cache=self.cache)
        self.cluster_manager = ClusterManager()
