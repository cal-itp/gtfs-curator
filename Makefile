add_precommit:
	pip install pre-commit
	pre-commit install
	#pre-commit run --all-files

install_env:
	cd _gtfs_curator_utils/ && pip install -r requirements.txt && cd ../
	make add_precommit

install_env_uv:
	pip install uv && uv sync

# Build and Deploy Production Portfolio Site with:
# make build_production_portfolio_site site='MY_SITE_IDENTIFIER'
build_production_portfolio_site:
	cd portfolio/ && pip install -r requirements.txt
	python portfolio/portfolio.py clean $(site)
	python portfolio/portfolio.py build $(site)
	gcloud auth login --login-config=iac/login.json && gcloud config set project cal-itp-data-infra
	python portfolio/portfolio.py build $(site) --no-execute-papermill --deploy --target production
	git add portfolio/sites/$(site).yml
	python portfolio/portfolio.py index --deploy --prod

# Build and Deploy Staging Portfolio Site with:
# make build_staging_portfolio_site site='MY_SITE_IDENTIFIER'
build_staging_portfolio_site:
	cd portfolio/ && pip install -r requirements.txt
	python portfolio/portfolio.py clean $(site)
	gcloud auth login --login-config=iac/login.json
	python portfolio/portfolio.py build $(site)
	#python portfolio/portfolio.py build $(site) --no-execute-papermill --deploy --target staging
	python portfolio/portfolio.py index --deploy --no-prod


build_production_portfolio_site_uv:
	uv sync --group portfolio
	uv run python portfolio/portfolio.py clean $(site)
	uv run python portfolio/portfolio.py build $(site)
	gcloud auth login --login-config=iac/login.json && gcloud config set project cal-itp-data-infra
	uv run python portfolio/portfolio.py build $(site) --no-execute-papermill --deploy --target production
	git add portfolio/sites/$(site).yml
	#make build_production_portfolio_index

build_staging_portfolio_site_uv:
	uv sync --group portfolio
	uv run python portfolio/portfolio.py clean $(site)
	gcloud auth login --login-config=iac/login.json
	uv run python portfolio/portfolio.py build $(site)
	uv run python portfolio/portfolio.py build $(site) --no-execute-papermill --deploy --target staging
	#make build_staging_portfolio_index

# need this to make sure index properly builds
# the index includes sites that others have deployed, and I'm making changes to just 1 site
# do this first, then make changes to 1 site for deploy
copy_portfolio_sites_for_index:
	cp ../data-analyses/portfolio/sites/ portfolio/ -r
