from . import group_data
from . import custom_renamer
from . import group_pie_menu
from . import addon_updater
from . import curve_namer

bl_info = {
    "name": "Group Renamer",
    "author": "Luka4D",
    "version": (1, 3, 0),
    "blender": (4, 2),
    "location": "View3D > Sidebar > Namer Tab",
    "description": "Rename objects based on group and sub-group, with pie menu support",
    "category": "Object",
}

if "bpy" in locals():
    import importlib
    importlib.reload(group_data)            # <--- RELOAD group_data NOW
    importlib.reload(custom_renamer)
    importlib.reload(group_pie_menu)
    importlib.reload(curve_namer)
    importlib.reload(collection_bundler)
    importlib.reload(addon_updater)
else:
    from . import group_data                 # <--- IMPORT group_data
    from . import custom_renamer
    from . import group_pie_menu
    from . import curve_namer
    from . import collection_bundler
    from . import addon_updater

def register():
    custom_renamer.register()
    group_pie_menu.register()
    curve_namer.register()
    collection_bundler.register()
    addon_updater.register_updater()
    addon_updater.check_for_update()

def unregister():
    group_pie_menu.unregister()
    custom_renamer.unregister()
    curve_namer.unregister()
    collection_bundler.unregister()
    addon_updater.register_updater()
    addon_updater.check_for_update()