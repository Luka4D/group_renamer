import bpy
from bpy.types import Operator, Panel
from .group_data import GROUPS


def ensure_collection(name, color_tag=None):
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)

    if color_tag:
        col.color_tag = color_tag

    return col


def ensure_empty(name):
    if name in bpy.data.objects:
        obj = bpy.data.objects[name]
    else:
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)
    return obj


def safe_link_to_collection(obj, target_col):
    for col in obj.users_collection:
        if col != target_col:
            col.objects.unlink(obj)
    if obj.name not in target_col.objects:
        target_col.objects.link(obj)


def bundle_selected_objects():
    selected_objs = [obj for obj in bpy.context.selected_objects if obj.type in {'MESH', 'CURVE'}]

    if not selected_objs:
        raise RuntimeError("No supported objects selected.")

    export_col = ensure_collection("EXPORT", color_tag='COLOR_04')
    orphan_col = ensure_collection("ORPHAN", color_tag='COLOR_01')

    group_empties = {}
    curves_empty = ensure_empty("Curves_Group")
    placeholder = ensure_empty("PLACEHOLDER")

    safe_link_to_collection(curves_empty, export_col)
    safe_link_to_collection(placeholder, export_col)

    for obj in selected_objs:
        name = obj.name.lower()
        assigned = False

        if "curve" in name:
            for group, subs in GROUPS.items():
                if any(sub.lower() in name for sub in subs):
                    safe_link_to_collection(obj, export_col)
                    if obj != curves_empty:
                        obj.parent = curves_empty
                    assigned = True
                    break
            if not assigned:
                safe_link_to_collection(obj, orphan_col)
            continue

        for group, subs in GROUPS.items():
            if any(sub.lower() in name for sub in subs):
                if group not in group_empties:
                    group_empties[group] = ensure_empty(group)
                    safe_link_to_collection(group_empties[group], export_col)
                    group_empties[group].parent = placeholder
                safe_link_to_collection(obj, export_col)
                if obj != group_empties[group]:
                    obj.parent = group_empties[group]
                assigned = True
                break

        if not assigned:
            safe_link_to_collection(obj, orphan_col)

    curves_empty.parent = placeholder


class OBJECT_OT_bundle_collection(Operator):
    bl_idname = "object.bundle_selected"
    bl_label = "Bundle Selection"
    bl_description = "Move selected objects/curves into EXPORT collection with parenting hierarchy"

    def execute(self, context):
        try:
            bundle_selected_objects()
        except Exception as e:
            self.report({'ERROR'}, f"Bundling failed: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, "Bundling complete.")
        return {'FINISHED'}


class VIEW3D_PT_bundle_panel(Panel):
    bl_label = "Collection Bundler"
    bl_idname = "VIEW3D_PT_collection_bundler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Rename"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.bundle_selected", icon="PACKAGE")


def register():
    bpy.utils.register_class(OBJECT_OT_bundle_collection)
    bpy.utils.register_class(VIEW3D_PT_bundle_panel)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_bundle_panel)
    bpy.utils.unregister_class(OBJECT_OT_bundle_collection)
