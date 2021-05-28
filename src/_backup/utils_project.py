# -*- coding: utf-8 -*-
from typing import List, Optional

from tinydb import Query
from utils.client import GQLQueryExecutor, get_requests_session

from src import settings


class ConfigManager:

    DB = None
    MISC = settings.MISC
    QUERY = Query()

    def set_active(self, _id, slug, **kwargs) -> dict:
        self.DB.update({"cli_active": False})
        obj = self.DB.get(self.QUERY.id == _id)
        if obj:
            obj.update(kwargs)
            obj["cli_active"] = True
            self.DB.write_back([obj])
        else:
            # object gets created for the very first time
            obj = {"id": _id, "name": slug, "cli_active": True}
            obj.update(kwargs)
            self.DB.insert(obj)
        return obj

    def update_active(self, obj):
        db_obj = self.DB.get(self.QUERY.id == obj["id"])
        db_obj.update(obj)
        self.DB.write_back([db_obj])

    def get_active(self) -> Optional[dict]:
        obj = self.DB.get(self.QUERY.cli_active == True)  # noqa
        return obj

    def get_all(self) -> List[dict]:
        return self.DB.all()

    def delete(self, _id):
        self.DB.remove(self.QUERY.id == _id)


class AppManager(ConfigManager):
    DB = settings.config.table("apps")

    def unset_app(self):
        self.DB.update({"cli_active": False})


class ProjectManager(ConfigManager):
    DB = settings.config.table("projects")
    APP_MGR = AppManager()

    def unset_project(self):
        self.DB.update({"cli_active": False})
        self.APP_MGR.unset_app()


class AllProjects(GQLQueryExecutor):
    query = """
    {
      projects(organizationId: "") {
        id
        slug
        description
      }
    }
    """
    key = "projects"


class ProjectInfo(GQLQueryExecutor):
    query = """
    {
      project(id: "$id") {
        id
        slug
        description
        organization {
          name
        }
        specRepository
        created
      }
    }
    """
    key = "project"


class ProjectApps(GQLQueryExecutor):
    query = """
    {
      project(id: "$id") {
        applications {
          id
          slug
          description
          namespace
          environment(level:"local"){
               specsUrl
          }
        }
      }
    }
    """
    key = "project"

    def get_data(self, **kwargs):
        data = self._query(**kwargs)["applications"]
        if "filter" in kwargs:
            _filter = kwargs["filter"]
            result = []
            if type(_filter) == list:
                for d in data:
                    [d.pop(x, None) for x in _filter]
                    result.append(d)
                return result
            else:
                for d in data:
                    d.pop(_filter)
                    result.append(d)
                return result
        return data


class AppSpecs(GQLQueryExecutor):
    query = """
    {
        applications(id: "$id") {
            namespace
            environment(level:"local"){
               specsUrl
            }
        }
    }
    """

    key = "applications"


class Deployments(GQLQueryExecutor):
    query = """
    {
        application(id: "$id") {
            namespace
            deployments(level: "local") {
                id
                slug
                description
                ports
                isSwitchable
            }
        }
    }
    """

    key = "application"


def download_specs(url):
    session = get_requests_session()
    r = session.get(settings.DEFAULT_UNIKUBE_GRAPHQL_HOST + url)
    if r.status_code == 200:
        return r.json()
    raise Exception(f"access to K8s specs failed (status {r.status_code})")
