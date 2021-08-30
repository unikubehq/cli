class ClickContext(object):
    def __init__(self):
        from src.authentication.authentication import get_authentication
        from src.context.context import Context
        from src.local.providers.manager import K8sClusterManager
        from src.storage.general import LocalStorageGeneral

        self.auth = get_authentication()
        self.storage_general = LocalStorageGeneral()
        self.context: Context = Context(auth=self.auth)
        self.cluster_manager = K8sClusterManager()
