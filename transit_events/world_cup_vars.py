import pandas as pd

event_name = "world_cup"

GCS_FILE_PATH = (
    f"gs://calitp-analytics-data/data-analyses/transit_event_analysis/{event_name}/"
)

# 2026-06-12 starts -5 ; 2026-07-10 ends + 5
event_start_end = ("2026-06-07", "2026-07-15")

event_date_range = pd.date_range(
    start=event_start_end[0],
    end=event_start_end[1],
)

# add this to get date filtering to work, unsure how to use STRUCT in parameter
# bigquery.ArrayParameter has error if not values and array_type in {"RECORD", "STRUCT"}:
event_date_range = [pd.to_datetime(c) for c in event_date_range]

sofi_dates = [
    "2026-06-12",
    "2026-06-15",
    "2026-06-18",
    "2026-06-21",
    "2026-06-25",
    "2026-06-28",
    "2026-07-02",
    "2026-07-10",
]

sofi_match_times = {
    **{
        d: "midday"
        for d in ["2026-06-18", "2026-06-21", "2026-06-28", "2026-07-02", "2026-07-10"]
    },
    **{d: "pm_peak" for d in ["2026-06-12", "2026-06-15", "2026-06-25"]},
    # night matches are a bit tricky, can span pm_peak to evening, but use the start time to determine
}

socal_names = [
    "LA Metro Events Schedule",
    "LA Metro Bus Schedule",
    "LA Metro Rail Schedule",
    "LA DOT Schedule",
    "G Trans Schedule",
    "Torrance Schedule",
    "Inglewood Schedule",
    "Beach Cities GMV Schedule",
    "Big Blue Bus Schedule",
    "Big Blue Bus Swiftly Schedule",
    "Culver City Schedule",
    "Metrolink Schedule",
]

# special routes to filter for
# notebook to visually inspect and populate these
special_socal_routes_dict = {
    "LA Metro Bus Schedule": None,  # thought 22 was Los Angeles Stadium Express, can't find
    "LA Metro Events Schedule": [
        "10__ S10 Harbor Gateway Transit Center",
        "11__ S11 LAX/Metro Transit Center",
        "12__ S12 Hotels & Parking LAX",
        "13__ T13 Pierce College Station",
        "14__ T14 Downtown Santa Monica",
        "15__ T15 North Hollywood Station",
        "1__ R1 El Camino College",
        "2__ R2 Union Station",
        "3__ R3 Crenshaw Station",
        "4__ R4 Hawthorne/Lennox Station",
        "5__ R5 Downtown Long Beach",
        "6__ R6 ARTIC Anaheim Station",
        "7__ R7 Newport Transportation Center",
        "8__ S8 Torrance Transit Center",
        "9__ S9 Culver City Transit Center",
    ],
    "LA DOT Schedule": ["712__DASH Chesterfield Square"],  # route map
    "G Trans Schedule": ["7X__7X Line 7X"],
    "Torrance Schedule": ["10__10 LINE 10"],
    "Inglewood Schedule": None,  # can't find inglewood?
    "Beach Cities GMV Schedule": None,
    "Big Blue Bus Schedule": [
        "T14__T14 Los Angeles Stadium"
    ],  # said no, but saw route name that does
    "Culver City Schedule": None,  # couldn't find 99X
    "Metrolink Schedule": [
        "91 Line__91-PV Line Metrolink 91-Perris Valley Line",
        "Antelope Valley Line__AV Line Metrolink Antelope Valley Line",
        "Orange County Line__OC Line Metrolink Orange County Line",
        "Riverside Line__RIV Line Metrolink Riverside Line",
        "San Bernardino Line__SB Line Metrolink San Bernardino Line",
        "Ventura County Line__VC Line Metrolink Ventura County Line",
    ],
    "LA Metro Rail Schedule": ["803__ Metro C Line", "807__ Metro K Line"],
}

levi_dates = [
    "2026-06-13",
    "2026-06-16",
    "2026-06-19",
    "2026-06-22",
    "2026-06-25",
    "2026-07-01",
]

levi_match_times = {
    **{d: "midday" for d in ["2026-06-13"]},
    **{d: "pm_peak" for d in ["2026-06-25", "2026-07-01"]},
    **{d: "evening" for d in ["2026-06-16", "2026-06-19", "2026-06-22"]},
}

bay_area_names = [
    "SCVTA Schedule",
    "Bay Area 511 Santa Clara Transit Schedule",
    "BART Schedule",
    "Bay Area 511 BART Schedule",
    "Caltrain Schedule",
    "Bay Area 511 Caltrain Schedule",
    "San Joaquin Schedule",  # is this needed?
    "ACE Schedule",
    "Bay Area 511 ACE Schedule",
    "Capitol Corridor Schedule",
    "Bay Area 511 Capitol Corridor Schedule",
    "Amtrak Schedule",
]

special_bayarea_routes_dict = {
    "SCVTA Schedule": [
        "BBSB__BBWC Bus Bridge WC26",  # route chart
        "BlueS__BlueS Blue Line WC26",  # route chart
        "Blue__Blue Line Baypointe - Santa Teresa",  # get regular one
        "GrenS__GreenS Green Line WC26",  # route chart
        "Green__Green Line Old Ironsides - Winchester",  # get regular one
        "OranE__OrangeE Orange Line East Segment WC26",  # route chart
        "OranW__OrangeW Orange Line West Segment WC26",  # route chart
        "Ornge__Orange Line Mountain View - Alum Rock",  # get regular one
    ],
    "Bay Area 511 Santa Clara Transit Schedule": [
        "BBWC__BBWC Bus Bridge WC26",  # route chart
        "BlueS__BlueS Blue Line WC26",  # route chart
        "Blue Line__Blue Line Baypointe - Santa Teresa",  # get regular one
        "GreenS__GreenS Green Line WC26",  # route chart
        "Green Line__Green Line Old Ironsides - Winchester",  # get regular one
        "OrangeE__OrangeE Orange Line East Segment WC26",  # route chart
        "OrangeW__OrangeW Orange Line West Segment WC26",  # route chart
        "Orange Line__Orange Line Mountain View - Alum Rock",  # get regular one
    ],
    "BART Schedule": None,
    "Bay Area 511 BART Schedule": None,
    "Bay Area 511 Caltrain Schedule": [
        "South County__South County South Santa Clara County Connector",  # unlikely based on chart, but maybe based on name
        "Local Weekday__Local Weekday",  # route chart
        "Local Weekend__Local Weekend",  # route chart
    ],  # Special trains with direct service to the Santa Clara-Great America Station
    "Bay Area 511 ACE Schedule": [
        "ACE__Altamont Commuter Express"
    ],  # Special trains with direct service to the Santa Clara-Great America Station adjacent to the stadium (around 0.2 to 0.3 miles).
    "Bay Area 511 Capitol Corridor Schedule": [
        "CC__CC Capitol Corridor"
    ],  # Increased capacity on Capitol Corridor routes serving the tournament crowds.
}
