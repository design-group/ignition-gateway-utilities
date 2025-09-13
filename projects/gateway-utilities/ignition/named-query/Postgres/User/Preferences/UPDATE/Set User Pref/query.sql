UPDATE user_preferences
SET user_settings = :userSettings::jsonb
WHERE username = :userName