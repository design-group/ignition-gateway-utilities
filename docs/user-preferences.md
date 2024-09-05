# User Preferences

User preferences are customizable settings that allow users to personalize their experience within the application. These preferences can include settings such as theme selection, language localization, and other user-specific configurations.

## Features
- Storing and retrieving user preferences
- Default preferences for new users
- Session-based preference management
- Individual preference updates

## Python Implementation

The Python scripts provide a set of functions to manage user preferences.

1. The Python scripts should be imported to `General.Users`, and work for either database type (MSSQL or Postgres).

2. After importing the scripts, add a new Custom Perspective Session Property called `userPreferences`.  
   **NOTE:** If this key is named differently, update the constant defined in `General.Users.USER_PREFERENCES_KEY`

3. Place a property binding on your new userPreferences key to refresh when the signed-in username changes.
    - Binding Type: Property
    - Config Property Binding: `this.props.auth.user.userName`
    - Enabled: True
    - Overlay Opt-Out: False
    - Bidirectional: False

4. When updating single properties of a user's preferences, call the function `General.User.set_user_preference_value(session, preference_name, preference_value)`.
    - This function will get the username from the session, update the supplied key within the userPreferences, and then refresh session.custom.userPreferences.
    - **Example: Updating Theme**  
      ```python
      General.User.set_user_preference_value(self.session, 'Theme', 'Lumen')
      ```

### Key Functions Reference

1. `get_username_for_session(session)`: Retrieves the username for the current session.
2. `get_preferences_from_session(session)`: Gets user preferences from the session.
3. `get_user_preferences(username)`: Retrieves user preferences from the database.
4. `set_user_preferences(username, user_preferences)`: Stores user preferences in the database. This function expects a dictionary as the `user_preferences` parameter. If a string is passed instead of a dictionary, a TypeError will be raised.
5. `set_user_preference_value(session, preference_name, preference_value)`: Updates a single preference value.

**Note for MSSQL:** User preferences are stored in the database as strings. The functions automatically handle the encoding and decoding of these preferences. When working with preferences in your Python code, you'll be dealing with dictionaries, and the conversion to and from strings is managed internally by these functions.

## Usage

1. Initialize user preferences with a session property based on their username.
2. Retrieve user preferences using `get_user_preferences()` or `get_preferences_from_session()`.
3. Update individual preferences using `set_user_preference_value()`.
4. For bulk updates, use `set_user_preferences()`. Remember to pass a dictionary as the `user_preferences` parameter.

Remember to handle any exceptions that may occur during database operations or JSON parsing.

## Best Practices

1. Always validate user input before storing preferences.
2. Use meaningful keys for preference names to ensure clarity.
3. Consider implementing a caching mechanism for frequently accessed preferences to reduce database load.
4. Implement proper error handling and logging for preference-related operations.


## Database Setup - MSSQL
*Note: Ensure that you use the appropriate queries for your chosen database system (either MSSQL or Postgres) and place them in the correct folders as specified.*
### Create UserPreference Table

```sql
--Initialization SQL Query - MSSQL
CREATE TABLE UserPreferences (
    [id]           INT            IDENTITY (1, 1) NOT NULL,
    [username]     NVARCHAR (100) NOT NULL,
    [userSettings] NVARCHAR (MAX),
    CONSTRAINT [PK_UserPreferences] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UQ_UserPreferences_username] UNIQUE NONCLUSTERED ([username] ASC)
);
```

### Named Query - Get User Preferences
**Query Path:** User/Preferences/SELECT/Get User Pref  
**Query Type:** Scalar Query  
**Use Fallback:** False

```sql
DECLARE @default_settings NVARCHAR(MAX) = '{"theme": "Auto", "localization": "en"}';

IF NOT EXISTS (SELECT 1 FROM UserPreferences WHERE username = :userName)
BEGIN
    INSERT INTO UserPreferences (username, userSettings)
    VALUES (:userName, @default_settings);
END

SELECT userSettings
FROM UserPreferences
WHERE username = :userName;
```

### Named Query - Set User Preferences
**Query Path:** User/Preferences/UPDATE/Set User Pref  
**Query Type:** Update Query  

```sql
UPDATE UserPreferences
SET userSettings = :userSettings
WHERE username = :userName
```


## Database Setup - Postgres
*Note: Ensure that you use the appropriate queries for your chosen database system (either MSSQL or Postgres) and place them in the correct folders as specified.*
### Create UserPreference Table

```sql
--Initialization SQL Query - Postgres
CREATE TABLE UserPreferences
(
    id integer NOT NULL GENERATED BY DEFAULT AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    username character varying(64) COLLATE pg_catalog."default" NOT NULL,
    userSettings jsonb,
    CONSTRAINT PK_UserPreferences PRIMARY KEY (id),
    CONSTRAINT UQ_UserPreferences_username UNIQUE (username)
)
```

### Named Query - Get User Preferences
**Query Path:** User/Preferences/SELECT/Get User Pref  
**Query Type:** Scalar Query  
**Use Fallback:** False

```sql
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
```

### Named Query - Set User Preferences
**Query Path:** User/Preferences/UPDATE/Set User Pref  
**Query Type:** Update Query  

```sql
UPDATE UserPreferences
SET userSettings = :userSettings::jsonb
WHERE username = :userName
```
