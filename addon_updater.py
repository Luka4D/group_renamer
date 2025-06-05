import bpy
from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, BoolProperty
import urllib.request
import zipfile
import os
import shutil
import json
import importlib

# Your repo information here
GITHUB_API_RELEASES = "https://api.github.com/repos/Luka4D/group_renamer/releases/latest"
DOWNLOAD_URL_TEMPLATE = "https://github.com/Luka4D/group_renamer/archive/refs/tags/v{tag_name}.zip"

def get_bl_info():
    """
    Dynamically load the bl_info dictionary from __init__.py
    to avoid a circular import.
    """
    module = importlib.import_module(__package__)
    return module.bl_info


def get_latest_version_info():
    url = GITHUB_API_RELEASES
    # Adding a simple User-Agent header so GitHub doesn’t reject the request
    req = urllib.request.Request(url,
        headers={"User-Agent": "group_renamer-addon/1.2.0"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            tag_name = data.get("tag_name", "")
            return tag_name.lstrip("v")  # e.g. "1.2.0"
    except Exception as e:
        print(f"Failed to fetch latest release: {e}")
        return None


def download_and_install_update(tag_name):
    download_url = DOWNLOAD_URL_TEMPLATE.format(tag_name=tag_name)
    temp_zip_path = os.path.join(bpy.app.tempdir, "group_renamer_update.zip")

    try:
        # Download the zip
        urllib.request.urlretrieve(download_url, temp_zip_path)

        # Extract it
        extract_path = os.path.join(bpy.app.tempdir, "group_renamer_extracted")
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # The extracted folder is usually named 'group_renamer-<tag_name>/'
        extracted_subfolder = next(os.scandir(extract_path)).path

        # Copy files over to the addon directory
        addon_dir = os.path.dirname(__file__)

        for item in os.listdir(extracted_subfolder):
            src = os.path.join(extracted_subfolder, item)
            dst = os.path.join(addon_dir, item)

            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        return True
    except Exception as e:
        print(f"Update failed: {e}")
        return False


class GroupRenamerPreferences(AddonPreferences):
    bl_idname = __package__

    update_available: BoolProperty(default=False)
    latest_version: StringProperty(default="")

    def draw(self, context):
        layout = self.layout
        bl_info = get_bl_info()
        current_ver = ".".join(map(str, bl_info["version"]))
        layout.label(text=f"Current Version: {current_ver}")

        if self.update_available:
            row = layout.row()
            row.alert = True
            row.operator("group_renamer.update_addon", text=f"UPDATE Available: {self.latest_version}")
        else:
            layout.label(text="Addon is up to date.")


class GROUPRENAMER_OT_UpdateAddon(Operator):
    bl_idname = "group_renamer.update_addon"
    bl_label = "Update Addon"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        success = download_and_install_update(prefs.latest_version)
        if success:
            self.report({'INFO'}, "Update successful. Please restart Blender.")
        else:
            self.report({'ERROR'}, "Update failed. See system console for details.")
        return {'FINISHED'}


def check_for_update():
    latest_version_str = get_latest_version_info()
    if not latest_version_str:
        return

    latest_version = tuple(map(int, latest_version_str.split(".")))
    bl_info = get_bl_info()
    current_version = bl_info["version"]

    prefs = bpy.context.preferences.addons[__package__].preferences
    if latest_version > current_version:
        prefs.update_available = True
        prefs.latest_version = latest_version_str
    else:
        prefs.update_available = False
        prefs.latest_version = ""


def register_updater():
    bpy.utils.register_class(GroupRenamerPreferences)
    bpy.utils.register_class(GROUPRENAMER_OT_UpdateAddon)


def unregister_updater():
    bpy.utils.unregister_class(GroupRenamerPreferences)
    bpy.utils.unregister_class(GROUPRENAMER_OT_UpdateAddon)
