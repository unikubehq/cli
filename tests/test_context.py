import unittest
from unittest.mock import patch

from src.context.helper import is_valid_uuid4


class IsValidUuid4Test(unittest.TestCase):
    def test_is_valid_uuid4_valid(self):
        result = is_valid_uuid4("51b1d6b3-8375-4859-94f6-73afc05d7275")
        self.assertTrue(result)

    def test_is_valid_uuid4_invalid(self):
        result = is_valid_uuid4("invalid")
        self.assertFalse(result)


# class ContextArgumentsTest(unittest.TestCase):
#     @patch("src.graphql.GraphQL.query")
#     def test_convert_organization_argument_to_uuid_name(self, mock_graph_ql_query):
#         test_organization_id = "51b1d6b3-8375-4859-94f6-73afc05d7275"
#         mock_graph_ql_query.return_value = {
#             "allOrganizations": {
#                 "results": [
#                     {
#                         "title": "title",
#                         "id": test_organization_id,
#                     },
#                 ]
#             }
#         }

#         organization_id = convert_organization_argument_to_uuid(auth=None)
#         self.assertEqual(organization_id, test_organization_id)

#     @patch("src.graphql.GraphQL.query")
#     def test_convert_organization_argument_to_uuid_uuid(self, mock_graph_ql_query):
#         test_organization_id = "51b1d6b3-8375-4859-94f6-73afc05d7275"
#         mock_graph_ql_query.return_value = {
#             "allOrganizations": {
#                 "results": [
#                     {
#                         "title": "title",
#                         "id": test_organization_id,
#                     },
#                 ]
#             }
#         }

#         organization_id = convert_organization_argument_to_uuid(auth=None, argument_value=test_organization_id)
#         self.assertEqual(organization_id, test_organization_id)

#     @patch("src.graphql.GraphQL.query")
#     def test_convert_context_arguments(self, mock_graph_ql_query):
#         test_organization_id = "51b1d6b3-8375-4859-94f6-73afc05d7275"
#         test_project_id = "51b1d6b3-8375-4859-94f6-73afc05d7275"
#         test_deck_id = "51b1d6b3-8375-4859-94f6-73afc05d7275"
#         mock_graph_ql_query.return_value = {
#             "allOrganizations": {
#                 "results": [
#                     {
#                         "title": "title",
#                         "id": test_organization_id,
#                     },
#                 ]
#             },
#             "allProjects": {
#                 "results": [
#                     {
#                         "title": "title",
#                         "id": test_project_id,
#                     },
#                 ]
#             },
#             "allDecks": {
#                 "results": [
#                     {
#                         "title": "title",
#                         "id": test_deck_id,
#                     },
#                 ]
#             },
#         }

#         organization_id, project_id, deck_id = convert_context_arguments(
#             auth=None,
#             organization_argument=test_organization_id,
#             project_argument=test_project_id,
#             deck_argument=test_deck_id,
#         )
#         self.assertEqual(organization_id, test_organization_id)
#         self.assertEqual(project_id, test_project_id)
#         self.assertEqual(deck_id, test_deck_id)

#     @patch("src.graphql.GraphQL.query")
#     def test_convert_context_arguments_duplicate_organization_title(self, mock_graph_ql_query):
#         mock_graph_ql_query.return_value = {
#             "allOrganizations": {
#                 "results": [
#                     {
#                         "title": "title",
#                         "id": "51b1d6b3-8375-4859-94f6-73afc05d7275",
#                     },
#                     {
#                         "title": "title",
#                         "id": "51b1d6b3-8375-4859-94f6-73afc05d7278",
#                     },
#                 ]
#             },
#         }

#         with self.assertRaises(Exception) as cm:
#             _, _, _ = convert_context_arguments(auth=None, organization_argument="title")

#         self.assertEqual(str(cm.exception), "Organization name/slug is not unique.")

#     @patch("src.graphql.GraphQL.query")
#     def test_convert_context_arguments_slug(self, mock_graph_ql_query):
#         test_organization_id = "51b1d6b3-8375-4859-94f6-73afc05d7275"
#         mock_graph_ql_query.return_value = {
#             "allOrganizations": {
#                 "results": [
#                     {
#                         "title": "Test Title",
#                         "id": test_organization_id,
#                     },
#                 ]
#             },
#         }

#         organization_id, _, _ = convert_context_arguments(auth=None, organization_argument="test-title")
#         self.assertEqual(organization_id, test_organization_id)
