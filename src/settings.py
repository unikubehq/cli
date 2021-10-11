import os

import urllib3

from src.cli.helper import exist_or_create
from src.local.providers.types import K8sProviderType

# disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# cli
CLI_CONFIG_FILE = os.path.expanduser("~/.unikube/config_dev")
exist_or_create(CLI_CONFIG_FILE)

CLI_KUBECONFIG_DIRECTORY = os.path.expanduser("~/.unikube/")
CLI_TABLEFMT = "psql"

CLI_LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR/SUCCESS
CLI_ALWAYS_SHOW_CONTEXT = False

# authentication
AUTH_DEFAULT_HOST = "https://login.unikube.io"  # "http://keycloak.127.0.0.1.nip.io:8085"

# unikube
UNIKUBE_FILE = "unikube.yaml"
UNIKUBE_DEFAULT_PROVIDER_TYPE = K8sProviderType.k3d

# token
TOKEN_REALM = "unikube"
TOKEN_ALGORITHM = "RS256"
TOKEN_PUBLIC_KEY = f"/auth/realms/{TOKEN_REALM}"
TOKEN_LOGIN_PATH = f"/auth/realms/{TOKEN_REALM}/protocol/openid-connect/token"
TOKEN_VERIFY_PATH = f"/auth/realms/{TOKEN_REALM}/protocol/openid-connect/userinfo"
TOKEN_REFRESH_PATH = f"/auth/realms/{TOKEN_REALM}/protocol/openid-connect/token"
TOKEN_TIMEOUT = 30
TOKEN_AUDIENCE = "gateway"
TOKEN_RPT_AUDIENCE = "gateway"
KC_CLIENT_ID = "cli"

# GraphQL
GRAPHQL_URL = "https://api.unikube.io/graphql/"  # "http://gateway.unikube.127.0.0.1.nip.io:8085/graphql/"
GRAPHQL_TIMEOUT = 30

# manifest
MANIFEST_DEFAULT_HOST = "https://api.unikube.io/manifests/"

# local system: dependencies + versions + settings
DOCKER_TEST_IMAGE = "busybox"
DOCKER_CLI_MIN_VERSION = "15.0.1"
DOCKER_WEBSITE = "https://docs.docker.com/install/"

K3S_CLI_MIN_VERSION = "1.17.1"

K3D_CLI_MIN_VERSION = "3.0.0"
K3D_WEBSITE = "https://github.com/rancher/k3d"
K3D_CLUSTER_PREFIX = "unikube-"
K3D_DEFAULT_INGRESS_PORT = 80
K3D_DEFAULT_WORKERS = 1

TELEPRESENCE_CLI_MIN_VERSION = "2.3.2"
TELEPRESENCE_TAG_PREFIX = "telepresence:dev"
TELEPRESENCE_DOCKER_IMAGE_FORMAT = "{project}-{deck}-{name}-" + TELEPRESENCE_TAG_PREFIX

HOMEBREW_CLI_MIN_VERSION = "3.2.0"
HOMEBREW_WEBSITE = "https://brew.sh/"

KUBECTL_MIN_CLI_VERSION = "1.18.0"

# Kubernetes
SERVICE_TOKEN_FILENAME = "/var/run/secrets/kubernetes.io/serviceaccount/token"
SERVICE_CERT_FILENAME = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
