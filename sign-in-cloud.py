import subprocess
import xml.etree.ElementTree as ET

# User-defined variables
server_url = 'https://us-west-2a.online.tableau.com/'
site_name = 'johndogfood'
PAT_name = 'cloudrunner'
PAT_value = '8NWdr5EPS9uWOJ0GGcOEFQ==:aAS0bNrkVY5VGjgNP7KbUVN63rcJLGE7'
api_version = "3.4"

# Step 1: Generate signin.xml file
signin_xml = f'''<tsRequest>
  <credentials personalAccessTokenName="{PAT_name}"
    personalAccessTokenSecret="{PAT_value}" >
      <site contentUrl="{site_name}" />
  </credentials>
</tsRequest>'''

with open('signin.xml', 'w') as file:
    file.write(signin_xml)

# Step 2: Sign in to Tableau Server and retrieve site-id and credentials-token
signin_command = f'curl "{server_url}/api/{api_version}/auth/signin" -X POST -d "@signin.xml"'
print(f"REST Command: {signin_command}")

signin_output = subprocess.check_output(signin_command, shell=True, encoding='utf-8')
print(f"Response:\n{signin_output}")

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

# Step 3: Query Tableau Server to get group information
groups_url = f'{server_url}/api/{api_version}/sites/{site_id}/groups'
headers = {'X-Tableau-Auth': credentials_token}
groups_command = f'curl "{groups_url}" -H "X-Tableau-Auth: {credentials_token}"'
print(f"\nREST Command: {groups_command}")

groups_output = subprocess.check_output(groups_command, shell=True, encoding='utf-8')
print(f"\nGroup Information:\n{groups_output}")

# Parse the XML response to extract group IDs and names
groups_root = ET.fromstring(groups_output)
groups = groups_root.findall('.//t:group', namespaces)

if len(groups) > 0:
    print("\nGroup IDs and Names:")
    for group in groups:
        group_id = group.attrib.get('id')
        group_name = group.attrib.get('name')
        print(f"Group ID: {group_id}\tGroup Name: {group_name}")
else:
    print("No groups exist on this server.")

# Step 4: Query Tableau Server to get project names and IDs
projects_url = f'{server_url}/api/{api_version}/sites/{site_id}/projects'
projects_command = f'curl "{projects_url}" -H "X-Tableau-Auth: {credentials_token}"'
print(f"\nREST Command: {projects_command}")

projects_output = subprocess.check_output(projects_command, shell=True, encoding='utf-8')
print(f"\nProject Information:\n{projects_output}")

# Parse the XML response to extract project IDs and names
projects_root = ET.fromstring(projects_output)
projects = projects_root.findall('.//t:project', namespaces)

if len(projects) > 0:
    print("\nProject IDs and Names:")
    for project in projects:
        project_id = project.attrib.get('id')
        project_name = project.attrib.get('name')
        print(f"Project ID: {project_id}\tProject Name: {project_name}")
else:
    print("No projects exist on this server.")

# Print the Site ID and Credentials Token
print(f"\nSite ID: {site_id}")
print(f"Credentials Token: {credentials_token}")

# Step 5: Check if test projects or groups exist
test_projects_exist = any(project.attrib.get('name', '').startswith("Project") for project in projects)
test_groups_exist = any(group.attrib.get('name', '').startswith("Group") for group in groups)

if test_projects_exist or test_groups_exist:
    prompt = input("\nTo delete the test Projects and Groups, enter 'delete': ")

    if prompt.lower() == "delete":
        # Delete test projects
        for project in projects:
            project_name = project.attrib.get('name')
            if project_name.startswith("Project"):
                project_id = project.attrib.get('id')
                delete_project_url = f'{server_url}/api/{api_version}/sites/{site_id}/projects/{project_id}'
                delete_project_command = f'curl "{delete_project_url}" -X DELETE -H "X-Tableau-Auth: {credentials_token}"'
                subprocess.run(delete_project_command, shell=True)
                print(f"\nDeleted Project: {project_name}")

        # Delete test groups
        for group in groups:
            group_name = group.attrib.get('name')
            if group_name.startswith("Group"):
                group_id = group.attrib.get('id')
                delete_group_url = f'{server_url}/api/{api_version}/sites/{site_id}/groups/{group_id}'
                delete_group_command = f'curl "{delete_group_url}" -X DELETE -H "X-Tableau-Auth: {credentials_token}"'
                subprocess.run(delete_group_command, shell=True)
                print(f"\nDeleted Group: {group_name}")

        print("\nDeletion completed.")
    else:
        print("\nDeletion not performed.")
else:
    print("\nNo test projects or groups exist on this server.")
