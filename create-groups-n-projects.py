import random
import subprocess
import csv
import xml.etree.ElementTree as ET

# User-defined variables
server_url = 'https://edg3.cyclingspokane.com'
PAT_name = 'scriptrunner'
PAT_value = 'djL7AwHJTGC87JNo740LoQ==:oloG8SJdzG3CbMUQdczVD44bDsqly7x1'
csv_file_path = 'users.csv'
api_version = "3.4"
num_groups = 5
num_projects = 4

# Define the group names
groups = []
for i in range(num_groups):
    group_name = f'Group{i+1}'
    groups.append(group_name)

# Authenticate with the remote Tableau Server
login_cmd = f'tabcmd login -s {server_url} --token-name "{PAT_name}" --token-value "{PAT_value}"'
subprocess.call(login_cmd, shell=True)

# Read usernames from the CSV file
usernames = []
with open(csv_file_path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
        username = row[0].strip()
        if username:
            usernames.append(username)

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


################# Create Projects #############

# Step 1: Generate signin.xml file
signin_xml = f'''<tsRequest>
  <credentials personalAccessTokenName="{PAT_name}"
    personalAccessTokenSecret="{PAT_value}" >
      <site contentUrl="" />
  </credentials>
</tsRequest>'''

with open('signin.xml', 'w') as file:
    file.write(signin_xml)

# Step 2: Sign in to Tableau Server and retrieve site-id and credentials-token
signin_command = f'curl "{server_url}/api/{api_version}/auth/signin" -X POST -d "@signin.xml"'
signin_output = subprocess.check_output(signin_command, shell=True, encoding='utf-8')

# Parse the XML response to extract site-id and credentials-token
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

# Step 3: Create projects in Tableau Server
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


