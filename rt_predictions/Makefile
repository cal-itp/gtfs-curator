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

stop_report:
	python download_warehouse_tables.py
	# things that should be done before report is run, but probably can't make it into dbt model
	# save it out as parquet
	python prep_data_for_viz.py
	python deploy_portfolio_yaml.py rt_msa_stops --month 2026-01-01
	cd ../portfolio/ && pip install -r requirements.txt && cd ../
	gcloud auth login --login-config=iac/login.json && gcloud config set project cal-itp-data-infra # will need to authenticate this step
	python portfolio/portfolio.py build rt_trip_updates_stop_metrics --hide-title-block --deploy --target staging
	python portfolio/portfolio.py index --deploy --no-prod

operator_report:
	#python download_warehouse_tables.py
	# things that should be done before report is run, but probably can't make it into dbt model
	# save it out as parquet
	#python prep_data_for_viz.py
	#python deploy_portfolio_yaml.py rt_msa_operators --month 2026-01-01
	#cd ../portfolio/ && pip install -r requirements.txt && cd ../
	cd ../ && python portfolio/portfolio.py clean rt_operator_metrics
	gcloud auth login --login-config=iac/login.json && gcloud config set project cal-itp-data-infra # will need to authenticate this step
	#python portfolio/portfolio.py build rt_operator_metrics --hide-title-block
	# still set H1, hide title instead
	python portfolio/portfolio.py build rt_operator_metrics --no-execute-papermill --hide-title-block --deploy --target production
	python portfolio/portfolio.py index --deploy --no-prod