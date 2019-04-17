.PHONY: build-oauth2-sync test-setup test test-image test-prerequisite test-db

test-setup: test-prerequisite build-mocks test-images egg-info

test-prerequisite:
	docker pull p0bailey/docker-flask
	docker pull rabbitmq
	docker pull swaggerapi/swagger-validator
	docker pull wazopbx/wait
	docker pull wazopbx/wazo-auth
	docker pull wazopbx/wazo-auth-db
	docker pull wazopbx/wazo-auth-mock
	docker pull wazopbx/wazo-dird
	docker pull wazopbx/wazo-dird-db

build-mocks:
	docker build --no-cache -t oauth2-synchronization-service -f assets/external_auth/oauth2_synchronization_service/Dockerfile assets/external_auth/oauth2_synchronization_service
	docker build --no-cache -t google-mock -f assets/external_auth/google-mock/Dockerfile assets/external_auth/google-mock

test-images:
	docker build --no-cache -t wazo-auth-google-test -f Dockerfile-auth-google-test ..
	docker build --no-cache -t wazo-dird-google-test -f Dockerfile-dird-google-test ..

egg-info:
	cd .. && python3 setup.py egg_info

test:
	pytest -x
