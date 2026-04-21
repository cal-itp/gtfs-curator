"""
Utility functions for geospatial data.
Some functions for dealing with census tract or other geographic unit dfs.
"""
from typing import Literal, Union

import geopandas as gpd  # type: ignore
import numpy as np
import pandas as pd
import shapely  # type: ignore

from scipy.spatial import KDTree

WGS84 = "EPSG:4326"
CA_NAD83Albers_ft = "ESRI:102600"  # units are in feet
CA_NAD83Albers_m = "EPSG:3310"  # units are in meters

SQ_MI_PER_SQ_M = 3.86 * 10**-7
FEET_PER_MI = 5_280
SQ_FT_PER_SQ_MI = 2.788 * 10**7


# Laurie's example: https://github.com/cal-itp/data-analyses/blob/752eb5639771cb2cd5f072f70a06effd232f5f22/gtfs_shapes_geo_examples/example_shapes_geo_handling.ipynb
# have to convert to linestring
def make_linestring(x: str) -> shapely.geometry.LineString:
    # shapely errors if the array contains only one point
    if len(x) > 1:
        # each point in the array is wkt
        # so convert them to shapely points via list comprehension
        as_wkt = [shapely.wkt.loads(i) for i in x]
        return shapely.geometry.LineString(as_wkt)

def create_point_geometry(
    df: pd.DataFrame,
    longitude_col: str = "stop_lon",
    latitude_col: str = "stop_lat",
    crs: str = WGS84,
) -> gpd.GeoDataFrame:
    """
    Parameters:
    df: pandas.DataFrame to turn into geopandas.GeoDataFrame,
        default dataframe in mind is gtfs_schedule.stops

    longitude_col: str, column name corresponding to longitude
                    in gtfs_schedule.stops, this column is "stop_lon"

    latitude_col: str, column name corresponding to latitude
                    in gtfs_schedule.stops, this column is "stop_lat"

    crs: str, coordinate reference system for point geometry
    """
    # Default CRS for stop_lon, stop_lat is WGS84
    df = df.assign(
        geometry=gpd.points_from_xy(df[longitude_col], df[latitude_col], crs=WGS84)
    )

    # ALlow projection to different CRS
    gdf = gpd.GeoDataFrame(df).to_crs(crs)

    return gdf


def create_segments(
    geometry: Union[
        shapely.geometry.linestring.LineString,
        shapely.geometry.multilinestring.MultiLineString,
    ],
    segment_distance: int,
) -> gpd.GeoSeries:
    """
    Splits a Shapely LineString into smaller LineStrings.
    If a MultiLineString passed, splits each LineString in that collection.

    Input a geometry column, such as gdf.geometry.

    Double check: segment_distance must be given in the same units as the CRS!

    Use case:
    gdf['segment_geometry'] = gdf.apply(
        lambda x:
        create_segments(x.geometry, int(segment_length)),
        axis=1,
    )

    gdf2 = explode_segments(
        gdf,
        group_cols = ['route_key'],
        segment_col = 'segment_geometry'
    )
    """
    lines = []

    if hasattr(geometry, "geoms"):  # check if MultiLineString
        linestrings = geometry.geoms
    else:
        linestrings = [geometry]

    for linestring in linestrings:
        for i in range(0, int(linestring.length), segment_distance):
            lines.append(shapely.ops.substring(linestring, i, i + segment_distance))

    return lines


def explode_segments(
    gdf: gpd.GeoDataFrame, group_cols: list, segment_col: str = "segment_geometry"
) -> gpd.GeoDataFrame:
    """
    Explode the column that is used to store segments, which is a list.
    Take the list and create a row for each element in the list.
    We'll do a rough rank so we can order the segments.

    Use case:
    gdf['segment_geometry'] = gdf.apply(
        lambda x:
        create_segments(x.geometry, int(segment_length)),
        axis=1,
    )

    gdf2 = explode_segments(
        gdf,
        group_cols = ['route_key'],
        segment_col = 'segment_geometry'
    )
    """
    gdf_exploded = gdf.explode(segment_col).reset_index(drop=True)

    gdf_exploded["temp_index"] = gdf_exploded.index

    gdf_exploded = gdf_exploded.assign(
        segment_sequence=(
            gdf_exploded.groupby(
                group_cols, observed=True, group_keys=False
            ).temp_index.transform("rank")
            - 1
            # there are NaNs, but since they're a single segment, just use 0
        )
        .fillna(0)
        .astype("int16")
    )

    # Drop the original line geometry, use the segment geometry only
    gdf_exploded2 = (
        gdf_exploded.drop(columns=["geometry", "temp_index"])
        .rename(columns={segment_col: "geometry"})
        .set_geometry("geometry")
        .set_crs(gdf_exploded.crs)
        .sort_values(group_cols + ["segment_sequence"])
        .reset_index(drop=True)
    )

    return gdf_exploded2


