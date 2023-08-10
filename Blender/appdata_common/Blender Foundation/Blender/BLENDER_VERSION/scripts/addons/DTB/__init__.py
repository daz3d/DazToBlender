bl_info = {
    "name": "DazToBlender",
    "author": "Daz 3D | https://www.daz3d.com",
    "version": (2023, 1, 1, 15),
    "blender": (2, 80, 0),
    "location": "3DView > ToolShelf",
    "description": "Daz 3D transfer to Blender",
    "warning": "",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/daz3d/DazToBlender/#readme",
    "tracker_url": "https://github.com/daz3d/DazToBlender/issues",
    "category": "Import-Export",
}

import sys
import os
import math

sys.path.append(os.path.dirname(__file__))

import bpy
from copy import deepcopy

from . import ToRigify
from . import Global
from . import Versions
from . import DtbDazMorph
from . import DtbOperators
from . import DtbPanels
from . import DtbMaterial
from . import Util
from . import DtbCommands
from . import DtbIKBones
from . import DtbProperties
from . import DataBase

from bpy.props import PointerProperty
from bpy.app.handlers import persistent
import threading
import time
import json

skinkeys = [
    "Base Color.Hue",
    "Base Color.Saturation",
    "Base Color.Value",
    "Base Color.Bright",
    "Base Color.Contrast",
    "Specular",
    "Roughness",
    "Roughness.Contrast",
    "Specular.Contrast",
    "Subsurface.Scale",
    "Normal.Strength",
    "Bump.Strength",
    "Bump.Distance",
    "Displacement.Height",
]
eyekeys = [
    "Base Color.Hue",
    "Base Color.Saturation",
    "Base Color.Value",
    "Base Color.Bright",
    "Base Color.Contrast",
    "Normal.Strength",
    "Bump.Strength",
    "Bump.Distance",
]

region = "UI"
BV = Versions.getBV()


class MATERIAL_OT_up(bpy.types.Operator):
    bl_idname = "material.up"
    bl_label = "UP"

    def execute(self, context):
        adjust_material(context, False)
        return {"FINISHED"}


def adjust_material(context, is_ms):
    w_mgr = context.window_manager
    Util.active_object_to_current_collection()

    if w_mgr.is_eye:
        arg = eyekeys[int(w_mgr.eye_prop) - 1]
    else:
        arg = skinkeys[int(w_mgr.skin_prop) - 1]
    val = 0.1
    if is_ms:
        val = -0.1
    if ("Hue" in arg) or ("Displacement" in arg):
        val = val / 10
    if w_mgr.ftime_prop:
        val = val * 4
    # if ('Normal' in arg) or ('Bump' in arg) or ('Displacement' in arg):
    #     val = val * 0.01 * Global.getSize()
    if arg != "":
        DtbMaterial.adjust_material(arg, val, w_mgr.is_eye)


class MATERIAL_OT_down(bpy.types.Operator):
    bl_idname = "material.down"
    bl_label = "DOWN"

    def execute(self, context):
        adjust_material(context, True)
        return {"FINISHED"}


class DEFAULT_OT_material(bpy.types.Operator):
    bl_idname = "df.material"
    bl_label = "RESET MATERIAL"

    def execute(self, context):
        Util.active_object_to_current_collection()
        default_material(context)
        return {"FINISHED"}


def default_material(context):
    w_mgr = context.window_manager
    if w_mgr.is_eye:
        # DtbShaders.toEyeDryDefault(bpy.data.node_groups.get(DtbShaders.getGroupNode(DtbShaders.EDRY)))
        DtbMaterial.getGroupNodeTree("EyeDry")
        DtbMaterial.getGroupNodeTree("EyeWet")
    else:
        DtbMaterial.getGroupNodeTree("IrayUberSkin")


class MATCH_OT_ikfk(bpy.types.Operator):
    bl_idname = "match.ikfk"
    bl_label = "Match IK & FK"

    def execute(self, context):
        b2 = ["upper_arm_parent", "thigh_parent"]
        lr = [".R", ".L"]
        trf = ToRigify.ToRigify()
        influence4 = []
        for i in range(2):
            for j in range(2):
                influence4.append(Global.getRgfy().pose.bones[b2[i] + lr[j]]["IK_FK"])
        trf.match_ikfk(influence4)
        return {"FINISHED"}


class SCULPT_OT_push(bpy.types.Operator):
    bl_idname = "to.sculpt"
    bl_label = "To Sculpt"

    def execute(self, context):
        Util.active_object_to_current_collection()
        w_mgr = bpy.context.window_manager
        ddm = DtbDazMorph.DtbDazMorph()
        if Versions.get_active_object().mode == "SCULPT":
            w_mgr.new_morph = False
            Global.setOpsMode("EDIT")
            ddm.select_to_daz_morph(False)
        elif Versions.get_active_object().mode == "OBJECT":
            Global.setOpsMode("SCULPT")
            ddm.select_to_daz_morph(w_mgr.new_morph)
        elif Versions.get_active_object().mode == "EDIT":
            w_mgr.new_morph = False
            Global.setOpsMode("OBJECT")
        return {"FINISHED"}


class EXP_OT_morph(bpy.types.Operator):
    bl_idname = "export.morph"
    bl_label = "To Daz Morph"

    def execute(self, context):
        is_body = context.active_object == Global.getBody()
        #global obj_exported
        ddm = DtbDazMorph.DtbDazMorph()
        ddm.before_execute(is_body)
        flg_ok = ddm.top_export()
        if flg_ok == False:
            self.report({"ERROR"}, "There is no suitable shape key")
        return {"FINISHED"}


