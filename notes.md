07/09/26- tried to run phrasal-verbs-app image however it didnt work as Flask was only accepting connections from 127.0.0.1, this needed to be changed to 0.0.0.0 so that connections from any network interface would be accepted

##Dockerizing the phrasal verbs app
-Wrote Dockerfile from scratch, following template from Claude
-Hit error as .env didnt automatically pass into containers
-Fixed with docker run --env-file .env
-At first app said localhost didnt send any data cos Flask wasnt reachable from outside the container

##Kubernetes set up
-INstalled kubectl and minikube
- Started local cluster with minikube start --driver=docker
- Then checked nodes with kubectl get nodes and the only existing node (Minikube) was labelled as Notready, after waiting a minute or so it showed to be Ready.

##First Kubernets deployment attempt
-Wrote yaml file
- Sent yaml file to k8s cluster, creating actual Deployment object
-At first it said 1 pod was ready then shortly after it said none
-As predicted, pods crashed due to KeyError due to missing API Key, this means Kubernetes Secret needs ti be added and referenced in the Deployment yaml

##Kubernetes Secrets setup + fixing error
-Created secret: kubectl secret generic phrasal-verbs-secret --from-env=.env
- Then added envFrom.secretRef to deployment.yaml and referenced the secret
- Used kubectl apply -f deployment.yaml and it resulted in all 3 pods ready 

##Kubernetes service.yaml written and applied and deployment working
-Created service.yaml with Nodeport type to expose the app to external traffic
-Confirmed apps loading in browser (used minikube service phrasal-verbs-service --url)

##Health probes - added to deployment.yaml later on
## Scaling replicas up and down and observing Deployments ability to maintain desired number of replicas
- Using kubectl scale deployment phrasal-verbs-app --replicas= (desired number of replicas) for temporary change which will be restored back to amount stated in deployment.yaml when next apply occurs
- Or to more permanently change replica number, edit deployment.yaml manually

- Then, separately, did kubectl delete pod <pod name> in one tab and kubectl get pods --watch in another tab to see Deployment restore actual number of replicas to number stated in deployment.yaml

## Terraform (IaC)
- Installed Terraform (sudo snap install terraform --classic)
- Installed AWS CLI (sudo apt install awscli)
- Learned the full theory first before writing anything: HCL blocks (resource/provider/variable/output/data), resource type vs name, the core workflow (init/plan/apply/destroy), state (Terraform's own record of what it created, and how it can drift from real AWS reality), variables, outputs, and dependencies between resources
- Hit a genuine access problem: original AWS account (ID 568898409779) became inaccessible - MFA locked, unrecoverable
- Created a fresh AWS account (ID 281712468499)
- Set up MFA properly on this new account (authenticator app)
- Created an IAM user, attached AdministratorAccess
- Generated an Access Key ID + Secret Access Key
- Ran aws configure locally, entered those credentials, region eu-west-2
- Confirmed it works via aws sts get-caller-identity
- Wrote main.tf defining a full network + server setup: VPC, public subnet, internet gateway, route table + association, security group (SSH restricted to my own IP, HTTP open to all), an SSH key pair, and an EC2 instance - used a `data` block to dynamically look up the latest official Ubuntu AMI rather than hardcoding one, so the config doesn't go stale over time
- Problems hit and fixed:
  1. First draft had a duplicate aws_instance block, plus resource references wrapped in quotes (e.g. "data.aws_ami.ubuntu.id") - quoting a reference turns it into a literal string instead of an actual reference, causing it to fail
  2. t2.micro was rejected as not Free Tier eligible for this account/region - confirmed the actual eligible type via `aws ec2 describe-instance-types --filters "Name=free-tier-eligible,Values=true"`, switched to t3.micro
- Ran terraform init -> plan -> apply successfully - confirmed real infrastructure created by SSHing directly into the new instance
- Instance is currently provisioned but has no app deployed on it yet - next step (not done yet) would be installing Docker and running the phrasal-verbs app container on this real infrastructure
