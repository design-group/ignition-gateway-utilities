# General.Logging
## Logger
`Logger` is a class that provides a simple interface for logging messages.
It reuses the built-in `system.util.getLogger` function to create a logger that uses the built-in Ignition functionality.

`Logger` also implements the `custom_print` method that allows for logs to also be printed into the Script Console and the Perspective Console if possible.

At the end of each method, before executing `custom_print` it will check if the logger is enabled (i.e. `logger.isDebugEnabled()`) so that it works in concert with the builtin logging settings.

This `Logger` class is used for all cases except when a transaction attempt occurs. In that case, the `FileLogger` class will be used.

## Sub Loggers
`Sub Loggers` allows for further organizing all logs within Ignition. This allows for searching based on a provided logger name which can be user defined in the configuration files as `logging_trigger_name` or by adding a `compilable_path` to the `logging_trigger_name` definition, can be compiled with the specific tag trigger or another compilable value. 

Once a sub logger is created, all logs will be logged both to the sub logger and the parent logger. 

For example: 

```JSON
{
    "logging_trigger_name": "custom_name"
}
```
```JSON
"logging_trigger_name": {
    "compilable_path": "transaction_config.trigger.tag_path"
}
```

### Example
```python
logger = General.Logging.Logger("MyLogger")
logger.info("Hello World!")
```


### Testing
A unit test, `test_logger.py` has been developed for this class. In order for a merge to occur, whether related to logging or not, this test must pass.

## FileLogger
`FileLogger` logs all transaction related events. All messages logged using this class go directly to a file called `tms-transaction-log.csv`. To log the information, a list containting the needed elements for the log are passed to `log_to_file`.

`tms-transaction-log.csv` was selected to be the name of the file because it includes specific information regarding the content of the transactions. This will not include information that is not specific to transactions.

**Constructor Parameter:** `delimiter`, value that separates the element in the list. Defaulted to a ",".

Example:
```python
log_contents_list = ["Hello", " ", "World", "!"]
log = Logger.FileLogger()
log.log_to_file(log_contents_list)
```

### Testing:

Because `FileLogger` is built off of Ignition's functionality, testing was performed manually in the development environment instead of a unit test. Follow steps below for testing manually:

_Note:_ The `logback.xml` file must be updated in order for the logger to work. Then the Gateway must be restarted to take the changes of the `logback.xml`.

-  Create instance of `FileLogger`. 
-  Using a defined list of as many elements as desired, call `log_to_file`.
-  Go to the `data/logs` directory and open `tms-transaction-log.csv`
-  **Success:** if the list is added to the file.
-  _If using Docker:_ use the terminal associated with the image to cd into the `logs` directory. To see if a change has been made, use commands `ls -l` to get the information of when the file was last changed and use `cat tms-transaction-log.csv` to read the file in the terminal.
 -  **Failure:** if the message was not changed and does not contain the message. 


# CSV Logging Definition

## `logback.xml`
`logback.xml` must be provided by the user. It is used to write custom logs to the `logs` folder within Ignition. This then allows for a custom csv message to be stored within it's own file. With the use of Ignition, it can log information easily and behind the scenes of the rest of the software.

a GUID will be used for determining the `unique_id`.

**CSV:** 

```CSV
14:27:31.435, e2491c3e-310e-473a-9f45-c078e2d81975, <compiled transaction config>, <compiled transaction response>
time_stamp, unique_id, configuration, response
TIME, 01234,`api_params`, `eyelit_failure`
TIME, 01234,`api_params`, `eyelit_success`
```
`api_params` = 
```JSON
{
    "post_processed_type": "api.post",
    "post_processed_config_file": "eyelit",
    "payload": {
        "header": {
            "type": "get_lot_info",
            "env": "prod",
            "source": "computer_name",
            "user_id": "estodghill"
        },
        "body": {
            "lot_id": "CA12345"
        }
    }
}
```
`eyelit_failure` = 
```JSON
{
        "header": {
        "user_id": "estodghill",
        "success": false,
        "source": "MES01-PROD",
        "time": "2021-12-15T18:23:10.169",
        "type": "get_lot_info",
        "env": "dev"
    },
    "body": {
        "message": "Error: No lot found matching id: CA12345"
    }
}
```
<details open>
<summary> `eyelit_success` </summary>

```JSON
{
    "header": {
        "user_id": "ggearing",
        "success": true,
        "source": "MES01-DEV",
        "time": "2021-12-15T18:27:07Z",
        "type": "get_lot_info",
        "env": "dev"
    },
    "body": {
        "product_version": 3,
        "curr_oper": "UNLOAD_DURABLE",
        "wip_type": "PRODUCTION",
        "curr_stage": "CNSTR",
        "durable": "DWF21240101224",
        "operations": [
            {
                "descr": "Remove the lot from the durable and leave it empty.",
                "op_item_id": "CA12345
                ~0000~UNLOAD_DURABLE~1",
                "op_id": "UNLOAD_DURABLE",
                "invisible": false,
                "type": "WORK_ACTIONS",
                "complete": false,
                "op_idx": 0
            },
            {
                "descr": "Record the constraint barcodes",
                "op_item_id": "CA12345
                ~0001~DC_CNSTR_BC~1",
                "collections": [
                    {
                        "visible": true,
                        "editable": true,
                        "id": "CNSTR_BC_1",
                        "type": "Text",
                        "mandatory": true,
                        "desc": "Scan first constraint barcode",
                        "order": 0
                    },
                    {
                        "visible": true,
                        "editable": true,
                        "id": "CNSTR_BC_2",
                        "type": "Text",
                        "mandatory": true,
                        "desc": "Scan second constraint barcode",
                        "order": 1
                    }
                ],
                "op_id": "DC_CNSTR_BC",
                "invisible": false,
                "type": "DATA_COLLECTION",
                "complete": false,
                "op_idx": 1
            },
            {
                "descr": "Move to next step",
                "op_item_id": "CA12345
                ~0002~NEXT_STEP~1",
                "op_id": "NEXT_STEP",
                "invisible": true,
                "type": "WORK_ACTIONS",
                "complete": false,
                "op_idx": 2
            }
        ],
        "material": "CELL",
        "product_id": "200268",
        "qty": 1,
        "alias": "CA12345
        ",
        "curr_step": "DECLAMP",
        "id": "CA12345
        ",
        "state": "READY"
    }
}
```
</details>
