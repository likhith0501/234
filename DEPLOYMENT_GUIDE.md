# HepatoX - Deployment Guide

This guide provides step-by-step instructions to deploy HepatoX to Render with Neon PostgreSQL.

## Prerequisites

Before you begin, ensure you have:
1. GitHub account (to host your repository)
2. Render account (https://render.com) - Free tier available
3. Neon account (https://console.neon.tech) - Free PostgreSQL database

## Step 1: Prepare Your Repository

### 1.1 Initialize Git Repository (if not already done)
```bash
cd HepatoX
git init
git add .
git commit -m "Initial commit - HepatoX application"
```

### 1.2 Create .env File (for local development)
```bash
cp .env.example .env
```

Update `.env` with your local settings:
```
SECRET_KEY=your-development-secret-key
DATABASE_URL=sqlite:///instance/hepatox.db
FLASK_ENV=development
DEBUG=True
```

### 1.3 Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/hepatox.git
git branch -M main
git push -u origin main
```

## Step 2: Create Neon PostgreSQL Database

1. Go to https://console.neon.tech
2. Sign up or log in to your account
3. Click "Create a new project"
4. Enter project details:
   - Project name: `hepatox`
   - Database name: `hepatox`
   - Region: Select closest to your users
5. Click "Create project"
6. After creation, you'll see the connection string. Copy it:
   ```
   postgresql://neon_user:password@host/hepatox
   ```

## Step 3: Deploy to Render

### 3.1 Connect GitHub Repository

1. Go to https://render.com
2. Sign up or log in
3. Click "New +" → "Web Service"
4. Connect your GitHub repository:
   - Authorize Render to access GitHub
   - Select your `hepatox` repository
   - Branch: `main`

### 3.2 Configure Web Service

Fill in the deployment form:

**Name:**
```
hepatox
```

**Environment:**
```
Python
```

**Build Command:**
```
pip install -r requirements.txt && python train_models.py
```

**Start Command:**
```
gunicorn app:app
```

**Plan:**
```
Free (or Paid if you want better performance)
```

### 3.3 Set Environment Variables

In the "Environment" section, add the following variables:

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Generate a random string (use: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | Your Neon connection string from Step 2 |
| `DEFAULT_ADMIN_USERNAME` | `admin` |
| `DEFAULT_ADMIN_EMAIL` | `admin@hepatox.com` |
| `DEFAULT_ADMIN_PASSWORD` | Change this to a secure password! |

**Example DATABASE_URL:**
```
postgresql://neon_user:your_secure_password@host-region.neon.tech/hepatox
```

### 3.4 Deploy

1. Review all settings
2. Click "Create Web Service"
3. Render will start building and deploying
4. Wait for the deployment to complete (usually 10-15 minutes on first deployment)
5. Once complete, you'll see a URL like: `https://hepatox-xxxx.onrender.com`

## Step 4: Monitor Deployment

### 4.1 View Logs
In Render dashboard:
1. Click your web service
2. Go to "Logs" tab
3. Monitor for any errors

### 4.2 Check Database Connection
Look for these logs:
```
Database initialized
✓ Model training completed
```

## Step 5: Initial Setup

### 5.1 First Login
1. Go to your Render URL: `https://hepatox-xxxx.onrender.com`
2. Use default credentials:
   - Username: `admin`
   - Password: (your `DEFAULT_ADMIN_PASSWORD`)

### 5.2 Change Admin Password
1. After login, go to Profile settings
2. Change the default password

### 5.3 Generate Sample Data
1. Navigate to Admin → Models
2. If no models are trained, the system will train them on first deployment

## Step 6: Custom Domain (Optional)

To use a custom domain:

1. In Render dashboard, go to your service settings
2. Click "Add Custom Domain"
3. Follow DNS configuration instructions
4. Point your domain DNS to Render's nameservers

## Troubleshooting

### Issue: "No PostgreSQL driver detected"
**Solution:** Update Render's Build Command:
```
pip install -r requirements.txt psycopg2-binary && python train_models.py
```

### Issue: Database connection fails
**Solution:**
1. Verify `DATABASE_URL` is correct in Render environment variables
2. Check Neon console for database status
3. Ensure firewall allows Render's IP ranges

### Issue: Models not trained
**Solution:**
1. Model training happens on first deployment (takes 10-15 minutes)
2. Check logs in Render dashboard
3. If still stuck, restart the service

### Issue: Out of memory on Free tier
**Solution:**
1. Upgrade to a Starter Plus plan ($12/month)
2. Or split training into a separate one-time job

## Database Backups

### Automatic Backups (Neon)
Neon automatically backs up your data. To restore:
1. Go to Neon console
2. Go to Branches → backup branch
3. Restore from backup

### Manual Backup
Export data from Neon:
```bash
pg_dump postgresql://user:password@host/hepatox > backup.sql
```

## Monitoring & Maintenance

### Monitor Application Health
1. Render provides basic monitoring
2. Set up email alerts for crashes
3. Monitor database usage in Neon console

### Update Dependencies
To update packages in production:
```bash
# Update requirements.txt locally
pip install --upgrade <package>
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```
Render will automatically redeploy.

### Scale Application
If traffic increases:
1. In Render, increase number of replicas
2. Monitor database performance in Neon
3. Consider upgrading Neon tier for more connections

## Security Checklist

- [ ] Changed default admin password
- [ ] Set strong SECRET_KEY
- [ ] Using HTTPS (Render provides free HTTPS)
- [ ] Database URL with strong password
- [ ] Firewall rules configured (if applicable)
- [ ] Regular database backups enabled
- [ ] Monitor logs for suspicious activity

## Post-Deployment

### 1. Test Key Features
- [ ] Login works
- [ ] Can register new patient
- [ ] Can make predictions
- [ ] Can view dashboard
- [ ] Admin panel accessible

### 2. Set Up Monitoring
- [ ] Check Render status page
- [ ] Monitor error logs
- [ ] Set up alerts

### 3. Documentation
- [ ] Update README with production URL
- [ ] Document any customizations
- [ ] Share credentials securely with team

## Scaling Strategy

### Free Tier (Current)
- Limited resources
- Sufficient for testing/small deployments
- Auto-sleeps after 15 minutes of inactivity

### Starter Plus ($12/month)
- Always on
- Shared resources
- Good for small production deployments

### Professional ($29/month+)
- More resources
- Auto-scaling
- Dedicated support
- Suitable for production applications

## Getting Help

- Render Support: https://render.com/docs
- Neon Documentation: https://neon.tech/docs
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com
- GitHub Issues: Report bugs in your repository

## Rollback Strategy

If something goes wrong:

1. **Recent deployments:** Click "Rollback" in Render to previous version
2. **Database issue:** Restore from Neon backup
3. **Complete reset:** Delete service, create new one with same environment variables

## Cost Estimation

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Render Web Service | Free (with limits) | $12/month+ |
| Neon PostgreSQL | Free (up to 3 projects) | $8/month+ |
| **Total** | **Free** | **~$20/month** |

## Next Steps

1. ✅ Deploy application
2. ✅ Test all features
3. ✅ Set up monitoring
4. ✅ Configure backups
5. ✅ Share with team
6. ✅ Monitor performance
7. ✅ Plan for scaling

---

**Congratulations!** Your HepatoX application is now live on Render! 🚀

For additional support or customization, refer to the main README.md file.
