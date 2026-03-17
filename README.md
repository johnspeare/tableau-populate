# tableau-populate -- Populating test installs of Tableau Server  and Tableau Cloud
Python scripts that create groups, projects for populating Tableau Cloud or Server test infrastructure.

The python scripts here were generated with ChatGPT 3.5.

This README is a companion to the python scripts stored in this repo.

### Recent changes

- **create-groups-n-projects.py:** Script now adds users from the CSV to the site via the REST API *before* creating groups and running `tabcmd addusers`. This fixes 404 "Item not found: [Users]" errors that occurred when users in the CSV did not yet exist on the site. Sign-in was moved to the start and is reused for both adding users and creating projects. 

The scripts are used to populate Tableau Server with users, groups, and projects. The intent is to populate (and wipe) Tableau Server/Cloud quickly for the purposes of testing different migration scenarios.

This document and scripts have been written for Tableau Server on Linux and Tableau Cloud from a remote script running from a Mac terminal. 


## Deployment types

The scripts support the following deployments . In some cases, a given script can be used for more than one of these. In other cases, you must use a script specific to your deployment. Each script description in this doc provides info on which to use.


* **Server, in-place:** You are running the script directly on the Tableau Server. For example, the server url parameter in REST and tabcmd is `http://localhost`.
* **Server, on internet**: You are running the script from a local computer but you are specifying an external address for the Tableau Server. For example, the server url parameter in REST and tabcmd is `https://tableau.domain.com`
* **Cloud:** You are running the script from a local computer but you are specifying a Tableau Cloud address. For example, the server url parameter in REST and tabcmd is `https://us-west-2a.online.tableau.com/`.

## Pre-requs

Before you begin do these things: 

