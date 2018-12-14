import graphGitHub.clean_data as preprocess


def main():

    # Plot distributions
    preprocess.compute_distributions(
        "results/rest/gephi/edges.csv", plot=True)

    # Clean data
    preprocess.clean("results/rest/gephi/nodes.csv",
                     "results/rest/gephi/edges.csv",
                     "results/rest/gephi/clean/",
                     rep_by_user_treshold=100,
                     users_by_rep_treshold=10)


if __name__ == "__main__":
    main()
