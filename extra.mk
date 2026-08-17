.PHONY: bump-upload test-python3

bump-upload:
	$(MAKE) bump
	$(MAKE) upload

test-python3:
	docker stop quickapp-python3 || true
	docker rm quickapp-python3 || true
	docker run -it -v "$(shell realpath $(PWD)):/quickapp" -w /quickapp --name quickapp-python3 python:3 /bin/bash
