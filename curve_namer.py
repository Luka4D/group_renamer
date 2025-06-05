import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty

# --- Suffix list
SUFFIXES = [
    "", "_second", "_third", "_fourth", "_fifth",
    "_sixth", "_seventh", "_eighth", "_ninth", "_tenth"
]

def get_suffix(index):
    if index < len(SUFFIXES):
        return SUFFIXES[index]
    else:
        return f"_{index+1}th"

def get_used_object_names(exclude_objects):
    exclude_set = set(exclude_objects)
    return {obj.name for obj in bpy.data.objects if obj not in exclude_set}

def get_used_curve_data_names(exclude_objects):
    exclude_data = {obj.data for obj in exclude_objects if obj.type == 'CURVE'}
    return {obj.data.name for obj in bpy.data.objects if obj.type == 'CURVE' and obj.data not in exclude_data}

# --- Operator
class OBJECT_OT_rename_curves(Operator):
    bl_idname = "object.rename_curves"
    bl_label = "Rename Selected Curves"
    bl_description = "Rename selected curves based on the selected sub-group name"

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'CURVE']

        if not selected:
            self.report({'WARNING'}, "No curves selected!")
            return {'CANCELLED'}

        rename_props = context.scene.rename_props
        base_name = rename_props.sub_group.strip()

        if not base_name:
            self.report({'WARNING'}, "No sub-group selected!")
            return {'CANCELLED'}

        selected.sort(key=lambda o: o.name)

        existing_object_names = get_used_object_names(selected)
        existing_curve_data_names = get_used_curve_data_names(selected)

        for i, obj in enumerate(selected):
            suffix = get_suffix(i)
            new_name = f"{base_name}_curve{suffix}"

            if new_name in existing_object_names or new_name in existing_curve_data_names:
                self.report({'WARNING'}, f"Name '{new_name}' already exists. Skipping '{obj.name}'.")
                continue

            obj.name = new_name
            obj.data.name = new_name

            existing_object_names.add(new_name)
            existing_curve_data_names.add(new_name)

        self.report({'INFO'}, f"Renamed {len(selected)} curves using base name '{base_name}'.")
        return {'FINISHED'}

# --- Panel
class VIEW3D_PT_curve_renamer(Panel):
    bl_label = "Curve Renamer"
    bl_idname = "VIEW3D_PT_curve_renamer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Rename"  # Same tab as your Namer

    def draw(self, context):
        layout = self.layout
        layout.label(text="Curve Renamer")
        layout.operator("object.rename_curves", icon='OUTLINER_OB_CURVE')

# --- Registration
classes = (
    OBJECT_OT_rename_curves,
    VIEW3D_PT_curve_renamer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