- [ ] Create a personal access ID and token (PAT). The scripts use a PAT to authenticate for all deployment scenarios.  You must create the PAT for the platform you’ll be running the scripts against. Instructions: [Tableau Server](https://help.tableau.com/current/server-linux/en-us/security_personal_access_tokens.htm) | [Tableau Cloud](https://help.tableau.com/current/online/en-us/security_personal_access_tokens.htm). 
- [ ] Update Python 
    
    Server: Upgrade Tableau Server to 3.7 or later. (Here’s [AWS Linux instructions](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install-linux.html) — do the PIP part in those instructions too!).
     
    Dev machine: If you are running scripts from your local computer against server or cloud, update to Python 3.10 or later. 
    
    To determine your python version, run the following command:
    
    `python3 --version`.
    
    If you get `Command not found: python3` then you’ve got a 2.0 or earlier version of python running, or none at all. 
- [ ] Install PIP
    
    Tableau Server: Here’s [AWS Linux instructions](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install-linux.html). 
    
    Dev machine: If you are running commands from your local computer against Server or Cloud, then install PIP there ([Mac](https://www.geeksforgeeks.org/how-to-install-pip-in-macos/) | Windows).
- [ ] Install tabcmd 2.0. 
    
    Server: The latest versions of Tableau Server do not yet include tabcmd 2.0. You must install it. 
    
    Dev machine: If you are running commands from a local computer against Server or Cloud, then you must install tabcmd 2.0 there also. Run the following pip command to install:
    
    `pip install tabcmd`
    
    Verify tabcmd version:
    
    `tabcmd -v`

## Preparing and running Scripts

Python scripts are just text files with .py file name. They are not executables.
 
To prepare a script:

1. Copy the entirety of the script you want to run onto your local clipboard.
2. Paste the contents into a text file and save it as *script-name*.py.

To run a script:


* Run the following command in the same directory where you have saved the script:
    `python3 script-name.py`
 
* If you are running the scripts on Tableau Server, you will need to run as administrator/sudo:
    `sudo python3 script-name.py`

## Step 1: Run Script 1 — REST Sign-in (and optional delete) 

Script name: sign-in.py

This script uses REST to sign in to your server. If it’s successful, then it will offer to delete the previous test groups and projects on the site. 

It will only delete the groups and projects that are created by the other scripts (deletes groups/projects with naming convention: Group1, Group2, etc and Project1, Project2, etc)

Delete action will not remove users. Quickest-easiest way to delete users is through the Tableau admin UI, select all users, "Remove from site."

### Script configuration

User-defined variables must be filled in before you run the script. They are in a section at the top:


```
# User-defined variables
server_url = "https://tableau.example.com"
site_name = "site-name" #Important: if you are running the script against the default Tableau Server site (called "Default"), then leave this as an empty set.
PAT_name = "exampleName"
PAT_value = "djL7AwHHYFD76JNo740LoQ==:oloG8SJdzG3CbMUQdczVD44bDsqly7x1"
api_version = "3.4"
```


Variable notes

* **server_url:** This must be the base URL for the Tableau Server or Tableau Cloud deployment you are connecting to. 
    * Tableau Server example url: “[https://tableau.example.com”](https://tableau.example.xn--com-9o0a/)
    * Tableau Cloud is the first part of the URL before the `/#/`. Example url: “[https://us-west-2a.online.tableau.com](https://us-west-2a.online.tableau.com/#/site/johndogfood/home)“
* **site_name**: 
  * Tableau Server: the script runs against the `Default` site. If you are running against the Default site, and use an empty set, for example: `site_name: ' '`.
  * Tableau Cloud: the site name is embedded in your Tableau Cloud URL after you log in:
    https://us-west-2a.online.tableau.com/#/site/`your-site-name`/home.


* **PAT_name and PAT_value:** these are the variables that you generated when you created your PAT. 
* **api_version**: This is likely 3.4 unless you’re running an older version of Tableau Server. As of August 2023, Tableau Cloud is 3.4.

## Step 2: Add users to Tableau Server/Tableau Cloud (optional if using create-groups-n-projects.py)

You can do this manually or add a bunch from a csv file. 

CSV files with 50 user accounts: users.csv. 

**If you run create-groups-n-projects.py (Step 3), that script now adds the users from `users.csv` to the site automatically via the REST API before creating groups.** So you can skip manual/CSV import in this step when using the script. If you prefer to add users yourself, follow the directions in public docs for adding users via CSV. ([Server](https://help.tableau.com/v0.0/server/en-us/users_import.htm) | [Cloud](https://help.tableau.com/v0.0/online/en-us/users_import.htm)).


## Step 3: Run script 2 — Create groups and projects

Script name: create-groups-n-projects.py

In a nutshell, this script adds users to the site (from the CSV), creates groups, assigns users to groups, and creates projects. 

**What the script does (in order):**

1. **Sign in** — Uses the REST API to sign in and obtain a session token.
2. **Add users to the site** — For each row in `users.csv`, calls the REST API to add that user to the site (username and site role from columns 1 and 4). This step must run before adding users to groups; otherwise `tabcmd addusers` returns 404 "Item not found: [Users]" because those users do not yet exist on the site.
3. **Tabcmd login** — Logs in with tabcmd for the group commands.
4. **Create groups and add users** — Creates each group (Group1, Group2, …), randomly assigns users from the CSV to groups, and runs `tabcmd addusers` to add them. Users are in one group only.
5. **Create projects** — Uses the REST API to create the specified number of projects (Project1, Project2, …).

**CSV format:** The script expects `users.csv` with at least: column 1 = username (email), column 4 = site role (Creator, Explorer, Viewer, Unlicensed). Same file as in Step 2.

**Note (Tableau Cloud):** If the REST "Add User" call returns 403/400 or invite-only behavior on your Cloud site, add or invite users via the Tableau Cloud UI or your normal process first, then run this script to create groups and assign those existing users.

### Script configuration

User-defined variables must be filled in before you run the script. Same configuration as sign-in.py.

Also includes: `csv_file_path` (e.g. `users.csv`), and the number of **Groups** and **Projects** to create. The script creates them with names GroupN and ProjectN, where N starts at 1.

## Step 4: Run script 3 -- Update project permissions

Script name: perms.py

This script removes "All Users" Write-Allow perms from the projects creeated by script 2. It then adds Write-Allow for each Group in a 1:1 mapping to projects. So Group1 has Write-Allow for Project 1, etc. If there are more groups than projects, then script will assign groups to projects round-robin until groups are used up. If there are more projects than groups, then groups will have access to multiple projects. 

### Script configuration

User-defined variables must be filled in before you run the script. Same configuration as sign-in.py.
        
