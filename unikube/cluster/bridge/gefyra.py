from unikube.cluster.bridge.bridge import AbstractBridge
from unikube.cluster.system import CMDWrapper


class Gefyra(AbstractBridge, CMDWrapper):
    base_command = "gefyra"

    def intercept_count(self) -> int:
        arguments = ["list", "--bridges"]
        process = self._execute(arguments)
        output = process.stdout.read()

        if "[INFO] No active bridges found\n" in output:
            return 0

        raise NotImplementedError("TODO")

    def pre_cluster_up(self):
        pass

    def post_cluster_up(self):
        arguments = ["up"]
        self._execute(arguments)

    def pre_cluster_down(self):
        arguments = ["down"]
        self._execute(arguments)

    def post_cluster_down(self):
        pass


class GefyraBuilder:
    def __call__(
        self,
        **kwargs,
    ):
        instance = Gefyra()
        return instance
