.PHONY: test test-unit test-integration test-shell test-clean

test:
	docker compose --profile test up --build --abort-on-container-exit --exit-code-from test test; \
	EXIT_CODE=$$?; \
	docker compose --profile test rm -s -f -v test postgres-test redis-test; \
	exit $$EXIT_CODE

test-unit:
	docker compose --profile test run --rm test pytest tests/unit

test-integration:
	docker compose --profile test run --rm test pytest tests/integration

test-shell:
	docker compose --profile test run --rm test bash

test-clean:
	docker compose --profile test rm -s -f -v test postgres-test redis-test
