class Bridge:
    def count(self) -> int:
        raise NotImplementedError

    def pre_cluster_up(self):
        pass

    def post_cluster_up(self):
        pass

    def pre_cluster_down(self):
        pass

    def post_cluster_down(self):
        pass
