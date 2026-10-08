from gtfs_curator_utils import bq_utils
from world_cup_vars import GCS_FILE_PATH

if __name__ == "__main__":
    """
    # use this to debug World Cup anomolies
    # LA Metro Rail, SCVTA
    world_cup_debug_dict = {
        "service_date": ["2026-07-12"],
        "feed_key": [
            "d062b23c6635fcf9b07204533e1b8e83",  # SCVTA
            "0b2690d82204cbfcb0558ca5b156d1cc",  # LA Metro Rail
        ],
    }


    bq_utils.download_table(
        sql_query="SELECT * FROM `cal-itp-data-infra.mart_gtfs.fct_scheduled_trips`",
        filter_dict=world_cup_debug_dict,
        output_path=f"{GCS_FILE_PATH}fct_scheduled_trips_2026-07-12.parquet",
    )
    """

    # add bq_utils to take custom job config, sql stuff, slightly different for cases like this
    # instead of using additional_sql
    bq_utils.download_table(
        sql_query="""
            SELECT 
                key AS gtfs_dataset_key,
                name,
                type,
                _valid_from,
                _valid_to
            FROM `cal-itp-data-infra.mart_transit_database.dim_gtfs_datasets`
            WHERE CONTAINS_SUBSTR(name, 'LA Metro Rail') OR CONTAINS_SUBSTR(name, 'SCVTA')
            """,
        filter_dict={},
        output_path=f"{GCS_FILE_PATH}debug_dim_gtfs_datasets.parquet",
    )
