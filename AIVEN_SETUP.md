# Aiven Cloud Database Setup Guide

This guide explains how to set up the SkillBridge MySQL database on Aiven Cloud (free tier).

## Why Aiven?

- **Free Tier**: €0/month with 20 GB storage and 20 concurrent connections
- **Cloud-based**: No local installation needed, accessible from anywhere
- **Production-ready**: Supports SSL/TLS, automatic backups, monitoring
- **Easy deployment**: Works seamlessly with Railway.app or other cloud hosting

## Step-by-Step Setup

### 1. Create Aiven Account

1. Go to [aiven.io](https://aiven.io)
2. Click **Sign Up**
3. Enter email, password, and organization name
4. Verify your email
5. Log in to [console.aiven.io](https://console.aiven.io)

### 2. Create MySQL Service

1. In Aiven console, click **Create Service**
2. Select **MySQL** from the service list
3. Configure:
   - **Service Name**: `skillbridge` (or preferred name)
   - **Cloud Provider**: Select your region (e.g., AWS Europe if in EU)
   - **Service Plan**: Select **Free** (€0/month)
   - **Version**: MySQL 8 (default)
4. Click **Create Service**
5. Wait 2-3 minutes for service to be ready

### 3. Get Connection Details

1. Go to your MySQL service page
2. Click **Connection Info** tab
3. Copy the following details:
   - **Host**: e.g., `mysql.c.skillbridge.aivencloud.com`
   - **Port**: e.g., `21513`
   - **Username**: `avnadmin` (default)
   - **Password**: (displayed in console, or reset if forgotten)
   - **Database**: `defaultdb` (default)

### 4. Update Local Configuration

1. In the `src` folder, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Aiven credentials:
   ```
   MYSQL_HOST=mysql.c.skillbridge.aivencloud.com
   MYSQL_USER=avnadmin
   MYSQL_PASSWORD=your-password-from-aiven
   MYSQL_DB=defaultdb
   MYSQL_PORT=21513
   MYSQL_USE_SSL=true
   ```

3. Save and ensure `.env` is in `.gitignore` (it is by default)

### 5. Initialize Database Schema

**Option A: Using MySQL Client**

```bash
# Install mysql client if not already installed
# macOS: brew install mysql-client
# Windows: Download from https://dev.mysql.com/downloads/shell/
# Linux: sudo apt-get install mysql-client

# Run the schema script
mysql -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p defaultdb < db/schema.sql

# Enter password when prompted (from Step 3)
```

**Option B: Using Python (Coming in Sprint 1)**

```bash
python scripts/init_db.py
```

### 6. Verify Connection

Test that the Flask app can connect:

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Run the app
python run.py
```

Visit `http://localhost:5000` — if you see the app without errors, the database connection is working!

### 7. Create Team Credentials

For team members, you can create additional database users:

1. In Aiven console, go to your MySQL service
2. Click **Users** tab
3. Click **Create User**
4. Set username and password
5. Grant appropriate permissions
6. Share credentials securely (not in Git!)

## Common Issues

### "Connection refused" or "Can't connect to MySQL"

**Check:**
- Is the service still running? (Aiven can pause free tier services)
- Are credentials correct in `.env`?
- Is your IP whitelisted? (Aiven auto-allows from Aiven network)
- Can you ping the host? `ping mysql.c.skillbridge.aivencloud.com`

**Solutions:**
1. Check Aiven console for service status
2. Reset password in Aiven console
3. Try connecting directly: `mysql -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p`

### "SSL connection error"

**Cause**: SSL certificate validation issue

**Solutions:**
1. Download CA certificate:
   ```bash
   openssl s_client -connect mysql.c.skillbridge.aivencloud.com:21513 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM > ca.pem
   ```

2. Or disable SSL verification in `.env` (less secure):
   ```
   MYSQL_USE_SSL=false
   ```

### "Too many connections"

**Cause**: Free tier limit of 20 concurrent connections exceeded

**Solutions:**
1. Restart Flask app to close idle connections
2. Check Aiven console for hanging connections
3. Upgrade to paid tier if needed

## Maintenance

### Regular Backups

Aiven automatically backs up to 7 days. For extra safety:

```bash
# Manual backup
mysqldump -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p defaultdb > backup-$(date +%Y%m%d).sql

# Restore backup
mysql -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p defaultdb < backup-20240509.sql
```

### Monitor Metrics

- Visit Aiven console → Service → **Metrics** tab
- View CPU, memory, connections, query performance
- Set up alerts if needed

### Reset Password

If password is lost:
1. Go to Aiven console → MySQL service → Users tab
2. Find `avnadmin` user
3. Click **Reset Password**
4. Update `.env` with new password

## Deployment Considerations

For production deployment (after testing):

### Using Railway.app

1. Create Railway account at [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables (copy from `.env`)
4. Deploy Flask app
5. Railway will auto-scale and manage SSL

### Using AWS/DigitalOcean

1. Deploy Flask app to your server
2. Configure firewall to allow Aiven connection
3. Deploy with gunicorn + nginx
4. Use environment variables for credentials

## Additional Resources

- Aiven Documentation: [aiven.io/docs](https://aiven.io/docs)
- MySQL Documentation: [mysql.com/doc](https://dev.mysql.com/doc/)
- Flask-MySQL Connection: [flask.palletsprojects.com](https://flask.palletsprojects.com)

---

**Questions?** Contact the PM or check the README.md for more details.