class FK2IK_OT_button(bpy.types.Operator):
    bl_idname = "my.fktoik"
    bl_label = "IK"

    def execute(self, context):
        Global.find_AMTR(context.object)
        Global.find_RGFY(context.object)
        if Global.get_Rgfy_name() != "":
            rgfy = ToRigify.ToRigify()
            rgfy.ik2fk(-1)
        else:
            DtbIKBones.hide_ik(-1, False)
            DtbIKBones.mute_bones.append("NG")
            for i in range(len(DtbIKBones.bone_name)):
                DtbIKBones.fktoik(i)
                DtbIKBones.adjust_shin_y(i, True)
            DtbIKBones.mute_bones = []
        return {"FINISHED"}


class IK2FK_OT_button(bpy.types.Operator):
    bl_idname = "my.iktofk"
    bl_label = "FK"

    def execute(self, context):
        Global.find_AMTR(context.object)
        Global.find_RGFY(context.object)
        if Global.get_Rgfy_name() != "":
            rgfy = ToRigify.ToRigify()
            rgfy.fk2ik(-1)
        else:
            DtbIKBones.hide_ik(-1, True)
            DtbIKBones.mute_bones.append("NG")
            for i in range(len(DtbIKBones.bone_name)):
                DtbIKBones.iktofk(i)
                DtbIKBones.adjust_shin_y(i, False)
            DtbIKBones.mute_bones = []
        return {"FINISHED"}


class LIMB_OT_redraw(bpy.types.Operator):
    bl_idname = "limb.redraw"
    bl_label = "ReDisplay Subtle FK/IK"

    def execute(self, context):
        if Global.getAmtr() is None:
            return
        w_mgr = bpy.context.window_manager
        for i in range(4):
            ik_value = DtbIKBones.get_ik_influence(
                DtbIKBones.get_influece_data_path(DtbIKBones.bone_name[i])
            )
            flg_ik = ik_value >= 0.5
            DtbIKBones.hide_ik(i, flg_ik == False)
            if i == 0:
                if w_mgr.ifk0 != flg_ik:
                    w_mgr.ifk0 = flg_ik
            elif i == 1:
                if w_mgr.ifk1 != flg_ik:
                    w_mgr.ifk1 = flg_ik
            elif i == 2:
                if w_mgr.ifk2 != flg_ik:
                    w_mgr.ifk2 = flg_ik
                c = Global.getAmtrConstraint(DataBase.translate_bonenames("rFoot"), "Copy Rotation")
                if c is not None and c.influence != ik_value:
                    c.influence = ik_value
            elif i == 3:
                if w_mgr.ifk3 != flg_ik:
                    w_mgr.ifk3 = flg_ik
                c = Global.getAmtrConstraint("lFoot", "Copy Rotation")
                if c is not None and c.influence != ik_value:
                    c.influence = ik_value
        return {"FINISHED"}


classes = (
    DtbProperties.CustomPathProperties,
    DtbProperties.ImportFilesCollection,
    DtbPanels.DTB_PT_MAIN,
    DtbPanels.DTB_PT_RIGGING,
    DtbPanels.DTB_PT_POSE,
    DtbPanels.DTB_PT_MORPHS,
    DtbPanels.DTB_PT_GENERAL,
    DtbPanels.DTB_PT_COMMANDS,
    DtbPanels.DTB_PT_UTILITIES,
    DtbPanels.DTB_PT_MORE_INFO,
    DtbOperators.OP_SAVE_CONFIG,
    DtbOperators.IMP_OT_POSE,
    DtbOperators.IMP_OT_FBX,
    DtbOperators.IMP_OT_ENV,
    DtbOperators.CLEAR_OT_Pose,
    DtbOperators.REFRESH_DAZ_FIGURES,
    DtbOperators.RENAME_MORPHS,
    DtbOperators.REMOVE_DAZ_OT_button,
    DtbOperators.OPTIMIZE_OT_material,
    DtbCommands.SEARCH_OT_Commands,
    IK2FK_OT_button,
    FK2IK_OT_button,
    MATERIAL_OT_up,
    MATERIAL_OT_down,
    DEFAULT_OT_material,
    DtbOperators.TRANS_OT_Rigify,
    MATCH_OT_ikfk,
    LIMB_OT_redraw,
    EXP_OT_morph,
    SCULPT_OT_push,
)

# Converts difference to a 0 to 1 range
# TO DO: Convert to Follow the rate similiar to Daz Studio
def erc_keyed(var, min, max, normalized_dist, dist):
    if dist < 0:
        if max <= var <= min:
            return abs((var - min) / dist)
        elif max >= var:
            return 1
        else:
            return 0
    if min <= var <= max:
        return abs((var - min * normalized_dist) / dist)
    elif max <= var:
        return 1
    else:
        return 0


@persistent
def load_handler(dummy):
    dns = bpy.app.driver_namespace
    # register your drivers
    dns["erc_keyed"] = erc_keyed


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    DtbProperties.init_props()
    DtbProperties.config_props()
    bpy.types.Scene.dtb_custom_path = PointerProperty(
        type=DtbProperties.CustomPathProperties
    )
    DtbProperties.update_config()
    load_handler(None)
    bpy.app.handlers.load_post.append(load_handler)
    print("DazToBlender: loaded, version %i.%i.%i.%i" % bl_info["version"] )
    intermediateFolder = Global.getRootPath()
    print("DazToBlender: Default Intermediate Folder path: \"%s\"." % intermediateFolder )


def unregister():
    bpy.app.handlers.load_post.remove(load_handler)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.dtb_custom_path


if __name__ == "__main__":
    register()
