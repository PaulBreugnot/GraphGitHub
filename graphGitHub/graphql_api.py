import requests
import json
import time
import os

entry_point = "https://api.github.com/graphql"


def fetch_data(github_user_name,
               oauth_password,
               first_page_cursor=None,
               total_node=100000,
               users_by_query=20,
               repositories_by_users=20,
               results_folder="results"):

    fetched_users = 0

    remaining = 5000
    lastCursor = first_page_cursor
    if not os.path.isdir(os.path.join(results_folder, "graphql")):
        os.mkdir(os.path.join(results_folder, "graphql"))

    with open(os.path.join(results_folder, "graphql", "graphql_data.txt"), "a+") as raw_data:
        with open(os.path.join(results_folder, "graphql", "page_cursors.txt"), "a+") as cursors_file:
            while fetched_users < total_node:
                print("Remaining : " + str(remaining))

                if remaining > 100:
                    if lastCursor is not None:
                        users = requests.post(entry_point,
                                             data="{\"query\":"
                                                  "\"query listContributions {"
                                                    "rateLimit{cost remaining resetAt} "
                                                    "search(query:\\\"created:>2008-04-10\\\", type:USER, first:"
                                                        + str(users_by_query) + ", after:\\\"" + lastCursor + "\\\"){"
                                                        "userCount pageInfo {endCursor} "
                                                        "edges{node{... on User{"
                                                            "id name repositoriesContributedTo(includeUserRepositories:true  first:"
                                                                + str(repositories_by_users) +" orderBy:{direction:DESC field:STARGAZERS}){"
                                                                "totalCount nodes{"
                                                                    "stargazers{totalCount}"
                                                                    "primaryLanguage{name}"
                                                                    "id name}}}}}}}\"}",
                                             auth=(github_user_name, oauth_password))
                    else:
                        users = requests.post(entry_point,
                                              data="{\"query\":"
                                                   "\"query listContributions {"
                                                   "rateLimit{cost remaining resetAt} "
                                                   "search(query:\\\"created:>2008-04-10\\\", type:USER, first:"
                                                        + str(users_by_query) + "){"
                                                      "userCount pageInfo {endCursor} "
                                                      "edges{node{... on User{"
                                                      "id name repositoriesContributedTo(includeUserRepositories:true first:"
                                                        + str(repositories_by_users) + " orderBy:{direction:DESC field:STARGAZERS}){"
                                                      "totalCount nodes{"
                                                      "stargazers{totalCount}"
                                                      "primaryLanguage{name}"
                                                      "id name}}}}}}}\"}",
                                              auth=(github_user_name, oauth_password))
                    if users.status_code == 200:
                        repos_json = users.json()
                        remaining = repos_json["data"]["rateLimit"]["remaining"]
                        lastCursor = repos_json["data"]["search"]["pageInfo"]["endCursor"]
                        cursors_file.write(lastCursor + "\n")

                        if len(repos_json) > 0:
                            for entry in repos_json["data"]["search"]["edges"]:
                                raw_data.write(json.dumps(entry) + "\n")
                        fetched_users += users_by_query
                        print(str(fetched_users) + " users fetched.")
                    else:
                        print("Request failed. error : " + str(users.status_code))
                        if users.status_code == 401:
                            print("You should check yout GitHub oauth token.")
                else:
                    print("Waiting...")
                    time.sleep(60)

    print("Convert raw file to json...")
    raw2json(os.path.join(results_folder, "graphql", "graphql_data.txt"), os.path.join(results_folder, "graphql", "data.json"))
    print("All done!")


def raw2json(source_file_path, destination_file_path):
    with open(source_file_path, "r") as raw_data:
        with open(destination_file_path, "w+") as json_file:
            json_data = []
            for line in raw_data.readlines():
                json_data.append(json.loads(line))
            json_file.write(json.dumps(json_data))


def graphql2csv(results_folder):

    registered_repositories = []

    try:
        with open(os.path.join(results_folder, "graphql", "data.json"), "r") as data_file:
            graphql_data = json.loads(data_file.read())
    except FileNotFoundError as e:
        print(e)
        print("graphql/data.json doesn't seem to exist in the specified results_folder."
              " Maybe you forgot to call fetch_data before this function.")
        return

    with open(os.path.join(results_folder, "graphql", "repositories.csv"), "w+") as repositories_file:
        with open(os.path.join(results_folder, "graphql", "contributions.csv"), "w+") as contributions_file:
            with open(os.path.join(results_folder, "graphql", "users.csv"), "w+") as users_file:
                processed_users = 0
                contributions_count = 0
                print("Processing " + str(len(graphql_data)) + " nodes...")
                print(graphql_data)
                for data in graphql_data:
                    # User data
                    user_id = data["node"]["id"]
                    users_file.write(str(user_id) + "," + str(data["node"]["name"] + "\n"))
                    for repository in data["node"]["repositoriesContributedTo"]["nodes"]:
                        rep_id = repository["id"]
                        if rep_id not in registered_repositories:

                            rep_name = repository["name"]
                            rep_stars = repository["stargazers"]
                            rep_language = repository["primaryLanguage"]

                            # Handling null entries
                            if rep_stars is None:
                                rep_stars = {"totalCount": 0}
                            if rep_language is None:
                                rep_language = {"name": "None"}

                            print("Add new repository : id = " + rep_id
                                  + ", name = " + rep_name
                                  + ", stars = " + str(rep_stars["totalCount"])
                                  + ", language = " + rep_language["name"])
                            repositories_file.write(rep_id + ","
                                                    + rep_name + ","
                                                    + str(rep_stars["totalCount"]) + ","
                                                    + rep_language["name"] + "\n")
                            registered_repositories.append(rep_id)
                        contributions_file.write(user_id + "," + rep_id + "\n")
                        contributions_count += 1
                    processed_users += 1

                print(str(len(graphql_data)) + " nodes processed.")
                print(str(processed_users) + " users, "
                      + str(len(registered_repositories)) + " repositories and "
                      + str(contributions_count) + " contributions found.")


def get_last_fetched_page(results_folder="results"):
    try:
        with open(os.path.join(results_folder, "graphql", "page_cursors.txt")) as page_file:
            pages = page_file.readlines()
            # Removes \n end character
            try:
                page_cursor = pages[-1][0:-1]
                return page_cursor
            except IndexError:
                return None
    except FileNotFoundError as e:
        print(e)
        print("graphql/page_cursor.txt doesn't seem to exist in the specified results_folder.")
        raise
