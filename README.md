# tableau-populate
Python scripts that creates groups, projects for populating Tableau Cloud or Server test infrastructure
# Populating test installs of Tableau Server  and Tableau Cloud

This doc is a companion to the python scripts stored here. The scripts are used to populate Tableau Server with users, groups, and projects. The intent is to populate (and wipe) Tableau Server/Cloud quickly for the purposes of testing different migration scenarios.

This document and scripts have been written for Tableau Server on Linux and Tableau Cloud from a remote script running from a Mac terminal. 


## Deployment types

The scripts support the following deployments . In some cases, a given script can be used for more than one of these. In other cases, you must use a script specific to your deployment. Each script description in this doc provides info on which to use.


* **Server, in-place:** You are running the script directly on the Tableau Server. For example, the server url parameter in REST and tabcmd is `http://localhost`.
* **Server, on internet**: You are running the script from a local computer but you are specifying an external address for the Tableau Server. For example, the server url parameter in REST and tabcmd is `https://tableau.domain.com`
* **Cloud:** You are running the script from a local computer but you are specifying a Tableau Cloud address. For example, the server url parameter in REST and tabcmd is `https://us-west-2a.online.tableau.com/`.

## Pre-requs

Before you begin do these things: 

- [ ] Create a personal access ID and token (PAT). The scripts use a PAT to authenticate for all deployment scenarios.  You must create the PAT for the platform you’ll be running the scripts against. Instructions: [Tableau Server](https://help.tableau.com/current/server-linux/en-us/security_personal_access_tokens.htm) | T[ableau Cloud](https://help.tableau.com/current/online/en-us/security_personal_access_tokens.htm). 
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
    
    `pip install tabcmd
    
    `Verify tabcmd version:
    
    `tabcmd -v`

## Preparing and running Scripts

Python scripts are just text files with .py file name. They are not executables.
 
To prepare a script:

1. Copy the entirety of the script you want to run onto your local clipboard.
2. Paste the contents into a text file and save it as *script-name*.py.

To run a script:


* Run the following command in the same directory where you have saved the script:
    `python3 script-name.py
    
    `
* If you are running the scripts on Tableau Server, you will need to run as administrator/sudo:
    `sudo python3 script-name.py`

## Step 1: Run Script #1 — REST Sign-in (and optional delete) 

Scripts:

* Server, In-place: sign-in.py
* Server, on internet: sign-in.py
* Cloud: sign-in-cloud.py

This script uses REST to sign in to your server. If it’s successful, then it will offer to delete the groups and projects on the site. 

It will only delete the groups and projects that are created by the other scripts (deletes groups/projects with naming convention: Group1, Group2, etc and Project1, Project2, etc)


### Script configuration

User-defined variables must be filled in before you run the script. They are in a section at the top:


```
# User-defined variables
server_url = "https://tableau.example.com"
site_name = "cloud-site-name" (do not use for server. see below)
PAT_name = "exampleName"
PAT_value = "djL7AwHHYFD76JNo740LoQ==:oloG8SJdzG3CbMUQdczVD44bDsqly7x1"
api_version = "3.4"
```


Variable notes

* **server_url:** This must be the base URL for the Tableau Server or Tableau Cloud deployment you are connecting to. 
    * Tableau Server example url: “[https://tableau.example.com”](https://tableau.example.xn--com-9o0a/)
    * Tableau Cloud is the first part of the URL before the `/#/`. Example url: “[https://us-west-2a.online.tableau.com](https://us-west-2a.online.tableau.com/#/site/johndogfood/home)“
* **site_name**: This option is only viable in the Cloud version of the script. 
    The site name is embedded in your Tableau Cloud URL after you log in:
    [https://us-west-2a.online.tableau.com/#/site/johndogfood/home
    
    F](https://us-west-2a.online.tableau.com/#/site/johndogfood/home)or server, the script runs against the Default site. If you are running against the Default site, do nothing.
    
     If you want to run the script against a different site on your server, update the sign-in.xml template in the script:

```
# Step 1: Generate signin.xml file
signin_xml = f'''<tsRequest>
  <credentials personalAccessTokenName="{PAT_name}"
    personalAccessTokenSecret="{PAT_value}" >
      <site contentUrl="site-name-goes-here" />
  </credentials>
</tsRequest>'''
```



* **PAT_name and PAT_value:** these are the variables that you generated when you created your PAT. 
* **api_version**: This is likely 3.4 unless you’re running an older version of Tableau Server. Tableau Cloud is 3.4.

## Step 2: Add users to Tableau Server/Tableau Cloud

You can do this manually or add a bunch from a csv file. 

CSV files with 50 user accounts: Users.csv is for Server and users-cloud.csv is for Cloud. 

Follow the directions in public docs for adding users via CSV. ([Server](https://help.tableau.com/v0.0/server/en-us/users_import.htm) | [Cloud](https://help.tableau.com/v0.0/online/en-us/users_import.htm)).


## Step 3: Run script #2 — Create groups and projects

Scripts:

* Server, In-place: create-groups-n-projects.py
* Server, on internet: create-groups-n-projects.py
* Cloud: create-groups-n-projects-cloud.py

In a nutshell, this script creates groups and projects on your Tableau site. 

Specifically, it uses tabcmd to create groups which it then populates with users. Users only belong to one group. They are randomly distributed across the groups. You can specify how many groups you want to create. The script requiires a csv file of user accounts. If you used a csv file to bulk import users in Step 1, then use that same csv for this script.

Projects: the script uses REST to create the number of projects that you specify.


        