# Could we use distance to filter for nearest neighbor?
# It can make the length of results more unpredictable...maybe we stick to
# k_neighbors and keep the nearest k, so that we can at least be
# more consistent with the arrays returned
geo_const_meters = 6_371_000 * np.pi / 180
geo_const_miles = 3_959_000 * np.pi / 180

def try_parallel(geometry):
    try:
        return geometry.parallel_offset(30, "right")
    except Exception:
        return geometry


def arrowize_segment(line_geometry, buffer_distance: int = 20):
    """Given a linestring segment from a gtfs shape,
    buffer and clip to show direction of progression"""
    arrow_distance = buffer_distance  # was buffer_distance * 0.75
    st_end_distance = arrow_distance + 3  # avoid floating point errors...
    try:
        segment = line_geometry.simplify(tolerance=5)
        if segment.length < 50:  # return short segments unmodified, for now
            return segment.buffer(buffer_distance)
        arrow_distance = max(arrow_distance, line_geometry.length / 20)
        shift_distance = buffer_distance + 1

        begin_segment = shapely.ops.substring(segment, 0, st_end_distance)
        r_shift = begin_segment.parallel_offset(shift_distance, "right")
        r_pt = shapely.ops.substring(r_shift, 0, 0)
        l_shift = begin_segment.parallel_offset(shift_distance, "left")
        l_pt = shapely.ops.substring(l_shift, 0, 0)
        end = shapely.ops.substring(
            begin_segment,
            begin_segment.length + arrow_distance,
            begin_segment.length + arrow_distance,
        )
        poly = shapely.geometry.Polygon((r_pt, end, l_pt))  # triangle to cut bottom of arrow
        # ends to the left
        end_segment = shapely.ops.substring(segment, segment.length - st_end_distance, segment.length)
        end = shapely.ops.substring(end_segment, end_segment.length, end_segment.length)  # correct
        r_shift = end_segment.parallel_offset(shift_distance, "right")
        r_pt = shapely.ops.substring(r_shift, 0, 0)
        r_pt2 = shapely.ops.substring(r_shift, r_shift.length, r_shift.length)
        l_shift = end_segment.parallel_offset(shift_distance, "left")
        l_pt = shapely.ops.substring(l_shift, 0, 0)
        l_pt2 = shapely.ops.substring(l_shift, l_shift.length, l_shift.length)
        t1 = shapely.geometry.Polygon((l_pt2, end, l_pt))  # triangles to cut top of arrow
        t2 = shapely.geometry.Polygon((r_pt2, end, r_pt))

        segment_clip_mask = shapely.geometry.MultiPolygon((poly, t1, t2))

        # buffer, then clip segment with arrow shape
        differences = segment.buffer(buffer_distance).difference(segment_clip_mask)
        # # of resulting geometries, pick largest (actual segment, not any scraps...)
        areas = [x.area for x in differences.geoms]
        for geom in differences.geoms:
            if geom.area == max(areas):
                return geom
    except Exception:
        return line_geometry.simplify(tolerance=5).buffer(buffer_distance)


def nearest_snap(line: Union[shapely.LineString, np.ndarray], point: shapely.Point, k_neighbors: int = 1) -> np.ndarray:
    """
    Based off of this function,
    but we want to return the index value, rather than the point.
    https://github.com/UTEL-UIUC/gtfs_segments/blob/main/gtfs_segments/geom_utils.py
    """
    if isinstance(line, shapely.LineString):
        line = np.asarray(line.coords)
    elif isinstance(line, np.ndarray):
        line = line
    point = np.asarray(point.coords)
    tree = KDTree(line)

    # np_dist is array of distances of result (let's not return it)
    # np_inds is array of indices of result
    _, np_inds = tree.query(
        point,
        workers=-1,
        k=k_neighbors,
    )

    return np_inds.squeeze()


def vp_as_gdf(vp: pd.DataFrame, crs: str = "EPSG:3310") -> gpd.GeoDataFrame:
    """
    Turn vp as a gdf and project to EPSG:3310.
    """
    vp_gdf = (
        create_point_geometry(vp, longitude_col="x", latitude_col="y", crs=WGS84)
        .to_crs(crs)
        .drop(columns=["x", "y"])
    )

    return vp_gdf


