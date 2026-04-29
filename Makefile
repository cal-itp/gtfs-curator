add_precommit:
	pip install pre-commit
	pre-commit install
	#pre-commit run --all-files

install_env:
	cd _gtfs_curator_utils/ && pip install -r requirements.txt && cd ../
	cd _rt_msa_utils/ && pip install -r requirements.txt && cd ../


setup_uv:
	cd _gtfs_curator_utils/ && pip install -r requirements.txt && cd ../
