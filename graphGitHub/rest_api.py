import requests
import time
import os
import csv

entry_point = "https://api.github.com/"


def fetch_repositories(github_user_name,
                       oauth_password,
                       begin_to_repo=0,
                       total_repositories=100,
                       results_folder="results"):
    """
    Fetch a total_repositories number of repositories, starting from begin_to_repo. Results are stored in a
    rest/repositories.csv file in the specified results_folder.

    If this file already exists, the new fetched results will be added at the end of the file such that it is possible
    to perform several calls of this function to increase your dataset at any moment.

    :param github_user_name: Your GitHub login.
    :type github_user_name: String
    :param oauth_password: Your GitHub oauth token.
    :type oauth_password: String
    :param begin_to_repo: Repository from which you want to start.
    :type begin_to_repo: id
    :param total_repositories: Number of repositories that you want to add.
    :type total_repositories: int
    :param results_folder: Path of the folder in which you want to store results.
    :type results_folder: path-like object
    """

    last_id = begin_to_repo
    fetched_repositories = 0

    if not os.path.isdir(os.path.join(results_folder, "rest")):
        os.mkdir(os.path.join(results_folder, "rest"))
    repositories_file = open(os.path.join(results_folder, "rest", "repositories.csv"), "a+")

    while fetched_repositories < total_repositories:
        rate_limit = requests.get(entry_point + "rate_limit",
                             auth=(github_user_name, oauth_password))
        if rate_limit.status_code == 200:
            remaining = int(rate_limit.json()["rate"]["remaining"])
            print("Remaining : " + str(remaining))
        else:
            print("Rate limit request failed. error : " + str(rate_limit.status_code))
            if rate_limit.status_code == 401:
                print("You should check yout GitHub oauth token.")
                return
            print("Let's assume remaining is ok.")
            remaining = 5000

        if remaining > 100:
            repos = requests.get(entry_point + "repositories",
                                 {"since": str(last_id)},
                                 auth=(github_user_name, oauth_password))

            if repos.status_code == 200:
                repos_json = repos.json()
                if len(repos_json) > 0:
                    for repo in repos_json:
                        repositories_file.write(str(repo["id"]) + "," + repo["full_name"] + "\n")
                    last_id = repos_json[-1]["id"]
                    fetched_repositories += len(repos_json)
                print(str(fetched_repositories) + " repositories fetched.")
            else:
                print("Request failed. error : " + str(repos.status_code))
                if repos.status_code == 401:
                    print("You should check yout GitHub oauth token.")
        else:
            print("Waiting...")
            time.sleep(60)


def get_last_fetched_repository(results_folder):
    """
    Returns the last fetched repository reading the repositories.csv file contained in the rest/repositories.csv.
    :param results_folder: Folder in which your results are stored.
    """

    try:
        with open(os.path.join(results_folder, "rest", "repositories.csv")) as page_file:
            repositories = csv.DictReader(page_file, fieldnames=("id", "full_name"))

            # Removes \n end character
            try:
                last_id = None
                for rep in repositories:
                    last_id = rep["id"]
                return last_id
            except IndexError:
                return None

    except FileNotFoundError as e:
        print("rest/repositories.csv doesn't seem to exist in the specified results_folder.")
        raise


def fetch_data(github_user_name,
               oauth_password,
               begin_to_repo=0,
               results_folder="results"):
    """
    Fetch all data from the begin_to_repo repository contained in the rest/repositories.csv in the specified
    results_folder, until the last repository of this file.

    Two other files will be created :
        - rest/contributions.csv
        - rest/users.csv

    :param github_user_name: Your GitHub login.
    :type github_user_name: String
    :param oauth_password: Your GitHub oauth token.
    :type oauth_password: String
    :param begin_to_repo:   Repository from which you want to start. (among those already fetched using
                            fetch_repositories() )
    :type begin_to_repo: id
    :param results_folder: Path of the folder in which you store your results.
    :type results_folder: path-like object
    """
    try:
        csv_repositories = open(os.path.join(results_folder, "rest", "repositories.csv"), "r")
    except FileNotFoundError:
        print("rest/repositories.csv doesn't seem to exists in the specified results_folder."
              "Maybe you forgot to call fetch_repositories before this function.")
        return

    registered_users = read_users(results_folder)
    contributions_files = open(os.path.join(results_folder, "rest", "contributions.csv"), "a+")
    users_file = open(os.path.join(results_folder, "rest", "users.csv"), "a+")

    repositories = csv.DictReader(csv_repositories, fieldnames=("id", "full_name"), delimiter=",")
    i = 0
    contributions_count = 0

    for repo in repositories:
        i += 1
        if int(repo["id"]) > int(begin_to_repo):
            rate_limit = requests.get(entry_point + "rate_limit",
                                      auth=(github_user_name, oauth_password))
            remaining = int(rate_limit.json()["rate"]["remaining"])
            print("Remaining : " + str(remaining))

            while remaining < 100:
                print("Waiting...")
                time.sleep(60)

                rate_limit = requests.get(entry_point + "rate_limit",
                                          auth=(github_user_name, oauth_password))
                remaining = int(rate_limit.json()["rate"]["remaining"])
                print("Remaining : " + str(remaining))

            print(entry_point + "repos/" + repo["full_name"] + "/contributors")
            response = requests.get(entry_point + "repos/" + repo["full_name"] + "/contributors",
                                    auth=(github_user_name, oauth_password))
            if response.status_code == 200:
                contributors = response.json()
                print("Fetched " + str(len(contributors)) + " contributors.")
                for contributor in contributors:
                    user_id = str(contributor["id"])
                    if user_id not in registered_users:
                        print("Add new user : id = " + user_id + ", login = " + contributor["login"])
                        users_file.write(user_id + ", " + contributor["login"] + "\n")
                        registered_users.append(user_id)

                    contributions_files.write(repo["id"] + "," + user_id + "," + str(contributor["contributions"]) + "\n")
                    contributions_count += 1

            else:
                print("Request failed. error : " + str(response.status_code))
                if response.status_code == 401:
                    print("You should check your GitHub oauth token.")

            print(str(i) + " processed repositories. (" + str(contributions_count) + " contributions)")


