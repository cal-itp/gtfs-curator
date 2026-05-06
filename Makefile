add_precommit:
	pip install pre-commit
	pre-commit install
	#pre-commit run --all-files

install_env:
	cd _gtfs_curator_utils/ && pip install -r requirements.txt && cd ../

install_env_uv:
	pip install uv && uv sync
