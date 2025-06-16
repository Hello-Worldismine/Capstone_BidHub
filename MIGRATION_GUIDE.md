# BidHub Cloud SQL Migration Guide

## Step 1: Create Cloud SQL Instance

```powershell
# Run Cloud SQL setup script
.\setup_cloudsql.ps1
```

Before running, ensure:
- Google Cloud CLI is installed and authenticated
- Your project ID is correctly set in the script

## Step 2: Export Existing SQLite Data

```powershell
# Export SQLite data to JSON
python migrate_data.py export
```

This command creates a `data_export.json` file.

## Step 3: Test Cloud SQL Connection Locally

```powershell
# Start Cloud SQL proxy (in a new terminal)
.\cloud_sql_proxy.exe -instances=agile-entry-457201-m9:asia-northeast3:bidhub-db=tcp:5432

# In another terminal, test PostgreSQL connection
$env:DJANGO_SETTINGS_MODULE="backend.settings_cloudsql"
$env:DB_HOST="localhost"
$env:DB_PASSWORD="[your database password]"

python manage.py migrate
```

## Step 4: Import Data to PostgreSQL

```powershell
# Set environment variables and import data
python migrate_data.py import
```

## Step 5: Deploy to Cloud Run

```powershell
# Update DB_PASSWORD in deploy-config.env, then run
.\deploy_cloudsql.ps1
```

## Step 6: Test New User Registration

In the deployed app:
1. Access the registration page
2. Create a new account
3. Test login functionality
4. Verify data persistence

## Important Notes

1. **Security**: Use strong database passwords in production
2. **Backup**: Always backup existing data before migration
3. **Testing**: Test thoroughly locally before deployment
4. **Monitoring**: Monitor Cloud SQL and Cloud Run logs

## Benefits

- **Data Persistence**: Data survives Cloud Run restarts
- **Scalability**: Multiple instances share the same database
- **Performance**: PostgreSQL's excellent performance
- **Management**: Fully managed Google Cloud service
- **Backup**: Automatic backup and recovery features

## Cost Optimization

- Using db-f1-micro instance (minimal cost)
- Can upgrade later as needed
- Leverage Cloud SQL's auto-scaling features
