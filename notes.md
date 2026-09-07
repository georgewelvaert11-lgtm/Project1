07/09/26- tried to run phrasal-verbs-app image however it didnt work as Flask was only accepting connections from 127.0.0.1, this needed to be changed to 0.0.0.0 so that connections from any network interface would be accepted

##Dockerizing the phrasal verbs app
-Wrote Dockerfile from scratch, following template from Claude
-Hit error as .env didnt automatically pass into containers
-Fixed with docker run --env-file .env
-At first app said localhost didnt send any data cos Flask wasnt reachable from outside the container
-
