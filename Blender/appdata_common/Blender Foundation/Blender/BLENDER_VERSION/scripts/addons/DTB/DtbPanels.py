import bpy
import mathutils
from copy import deepcopy
from . import DazRigBlend
from . import DtbShapeKeys
from . import DataBase
from . import ToRigify
from . import Global
from . import Versions
from . import DtbDazMorph
from . import DtbOperators
from . import DtbMaterial
from . import CustomBones
from . import Poses
from . import Animations
from . import Util
from . import DtbCommands
from . import DtbIKBones
from bpy.props import EnumProperty
from bpy.props import BoolProperty
from bpy.props import StringProperty
import threading
import time


region = "UI"
BV = Versions.getBV()


class View3DPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = region
    if BV < 2.80:
        bl_category = "Tools"
    else:
        bl_category = "Daz To Blender"


class DTB_PT_MAIN(View3DPanel, bpy.types.Panel):
    bl_label = "Daz To Blender"
    bl_idname = "VIEW3D_PT_main_daz"

    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        box.operator("import_dtu.fig", icon="POSE_HLT")
        box.operator("import_dtu.env", icon="WORLD")
        if context.object and context.active_object:
            cobj = context.active_object
            if (
                Global.get_Body_name() == ""
                and Global.get_Rgfy_name() == ""
                and Global.get_Amtr_name() == ""
            ):
                Global.clear_variables()
                Global.decide_HERO()
            if (
                context.object.type == "ARMATURE"
                and Global.getRgfy() is None
                and Global.getAmtr() is None
            ):
                Global.clear_variables()
                Global.find_AMTR(cobj)
                Global.find_RGFY(cobj)
            if context.object.type == "MESH" and Global.getBody() is None:
                Global.clear_variables()
                Global.find_BODY(cobj)
            if cobj.mode == "POSE":
                if (
                    Global.get_Amtr_name() != cobj.name
                    and len(cobj.data.bones) > 90
                    and len(cobj.data.bones) < 200
                ):
                    Global.clear_variables()
                    Global.find_Both(cobj)
                if Global.get_Rgfy_name() != cobj.name and len(cobj.data.bones) > 600:
                    Global.clear_variables()
                    Global.find_Both(cobj)
            elif context.object.type == "MESH":
                if (
                    Global.get_Body_name() != ""
                    and Global.get_Body_name() != cobj.name
                    and len(cobj.vertex_groups) > 163
                    and len(cobj.data.vertices) >= 16384
                    and len(cobj.vertex_groups) < 500
                    and len(cobj.data.vertices) < 321309
                ):
                    Global.clear_variables()
                    Global.find_Both(cobj)

            if Global.amIBody(context.object):
                col = l.column(align=True)
                box = col.box()
                row = box.row(align=True)
                row.alignment = "EXPAND"
                row.prop(w_mgr, "is_eye", text="Eye")
                row.prop(w_mgr, "ftime_prop", text="x 4")
                if w_mgr.is_eye:
                    box.prop(w_mgr, "eye_prop", text="")
                else:
                    box.prop(w_mgr, "skin_prop", text="")
                row = box.row(align=True)
                row.alignment = "EXPAND"
                row.operator("material.up", icon="TRIA_UP")
                row.operator("material.down", icon="TRIA_DOWN")
                box.operator("df.material")
            if context.object.type == "MESH":
                if Global.isRiggedObject(context.object):
                    if Versions.get_active_object().mode == "OBJECT":
                        l.prop(w_mgr, "new_morph", text="Make New Morph")
                    row = l.row(align=True)
                    row.operator("export.morph", icon="TRIA_LEFT")
                    row.operator("to.sculpt", icon="MONKEY")
                    if DtbIKBones.obj_exported != "":
                        l.label(text=DtbIKBones.obj_exported)

                l.separator()


