.PHONY: test-setup test images mocks pull-images

test-setup: pull-images mocks images egg-info

pull-images:
	docker pull jamesdbloom/mockserver:mockserver-5.2.3
	docker pull p0bailey/docker-flask
	docker pull rabbitmq
	docker pull swaggerapi/swagger-validator
	docker pull wazopbx/wait
	docker pull wazopbx/wazo-auth
	docker pull wazopbx/wazo-auth-db
	docker pull wazopbx/wazo-auth-mock
	docker pull wazopbx/wazo-dird
	docker pull wazopbx/wazo-dird-db

mocks:
	docker build --no-cache -t oauth2-synchronization-service -f assets/external_auth/oauth2_synchronization_service/Dockerfile assets/external_auth/oauth2_synchronization_service

images:
	docker build --no-cache -t wazo-auth-google-test -f Dockerfile-auth-google-test ..
	docker build --no-cache -t wazo-dird-google-test -f Dockerfile-dird-google-test ..

egg-info:
	cd .. && python3 setup.py egg_info

test:
	pytest -x
