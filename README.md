# Chess Heroes

## Description 

This repo contains the project for the UNIPI Advanced Software Engineering course.

The project members are:
- Deri Gabriele
- Parlanti Massimo
- Turchetti Gabriele

The project consists in a gacha game where the gacha items are the pieces of chess. A player can buy a packet where it can pull diverse pieces with specific probabilities, or it can obtain the pieces joining the audicions created by other players.

## Microservices

### Players

This module operate as an interface for the players database. With this module is possible to retrieve, add and modify informations about the players.

The APIs for this module are:
- /player/{player_id}
- /player/collection/{player_id}
- /player/auction/won/{player_id}
- /player/auction/created/{player_id}
- /player/payment/history/{player_id}
- /player/payment/{player_id}
- /player/gold/{player_id}
- /player/gold/history/{player_id}
- /player/all

### Admin

This module operate as an interface for the admin database. With this module is possible to retrive and add informations about the admin, specifically the actions of the admin.

The APIs for this module are:
- /admin/{admin_id}
- /admin/log/history/{admin_id}
- /admin/log/{admin_id}

### Banners

This module is composed by 2 components:
1. The first component operate as an interface for the banners database
2. The second component execute the business logic about the pull actions made by a player.

The APIs for this module are:
- /banner
- /banner/{banner_id}
- /banner/pull/{banner_id}

### Auctions

This module is composed by 3 components:
1. The first component operate as a interface for the auctions database
2. The second component execute the business logic about the managment of the auctions
3. The third component has the task to periodically see if an auction have to be closed, and in that case call the fuction of the second component that manage the closure of that auction

The APIs for this module are:
- /auction
- /auction/{auction_id}
- /auction/history
- /auction/running
- /auction/running/{pieces_id}
- /auction/bid/{auction_id}

### Pieces

This module operate as an interface for the pieces database.

The APIs for this module are:
- /piece
- /piece/{piece_id}
- /piece/all

### Auth

This module allow the players and the admin to register, log in and log out to the system.

The APIs for this module are:
- /auth/register
- /auth/login
- /auth/logout

### Payments

This module allow the players to buy the internal currency of the game with real money.

The API for this module is:
- /payment/buy
