class AbstractBridge:
    def intercept_count(self) -> int:
        return 0

    def pre_cluster_up(self):
        pass

    def post_cluster_up(self):
        pass

    def pre_cluster_down(self):
        pass

    def post_cluster_down(self):
        pass
