-- Set default user settings (can be modified for each application)
-- Check if user exists and insert a new row for the user if it doesn't exist
-- Return the user settings for the user
WITH
DefaultSettings AS (
  SELECT '{"theme": "Auto", "localization": "en"}'::jsonb AS user_settings
),
insert_new_user AS (
  INSERT INTO user_preferences (username, user_settings)
  SELECT :userName, user_settings
  FROM DefaultSettings
  WHERE NOT EXISTS (SELECT 1 FROM user_preferences WHERE username = :userName)
  RETURNING user_settings::text AS userSettings
)
SELECT userSettings
FROM insert_new_user
UNION ALL
SELECT user_settings::text AS userSettings
FROM user_preferences
WHERE username = :userName