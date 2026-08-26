digest_report:
	make gtfs_digest_data
	make operator_report_portfolio

gtfs_digest_data:
	uv run python _prep_crosswalk_ntd.py
	uv run python _load_gtfs_data.py
	uv run python _prep_gtfs_data.py
	uv run python _publish_public_data.py
	uv run python deploy_portfolio_yaml.py

operator_report_portfolio:
	# uv run calitp-portfolio build gtfs_digest.yml --hide-title-block --limit 4 # use this for dry run
	uv run calitp-portfolio build gtfs_digest.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy gtfs_digest.yml --target staging
	uv run calitp-portfolio deploy gtfs_digest.yml --target prod

district_report_portfolio:
	#uv run python deploy_district_yaml.py # only run script if yaml changes
	# uv run calitp-portfolio build district_digest.yml --hide-title-block --limit 4 # use this for dry run
	uv run calitp-portfolio build district_digest.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy district_digest.yml --target staging
	uv run calitp-portfolio deploy district_digest.yml --target prod

legislative_report_portfolio:
	uv run python _legislative_district_prep.py
	# uv run calitp-portfolio build legislative_district_digest.yml --hide-title-block --limit 4 # use this for dry run
	# benchmark build times: 30 seconds per district, up to 120 districts (118), deploy is about 2-3 minutes
	uv run calitp-portfolio build legislative_district_digest.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy legislative_district_digest.yml --target staging
	uv run calitp-portfolio deploy legislative_district_digest.yml --target prod
