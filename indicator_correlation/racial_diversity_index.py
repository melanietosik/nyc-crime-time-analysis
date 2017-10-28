import csv
import json
import os
import sys

import pandas as pd

from collections import defaultdict
from scipy.stats.stats import pearsonr


def get_crime_stats(nypd_fp):
    """
    Get crime frequency per borough per year
    """
    # Read data CSV
    df = pd.read_csv(nypd_fp)
    # Drop rows without x- or y-coordinates, borough name, or report date
    df.dropna(subset=['X_COORD_CD', 'Y_COORD_CD', 'BORO_NM', 'RPT_DT'], inplace=True)
    # Drop irrelevant/redundant columns
    df.drop([
        'CMPLNT_NUM',
        'OFNS_DESC',  # correlated with 'KY_CD'
        'PD_DESC',  # correlated with 'PD_CD'
        'CRM_ATPT_CPTD_CD',  # crime completion rate not relevant
        'Latitude',  # using 'Y_COORD_CD' instead
        'Longitude',  # using 'X_COORD_CD' instead
    ], axis=1, inplace=True)

    # Crime frequency counts per year per borough
    stats = defaultdict(lambda: defaultdict(int))

    for idx, row in df.iterrows():

        # Borough name
        boro = row['BORO_NM']

        # Last four digits of report date
        year = row['RPT_DT'][-4:]

        stats[year][boro] += 1

        if idx % 50000 == 0:
            print(idx)

    # Write statistics to JSON
    with open('nypd_crime_stats.json', 'w') as out:
        json.dump(stats, out, sort_keys=True)

    return stats


def get_correlation(stats, indicator_fp):
    """
    Get correlation between crime stats and indicator data
    """
    # Read data CSV
    df = pd.read_csv(indicator_fp)
    df.set_index('Borough', inplace=True)

    # List of boroughs
    boros = ['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island']
    # List of years
    years = sorted(set(df.columns.values).intersection(list(stats.keys())))

    for boro in boros:
        print(boro)

        nypd = []  # Append crime stats data
        core = []  # Append demographics data

        for year in years:
            nypd.append(stats[year][boro.upper()])
            core.append(df.loc[boro][year])

        assert(len(nypd) == len(core))

        # Print Pearson correlation
        print(pearsonr(nypd, core))

    return None


def main(nypd_fp, corenyc_fp):
    """
    main()
    """

    # Get frequency counts from NYPD data
    if os.path.isfile('nypd_crime_freqs.json'):
        crime_stats = json.load(open('nypd_crime_freqs.json'))
    else:
        crime_stats = get_crime_stats(nypd_fp)

    # Get Pearson correlation
    get_correlation(crime_stats, corenyc_fp)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('USAGE: python racial_diversity_index.py <NYPD CSV> <CoreData CSV>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
