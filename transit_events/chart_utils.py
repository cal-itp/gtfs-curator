import altair as alt
import pandas as pd


def event_date_rule_chart(list_of_dates: list):
    """
    add a vertical line for specific dates, get it formatted correctly for altair axis
    https://github.com/vega/altair/issues/2379
    """
    date_df = pd.DataFrame({"service_date": list_of_dates, "color": "gray"})

    date_df.service_date = pd.to_datetime(date_df.service_date).dt.normalize()

    rules = (
        alt.Chart(date_df)
        .mark_rule(strokeDash=[12, 6], size=2)
        .encode(x="service_date:T", color=alt.Color("color:N", scale=None))
    )
    return rules


def trip_chart_with_event_dates(
    trips_df: pd.DataFrame, list_of_dates: list, color_col: str = "schedule_name"
) -> alt.Chart:
    """
    instead of point=True, can set the fill to white.
    https://altair-viz.github.io/user_guide/marks/line.html
    """
    selection = alt.selection_point(fields=[color_col], bind="legend")

    if color_col == "schedule_name":
        color_title = "GTFS Schedule Name"
        color_scheme = "plasma"
    elif color_col == "route_name":
        color_title = "Route Name"
        color_scheme = "category20"

    trips_chart = (
        alt.Chart(trips_df)
        .mark_line(point=alt.OverlayMarkDef(filled=False, fill="white"))
        .encode(
            x=alt.X("service_date:T", title="date"),
            y=alt.Y("n_trips:Q", title="Daily Trips"),
            color=alt.Color(
                f"{color_col}:N",
                title=color_title,
                scale=alt.Scale(scheme=color_scheme),
            ),
            tooltip=["service_date", color_col, "n_trips"],
            opacity=alt.when(selection).then(alt.value(1)).otherwise(alt.value(0.1)),
        )
        .interactive()
        .add_params(selection)
    )

    rules = event_date_rule_chart(list_of_dates)

    chart = trips_chart + rules

    return chart


def change_arrivals_by_operator(
    df: pd.DataFrame,
    one_operator: str,
    y_col: str,
) -> alt.Chart:

    # do aggregation here, to add a bit of buffer around x-axis edges
    operator_df = df[df.schedule_name == one_operator].reset_index(drop=True)

    metric_title = y_col.split("_")[0].title()

    # horiz bar chart, but stop_name as y-axis
    chart = (
        alt.Chart(operator_df)
        .mark_bar()
        .encode(
            x=alt.X(
                f"sum({y_col})",
                title=f"{metric_title} Service Change",
            ),
            y=alt.Y(
                "stop_name",
                title="Stop Name",  # sort="-x"
            ),
            color=alt.Color(
                "route_id_array:N", title="Routes", scale=alt.Scale(scheme="viridis")
            ),
            tooltip=[
                "schedule_name",
                "stop_name",
                "route_id_array",
                y_col,
                "n_stop_ids",
            ],
        )
        .interactive()
    )

    vertical_line = (
        alt.Chart()
        .mark_rule(strokeDash=[12, 6], size=2, color="gray")
        .encode(x=alt.datum(0))
    ).interactive()

    return chart + vertical_line


def weekday_weekend_chart_by_operator(df: pd.DataFrame, one_operator: str) -> alt.Chart:
    weekday_chart = change_arrivals_by_operator(
        df, one_operator, y_col="weekday_change_daily_arrivals"
    ).properties(title="Weekday")

    weekend_chart = change_arrivals_by_operator(
        df, one_operator, y_col="weekend_change_daily_arrivals"
    ).properties(title="Weekend")

    combined_chart = (
        alt.hconcat(weekday_chart, weekend_chart)
        .properties(
            title={
                "text": one_operator,
                "subtitle": "Sum of World Cup stop arrivals for routes with planned service changes vs regular service",
            }
        )
        .resolve_scale(y="shared", x="independent")
        .interactive()
    )

    return combined_chart
