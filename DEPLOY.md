# UMIP 2.0 Deployment to Snowpark Container Services

## Prerequisites
- Docker Desktop installed
- Snowflake account with Container Services enabled
- Admin access to create compute pools, secrets, etc.

## Step-by-Step Deployment

### 1. Run initial Snowflake setup
Open Snowsight and run sections 1-4 of `snowflake-setup.sql`:
- Creates database/schema
- Creates image repository  
- Creates compute pool
- Creates secrets

**Important:** Note the `repository_url` from `SHOW IMAGE REPOSITORIES` - you'll need it.

### 2. Authenticate Docker with Snowflake
```powershell
# Login to Snowflake container registry
docker login <org>-<account>.registry.snowflakecomputing.com -u <your-username>
# When prompted for password, use your Snowflake password
```

### 3. Build and push the Docker image
```powershell
cd umip-2

# Build the image
docker build -t umip:latest .

# Tag for Snowflake registry
docker tag umip:latest <repository_url>/umip:latest

# Push to Snowflake
docker push <repository_url>/umip:latest
```

### 4. Create the service
Go back to Snowsight and run section 5 of `snowflake-setup.sql`.
**Remember to replace `<repository_url>` with your actual URL.**

### 5. Get your app URL
```sql
SHOW ENDPOINTS IN SERVICE umip_service;
```
The `ingress_url` column is your public URL. Share it with your team!

## Updating the App

After making changes:
```powershell
docker build -t umip:latest .
docker tag umip:latest <repository_url>/umip:latest
docker push <repository_url>/umip:latest

# In Snowflake, restart the service
ALTER SERVICE umip_service SUSPEND;
ALTER SERVICE umip_service RESUME;
```

## Troubleshooting

### Check logs
```sql
SELECT SYSTEM$GET_SERVICE_LOGS('umip_service', 0, 'umip', 100);
```

### Service not starting
1. Check compute pool is ACTIVE: `DESCRIBE COMPUTE POOL umip_pool;`
2. Check secrets are created correctly
3. Verify image was pushed successfully

### Can't reach external APIs
Make sure the external access integration is set up (section at bottom of SQL file).
