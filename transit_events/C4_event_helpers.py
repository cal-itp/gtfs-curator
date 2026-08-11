import pandas as pd


def tag_event_days_and_times(df: pd.DataFrame, event_day_time_bucket_dict: dict):

    # fix the dict to work with datetime
    # hard to set this dict up correctly with dtypes
    event_day_time_bucket_dict = {
        pd.to_datetime(k): v for k, v in event_day_time_bucket_dict.items()
    }

    df = df.assign(
        event_day=df.apply(
            lambda x: (
                True
                if x.service_date in list(event_day_time_bucket_dict.keys())
                else False
            ),
            axis=1,
        ),
        day_type=df.apply(
            lambda x: "weekend" if x.service_date.dayofweek >= 5 else "weekday", axis=1
        ),
        event_time_of_day=df.service_date.map(event_day_time_bucket_dict).fillna(
            "non_event_day"
        ),
    )

    return df
