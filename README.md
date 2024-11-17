# distributed-recommendation-system

```
aws ec2 create-key-pair --key-name movie-rec-key --query 'KeyMaterial' --output text > movie-rec-key.pem
chmod 400 movie-rec-key.pem
```

```
cd deploy/terraform
terraform init
terraform apply
terraform output
```

For master nodes:
```
ssh -i movie-rec-key.pem ec2-user@<master_public_ip>

# Clone your repository
git clone <your-repo-url>
cd <repo-directory>

# Create .env file
cat > .env << EOL
REDIS_HOST=<redis_private_ip>
MONGODB_HOST=<mongodb_private_ip>
EOL

# Start master service
docker-compose -f docker-compose.aws.yml up -d master
```

For worker nodes:
```
ssh -i movie-rec-key.pem ec2-user@<worker_public_ip>

# Clone repository and start worker
git clone <your-repo-url>
cd <repo-directory>

# Create .env file
cat > .env << EOL
REDIS_HOST=<redis_private_ip>
MONGODB_HOST=<mongodb_private_ip>
EOL

# Start worker service
docker-compose -f docker-compose.aws.yml up -d worker
```


test 
```
curl -X POST http://<master_public_ip>:5000/similar \
  -H "Content-Type: application/json" \
  -d '{"movie_name": "The Dark Knight"}'
```
