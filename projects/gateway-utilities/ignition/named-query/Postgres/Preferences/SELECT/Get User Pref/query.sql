-- Set default user settings (can be modified for each application)
-- Check if user exists and insert a new row for the user if it doesn't exist
-- Return the user settings for the user
WITH 
DefaultSettings AS (
  SELECT '{"theme": "Auto", "localization": "en"}'::jsonb AS userSettings
),
insert_new_user AS (
  INSERT INTO UserPreferences (username, userSettings)
  SELECT :userName, userSettings
  FROM DefaultSettings
  WHERE NOT EXISTS (SELECT 1 FROM UserPreferences WHERE username = :userName)
  RETURNING userSettings
)
SELECT userSettings 
FROM insert_new_user
UNION ALL
SELECT userSettings
FROM UserPreferences
WHERE username = :userName