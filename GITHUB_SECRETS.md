# GitHub Actions Secrets Configuration for HepatoX CI/CD
#
# Instructions: Add these secrets to your GitHub repository
# Settings → Secrets and variables → Actions → New repository secret
#
# Production Deployment Secrets:
# ============================================

# Render.com Configuration
RENDER_API_KEY=your-render-api-key
RENDER_SERVICE_ID=your-render-service-id
RENDER_DEPLOY_HOOK=your-render-deploy-webhook

# Heroku Configuration (Alternative)
HEROKU_API_KEY=your-heroku-api-key
HEROKU_APP_NAME=your-heroku-app-name

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/hepatox
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=hepatox

# Application Secrets
SECRET_KEY=your-very-long-secret-key
FLASK_ENV=production

# Cloud Provider Credentials
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket-name

# Monitoring & Notifications
SLACK_WEBHOOK=your-slack-webhook-url
SENTRY_DSN=your-sentry-dsn-url

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# API Keys
OPENWEATHER_API_KEY=optional-api-keys
EXTERNAL_API_KEY=optional-external-services

# Testing & Coverage
CODECOV_TOKEN=your-codecov-token

# Docker Registry (if using container deployments)
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
DOCKER_REGISTRY=docker.io

# To add these secrets:
# 1. Go to your repository on GitHub
# 2. Click Settings → Secrets and variables → Actions
# 3. Click "New repository secret"
# 4. Add each secret name and value
# 5. These will be available in GitHub Actions as ${{ secrets.SECRET_NAME }}