class DTB_PT_RIGGING(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_rigging_daz"
    bl_label = "Rigging Tools"

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        if context.object and context.active_object:
            cobj = context.active_object
            if (
                DtbIKBones.ik_access_ban == False
                and context.active_object.mode == "POSE"
            ):
                if Global.amIAmtr(context.object):
                    col = l.column(align=True)
                    r = col.row(align=True)
                    for i in range(len(DtbIKBones.ik_name)):
                        if i == 2:
                            r = col.row(align=True)
                        influence_data_path = DtbIKBones.get_influece_data_path(
                            DtbIKBones.bone_name[i]
                        )
                        if influence_data_path is not None:
                            r.prop(
                                w_mgr,
                                "ifk" + str(i),
                                text=DtbIKBones.ik_name[i],
                                toggle=True,
                            )
                    col.operator("limb.redraw", icon="LINE_DATA")
                    l.separator()
                elif Global.amIRigfy(context.object):
                    if BV < 2.81:
                        row = l.row(align=True)
                        row.alignment = "EXPAND"
                        row.operator("my.iktofk", icon="MESH_CIRCLE")
                        row.operator("my.fktoik", icon="MESH_CUBE")
                if Global.amIAmtr(context.object):
                    l.operator("to.rigify", icon="ARMATURE_DATA")
                if Global.amIRigfy(context.object):
                    if BV < 2.81:
                        row = l.row(align=True)
                        row.alignment = "EXPAND"
                        row.operator("match.ikfk")
                        row.prop(
                            w_mgr,
                            "br_onoff_prop",
                            text="Limit Bone Rotation",
                            toggle=True,
                        )
                    else:
                        l.prop(
                            w_mgr,
                            "br_onoff_prop",
                            text="Limit Bone Rotation",
                            toggle=True,
                        )


class DTB_PT_POSE(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_pose_daz"
    bl_label = "Pose Tools"

    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        l.operator("my.clear")
        l.separator()
        row = box.row(align=True)
        row.prop(w_mgr, "choose_daz_figure", text="")
        row.operator("refresh.alldaz", text="", icon="FILE_REFRESH")
        box.operator("import.pose", icon="POSE_HLT")
        row = box.row(align=True)
        row.prop(w_mgr, "add_pose_lib", text="Add to Pose Library", toggle=False)


class DTB_PT_MATERIAL(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_material_daz"
    bl_label = "Material Settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        box.label(text="Import Settings")
        row = box.row(align=True)
        row.prop(
            w_mgr, "combine_materials", text="Combine Dupe Materials", toggle=False
        )


class DTB_PT_GENERAL(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_general_daz"
    bl_label = "Import Settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        scn = context.scene

        box = l.box()
        col = box.column(align=True, heading="Material Settings")
        col.prop(
            w_mgr, "combine_materials", text="Combine Dupe Materials", toggle=False
        )

        box = l.box()
        col = box.column(align=True, heading="Morph Settings")
        col.prop(w_mgr, "morph_prefix", text="Remove Morph Prefix", toggle=False)
        col.prop(w_mgr, "morph_optimize", text="Optimize Morphs", toggle=False)

        box = l.box()
        col = box.column(align=True, heading="Scenes Settings")
        col.prop(
            w_mgr, "update_scn_settings", text="Update Viewport Shading", toggle=False
        )
        col.prop(w_mgr, "update_viewport", text="Update Camera and Units", toggle=False)
        col.prop(w_mgr, "scene_scale", text="")

        box = l.box()
        col = box.column(align=True, heading="Auto-Import Settings")
        col.prop(w_mgr, "use_custom_path", toggle=False)
        col.prop(scn.dtb_custom_path, "path", text="")

        l.operator("save.daz_settings", icon="DISK_DRIVE")

#TODO: [BRIDGEBUGS-1] Commands Currently do not work as intended need to be refactored and reactivated. 
class DTB_PT_COMMANDS(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_commands_daz"
    bl_label = "Commands List"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        l.label(text="What does it do?:  Command")
        l.label(text="Imports Pose:   #getpose")
        row = l.row(align=True)
        row.alignment = "EXPAND"
        row.prop(w_mgr, "search_prop")
        if context.object and context.active_object:
            if context.object.type == "MESH":
                row.operator("command.search", icon="VIEWZOOM")
        else:
            row.operator("command.search", icon="HAND")


class DTB_PT_MORPHS(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_morphs_daz"
    bl_label = "Morphs List"

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        box = l.box()
        row = box.row(align=True)
        row.alignment = "EXPAND"
        row.prop(w_mgr, "choose_daz_figure", text="")
        row.operator("refresh.alldaz", text="", icon="FILE_REFRESH")
        row = box.row(align=True)
        row.alignment = "EXPAND"
        row.prop(w_mgr, "search_morph_list")
        morph_filter = w_mgr.search_morph_list
        morph_custom_props = Global.get_shape_key_custom_props()
        if len(morph_custom_props) == 0:
            return
        # For each mesh shape add custom shape key properties if any
        for custom_prop in reversed(morph_custom_props):
            mesh_name = custom_prop["mesh"]
            if mesh_name not in bpy.data.objects:
                continue
            mesh_obj = bpy.data.objects[mesh_name]
            l.label(text=mesh_name)
            for morph_prop_name in reversed(custom_prop["props"]):
                if (
                    len(morph_filter) == 0
                    or morph_filter.lower() in morph_prop_name.lower()
                    or morph_filter == "Type Keyword Here"
                ):
                    l.prop(mesh_obj, '["' + morph_prop_name + '"]', slider=True)


class DTB_PT_UTILITIES(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_utilities_daz"
    bl_label = "Utilities"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        box = l.box()
        row = box.row(align=True)
        row.alignment = "EXPAND"
        row.prop(w_mgr, "choose_daz_figure", text="")
        row.operator("refresh.alldaz", text="", icon="FILE_REFRESH")
        box.operator("rename.morphs", icon="OUTLINER_DATA_MESH")
        l.operator("refresh.alldaz", icon="BOIDS")
        l.operator("remove.alldaz", icon="BOIDS")


class DTB_PT_MORE_INFO(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_info_daz"
    bl_label = "More Info"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        l.label(text="Check out these links for more info!")
        box = l.box()
        row = l.row(align=True)
        row.alignment = "EXPAND"
        box.operator(
            "wm.url_open", text="Create a Support Ticket", icon="URL"
        ).url = "https://helpdaz.zendesk.com/hc/en-us/requests/new?ticket_form_id=23788"
        box.operator(
            "wm.url_open", text="Meet the Bridge Team", icon="URL"
        ).url = "https://www.daz3d.com/forums/discussion/469341/daz-to-blender-bridge-meet-the-team#latest"
        box.operator(
            "wm.url_open", text="Report a Bug", icon="URL"
        ).url = "https://github.com/daz3d/DazToBlender/issues"
        box.operator(
            "wm.url_open", text="Past Versions", icon="URL"
        ).url = "https://github.com/daz3d/DazToBlender/releases"
