# Chess Heroes

## Description 

This repo contains the project for the UNIPI Advanced Software Engineering course.

The project members are:
- Deri Gabriele
- Parlanti Massimo
- Turchetti Gabriele

The game consists of a gacha game where the gacha items are pieces of chess. A player can buy a packet where it can pull diverse pieces with specific probabilities, or it can obtain the pieces joining the audicions created by other players. It is also possible to delete a player account

## Architecture

<img src="./assets/architecture.png" width="500">

## Modules

### Players

With this module is possible to retrieve, add and modify information about the players. The information about the players concerns the basic data of the account (e.g. name and e-mail), the collection of pieces, the auctions created and won, the payment history and the transactions of the in-game currency.

The APIs for this module are:
- /player [POST]
- /player/{player_id} [GET]
- /player/{player_id} [PUT]
- /player/{player_id} [DELETE]
- /player/collection/{player_id} [GET]
- /player/collection/{player_id} [PUT]
- /player/auction/won/{player_id} [GET]
- /player/auction/created/{player_id} [GET]
- /player/payment/history/{player_id} [GET]
- /player/payment/{player_id} [POST]
- /player/gold/{player_id} [PUT]
- /player/gold/history/{player_id} [GET]
- /player/all [GET]

### Admin

With this module is possible to retrive and add information about the admin, specifically the actions of the admin.

The APIs for this module are:
- /admin/{admin_id} [GET]
- /admin/log/history/{admin_id} [GET]
- /admin/log/{admin_id} [POST]

### Banners

With this module is possible to get, add, modify and delete information about the banners. It is also possible to perform pull action by the players.

This module is composed by 2 components:
1. The first component operate as an interface for the banners database
2. The second component execute the business logic about the pull actions made by a player.

The APIs for this module are:
- /banner [POST]
- /banner/{banner_id} [GET]
- /banner/{banner_id} [PUT]
- /banner/{banner_id} [DELETE]
- /banner/pull/{banner_id} [GET]

### Auctions

With this module is possible to get, add and modify information about the auctions. It is also possible to create and close auctions, retrieve all the running auctions or specific for a piece and make a bid for one of these.

This module is composed by 3 components:
1. The first component operate as a interface for the auctions database
2. The second component execute the business logic about the management of the auctions
3. The third component has the task to periodically see if an auction must be closed, and in that case call the function of the second component that manage the closure of that auction

The APIs for this module are:
- /auction [POST]
- /auction/{auction_id} [GET]
- /auction/{auction_id} [PUT]
- /auction/history [GET]
- /auction/running [GET]
- /auction/running/{pieces_id} [GET]
- /auction/bid/{auction_id} [POST]

### Pieces

This module operates as an interface for the pieces database. With this module is possible to get, add and modify information about the pieces.

The APIs for this module are:
- /piece [GET]
- /piece [POST]
- /piece/{piece_id} [PUT]
- /piece/all [GET]

### Auth

This module allows the players and the admin to register, log in and log out to the system.

The APIs for this module are:
- /auth/register [POST]
- /auth/login [POST]
- /auth/logout [POST]

### Payments

This module allows the players to buy the internal currency of the game with real money.

The API for this module is:
- /payment/buy [POST]
