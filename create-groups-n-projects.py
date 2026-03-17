import os
import random
import subprocess
import csv
import xml.etree.ElementTree as ET




# User-defined variables

server_url = 'https://us-west-2a.online.tableau.com/' # 'https://example.example.com'
site_name = '' #For default Tableau Server site, leave this as empty set.
PAT_name = ''
PAT_value = ''
csv_file_path = 'users.csv'
api_version = "3.4"
num_projects = 4
num_groups = 2

####End of user-defined variables - Do not edit below this line ##

# Define the group names
groups = []
for i in range(num_groups):
    group_name = f'Group{i+1}'
    groups.append(group_name)

# ----- Sign in via REST to get credentials (used for adding users and creating projects) -----
signin_xml = f'''<tsRequest>
  <credentials personalAccessTokenName="{PAT_name}"
    personalAccessTokenSecret="{PAT_value}" >
      <site contentUrl="{site_name}" />
  </credentials>
</tsRequest>'''
with open('signin.xml', 'w') as file:
    file.write(signin_xml)
signin_command = f'curl -s "{server_url}/api/{api_version}/auth/signin" -X POST -d "@signin.xml"'
signin_output = subprocess.check_output(signin_command, shell=True, encoding='utf-8')
namespaces = {'t': 'http://tableau.com/api'}
root = ET.fromstring(signin_output)
site_element = root.find('.//t:site', namespaces)
if site_element is None:
    print("Error: Site element not found in the XML response.")
    exit(1)
site_id = site_element.attrib.get('id')
if site_id is None:
    print("Error: Site ID attribute not found in the XML response.")
    exit(1)
credentials_element = root.find('.//t:credentials', namespaces)
if credentials_element is None:
    print("Error: Credentials element not found in the XML response.")
    exit(1)
credentials_token = credentials_element.attrib.get('token')
if credentials_token is None:
    print("Error: Credentials token attribute not found in the XML response.")
    exit(1)

# ----- Add users to the site first (required before adding them to groups) -----
# CSV columns: username, password, display name, site role, admin level, publishing
user_rows = []
with open(csv_file_path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
        if len(row) >= 1 and row[0].strip():
            user_rows.append(row)
for row in user_rows:
    username = row[0].strip()
    site_role = row[3].strip() if len(row) > 3 else 'Unlicensed'
    add_user_xml = f'<tsRequest>\n  <user name="{username}" siteRole="{site_role}" />\n</tsRequest>'
    with open('_add_user.xml', 'w') as f:
        f.write(add_user_xml)
    add_user_cmd = (
        f'curl -s -w "\\n%{{http_code}}" "{server_url}/api/{api_version}/sites/{site_id}/users" '
        f'-X POST -H "X-Tableau-Auth: {credentials_token}" -H "Content-Type: application/xml" -d @_add_user.xml'
    )
    result = subprocess.run(add_user_cmd, shell=True, capture_output=True, text=True)
    out = (result.stdout or '').strip()
    if out:
        body_and_code = out.rsplit('\n', 1)
        code = body_and_code[-1] if len(body_and_code) == 2 else ''
        if code == '201' or code == '200':
            print(f"  Added user to site: {username}")
        elif 'already exists' in out or 'already a member' in out.lower():
            print(f"  User already on site: {username}")
        else:
            print(f"  Warning adding {username}: HTTP {code} - {out[:200]}")
try:
    os.remove('_add_user.xml')
except OSError:
    pass

# Authenticate with the remote Tableau Server (for tabcmd group commands)
login_cmd = f'tabcmd login -s {server_url} -t "{site_name}" --token-name "{PAT_name}" --token-value "{PAT_value}"'
subprocess.call(login_cmd, shell=True)

# Usernames list (already read above from user_rows)
usernames = [row[0].strip() for row in user_rows]

# Shuffle the usernames randomly
random.shuffle(usernames)

# Calculate the number of users per group
users_per_group = len(usernames) // len(groups)

# Iterate over the groups
for i, group in enumerate(groups):
    # Create the group
    create_group_cmd = f'tabcmd creategroup "{group}"'
    subprocess.call(create_group_cmd, shell=True)
    
    # Get the users for the current group
    group_users = random.sample(usernames, users_per_group)
    
    # Remove the assigned users from the list
    for user in group_users:
        usernames.remove(user)
    
    # Write group users to a temporary text file
    temp_text_file_path = f'{group}_users.txt'
    with open(temp_text_file_path, 'w') as temp_file:
        temp_file.write('\n'.join(group_users))
    
    # Add the users to the group
    add_users_cmd = f'tabcmd addusers "{group}" --users "{temp_text_file_path}"'
    subprocess.call(add_users_cmd, shell=True)

    # Remove the temporary text file
    subprocess.call(f'rm "{temp_text_file_path}"', shell=True)

print("Groups created successfully!")

# ######### CREATE PROJECTS ###############
# (site_id and credentials_token already set from sign-in above)
project_xml_template = '''<tsRequest>
    <project
      name="{ProjectName}"
      description="This is a new project number {n}" />
</tsRequest>'''

# Loop to create projects
for n in range(1, num_projects + 1):
    project_name = f"Project{n}"
    create_project_xml = project_xml_template.format(ProjectName=project_name, n=n)
    
    create_project_command = (
        f'curl "{server_url}/api/{api_version}/sites/{site_id}/projects" '
        f'-X POST -H "X-Tableau-Auth:{credentials_token}" -d "@-"'
    )
    
    subprocess.run(create_project_command, shell=True, input=create_project_xml.encode('utf-8'))

