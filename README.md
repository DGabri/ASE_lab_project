# Chess Heroes 

This repo contains the project for the UNIPI Advanced Software Engineering course.

The project members are:
- Deri Gabriele
- Turchetti Gabriele

## Description

The project consists of a gacha game where the gacha items are pieces of chess. A player can buy a packet where it can pull diverse pieces with specific probabilities, or it can obtain the pieces joining the audicions created by other players.

## Get Started
This section will explain how to run the microservices, execute unit and integration tests.

## Microservices start
To run the microservices:

```
cd server
docker compose up
```

## Integration tests
To execute integration tests please run the same command as the previous section. Before starting the build please remove all previous volumes and images so that the service starts with a fresh environment. This is needed so that we do not get errors when creating a new user which could result in a duplicate user.

```
cd server
docker compose down -v
docker compose up
```

Now import you are ready to import the Postman collections in postman. You can find collections exported in JSON format under `docs/tests/integration_test`. After having imported the collection first execute the integration test for auth, user and auction so that a fresh enviroment is available for user creation.

Execute in this order:
1. `docs/tests/integration_test/User.Auth.Auction.postman_collection.json`
2. 

## Unit tests

First, remove all previouse volumes and restart new tests (in case you had already executed tests):

- `docker compose -f docker-compose-unit-tests.yml down -v `

To build and execute all tests in isolation: 

- `docker compose -f docker-compose-unit-tests.yml up --build`

You are now ready to import the collections in Postman and execute them. This time order is not important but a fresh environment is needed

### Client

To install the dependencies for the client:
```
cd client/chess-heroes
npm install
```

To run the client from the chess-heroes folder:
```
npm start
```

### Tests

## Architecture

<img src="./assets/architecture.png">