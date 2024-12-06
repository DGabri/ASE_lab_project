# Chess Heroes 

This repo contains the project for the UNIPI Advanced Software Engineering course.

The project members are:
- Deri Gabriele
- Turchetti Gabriele

## Description

The project consists of a gacha game where the gacha items are pieces of chess. A player can buy a packet where it can pull diverse pieces with specific probabilities, or it can obtain the pieces joining the audicions created by other players.

## Get Started
In this section it's explained how to run the application (both backend and frontend).

### Run the Backend
To run the backend:

```
cd server
docker compose up
```

### Run the client
First it's needed to install the dependencies for the client. So, from the project forlder:

```
cd client/chess-heroes
npm install
```

To run the client from the chess-heroes folder:

```
npm start
```

## Tests
In this section it's explained how to perform unit, integration and performance tests.

### Unit Tests
First remove all previous volumes and images (if you had already executed unit tests):

```
cd server
docker compose -f docker-compose-unit-tests.yml down -v
```

Then, to build the docker compose and run the backend: 

```
docker compose -f docker-compose-unit-tests.yml up
```

In order to perform unit tests you have to import the collections in Postman (from the folder `docs/tests/unit_tests`) and execute them. The order of the individual collections is not important, but a fresh environment is needed.

### Integration Tests
Before starting the build remove all volumes and images from the unit tests (if you had executed them), so that the service starts with a fresh environment:

```
cd server
docker compose -f docker-compose-unit-tests.yml down -v
```

This is needed so that we do not get errors when creating a new user which could result in a duplicate user. Then, to perform the integration tests:

```
docker compose -f docker-compose-tests.yml down -v
docker compose -f docker-compose-tests.yml up
```

In order to perform unit tests you have to import the collections in Postman (from the folder `docs/tests/integration_tests`) and execute them. The order of the individual collections is not important, but a fresh environment is needed.

### Performance Tests

As the integration tests, to run the performance tests it's needed to clean the environment from the previous tests (if they were made). So:

```
docker compose -f docker-compose-tests.yml down -v
docker compose -f docker-compose-tests.yml up
```

Now go to the performance_tests forder and run the first collection of tests:
```
cd docs/tests/performance_tests
locust
```

The host is `https://localhost:3000`.

For the distribution tests:

```
locust -f locustfile_distribution.py
```

The distribution of the last test is written in output when the test stops. The distribution is rappresented by a dictionary where the keys are the grade of the pieces pulled (`C` for common, `R` for rare and `SR` for super rare).

## Architecture

<img src="./assets/architecture.png">