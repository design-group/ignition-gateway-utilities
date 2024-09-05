UPDATE UserPreferences
SET userSettings = :userSettings::jsonb
WHERE username = :userName