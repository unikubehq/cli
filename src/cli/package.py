import click

import src.cli.console as console
from src.graphql import ClusterLevelType, GraphQL
from src.helpers import download_specs
from src.local.system import KubeAPI, KubeCtl


# click -----
@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.pass_obj
def list(ctx, organization=None, project=None, **kwargs):
    """
    List all packages.
    """

    context = ctx.context(organization=organization, project=project)

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($organization_id: UUID, $project_id: UUID) {
                allPackages(organizationId: $organization_id, projectId: $project_id) {
                    results {
                        id
                        title
                        project {
                            title
                            organization {
                                title
                            }
                        }
                    }
                }
            }
            """,
            query_variables={
                "organization_id": organization,
                "project_id": project,
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    package_list = data["allPackages"]["results"]

    # format list to table
    table_data = []
    for package in package_list:
        data = {}

        if not context.organization_id:
            data["organization"] = package["project"]["organization"]["title"]

        if not context.project_id:
            data["project"] = package["project"]["title"]

        data["id"] = package["id"]
        data["title"] = package["title"]

        table_data.append(data)

    # console
    console.table(data=table_data)


@click.command()
@click.argument("package_name", required=False)
def info(package_name, **kwargs):
    raise NotImplementedError


@click.command()
@click.argument("package_name", required=False)
def use(package_name, **kwargs):
    raise NotImplementedError


@click.command()
@click.argument("package_title", required=False)
@click.pass_obj
def install(ctx, package_title, **kwargs):
    """
    Install package.
    """

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            {
                allPackages {
                    results {
                        id
                        title
                        namespace
                        clusterLevel {
                            id
                            type
                            valuesPath
                        }
                        project {
                            id
                            title
                            organization {
                                title
                            }
                        }
                    }
                }
            }
            """
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    package_list = data["allPackages"]["results"]

    # argument
    if not package_title:
        # argument from context
        context = ctx.context()
        if context.package_id:
            # TODO
            package_title = context.package_id

        # argument from console
        else:
            package_list_choices = [item["title"] for item in package_list]
            package_title = console.list(
                message="Please select a project",
                choices=package_list_choices,
            )
            if package_title is None:
                return False

    # check access to the package
    package_title_list = [package["title"] for package in package_list]
    if package_title not in package_title_list:
        console.info(f"The package '{package_title}' could not be found.")
        return None

    # get project_id
    project_id = None
    package = None
    for package in package_list:
        if package["title"] == package_title:
            project_id = package["project"]["id"]
            break

    # check if cluster is ready
    cluster_data = ctx.cluster_manager.get(id=project_id)
    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)
    if not cluster:
        console.error("The project cluster does not exist.")
        return None

    # check if kubernetes cluster is running/ready
    if not cluster.ready():
        console.info(f"Kubernetes cluster for '{cluster.display_name}' is not running")
        return None

    # check cluster level
    try:
        cluster_level = ClusterLevelType(package["clusterLevel"][0]["type"])
    except Exception as e:
        console.debug(e)
        cluster_level = None

    if cluster_level != ClusterLevelType.LOCAL:
        console.error("This package cannot be installed locally.")
        return None

    # download manifest
    try:
        cluster_level_id = package["clusterLevel"][0]["id"]
        general_data = ctx.storage_general.get()
        all_specs = download_specs(
            access_token=general_data.authentication.access_token,
            cluster_level_id=cluster_level_id,
        )
    except Exception as e:
        console.error("Could not load manifest: " + str(e))
        return None

    provider_data = cluster.storage.get()

    # KubeCtl
    kubectl = KubeCtl(provider_data=provider_data)

    namespace = package["namespace"]
    kubectl.create_namespace(namespace)
    with click.progressbar(
        all_specs,
        label="[Info] Installing Kubernetes resources to the cluster",
    ) as files:
        for file in files:
            kubectl.apply_str(namespace, file["content"])
    console.info("The cluster is currently applying all changes, this may takes several minutes")

    ingresss = KubeAPI(provider_data, package).get_ingress()
    ingress_data = []
    for ingress in ingresss.items:
        hosts = []
        paths = []
        for rule in ingress.spec.rules:
            hosts.append(f"http://{rule.host}:{provider_data.publisher_port}")
            for path in rule.http.paths:
                paths.append(f"{path.path} -> {path.backend.service_name}")
                # this is an empty line in output
            hosts.append("")
            paths.append("")

        ingress_data.append(
            {
                "name": ingress.metadata.name,
                "url": "\n".join(hosts),
                "paths": "\n".join(paths),
            }
        )

    # console
    console.table(
        ingress_data,
        headers={"name": "Name", "url": "URLs"},
    )


@click.command()
@click.argument("package_name", required=False)
def uninstall(package_name, **kwargs):
    raise NotImplementedError


@click.command()
@click.argument("package_name", required=False)
@click.option("--app", "-a", help="Stream aggregated logs")
def logs(package_name, **kwargs):
    raise NotImplementedError


@click.command()
@click.argument("package_name", required=False)
@click.option("--app", "-a", help="Request a new environment variable")
def request_env(package_name, **kwargs):
    raise NotImplementedError
