class ClickContext(object):
    def __init__(self):
        from unikube.authentication.authentication import get_authentication
        from unikube.context.context import Context
        from unikube.local.providers.manager import K8sClusterManager
        from unikube.storage.general import LocalStorageGeneral

        self.auth = get_authentication()
        self.storage_general = LocalStorageGeneral()
        self.context: Context = Context(auth=self.auth)
        self.cluster_manager = K8sClusterManager()
