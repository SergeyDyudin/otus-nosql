#! /bin/bash

docker exec mongo mongoimport --db meflix --collection comments --file /mongo_import/comments.json
docker exec mongo mongoimport --db meflix --collection movies --file /mongo_import/movies.json
docker exec mongo mongoimport --db meflix --collection sessions --file /mongo_import/sessions.json
docker exec mongo mongoimport --db meflix --collection theaters --file /mongo_import/theaters.json
docker exec mongo mongoimport --db meflix --collection users --file /mongo_import/users.json
