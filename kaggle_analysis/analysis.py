import numpy
import typing
import scipy.stats
import pkg_resources
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
matplotlib.pyplot.ioff()


def plot_slope(x: numpy.ndarray,
               xs: typing.List[typing.Union[int, float]],
               ys: typing.List[typing.Union[int, float]],
               format_string: str) -> None:
    slope = scipy.stats.pearsonr(numpy.array(xs), -numpy.array(ys))
    b = -numpy.mean(ys) - slope[0]*numpy.mean(xs)
    y = slope[0]*x + b
    matplotlib.pyplot.plot(x, y, format_string)


def plot_team_size_histogram(competitions: list) -> None:
    matplotlib.pyplot.figure()

    all_team_sizes = []
    for competition in competitions:
        all_team_sizes += competition["real_team_sizes"]
        all_team_sizes += [1]*(len(competition["team_list"]) - len(competition["real_team_sizes"]))

    matplotlib.pyplot.yscale('log')
    matplotlib.pyplot.hist(all_team_sizes, bins=range(min(all_team_sizes), max(all_team_sizes)+1), align='left')
    matplotlib.pyplot.xlabel('Team Size')
    matplotlib.pyplot.ylabel('Count')
    matplotlib.pyplot.savefig(pkg_resources.resource_filename("figures", "team_size_histogram.png"))


def get_nominal_teams(good_competitions: list) -> tuple:
    matplotlib.pyplot.figure()

    real_team_scores_all = []
    indiv_team_scores_all = []
    nominal_team_scores_all = []

    real_team_tefforts_all = []
    indiv_team_tefforts_all = []
    nominal_team_tefforts_all = []

    real_team_sizes_all = []
    nominal_team_sizes_all = []

    for competition in good_competitions:
        real_team_scores = []
        indiv_team_scores = []
        real_team_tefforts = []
        indiv_team_tefforts = []
        real_team_sizes = []
        nominal_team_sizes = []

        # Check directionality
        diffscore = competition["team_list"][0]["Score"] - competition["team_list"][1]["Score"]
        diffrank = competition["team_list"][0]["Ranking"] - competition["team_list"][1]["Ranking"]
        if diffscore*diffrank < 0:
            m = -1
        else:
            m = 1

        # Assess quality of teams and individuals
        for team in competition["team_list"]:

            effort = 0
            for userkey in team["user_list"]:
                effort += team["user_list"][userkey]

            if len(team["user_list"]) == 1:
                indiv_team_scores.append(m*team["Score"])
                indiv_team_tefforts.append(effort)
            else:
                real_team_scores.append(m*team["Score"])
                real_team_tefforts.append(effort)
                real_team_sizes.append(len(team["user_list"]))

        # Normalize values according to mean and standard distribution
        mm = numpy.mean(indiv_team_scores)
        sm = numpy.std(indiv_team_scores)
        real_team_scores = [(x-mm)/sm for x in real_team_scores]
        indiv_team_scores = [(x-mm)/sm for x in indiv_team_scores]

        # Normalize values according to mean and standard distribution
        mm = numpy.mean(indiv_team_tefforts)
        real_team_tefforts = [x/mm for x in real_team_tefforts]
        indiv_team_tefforts = [x/mm for x in indiv_team_tefforts]

        # Get scores for teams resampled from individuals
        nominal_team_scores = []
        nominal_team_tefforts = []
        for _ in range(int(0.5*len(competition["team_list"]))):
            # Choose a team size
            team_size = numpy.random.choice(competition["real_team_sizes"])
            nominal_team_sizes.append(team_size)

            # Get remixed average effort
            efforts = numpy.random.choice(indiv_team_tefforts, team_size, replace=False)
            nominal_team_tefforts.append(numpy.sum(efforts))

            # Get remixed scores
            scores = numpy.random.choice(indiv_team_scores, team_size, replace=False)
            nominal_team_scores.append(numpy.min(scores))

        # Save sores
        real_team_scores_all += real_team_scores
        indiv_team_scores_all += indiv_team_scores
        nominal_team_scores_all += nominal_team_scores

        real_team_tefforts_all += real_team_tefforts
        indiv_team_tefforts_all += indiv_team_tefforts
        nominal_team_tefforts_all += nominal_team_tefforts

        real_team_sizes_all += real_team_sizes
        nominal_team_sizes_all += nominal_team_sizes

    return [real_team_scores_all, real_team_tefforts_all, real_team_sizes_all], \
           [indiv_team_scores_all, indiv_team_tefforts_all, [1]*len(indiv_team_scores_all)], \
           [nominal_team_scores_all,  nominal_team_tefforts_all, nominal_team_sizes_all]


