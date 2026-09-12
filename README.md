# Project1
# Helping Mandarin speakers learn phrasal verbs

Mandarin speakers learning English often develop advanced vocabularies and are competent in tasks which involve formal language, however may struggle grasping colloquial phrases and idioms.

## Goal
To build an app which helps Mandarin speakers learn to use and understand colloquial phrases and expressions, through a 2-stage process: contextual introduction with an opportunity for the learner to guess the meaning and have the answer revealed, followed by AI conversation practice. As well as practicing implementation of AI to help solve real language learning problems.

## Status
App functional, backend Dockerized, deployed to a local Kubernetes cluster (Minikube), with real AWS infrastructure now provisioned via Terraform (app not yet deployed onto it).

## Tech stack

| Layer     | Choice                    |
|-----------|---------------------------|
| Frontend  | HTML, CSS, JavaScript     |
| Backend   | Python (Flask)            |
| Database  | SQLite                    |
| Hosting   | AWS EC2, Docker, nginx    |
| AI        | Claude API                |

## Dockerizing - 07/09/26
Started by writing a new Dockerfile, then built it to create an image and ran it as a container.

**Base image**: python:3.14-slim - chose this since the app is written in Python, matching the local development version.

**Problems faced**:
- The `.env` file couldn't be accessed by the container - fixed by passing `--env-file .env` at run time.
- The host was binding to the wrong address, meaning nothing could be received from outside the container - fixed by changing `app.run(debug=True)` to `app.run(host='0.0.0.0', debug=True)`.

**How to build and run it**:
```bash
docker build -t phrasal-verbs-app -f Dockerfile.new .
docker run -p 5000:5000 --env-file .env phrasal-verbs-app
```
Then visit `http://localhost:5000` to confirm it's working.

## Kubernetes Deployment
Deployed the Dockerized app to a local Minikube cluster - a Deployment (3 replicas, liveness/readiness health probes), a NodePort Service for external access, and a Secret holding the Anthropic API key (loaded via `envFrom`, replacing the plain `.env` file approach used with Docker alone).

**Tested and confirmed**:
- Self-healing - deleted a pod manually, confirmed Kubernetes automatically created a replacement.
- Scaling - adjusted replicas up and down live, confirmed pod count updated correctly both directions.

**Problems hit**: the same environment-variable issue from the Docker stage reappeared in a new form - Kubernetes pods have no automatic access to a local `.env` file either. Solved properly this time with a Kubernetes Secret rather than a workaround.

## Infrastructure (Terraform)
Provisioned real AWS infrastructure as code: a VPC with a public subnet, internet gateway, route table, a security group (SSH restricted to my own IP, HTTP open publicly), and an EC2 instance (Ubuntu, t3.micro - Free Tier eligible) using a Terraform `data` source to dynamically fetch the latest official Ubuntu AMI rather than hardcoding one.

Verified by SSHing directly into the provisioned instance.

**Problems hit**:
- `t2.micro` was rejected as not Free Tier eligible on this account/region - confirmed the correct type via the AWS CLI (`aws ec2 describe-instance-types --filters "Name=free-tier-eligible,Values=true"`) and switched to `t3.micro`.
- Quoted resource references in an early draft (e.g. `"data.aws_ami.ubuntu.id"`) were silently treated as literal strings instead of actual references, causing the apply to fail.

**Not yet done**: deploying the app itself onto this instance - this phase focused on getting the underlying infrastructure right first.
