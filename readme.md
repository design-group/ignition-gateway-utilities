## Ignition Gateway Utilities
This repository is a collection of utilities for developing in Ignition. The utilities are designed to be run in parallel to the existing project, and can add features like config file access, feature flagging, and more.

### Installation
1. Download the latest release asset (`gateway-utilities.zip`) from the [releases page](https://github.com/design-group/ignition-gateway-utilities/releases)
2. Import the project into Ignition, either through the gateway webpage or while inside of another project.


### Functionality

#### [Config File Explorer](./docs/config-files.md)
Convenience functions for accessing config files on the gateway. This includes the ability to view, upload, download, and customize config files through a dedicated explorer.

![Config File Viewer](./images/ConfigFileExplorer.png)

#### [Feature Flagging](./docs/feature-flags.md)
Convenience functions for accessing feature flags on the gateway. This includes the ability to view, upload, download, and customize feature flags through a dedicated explorer.

![Feature Flag Viewer](./images/FeatureFlagEditor.png)

#### Multithreading
Convenience functions for running scripts in parallel. This includes the ability to run scripts in parallel with a set thread count. 

This could be used if multiple heavy operations need to happen before a user can move on. Executing the same script multiple times in parallel could resolve in a faster user experience.

##### Example
```python
General.Multithreading.wait_for_async_execution(
        func=myFunction, 
        kwargs_list=[
                {"myArg":"val1"}, 
                {"myArg":"val2"}
                ]
        )
```