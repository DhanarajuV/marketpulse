# AWS Deployment Guide — MarketPulse

Deploy MarketPulse as a scheduled ECS Fargate task with DynamoDB storage.

## Architecture

```
EventBridge (8AM & 1PM EST, Mon-Fri)
    │
    ▼
ECS Fargate (spins up container)
    │
    ▼
run_scan.py → DynamoDB (save signals) → Telegram (send alerts)
    │
    ▼
Container shuts down (you stop paying)
```

## Prerequisites

- AWS account
- GitHub repo with this code pushed
- API keys ready: Google Gemini, Finnhub, Telegram Bot Token + Chat ID

---

## Step 1: Get VPC and Subnet IDs

You need these for CloudFormation. Every AWS account has a default VPC.

1. Go to **AWS Console → VPC → Your VPCs**
2. Copy the **VPC ID** of the default VPC (e.g., `vpc-0abc123def456`)
3. Go to **VPC → Subnets**
4. Copy any **public subnet ID** from the default VPC (e.g., `subnet-0abc123def456`)
   - Make sure "Auto-assign public IPv4" is Yes, or pick one in an AZ you prefer

---

## Step 2: Deploy CloudFormation Stack

This creates: DynamoDB table, ECR repo, ECS cluster, task definition, EventBridge rules, IAM roles.

1. Go to **AWS Console → CloudFormation → Create Stack → With new resources**
2. Choose **Upload a template file** → upload `infra/cloudformation.yaml`
3. Click **Next**
4. Fill in parameters:

| Parameter | Value |
|-----------|-------|
| EnvironmentName | `marketpulse` (or leave default) |
| GoogleApiKey | Your Gemini API key |
| FinnhubApiKey | Your Finnhub API key |
| TelegramBotToken | Your bot token from @BotFather |
| TelegramChatId | Your chat ID |
| MarketPulseApiKey | Any random string (or leave empty) |
| VpcId | From Step 1 |
| SubnetId | From Step 1 |

5. Click **Next** → Next
6. Check **"I acknowledge that AWS CloudFormation might create IAM resources with custom names"**
7. Click **Submit**
8. Wait for status: `CREATE_COMPLETE` (~2-3 minutes)

---

## Step 3: Create IAM User for GitHub Actions

GitHub needs permission to push Docker images to ECR.

1. Go to **AWS Console → IAM → Users → Create user**
2. Name: `github-ecr-push`
3. Attach policy — create an inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:us-east-1:YOUR_ACCOUNT_ID:repository/marketpulse"
    }
  ]
}
```

4. Create the user → **Security credentials** → **Create access key** → Choose "Third-party service"
5. Save the **Access Key ID** and **Secret Access Key**

---

## Step 4: Add GitHub Secrets

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | From Step 3 |
| `AWS_SECRET_ACCESS_KEY` | From Step 3 |

---

## Step 5: Push Code & Trigger Build

```bash
git add .
git commit -m "AWS deployment: ECS Fargate + DynamoDB"
git push -u origin aws-deployment
```

This triggers the `deploy-ecr.yml` workflow which:
1. Builds the Docker image
2. Pushes it to ECR

Check progress: GitHub repo → **Actions** tab

---

## Step 6: Verify

1. **Check ECR image**: AWS Console → ECR → `marketpulse` → should see an image tagged `latest`
2. **Test manually**: AWS Console → ECS → Clusters → `marketpulse` → Run task
   - Launch type: FARGATE
   - VPC, Subnet, Security Group: same as in CloudFormation
   - Enable public IP
   - Run → check CloudWatch Logs for output
3. **Wait for schedule**: EventBridge will trigger at 8AM and 1PM EST on weekdays
4. **Check Telegram**: You should receive alerts (or "No signals" message)

---

## Monitoring

- **Logs**: CloudWatch → Log groups → `/ecs/marketpulse`
- **Task history**: ECS → Clusters → `marketpulse` → Tasks (stopped)
- **DynamoDB data**: DynamoDB → Tables → `marketpulse-signals` → Explore items
- **EventBridge**: EventBridge → Rules → check last invocation

---

## Costs

| Service | Monthly Cost |
|---------|-------------|
| ECS Fargate (2 runs/day × 3 min) | ~$0.10 |
| DynamoDB (free tier: 25GB) | $0 |
| ECR (5 images × ~500MB) | ~$0.25 |
| CloudWatch Logs | ~$0 (minimal) |
| EventBridge | $0 |
| **Total** | **~$0.35/month** |

---

## Updating the App

Just push to `aws-deployment`:

```bash
# Make code changes
git add .
git commit -m "description of change"
git push
```

GitHub Actions rebuilds and pushes a new image. The next scheduled ECS task will use the updated image automatically.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Task fails immediately | Check CloudWatch Logs for Python errors |
| No Telegram alerts | Verify TELEGRAM_BOT_TOKEN and CHAT_ID in CloudFormation params |
| "Access Denied" on DynamoDB | Check TaskRole has DynamoDB permissions |
| GitHub Actions fails | Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY secrets |
| Image not found | Make sure ECR repo name matches (`marketpulse`) |
| Task timeout | Increase CPU/Memory in CloudFormation TaskDefinition |
