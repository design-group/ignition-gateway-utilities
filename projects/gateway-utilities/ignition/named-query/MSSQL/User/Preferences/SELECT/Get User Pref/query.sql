-- Set default user settings (can be modified for each application)
-- Check if user exists and insert a new row for the user if it doesn't exist
-- Return the user settings for the user

DECLARE @default_settings NVARCHAR(MAX) = '{"theme": "Auto", "localization": "en"}';

IF NOT EXISTS (SELECT 1 FROM UserPreferences WHERE username = :userName)
BEGIN
    INSERT INTO UserPreferences (username, userSettings)
    VALUES (:userName, @default_settings);
END

SELECT userSettings
FROM UserPreferences
WHERE username = :userName;