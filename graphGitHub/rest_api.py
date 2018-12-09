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
    last_id = begin_to_repo
    fetched_repositories = 0

    if not os.path.isdir(os.path.join(results_folder, "rest")):
        os.mkdir(os.path.join(results_folder, "rest"))
    repositories_file = open(os.path.join(results_folder, "rest", "repositories.csv", "a+"))

    while fetched_repositories < total_repositories:
        rate_limit = requests.get(entry_point + "rate_limit",
                             auth=(github_user_name, oauth_password))
        remaining = int(rate_limit.json()["rate"]["remaining"])
        print("Remaining : " + str(remaining))

        if remaining > 100:
            repos = requests.get(entry_point + "repositories",
                                 {"since": str(last_id)},
                                 auth=(github_user_name, oauth_password))

            repos_json = repos.json()
            if len(repos_json) > 0:
                for repo in repos_json:
                    repositories_file.write(str(repo["id"]) + "," + repo["full_name"] + "\n")
                last_id = repos_json[-1]["id"]
                fetched_repositories += len(repos_json)
            print(str(fetched_repositories) + " repositories fetched.")
        else:
            print("Waiting...")
            time.sleep(60)


def fetch_data(github_user_name,
               oauth_password,
               begin_to_repo=0,
               results_folder="results"):
    try:
        csv_repositories = open(os.path.join(results_folder, "rest", "repositories.csv"), "r")
    except FileNotFoundError:
        print("rest/repositories.csv doesn't seem to exists in the specified results_folder."
              "Maybe you forgot to call fetch_repositories before this function.")
        return

    registered_users = read_users()
    contributions_files = open(os.path.join(results_folder, "rest", "contributions.csv"), "a+")
    users_file = open(os.path.join(results_folder, "results", "users.csv"), "a+")

    repositories = csv.DictReader(csv_repositories, fieldnames=("id", "full_name"), delimiter=",")
    i = 0
    contributions_count = 0

    for repo in repositories:
        i += 1
        if int(repo["id"]) > begin_to_repo:
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

            print(str(i) + " processed repositories. (" + str(contributions_count) + " contributions)")


def read_users(results_folder):
    user_ids = []
    try:
        with open(os.path.join(results_folder, "rest", "users.csv", "r")) as users_file:
            users_csv = csv.DictReader(users_file, fieldnames=("id", "login"), delimiter=",")
            for user in users_csv:
                user_ids.append(user["id"])
        return user_ids

    except FileNotFoundError:
        return []



