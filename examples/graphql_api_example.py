import os
import graphGitHub.graphql_api as api

your_login = ""
your_oauth_token = ""


def main(github_user_name, oauth):

    # Fetch next 40 nodes
    api.fetch_data(github_user_name,
                   oauth,
                   total_node=40,
                   results_folder="results",
                   first_page_cursor=api.get_last_fetched_page("results"),
                   users_by_query=20)

    # Converts results/graphql/data.json to .csv files
    api.graphql2csv(results_folder="results")


if __name__ == "__main__":
    main(your_login, your_oauth_token)
