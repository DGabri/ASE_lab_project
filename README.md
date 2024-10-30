# Chess Heroes 

This repo contains the project for the UNIPI Advanced Software Engineering course.

The project members are:
- Deri Gabriele
- Parlanti Massimo
- Turchetti Gabriele

## Description

The game consists of a gacha game where the gacha items are pieces of chess. A player can buy a packet where it can pull diverse pieces with specific probabilities, or it can obtain the pieces joining the audicions created by other players.

## Architecture

<img src="./assets/architecture.png" width="500">

## Modules

### Players

With this module is possible to retrieve, add and modify information about the players. The information about the players concerns the basic data of the account (e.g. name and e-mail), the collection of pieces, the auctions created and won, the payment history and the transactions of the in-game currency. It is also possible for a player to delete his account.

### Admin

With this module is possible to retrive and add information about the admin, specifically the actions of the admin.

### Banners

With this module is possible to get, add, modify and delete information about the banners. It is also possible to perform pull action by the players.

This module is composed by 2 components:
1. The first component operate as an interface for the banners database
2. The second component execute the business logic about the pull actions made by a player.

### Auctions

With this module is possible to get, add and modify information about the auctions. It is also possible to create and close auctions, retrieve all the running auctions or specific for a piece and make a bid for one of these.

This module is composed by 3 components:
1. The first component operate as a interface for the auctions database
2. The second component execute the business logic about the management of the auctions
3. The third component has the task to periodically see if an auction must be closed, and in that case call the function of the second component that manage the closure of that auction

### Pieces

This module operates as an interface for the pieces database. With this module is possible to get, add and modify information about the pieces.

### Auth

This module allows the players and the admin to register, log in and log out to the system.

### Payments

This module allows the players to buy the internal currency of the game with real money.
