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
	python download_warehouse_tables.py
	quarto convert marin_operator.ipynb # update the yaml snippet
	quarto render marin_operator.qmd


test_operator_report:
	cd ../ && python portfolio/portfolio.py clean test_tu
	cd ../ && python portfolio/portfolio.py build test_tu
	gcloud auth login --login-config=iac/login.json && gcloud config set project cal-itp-data-infra
	cd ../ && python portfolio/portfolio.py build test_tu --no-execute-papermill --hide-title-block --deploy --target staging
	cd ../ && python portfolio/portfolio.py index --deploy --no-prod
