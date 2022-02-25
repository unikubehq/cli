class ClickContext(object):
    def __init__(self):
        from unikube.cache.cache import Cache
        from unikube.context.context import Context
        from unikube.local.providers.manager import K8sClusterManager

        # add cache to the context (loading the cache is required to identify the user)
        cache = Cache()
        self.cache = cache
        self.user_id = cache.userId

        self.context = Context(cache=self.cache)
        self.cluster_manager = K8sClusterManager()
