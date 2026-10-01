import folium
import geopandas as gpd
import pandas as pd
import polars as pl
from great_tables import GT


def make_wide_by_service_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Set this up for polars df to use with nanoplots
    """

    df2 = (
        df.sort_values(["schedule_name", "route_name", "direction_id", "service_date"])
        .groupby(["schedule_name", "route_name", "direction_id"])
        .agg(
            {
                # "service_date": lambda x: list(pd.to_datetime(x).dt.date),
                "n_trips": lambda x: list(x),
                "num_stop_times": lambda x: list(x),
                "avg_stops_served": lambda x: list(x),
            }
        )
        .reset_index()
    )

    return pl.from_pandas(df2)


def simple_nanoplot(df):

    table = (
        GT(df)
        .fmt_nanoplot("n_trips")
        .fmt_nanoplot("num_stop_times")
        .fmt_nanoplot("avg_stops_served")
    )
    return table


def add_stadium_layer(poi: gpd.GeoDataFrame, m: folium.Map):
    # https://stackoverflow.com/questions/73317052/geopandas-explore-how-to-set-marker-icon
    # https://fontawesome.com/v4/icons/
    # must take format "fa fa-[name_of_icon]"
    # example of marker: https://python-visualization.github.io/folium/latest/user_guide/geojson/geojson_marker.html

    specific_icon = "fa fa-building"  # fa fa-home

    m = poi.explore(
        "point_of_interest",
        m=m,
        marker_type="marker",
        name="SoFi Stadium",
        marker_kwds=dict(icon=folium.DivIcon(class_name="mapIcon")),
        style_kwds=dict(
            style_function=lambda x: {
                "html": f"""<span   class=f"{specific_icon}" 
                                    style="color:orange;
                                    font-size:14px"></span>"""
            },
        ),
    )

    return m
