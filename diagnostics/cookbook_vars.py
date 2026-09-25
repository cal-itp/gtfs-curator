import datetime

GCS_FILE_PATH = "gs://calitp-analytics-data/data-analyses/gtfs_diagnostics/"


def define_date_periods(start_year: int = 2023):

    jan = "01-01"
    jun = "06-30"
    jul = "07-01"
    dec = "12-31"

    DATE_PERIODS_DICT = {}

    for year in range(start_year, datetime.datetime.today().year + 1, 1):
        DATE_PERIODS_DICT[f"{year}_H1"] = [f"{year}-{jan}", f"{year}-{jun}"]
        DATE_PERIODS_DICT[f"{year}_H2"] = [f"{year}-{jul}", f"{year}-{dec}"]

    return DATE_PERIODS_DICT


DATE_PERIODS_DICT = define_date_periods(2023)
