download_data:
	uv run python extract_feeds.py
	uv run python filter_fct_gtfs.py
	uv run python filter_dim_gtfs.py

clean_data:
	uv run python C1_service_by_route.py
	uv run python C2_service_by_stop.py

report:
	uv run calitp-portfolio build transit_events.yml	
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy transit_events.yml --target prod