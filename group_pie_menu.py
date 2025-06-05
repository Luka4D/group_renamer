import bpy
from bpy.types import Menu, Operator
from bpy.props import StringProperty
from .group_data import GROUPS
import bmesh

# --- Operator to rename
class OBJECT_OT_rename_to_subgroup_pie(Operator):
    bl_idname = "object.rename_to_subgroup_pie"
    bl_label = "Rename to Sub-Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No valid mesh object selected.")
            return {'CANCELLED'}

        new_name = self.name.strip()
        if not new_name:
            self.report({'ERROR'}, "Invalid name provided.")
            return {'CANCELLED'}

        mesh = obj.data

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.to_mesh(mesh)
        bm.free()

        obj.name = new_name
        mesh.name = new_name

        self.report({'INFO'}, f"Renamed to {new_name}")
        return {'FINISHED'}

# --- Submenus per group (Dropdowns, not pies)
def make_dropdown_menu(group, items):
    class SubMenu(Menu):
        bl_idname = f"SUBMENU_MT_{group}"
        bl_label = group.replace("_", " ")

        def draw(self, context):
            layout = self.layout
            for sub in items:
                op = layout.operator("object.rename_to_subgroup_pie", text=sub)
                op.name = sub

    return SubMenu

# --- Main Pie Menu
class PIE_MT_group_menu(Menu):
    bl_label = "Group Pie Menu"
    bl_idname = "PIE_MT_group_menu"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for group in GROUPS:
            pie.menu(f"SUBMENU_MT_{group}", text=group.replace("_", " "), icon='GROUP')

# --- Dynamic Submenus Storage
submenus = []

def generate_submenus():
    """Generate submenus based on current GROUPS"""
    global submenus
    submenus.clear()
    for group, items in GROUPS.items():
        submenu = make_dropdown_menu(group, items)
        submenus.append(submenu)

# --- Operator to Regenerate Pie Menus
class OBJECT_OT_refresh_group_pie_menus(Operator):
    bl_idname = "wm.refresh_group_pie_menus"
    bl_label = "Refresh Group Pie Menus"
    bl_description = "Regenerate group pie menus after changing GROUPS"

    def execute(self, context):
        unregister_submenus()
        generate_submenus()
        register_submenus()
        self.report({'INFO'}, "Group Pie Menus refreshed.")
        return {'FINISHED'}

def register_submenus():
    for cls in submenus:
        bpy.utils.register_class(cls)

def unregister_submenus():
    for cls in reversed(submenus):
        bpy.utils.unregister_class(cls)

# --- Registration
addon_keymaps = []

def register():
    bpy.utils.register_class(OBJECT_OT_rename_to_subgroup_pie)
    bpy.utils.register_class(PIE_MT_group_menu)
    bpy.utils.register_class(OBJECT_OT_refresh_group_pie_menus)

    generate_submenus()
    register_submenus()

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_menu_pie", "U", "PRESS", alt=True)
        kmi.properties.name = "PIE_MT_group_menu"
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    unregister_submenus()
    bpy.utils.unregister_class(PIE_MT_group_menu)
    bpy.utils.unregister_class(OBJECT_OT_rename_to_subgroup_pie)
    bpy.utils.unregister_class(OBJECT_OT_refresh_group_pie_menus)

def draw(self, context):
    layout = self.layout
    props = context.scene.rename_props

    layout.prop(props, "group")
    layout.prop(props, "sub_group")

    row = layout.row()
    row.scale_y = 1.3
    row.operator("object.rename_to_subgroup", icon="FILE_TICK")

    layout.separator()
    layout.operator("wm.refresh_group_pie_menus", icon="FILE_REFRESH")
