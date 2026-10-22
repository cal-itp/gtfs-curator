"""
Create the points of interest gdf.

Can be points, lines, polygons.
For World Cup stadiums, set the points.
Could be used for drawing buffers around a neighborhood,
taking CA county boundary, Caltrans district boundary.
"""

import geopandas as gpd
import google.auth
import pandas as pd
from gtfs_curator_utils import utils
from gtfs_curator_utils.geography_utils import WGS84
from world_cup_vars import GCS_FILE_PATH, event_name

credentials, _ = google.auth.default()


def create_stadiums_poi_gdf(points_dict: dict) -> gpd.GeoDataFrame:
    df = pd.DataFrame(
        {
            "point_of_interest": [label for label, xy_point in points_dict.items()],
            "latitude": [xy_point[1] for label, xy_point in points_dict.items()],
            "longitude": [xy_point[0] for label, xy_point in points_dict.items()],
        }
    )

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=WGS84
    ).drop(columns=["longitude", "latitude"])

    return gdf


if __name__ == "__main__":
    # Set the stadium points
    stadium_points_dict = {
        "SoFi Stadium": (-118.338635, 33.953304),
        "Levi's Stadium": (-121.969342, 37.403294),
    }
    stadium_gdf = create_stadiums_poi_gdf(stadium_points_dict)

    utils.geoparquet_gcs_export(
        stadium_gdf, GCS_FILE_PATH, f"points_of_interest_{event_name}"
    )