def plot_nominal_teams(real_team: tuple, indiv_team: tuple, nominal_team: tuple) -> None:

    matplotlib.pyplot.errorbar(numpy.mean(indiv_team[1]), -numpy.mean(indiv_team[0]),
                               scipy.stats.sem(indiv_team[1]), scipy.stats.sem(indiv_team[0]), 'rs')
    matplotlib.pyplot.errorbar(numpy.mean(real_team[1]), -numpy.mean(real_team[0]),
                               scipy.stats.sem(real_team[1]), scipy.stats.sem(real_team[0]), 'bo')
    matplotlib.pyplot.errorbar(numpy.mean(nominal_team[1]), -numpy.mean(nominal_team[0]),
                               scipy.stats.sem(nominal_team[1]), scipy.stats.sem(nominal_team[0]), 'g^')

    # Add legend and labels
    matplotlib.pyplot.legend(["Individuals (n="+str(len(indiv_team[0]))+")",
                              "True Teams (n="+str(len(real_team[0]))+")",
                              "Nominal Teams (n="+str(len(nominal_team[0]))+")"])

    delta = 0.1
    plot_slope(numpy.array([0.9, 1.1]),
               indiv_team[1],
               indiv_team[0], 'r:')
    plot_slope(numpy.mean(real_team[1])+[-delta, delta],
               real_team[1],
               real_team[0], 'b:')
    plot_slope(numpy.mean(nominal_team[1])+[-delta, delta],
               nominal_team[1],
               nominal_team[0], 'g:')
    plot_slope(numpy.array([1.0, numpy.mean(nominal_team[1])]),
               indiv_team[1],
               indiv_team[0], 'r:')
    plot_slope(numpy.array([numpy.mean(real_team[1])-delta, numpy.mean(nominal_team[1])]),
               real_team[1],
               real_team[0], 'b:')

    matplotlib.pyplot.xlabel("Total Submissions (Normalized)")
    matplotlib.pyplot.ylabel("Quality of Best Solution (Normalized)")
    matplotlib.pyplot.savefig(pkg_resources.resource_filename("figures", "nominal_teams.png"))


def plot_performance_v_size(team, indiv=None, file_name=None):
    team_performance = team[0]
    team_effort = team[1]
    team_size = team[2]

    if indiv is not None:
        team_performance += indiv[0]
        team_effort += indiv[1]
        team_size += indiv[2]

    team_performance = numpy.array(team_performance)
    team_effort = numpy.array(team_effort)
    team_size = numpy.array(team_size)
    unique_team_sizes = numpy.unique(team_size)

    data_mean = []
    data_sem = []
    for size in unique_team_sizes:
        idx = numpy.where(team_size == size)[0]
        data_mean.append(-numpy.mean(team_performance[idx]))
        data_sem.append(scipy.stats.sem(team_performance[idx]))

    matplotlib.pyplot.errorbar(unique_team_sizes, data_mean, yerr=data_sem)

def plot_nominal_performance_v_size(indiv, max_team_size=25, sample_size=100, file_name=None):
    indiv_performance = indiv[0]
    indiv_effort = indiv[1]
    indiv_size = indiv[2]

    team_mean = []
    team_sem = []
    for size in range(1, max_team_size+1):
        nominal_team_scores = []
        for _ in range(sample_size):
            # Get remixed scores
            scores = numpy.random.choice(indiv_performance, size, replace=False)
            nominal_team_scores.append(numpy.min(scores))
        team_mean.append(-numpy.mean(nominal_team_scores))
        team_sem.append(-scipy.stats.sem(nominal_team_scores))

    matplotlib.pyplot.errorbar(range(1, max_team_size+1), team_mean, yerr=team_sem)
