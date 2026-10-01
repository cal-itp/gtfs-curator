download_data:
	uv run python extract_feeds.py
	uv run python filter_fct_gtfs.py
	uv run python filter_dim_gtfs.py
	uv run python prep_service_alerts.py

clean_data:
	uv run python create_poi_gdf.py
	uv run python create_route_and_stop_event_summary.py

report:
	uv run calitp-portfolio build transit_events.yml	
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy transit_events.yml --target prod