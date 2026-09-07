# Project1
# Helping Mandarin speakers learn phrasal verbs

## Mandarin speakers learning English often develop advanced vocabularies
and are competent in tasks which involve formal language, however may
struggle grasping colloquial phrases and idioms.

## Status - app functional, backend dockerized.

## Goal - To build an app which helps Mandarin speakers learn to use and understand colloquial phrases and expressions, through a 2-stage process. Contextual introduction with an opportunity for the learner to guess the meaning and then have the answer revealed, and then, AI conversation practice. As well as practicing implementation of AI to help solve real language learning problems.

## Tech stack -

| Layer     | Choice                              |
|-----------|--------------------------------------|
| Frontend  | HTML, CSS, JavaScript               |
| Backend   | Python (Flask)                      |
| Database  | SQLite                              |
| Hosting   | AWS EC2, Docker, nginx              |
| AI        | Claude API                          |

##Dockerizing - 07/09/26
Started by writing new dockerfile, then building the file to create an image and finally pushing that image.
## Base image - Python 3.14-slim, chose this as the app is written in Python/Flask and 3.14 matches local development version and slim version keeps image size smaller
##Problems faced - .env file could not be accessed by the container so I had to tell Docker to read the file and put all the variables into the container's environment
Also, host was binding to wrong port, which meant nothing could be received from outside the container. To solve this, I changed the port to 0.0.0.0 so everything from network was accepted.
## How to build and run it - 
To build the image: docker build -t phrasal-verbs-app -f Dockerfile.new .
To run the image: docker run -p 5000:5000 --env-file .env phrasal-verbs-app
(Then go to http://localhost:5000 to confirm it is working)
