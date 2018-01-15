default: run

upgrade: install
	
install:
	python3 -m venv .virtualenv
	./ve pip install --upgrade pip
	./ve pip install --upgrade wheel
	./shell_scripts/hass_upgrade.sh
	
check_config:
	./ve hass -c . --script check_config
	
commit:
	./shell_scripts/git_commit.sh

run:
	./shell_scripts/hass_start.sh

run_daemon:
	nohup ./shell_scripts/hass_start.sh > /dev/null 2>&1 &

stop:
	- ./shell_scripts/hass_stop.sh
	exit 0

restart: stop run_daemon