add_precommit:
	pip install pre-commit
	pre-commit install
	#pre-commit run --all-files

install_env:
	cd _gtfs_curator_shared_utils/ && pip install -r requirements.txt && cd ../
