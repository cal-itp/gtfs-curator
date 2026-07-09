digest_report:
	make gtfs_digest_data
	#make portfolio_deploy

portfolio_deploy:
	#python deploy_portfolio_yaml.py

gtfs_digest_data:
	uv run python _prep_crosswalk_ntd.py
	uv run python _load_gtfs_data.py
	#python _prep_gtfs_data.py
	#python _publish_public_data.py

legislative_digest:
	uv run python _legislative_district_prep.py
