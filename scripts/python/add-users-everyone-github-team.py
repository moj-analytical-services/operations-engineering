import sys
import time
import traceback

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from services.GithubService import GithubService


def print_stack_trace(message):
    """Print a stack trace when an exception occurs

    Args:
        message (string): A message to print when exception occurs
    """
    print(message)
    try:
        exc_info = sys.exc_info()
    finally:
        traceback.print_exception(*exc_info)
        del exc_info


if len(sys.argv) == 2:
    # Get the GH Action token
    oauth_token = sys.argv[1]
else:
    print("Missing a script input parameter")
    sys.exit(1)

# Setup a transport and client to interact with the GH GraphQL API
try:
    transport = AIOHTTPTransport(
        url="https://api.github.com/graphql",
        headers={"Authorization": "Bearer {}".format(oauth_token)},
    )
except Exception:
    print_stack_trace("Exception: Problem with the API URL or GH Token")

try:
    client = Client(transport=transport, fetch_schema_from_transport=False)
except Exception:
    print_stack_trace("Exception: Problem with the Client.")

github_service = GithubService(oauth_token, "moj-analytical-services")


def organisation_team_id_query() -> gql:
    """A GraphQL query to get the id of an organisation team

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        organization(login: "moj-analytical-services") {
            team(slug: "everyone") {
                databaseId
            }
        }
    }
    """

    return gql(query)


def fetch_team_id() -> int:
    """A wrapper function to run a GraphQL query to get the team ID

    Returns:
        int: The team ID of the team
    """
    query = organisation_team_id_query()
    data = client.execute(query)
    if (
        data["organization"]["team"]["databaseId"] is not None
        and data["organization"]["team"]["databaseId"]
    ):
        return data["organization"]["team"]["databaseId"]
    else:
        return 0


def run():
    """A function for the main functionality of the script"""

    try:
        gh = github_service.client
        org = gh.get_organization("moj-analytical-services")
        team_id = fetch_team_id()
        gh_team = org.get_team(team_id)
        all_org_members = gh_team.get_members()
        org_members = org.get_members()
        for member in org_members:
            if member not in all_org_members:
                print(member)
                gh_team.add_membership(member)
                # Delay for GH API
                time.sleep(3)
    except Exception:
        message = "Warning: Exception in Run()"
        print_stack_trace(message)


print("Start")
run()
print("Finished")
sys.exit(0)
