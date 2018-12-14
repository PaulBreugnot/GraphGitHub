import graphGitHub.rest_api as api

your_login = ""
your_oauth_token = ""


def main(github_user_name, oauth):
    print(api.get_last_fetched_repository("results"))

    # Fetch the first 100 repositories from last fetched repositories.
    api.fetch_repositories(github_user_name,
                           oauth,
                           begin_to_repo=api.get_last_fetched_repository("results"),
                           total_repositories=100,
                           results_folder="results")

    # Fetch all repositories data
    print("Fetching results from " + api.get_last_repository_data_fetched("results"))
    api.fetch_data(github_user_name,
                   oauth,
                   begin_to_repo=api.get_last_repository_data_fetched("results"),
                   results_folder="results")

    convert2gephi()


def convert2gephi():
    # Convert .csv files to nodes.csv and edges.csv
    # /!\ No data cleaning yet
    api.raw2gephi("results/rest/users.csv",
                  "results/rest/repositories.csv",
                  "results/rest/contributions.csv", "results/rest/gephi")


if __name__ == "__main__":
    main(your_login, your_oauth_token)
