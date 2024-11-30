To build and execute all tests in isolation: 

- `docker compose -f docker-compose-unit-tests.yml up --build`

To remove all volumes and restart new tests (before rebuilding):

- `docker compose -f docker-compose-unit-tests.yml down -v `