def get_last_repository_data_fetched(results_folder):
    """
    Returns the last repository from which data as already been fetched, based on the content of the
    rest/contributions.csv contained in the specified results_folder.
    :param results_folder: Folder where you store your results.
    :type results_folder: path-like object
    """

    try:
        with open(os.path.join(results_folder, "rest", "contributions.csv")) as page_file:
            repositories = csv.DictReader(page_file, fieldnames=("id_folder", "id_user", "contributions"))
            # Removes \n end character
            last_id = None
            for rep in repositories:
                last_id = rep["id_folder"]
            return last_id
    except FileNotFoundError as e:
        print(e)
        print("rest/contributions.csv doesn't seem to exist in the specified results_folder.")


def read_users(results_folder):
    """
    Returns the list of ids of the currently fetched users, reading the rest/users.csv file contained in the specified
    results_folder.

    :param results_folder: Folder where you store your results.
    :type results_folder: path-like object
    :return: list of user ids
    :rtype: list of int
    """

    user_ids = []
    try:
        with open(os.path.join(results_folder, "rest", "users.csv"), "r") as users_file:
            users_csv = csv.DictReader(users_file, fieldnames=("id", "login"), delimiter=",")
            for user in users_csv:
                user_ids.append(user["id"])
        return user_ids

    except FileNotFoundError:
        return []


def raw2gephi(user_file, repositories_file, contributions_file, destination_folder):
    """
    Convert fetched data into Gephi compatible files.
    Basically, from user_file, repositories_file and contributions_file, you will obtain two csv files, nodes.csv and
    edges.csv that contains all the currently fetched data and that you can import directly in Gephi.

    :param user_file: Path of the users.csv file.
    :param repositories_file: Path of the repositories.csv file.
    :param contributions_file: Path of the contributions.csv file.
    :param destination_folder: Path of the folder in which you want to store results.
    """

    new_user_ids = {}
    new_users = []
    with open(user_file, "r") as users_data:
        print("Reading users...")
        users = csv.DictReader(users_data, fieldnames=("id", "login"), delimiter=",")
        # Generating new user ids
        new_id = 0
        for user in users:
            new_users.append((new_id, user["login"]))
            new_user_ids[user["id"]] = new_id
            new_id += 1

    new_repositories_ids = {}
    new_repositories = []
    with open(repositories_file, "r") as repositories_data:
        print("Reading repositories...")
        repositories = csv.DictReader(repositories_data, fieldnames=("id", "full_name"), delimiter=",")
        # Generating new repositories ids
        for repository in repositories:
            new_repositories.append((new_id, repository["full_name"]))
            new_repositories_ids[repository["id"]] = new_id
            new_id += 1

    new_contributions = []
    with open(contributions_file, "r") as contributions_data:
        contributions = csv.DictReader(contributions_data, fieldnames=("user_id", "repository_id", "contributions"), delimiter=",")
        print("Processing contributions...")
        # Generating new contributions
        for contribution in contributions:
            new_contributions.append((new_user_ids[contribution["repository_id"]],
                                     new_repositories_ids[contribution["user_id"]],
                                     contribution["contributions"]))

    # Writting new Gephi compliant files in destination_folder
    print(os.getcwd())
    with open(os.path.join(destination_folder, "nodes.csv"), "w") as node_file:
        print("Writting new nodes...")
        node_file.write("id,label,type\n")
        for user in new_users:
            node_file.write(str(user[0]) + "," + user[1] + ",user\n")
        for repository in new_repositories:
            node_file.write(str(repository[0]) + "," + repository[1] + ",repository\n")

    with open(os.path.join(destination_folder, "edges.csv"), "w") as edge_file:
        print("Writting new edges...")
        edge_file.write("Source,Target,Weight\n")
        for contribution in new_contributions:
            edge_file.write(str(contribution[0]) + "," + str(contribution[1]) + "," + str(contribution[2]) + "\n")

    print("All done!")


