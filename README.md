## Script Requirements
---

### Installation Requirements
1. Python
2. ChromeDriver
3. Selenium Web Driver

### User Requirements
4. Your WHMCS Login Credentials
5. Your pc shouldn't enter sleep mode whilst the script is running

## Meeting the installation requirements
---
### Installing Python

1. Make sure you have python installed, if it's not already installed, please visit [Python.org/Downloads](https://www.python.org/downloads/)

### Installing Python Packages

1. Open terminal
2. In your terminal run the following commands
```
pip install selenium
```

```
pip install webdriver-manager
```

## What does this script do?
---
### Script Action Walkthrough

```text
1.  You will first be prompted to enter your WHMCS Credentials
2.  Opens Google Chrome
3.  Navigates and logs into WHMCS
4.  Navigates to the products and services page
5.  Gets all user hrefs in all pages using pagination
6.  Iterates through each users WHMCS panel

    6.1 For each user the script opens a new tab and visits the users cPanel
    6.2 Navigates into "MyApps"
    6.3 Then, for each app (e.g. wordpress, omeka, scalar)

        6.3.1 Navigates to the users notification center
        6.3.2 Updates the notifications based on the whmcs_notif_config.json file

        6.3.3 Save's all changes and closes the tab
        6.3.4 Logs all changes to a log.csv file

7.  The script loops until all users have been visited.
```

## Running the script
---

1. Open terminal
2. In your terminal, change to your projects directory, wherever it may be, using the "change directory" command. Example: ```cd <path>```
2. Then, run the following command to start the script:
```python3 main.py```
