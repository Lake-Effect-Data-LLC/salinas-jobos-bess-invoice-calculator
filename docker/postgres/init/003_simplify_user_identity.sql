DROP TABLE IF EXISTS auth_email_token;

DROP TABLE IF EXISTS allowed_user;

ALTER TABLE app_user
    DROP COLUMN IF EXISTS email_verified_at;
