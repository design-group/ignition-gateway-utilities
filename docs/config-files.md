### Why Config Files
Config files make it easy to configure the differences between different environments. They allow you to remove environment specific information out of your code, and streamline future development.


### Config Files in Ignition
To leverage config files in Ignition common practice is to store them in the `ignition/data` directory under a folder called `configs`. Ignition wont look at this folder in any specific way, but its a clear and obvious name for future developers looking at the system.

In order to access these config files, a common practice is to implement a global library script, that handles reading the config files from the OS without needing to use read commands every time. Storing them in cache makes it easier to reference them quickly and rapidly, without needing to worry about the IO operations for file reads every time they are needed. Then whenever a config is requested, the script checks against the modification time of the file, to verify that it hasn't been updated since it was last cached. In Ignition this is achieved with Globals, and storing the file contents as an object. To make it easy convert and store the config files, a common practice is to store the config files as JSON objects, and then reference them by their key. 

An example of the script can be found in [this github repo](https://github.com/design-group/gists/blob/master/GatewayFileContents.py)

In this example script, when configs are updated the script should automatically capture the changes when next requested. It will look at a files modification time when it is first requested, and then again when it is requested again. If the modification time has changed, it will read the file again and update the cache. This allows for the config files to be updated without needing to restart the gateway.

### An example config file:
```json
{
    "report_server": "http://rptdev01.example.com/ibi_apps/WFServlet?",
    "apps": {
            "sap": {
                "host": "sap.dev.example.com",
                "port": 8080,
                "client_id": "1234567890",
                "client_secret": "1234567890"
            },
            "mulesoft": {
                "host": "mulesoft.dev.example.com",
                "port": 8080,
                "client_id": "1234567890",
                "client_secret": "1234567890"
            }
        }
    },
    "theme": "custom-dev",
    "testing": {
        "allow_invasive": false,
        "browser": "chrome",
        "credentials": {
            "username": "TestAccount",
            "password": "TestAccountPassword"
        },
        "default_test_env": "localhost",
        "headless": false,
        "remote": {
            "command_executor": "http://localhost:4444/wd/hub",
            "insecure": true
        }
    }
}
```

### Editing Configuration Files
The config files are typically just edited in the developers IDE of choice. This allows for easy editing and version control. When working in a shared development environment, it is important to make sure that the config files are not checked into source control. This is because they contain environment specific information, and should not move with the project. In order to access these files on a remote server, one can use the VS-Code remote development functionality to SSH into the server and edit the files directly. If the developers are unable to access the file system of the gateway, this could also be done by creating a perspective webpage that allows for file uploading and downloading, with the developer editing locally.

### Config File Viewer
This project contains a config file viewer, located under `Utilities/Config Explorer`. It includes the capability to view, upload, download, and customize config files on the gateway.
![Config File Viewer](../images/ConfigFileExplorer.png)

