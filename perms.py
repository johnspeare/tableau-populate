import subprocess
import xml.etree.ElementTree as ET

# User-defined variables
server_url = 'https://us-west-2a.online.tableau.com/' #'https://example.yourdomain.org'
site_name = '' #leave this as empty set if running against Default Tablau Server site
PAT_name = "name"
PAT_value = "A38FlZnrSc-blah-blah-blahKNEwXoZVbKHX2fDB0dPMmS"
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

# Step 5: Remove "All Users" group Write-Allow from projects with names containing "Project"
for project in projects:
    project_name = project.attrib.get('name')
    project_id = project.attrib.get('id')

    # Check if the project name contains "Project"
    if "Project" in project_name:
        # Find the group_id for "All Users" based on its name
        all_users_group = next((group for group in groups if group.attrib.get('name') == "All Users"), None)
        if all_users_group is not None:
            group_id = all_users_group.attrib.get('id')

            # Construct the Remove Permission REST API command
            project_permissions_command = f'curl "{server_url}/api/{api_version}/sites/{site_id}/projects/{project_id}/permissions/groups/{group_id}/Write/Allow" -X DELETE -H "X-Tableau-Auth: {credentials_token}"'

            # Execute the command
            print(f"\nRemoving Write-Allow permission for 'All Users' group from Project {project_name}...")
            subprocess.call(project_permissions_command, shell=True)
        else:
            print(f"Warning: 'All Users' group not found for Project {project_name}.")

print("\nWrite-Allow permission removed for 'All Users' group from eligible projects.")



# Step 6: Add "Write-Allow" permissions for each group to at least one project
group_index = 0  # To keep track of the current group
project_index = 0  # To keep track of the current project

while project_index < len(projects):
    project = projects[project_index]
    project_name = project.attrib.get('name', '')

    # Check if the project name starts with "Project" followed by an integer
    if project_name.startswith("Project") and project_name[7:].isdigit():
        group = groups[group_index % len(groups)]  # Reuse groups in order
        group_name = group.attrib.get('name', '')

        # Check if the group name starts with "Group" followed by an integer
        if group_name.startswith("Group") and group_name[5:].isdigit():
            # Assign the group to the project
            group_id = group.attrib.get('id')
            project_id = project.attrib.get('id')

            # Construct the XML request file for adding permission
            xml_request = f'''<tsRequest>
              <permissions>
                <granteeCapabilities>
                  <group id="{group_id}" />
                  <capabilities>
                    <capability name="Write" mode="Allow" />
                  </capabilities>
                </granteeCapabilities>
              </permissions>
            </tsRequest>'''

            # Save the XML request to a file
            with open('add_perms.xml', 'w') as file:
                file.write(xml_request)

            # Use the cURL command to add permission
            add_project_permissions_command = f'curl "{server_url}/api/{api_version}/sites/{site_id}/projects/{project_id}/permissions/" -X PUT -H "X-Tableau-Auth:{credentials_token}" -d @add_perms.xml'

            # Execute the command
            print(f"\nAdding Write-Allow permission for Group {group_name} to Project {project_name}...")
            subprocess.call(add_project_permissions_command, shell=True)

            # Move to the next group
            group_index += 1
        else:
            # Move to the next group if the current group is not in the correct format
            group_index += 1
            continue

    # Move to the next project
    project_index += 1

print("\nWrite-Allow permissions added for groups to projects.")