def add_arrowized_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Add a column where the segment is arrowized.
    """
    segment_geom = gpd.GeoSeries(gdf.geometry)
    CRS = gdf.crs.to_epsg()

    # TODO: parallel_offset is going to be deprecated? offset_curve is the new one
    geom_parallel = gpd.GeoSeries([try_parallel(i) for i in segment_geom], crs=CRS)
    # geom_parallel = gpd.GeoSeries(
    #    [i.offset_curve(30) for i in segment_geom],
    #    crs=CRS
    # )

    geom_arrowized = arrowize_segment(geom_parallel, buffer_distance=20)

    gdf = gdf.assign(geometry_arrowized=geom_arrowized)

    return gdf


def get_direction_vector(start: shapely.geometry.Point, end: shapely.geometry.Point) -> tuple:
    """
    Given 2 points (in a projected CRS...not WGS84), return a
    tuple that shows (delta_x, delta_y).

    https://www.varsitytutors.com/precalculus-help/find-a-direction-vector-when-given-two-points
    https://stackoverflow.com/questions/17332759/finding-vectors-with-2-points

    """
    return ((end.x - start.x), (end.y - start.y))


def distill_array_into_direction_vector(array: np.ndarray) -> tuple:
    """
    Given an array of n items, let's take the start/end of that.
    From start/end, we can turn 2 coordinate points into 1 distance vector.
    Distance vector is a tuple that equals (delta_x, delta_y).
    """
    origin = array[0]
    destination = array[-1]
    return get_direction_vector(origin, destination)


def get_vector_norm(vector: tuple) -> float:
    """
    Get the length (off of Pythagorean Theorem) by summing up
    the squares of the components and then taking square root.

    Use Pythagorean Theorem to get unit vector. Divide the vector
    by the length of the vector to get unit/normalized vector.
    This equation tells us what we need to divide by.
    """
    return np.sqrt(vector[0] ** 2 + vector[1] ** 2)


def get_normalized_vector(vector: tuple) -> tuple:
    """
    Apply Pythagorean Theorem and normalize the vector of distances.
    https://stackoverflow.com/questions/21030391/how-to-normalize-a-numpy-array-to-a-unit-vector
    """
    x_norm = vector[0] / get_vector_norm(vector)
    y_norm = vector[1] / get_vector_norm(vector)

    return (x_norm, y_norm)


def dot_product(vec1: tuple, vec2: tuple) -> float:
    """
    Take the dot product. Multiply the x components, the y components, and
    sum it up.
    """
    return vec1[0] * vec2[0] + vec1[1] * vec2[1]


def segmentize_by_indices(line_geometry: shapely.LineString, start_idx: int, end_idx: int) -> shapely.LineString:
    """
    Cut a line according to index values.
    Similar to shapely.segmentize, which allows you to cut
    line according to distances.
    Here, we don't have specified distances, but we want to customize
    where segment the line.
    """
    all_coords = shapely.get_coordinates(line_geometry)

    if end_idx + 1 > all_coords.size:
        subset_coords = all_coords[start_idx:end_idx]
    else:
        subset_coords = all_coords[start_idx : end_idx + 1]

    if len(subset_coords) < 2:
        return shapely.LineString()
    else:
        return shapely.LineString([shapely.Point(i) for i in subset_coords])


def draw_line_between_points(gdf: gpd.GeoDataFrame, group_cols: list) -> gpd.GeoDataFrame:
    """
    Use the current postmile as the
    starting geometry / segment beginning
    and the subsequent postmile (based on odometer)
    as the ending geometry / segment end.

    Segment goes from current to next postmile.
    """
    # Grab the subsequent point geometry
    # We can drop whenever the last point is missing within
    # a group. If we have 3 points, we can draw 2 lines.
    gdf = gdf.assign(end_geometry=(gdf.groupby(group_cols, group_keys=False, dropna=False).geometry.shift(-1))).dropna(
        subset="end_geometry"
    )

    # Construct linestring with 2 point coordinates
    gdf = (
        gdf.assign(
            line_geometry=gdf.apply(
                lambda x: shapely.LineString([x.geometry, x.end_geometry]), 
                axis=1
            ).set_crs(WGS84)
        )
        .drop(columns=["geometry", "end_geometry"])
        .rename(columns={"line_geometry": "geometry"})
    )

    return gdf


def convert_to_gdf(
    df: pd.DataFrame, 
    geom_col: str,
    geom_type: Literal["point", "line"]
) -> gpd.GeoDataFrame:
    """
    For stops, we want to make pt_geom a point.
    For vp_path and shapes, we want to make pt_array a linestring.
    """
    if geom_type == "point":
        df["geometry"] = [shapely.wkt.loads(x) for x in df[geom_col]]

    elif geom_type == "line":
        df["geometry"] = df[geom_col].apply(make_linestring)

    gdf = gpd.GeoDataFrame(
        df.drop(columns = geom_col), geometry="geometry", 
        crs="EPSG:4326"
    )

    return gdf

