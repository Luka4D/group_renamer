import bpy
import bmesh
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import EnumProperty, PointerProperty
from .group_data import GROUPS

def link_material(material_name, blend_path):
    if not blend_path:
        print("No blend path set, skipping material link.")
        return None
    
    try:
        with bpy.data.libraries.load(blend_path, link=True) as (data_from, data_to):
            if material_name in data_from.materials:
                if material_name not in bpy.data.materials:
                    data_to.materials.append(material_name)
        return bpy.data.materials.get(material_name)
    except Exception as e:
        print(f"Failed to link material '{material_name}': {e}")
        return None        

def update_subgroup(self, context):
    if self.group in GROUPS:
        subgroups = GROUPS[self.group]
        self.sub_group = subgroups[0] if subgroups else ""

class RenameProps(PropertyGroup):
    group: EnumProperty(
        name="Group",
        items=[(str(k), k.replace("_", " "), "") for k in GROUPS.keys()],
        default="Arm_Group",
        update=update_subgroup
    )

    def get_subgroup_items(self, context):
        group_items = GROUPS.get(self.group, [])
        return [(str(item), item.replace("_", " "), "") for item in group_items]

    sub_group: EnumProperty(
        name="Sub-Group",
        items=get_subgroup_items,
    )

    def init_defaults(self):
        """Force initial sub_group assignment after registration"""
        if self.group in GROUPS:
            subgroups = GROUPS[self.group]
            if subgroups:
                self.sub_group = subgroups[0]

class OBJECT_OT_rename_to_subgroup(Operator):
    bl_idname = "object.rename_to_subgroup"
    bl_label = "Rename"
    bl_description = "Rename the active object and its mesh data to the selected sub-group without causing context switches"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and obj.data is not None

    def execute(self, context):
        props = context.scene.rename_props
        obj = context.active_object
        mesh = obj.data

        new_name = props.sub_group.strip()
        if not new_name:
            self.report({'ERROR'}, "Sub-group name is empty. Cannot rename.")
            return {'CANCELLED'}

        # Safe BMesh operations without needing to enter edit mode
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.to_mesh(mesh)
        bm.free()

        obj.name = new_name
        mesh.name = new_name

        self.report({'INFO'}, f"Renamed object and mesh to {new_name}")
    
        # Link and assign material
        try:
            preferences = context.preferences.addons[__package__].preferences
            blend_path = preferences.materials_blend_path
            material_name = new_name.lower()

            mat = link_material(material_name, blend_path)
            if mat:
                # Clear existing materials and assign new one
                obj.data.materials.clear()
                obj.data.materials.append(mat)
                self.report({'INFO'}, f"Renamed and assigned material '{material_name}'")
            else:
                self.report({'WARNING'}, f"Material '{material_name}' not found or failed to link.")
        except Exception as e:
            self.report({'ERROR'}, f"Material assignment error: {e}")

        return {'FINISHED'}

class VIEW3D_PT_group_renamer(Panel):
    bl_label = "Group Renamer"
    bl_idname = "VIEW3D_PT_group_renamer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Rename"

    def draw(self, context):
        layout = self.layout
        props = context.scene.rename_props

        # Lazy Init: Only if empty!
        if not props.sub_group:
            props.init_defaults()

        layout.prop(props, "group")
        layout.prop(props, "sub_group")

        row = layout.row()
        row.scale_y = 1.3
        row.operator("object.rename_to_subgroup", icon="FILE_TICK")

        layout.separator()
        layout.operator("wm.refresh_group_pie_menus", icon="FILE_REFRESH")


classes = (
    RenameProps,
    OBJECT_OT_rename_to_subgroup,
    VIEW3D_PT_group_renamer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rename_props = PointerProperty(type=RenameProps)
    # ❌ No more direct scene access!

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.rename_props
