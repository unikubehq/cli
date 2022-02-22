from typing import Optional

from unikube.cli import console
from unikube.graphql_utils import GraphQL


def organization_id_2_display_name(ctx, id: str = None) -> str:
    if not id:
        return "-"

    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID!) {
                organization(id: $id) {
                    title
                }
            }
            """,
            query_variables={
                "id": id,
            },
        )
        title = data["organization"]["title"]
    except Exception as e:
        console.debug(e)
        title = "-"

    return f"{title} ({id})"


def project_id_2_display_name(ctx, id: str = None) -> Optional[str]:
    if not id:
        return "-"

    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID!) {
                project(id: $id) {
                    title
                }
            }
            """,
            query_variables={
                "id": id,
            },
        )
        title = data["project"]["title"]
    except Exception as e:
        console.debug(e)
        title = "-"

    return f"{title} ({id})"


def deck_id_2_display_name(ctx, id: str = None) -> Optional[str]:
    if not id:
        return "-"

    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID!) {
                deck(id: $id) {
                    title
                }
            }
            """,
            query_variables={
                "id": id,
            },
        )
        title = data["deck"]["title"]
    except Exception as e:
        console.debug(e)
        title = "-"

    return f"{title} ({id})"
