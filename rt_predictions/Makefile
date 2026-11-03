create_marin_bq_tables:
	# this is view, filter and save
	uv run dbt run -s int_gtfs_rt__trip_updates_trip_stop_day_map_grouping_marin

	# pass these along
	uv run dbt run -s fct_stop_time_metrics_marin
	uv run dbt run -s fct_trip_updates_stop_metrics_marin
	uv run dbt run -s fct_trip_updates_trip_metrics_marin

	uv run dbt run -s fct_daily_schedule_rt_route_direction_summary_marin # this one had to be updated because prod column name changed
	uv run dbt run -s fct_monthly_schedule_rt_route_direction_summary_marin

	uv run dbt run -s fct_daily_schedule_rt_operator_summary_marin # add extra subsetting in parent tables
	uv run dbt run -s fct_monthly_operator_summary_marin

marin_report:
	python download_warehouse_tables_marin.py
	quarto convert marin_operator.ipynb # update the yaml snippet
	quarto render marin_operator.qmd

rt_download_data:
	uv run python download_warehouse_tables.py

stop_report:
	# things that should be done before report is run, but probably can't make it into dbt model
	# save it out as parquet
	python prep_data_for_viz.py
	python deploy_stops_yaml.py

operator_report:
	# things that should be done before report is run, but probably can't make it into dbt model
	# save it out as parquet
	uv run python prep_data_for_viz.py
	uv run python deploy_operator_yaml.py
	# uv run calitp-portfolio build rt_operator_metrics.yml --hide-title-block --limit 2 # use this for dry run
	uv run calitp-portfolio build rt_operator_metrics.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy rt_operator_metrics.yml --target staging
	uv run calitp-portfolio deploy rt_operator_metrics.yml --target prod

convert_nb_to_qmd:
	uv run quarto convert operator_report.ipynb