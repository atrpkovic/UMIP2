-- ============================================================
-- UMIP 2.0 Snowpark Container Services Setup
-- Run these commands in Snowsight
-- ============================================================

-- 1. Create a database for container services (or use existing)
CREATE DATABASE IF NOT EXISTS CONTAINER_SERVICES;
USE DATABASE CONTAINER_SERVICES;
CREATE SCHEMA IF NOT EXISTS UMIP;
USE SCHEMA UMIP;

-- 2. Create an image repository
CREATE IMAGE REPOSITORY IF NOT EXISTS umip_repo;

-- Get the repository URL (you'll need this for docker push)
SHOW IMAGE REPOSITORIES;
-- Note the 'repository_url' column - it looks like:
-- <org>-<account>.registry.snowflakecomputing.com/container_services/umip/umip_repo

-- 3. Create a compute pool
CREATE COMPUTE POOL IF NOT EXISTS umip_pool
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_XS;

-- Check pool status (wait until ACTIVE/IDLE)
DESCRIBE COMPUTE POOL umip_pool;

-- 4. Create secrets for sensitive values
CREATE SECRET IF NOT EXISTS anthropic_api_key
    TYPE = GENERIC_STRING
    SECRET_STRING = 'your-anthropic-api-key-here';

CREATE SECRET IF NOT EXISTS snowflake_account
    TYPE = GENERIC_STRING
    SECRET_STRING = 'umc92597.us-east-1';

CREATE SECRET IF NOT EXISTS snowflake_user
    TYPE = GENERIC_STRING
    SECRET_STRING = 'your-username';

CREATE SECRET IF NOT EXISTS snowflake_password
    TYPE = GENERIC_STRING
    SECRET_STRING = 'your-password';

CREATE SECRET IF NOT EXISTS snowflake_warehouse
    TYPE = GENERIC_STRING
    SECRET_STRING = 'your-warehouse';

-- 5. Create the service (run AFTER pushing docker image)
-- Replace <repository_url> with your actual repo URL from step 2
CREATE SERVICE umip_service
    IN COMPUTE POOL umip_pool
    FROM SPECIFICATION $$
spec:
  containers:
    - name: umip
      image: <repository_url>/umip:latest
      env:
        ANTHROPIC_API_KEY: "{{secrets.anthropic_api_key}}"
        SNOWFLAKE_ACCOUNT: "{{secrets.snowflake_account}}"
        SNOWFLAKE_USER: "{{secrets.snowflake_user}}"
        SNOWFLAKE_PASSWORD: "{{secrets.snowflake_password}}"
        SNOWFLAKE_WAREHOUSE: "{{secrets.snowflake_warehouse}}"
        SNOWFLAKE_DATABASE: "PRIORITY_TIRE_DATA"
        SNOWFLAKE_SCHEMA: "UMIP_MOCK"
      readinessProbe:
        port: 8080
        path: /health
  endpoints:
    - name: umip-ui
      port: 8080
      public: true
$$
EXTERNAL_ACCESS_INTEGRATIONS = (ALLOW_ALL_ACCESS_INTEGRATION)
MIN_INSTANCES = 1
MAX_INSTANCES = 1;

-- 6. Check service status
DESCRIBE SERVICE umip_service;
SELECT SYSTEM$GET_SERVICE_STATUS('umip_service');

-- 7. Get the public endpoint URL
SHOW ENDPOINTS IN SERVICE umip_service;
-- The 'ingress_url' is your app URL!

-- ============================================================
-- TROUBLESHOOTING COMMANDS
-- ============================================================

-- View service logs
SELECT SYSTEM$GET_SERVICE_LOGS('umip_service', 0, 'umip', 100);

-- Restart service
ALTER SERVICE umip_service SUSPEND;
ALTER SERVICE umip_service RESUME;

-- Drop and recreate if needed
DROP SERVICE IF EXISTS umip_service;

-- ============================================================
-- NETWORK ACCESS (if not already set up)
-- ============================================================

-- Create network rule for external APIs (Anthropic)
CREATE OR REPLACE NETWORK RULE anthropic_api_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('api.anthropic.com:443');

-- Create external access integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION allow_all_access_integration
    ALLOWED_NETWORK_RULES = (anthropic_api_rule)
    ENABLED = true;
