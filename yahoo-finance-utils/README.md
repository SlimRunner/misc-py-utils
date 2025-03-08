# Yahoo Finance Library
This script uses a CLI menu navigation to execute its operations. The menu structure is as follows:
```
1. Make query
    1. input manually
    2. from file...
    0. back to main
2. visualize
    1. show columns
    0. back to main
3. generate file
    1. Save to TSV
    0. back to main
0. exit
```

You enter the appropriate number to navigate into that menu or the exit option to exit or go back one level (which is always 0).

## Make Query
### Input manually
It prompts you for a space separated list of valid tickers, the starting date, and the ending date respectively. When you pres enter nothing is shown if it was successful and it will save the data into memory.

### From File
It prompts you to select from a list of files in the directory `./data-in` you may create this folder and add `.yaml` files with the following structure
```yaml
tickers:
  - TCKR_1
  - TCKR_2
  # ...
  - TCKR_N
# dates are in yyyy-mm-dd format
from: 2015-01-01
to: 2025-03-01
```
Once you pick your file from the list that is shown to you it will tell you if the query was successful. If it is the data will be loaded into memory and nothing will be shown.

## Visualize
It allows you to visualize the data you've loaded from Make Query. Currently it only shows the columns loaded into the `DataFrame`.

## Generate File
It allows you to store to the directory `./data-out` generated files. Currently there is only one option to output `Adj Close` data binned by month in TSV format, and it won't ask you to override the file if it exists. More options may be added in the future.
