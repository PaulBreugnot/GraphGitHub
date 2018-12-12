import csv
import matplotlib.pyplot as plt
import os


def compute_distributions(edges_file, plot=True):
    with open(edges_file, "r") as edges:
        contributions = csv.DictReader(edges, delimiter=",")
        rep_by_users_counts = {}
        users_by_rep_counts = {}

        print("Compute users and repositories counts...")
        for contribution in contributions:
            user = contribution["Source"]
            if user not in list(rep_by_users_counts.keys()):
                rep_by_users_counts[user] = 1
            else:
                rep_by_users_counts[user] = rep_by_users_counts[user] + 1

            repository = contribution["Target"]
            if repository not in list(users_by_rep_counts.keys()):
                users_by_rep_counts[repository] = 1
            else:
                users_by_rep_counts[repository] = users_by_rep_counts[repository] + 1

        print("Compute distributions...")
        rep_by_users_distrib = {}
        for user in list(rep_by_users_counts.keys()):
            count = rep_by_users_counts[user]
            if count not in list(rep_by_users_distrib.keys()):
                rep_by_users_distrib[count] = 1
            else:
                rep_by_users_distrib[count] = rep_by_users_distrib[count] + 1

        users_by_rep_distrib = {}
        for rep in list(users_by_rep_counts.keys()):
            count = users_by_rep_counts[rep]
            if count not in list(users_by_rep_distrib.keys()):
                users_by_rep_distrib[count] = 1
            else:
                users_by_rep_distrib[count] = users_by_rep_distrib[count] + 1

        print("Results : ")
        print("Max repository count by user : " + str(max(list(rep_by_users_distrib.keys()))))
        print("Max contributors by repository : " + str(max(list(users_by_rep_distrib.keys()))))
        if plot:
            plt.plot(list(rep_by_users_distrib.keys()), list(rep_by_users_distrib.values()),
                     linestyle='None', marker=".", label="repositories by users")
            plt.plot(list(users_by_rep_distrib.keys()), list(users_by_rep_distrib.values()),
                     linestyle='None', marker=".", label="contributors by repositories")
            plt.legend()
            plt.show()
        return users_by_rep_counts, rep_by_users_counts


def clean(nodes_file, edges_file, destination_folder, users_by_rep_treshold=10, rep_by_user_treshold=10):
    nodes_to_delete = []

    users_by_rep_counts, rep_by_user_counts = compute_distributions(edges_file, plot=False)
    # Check repositories
    print("Cleaning repositories...")
    for rep in list(users_by_rep_counts.keys()):
        if users_by_rep_counts[rep] < users_by_rep_treshold:
            nodes_to_delete.append(rep)

    # Check users
    print("Cleaning users...")
    for user in list(rep_by_user_counts.keys()):
        if rep_by_user_counts[user] < rep_by_user_treshold:
            nodes_to_delete.append(user)
    print("Nodes to delete : " + str(len(nodes_to_delete)))

    # Writes clean edges
    linked_nodes = []
    with open(edges_file, "r") as original_edges_file:
        with open(os.path.join(destination_folder, "clean_edges.csv"), "w") as clean_edges:
            print("Writing new edges to " + str(os.path.join(destination_folder, "clean_edges.csv")) + "...")
            clean_edges.write("Source,Target,Weight\n")
            original_edges = csv.DictReader(original_edges_file, delimiter=",")
            new_edges_count = 0
            for original_edge in original_edges:
                # We keep only the edges that link two living nodes
                if (original_edge["Source"] not in nodes_to_delete) and (original_edge["Target"] not in nodes_to_delete):
                    clean_edges.write(original_edge["Source"] + ","
                                      + original_edge["Target"] + ","
                                      + original_edge["Weight"] + "\n")
                    new_edges_count += 1
                    linked_nodes.append(original_edge["Source"])
                    linked_nodes.append(original_edge["Target"])
            print("New edges count : " + str(new_edges_count))

    # Writes clean nodes
    with open(nodes_file, "r") as original_nodes_file:
        with open(os.path.join(destination_folder, "clean_nodes.csv"), "w") as clean_nodes:
            print("Writing new nodes to " + str(os.path.join(destination_folder, "clean_nodes.csv")) + "...")
            clean_nodes.write("id,label,type\n")
            original_nodes = csv.DictReader(original_nodes_file, delimiter=",")
            new_nodes_count = 0
            for original_node in original_nodes:
                # Also removes nodes that left without any connection after edges cleaning.
                if original_node["id"] in linked_nodes and original_node["id"] not in nodes_to_delete:
                    clean_nodes.write(original_node["id"] + ","
                                      + original_node["label"] + ","
                                      + original_node["type"] + "\n")
                    new_nodes_count += 1
            print("New nodes count : " + str(new_nodes_count))

