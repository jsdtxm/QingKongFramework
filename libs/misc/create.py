import os
import shutil
from pathlib import Path
from libs.utils.strings import to_camel_case

def create_app(app_name):
    apps_dir = Path('apps')
    template_dir = Path('libs/apps/template')
    
    # Check if the app_name directory already exists in the apps folder
    new_app_path = apps_dir / app_name
    if new_app_path.exists():
        raise FileExistsError(f"An app with the name '{app_name}' already exists.")
    
    # Copy the template directory to the new app directory
    shutil.copytree(template_dir, new_app_path)
    
    # Replace the placeholder in all files within the new app directory
    for root, dirs, files in os.walk(new_app_path):
        for file_name in files:
            file_path = Path(root) / file_name
            
            # Read in the file
            with open(file_path, 'r', encoding='utf-8') as file :
              file_data = file.read()
            
            # Replace the target string
            new_data = file_data.replace("app_name", app_name).replace("AppName", to_camel_case(app_name))
            
            # Write the file out again
            with open(file_path, 'w', encoding='utf-8') as file:
              file.write(new_data)
