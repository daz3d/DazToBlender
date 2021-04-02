bl_info = {
    "name": "DazToBlender",
    "author": "Daz 3D | https://www.daz3d.com",
    "version": (2, 3, 0, 4),
    "blender": (2, 80, 0),
    "location": "3DView > ToolShelf",
    "description": "Daz 3D Genesis 3/8 transfer to Blender",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Armature"
}

import sys
import os
import math
sys.path.append(os.path.dirname(__file__))
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
from . import DtbPanels
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
skinkeys = [
    'Base Color.Hue',
    'Base Color.Saturation',
    'Base Color.Value',
    'Base Color.Bright',
    'Base Color.Contrast',
    'Specular',
    'Roughness',
    'Roughness.Contrast',
    'Specular.Contrast',
    'Subsurface.Scale',
    'Normal.Strength',
    'Bump.Strength',
    'Bump.Distance',
    'Displacement.Height',
]
eyekeys=[
    'Base Color.Hue',
    'Base Color.Saturation',
    'Base Color.Value',
    'Base Color.Bright',
    'Base Color.Contrast',
    'Normal.Strength',
    'Bump.Strength',
    'Bump.Distance',
]

region = 'UI'
BV = Versions.getBV()



class MATERIAL_OT_up(bpy.types.Operator):
    bl_idname = "material.up"
    bl_label = "UP"
    def execute(self, context):
        adjust_material(context,False)
        return {'FINISHED'}

def adjust_material(context,is_ms):
    w_mgr = context.window_manager
    Util.active_object_to_current_collection()

    if w_mgr.is_eye:
        arg = eyekeys[int(w_mgr.eye_prop)-1]
    else:
        arg = skinkeys[int(w_mgr.skin_prop)-1]
    val = 0.1
    if is_ms:
        val = -0.1
    if ('Hue' in arg) or ('Displacement' in arg):
        val = val / 10
    if w_mgr.ftime_prop:
        val = val * 4
    # if ('Normal' in arg) or ('Bump' in arg) or ('Displacement' in arg):
    #     val = val * 0.01 * Global.getSize()
    if arg != '':
        DtbMaterial.adjust_material(arg, val, w_mgr.is_eye)

class MATERIAL_OT_down(bpy.types.Operator):
    bl_idname = "material.down"
    bl_label = "DOWN"
    def execute(self, context):
        adjust_material(context, True)
        return {'FINISHED'}



def clear_pose():
    if bpy.context.object is None:
        return
    if Global.getAmtr() is not None and Versions.get_active_object() == Global.getAmtr():
        for pb in Global.getAmtr().pose.bones:
            pb.bone.select = True
    if Global.getRgfy() is not None and Versions.get_active_object() == Global.getRgfy():
        for pb in Global.getRgfy().pose.bones:
            pb.bone.select = True
    bpy.ops.pose.transforms_clear()
    bpy.ops.pose.select_all(action='DESELECT')

class TRANS_OT_Rigify(bpy.types.Operator):
    bl_idname = 'to.rigify'
    bl_label = 'To Rigify'
    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        clear_pose()
        Util.active_object_to_current_collection()

        trf = ToRigify.ToRigify()
        db = DataBase.DB()
        DtbIKBones.adjust_shin_y(2, False)
        DtbIKBones.adjust_shin_y(3, False)
        trf.toRigify(db, self)
        return {'FINISHED'}

class DEFAULT_OT_material(bpy.types.Operator):
    bl_idname = "df.material"
    bl_label = 'RESET MATERIAL'
    def execute(self, context):
        Util.active_object_to_current_collection()
        default_material(context)
        return {'FINISHED'}



def default_material(context):
    w_mgr = context.window_manager
    if w_mgr.is_eye:
        #DtbShaders.toEyeDryDefault(bpy.data.node_groups.get(DtbShaders.getGroupNode(DtbShaders.EDRY)))
        DtbMaterial.getGroupNodeTree("EyeDry")
        DtbMaterial.getGroupNodeTree("EyeWet")
    else:
        DtbMaterial.getGroupNodeTree("IrayUberSkin")

class MATCH_OT_ikfk(bpy.types.Operator):
    bl_idname = 'match.ikfk'
    bl_label = 'Match IK & FK'

    def execute(self, context):
        b2 = ['upper_arm_parent', 'thigh_parent']
        lr = ['.R', '.L']
        trf = ToRigify.ToRigify()
        influence4 = []
        for i in range(2):
            for j in range(2):
                influence4.append(Global.getRgfy().pose.bones[b2[i] + lr[j]]['IK_FK'])
        trf.match_ikfk(influence4)
        return {'FINISHED'}



class SCULPT_OT_push(bpy.types.Operator):
    bl_idname = 'to.sculpt'
    bl_label = 'To Sculpt'
    def execute(self, context):
        Util.active_object_to_current_collection()
        w_mgr = bpy.context.window_manager
        ddm = DtbDazMorph.DtbDazMorph()
        if Versions.get_active_object().mode=='SCULPT':
            w_mgr.new_morph = False
            Global.setOpsMode('EDIT')
            ddm.select_to_daz_morph(False)
        elif Versions.get_active_object().mode=='OBJECT':
            Global.setOpsMode("SCULPT")
            ddm.select_to_daz_morph(w_mgr.new_morph)
        elif Versions.get_active_object().mode=='EDIT':
            w_mgr.new_morph = False
            Global.setOpsMode('OBJECT')
        return {'FINISHED'}

class EXP_OT_morph(bpy.types.Operator):
    bl_idname = 'exsport.morph'
    bl_label = 'To Daz Morph'

    def execute(self,context):
        is_body = context.active_object==Global.getBody()
        global obj_exsported
        ddm = DtbDazMorph.DtbDazMorph()
        ddm.before_execute(is_body)
        flg_ok = ddm.top_exsport()
        if flg_ok==False:
            self.report({"ERROR"}, "There is no suitable shape key")
        return {'FINISHED'}

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
            DtbIKBones.bone_disp(-1, False)
            DtbIKBones.mute_bones.append('NG')
            for i in range(len(DtbIKBones.bone_name)):
                DtbIKBones.fktoik(i)
                DtbIKBones.adjust_shin_y(i, True)
            DtbIKBones.mute_bones = []
        return {'FINISHED'}


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
            DtbIKBones.bone_disp(-1, True)
            DtbIKBones.mute_bones.append('NG')
            for i in range(len(DtbIKBones.bone_name)):
                DtbIKBones.iktofk(i)
                DtbIKBones.adjust_shin_y(i, False)
            DtbIKBones.mute_bones = []
        return {'FINISHED'}


class LIMB_OT_redraw(bpy.types.Operator):
    bl_idname = "limb.redraw"
    bl_label = "ReDisplay Subtle FK/IK"

    def execute(self, context):
        if Global.getAmtr() is None:
            return
        w_mgr = bpy.context.window_manager
        for i in range(4):
            ik_value = DtbIKBones.get_ik_influence(DtbIKBones.get_influece_data_path(DtbIKBones.bone_name[i]))
            flg_ik = ik_value >= 0.5
            DtbIKBones.bone_disp(i, flg_ik == False)
            if i == 0:
                if w_mgr.ifk0 != flg_ik:
                    w_mgr.ifk0 = flg_ik
            elif i == 1:
                if w_mgr.ifk1 != flg_ik:
                    w_mgr.ifk1 = flg_ik
            elif i == 2:
                if w_mgr.ifk2 != flg_ik:
                    w_mgr.ifk2 = flg_ik
                c = Global.getAmtrConstraint('rFoot', 'Copy Rotation')
                if c is not None and c.influence != ik_value:
                    c.influence = ik_value
            elif i == 3:
                if w_mgr.ifk3 != flg_ik:
                    w_mgr.ifk3 = flg_ik
                c = Global.getAmtrConstraint('lFoot', 'Copy Rotation')
                if c is not None and c.influence != ik_value:
                    c.influence = ik_value
        return {'FINISHED'}



def init_props():
    w_mgr = bpy.types.WindowManager
    w_mgr.skin_prop = EnumProperty(
        name="skin",
        description="Skin Adjust",
        items = [
            ('1', 'Base Color.Hue','1'),
            ('2', 'Base Color.Saturation','2'),
            ('3', 'Base Color.Value','3'),
            ('4', 'Base Color.Bright','4'),
            ('5', 'Base Color.Contrast','5'),
            ('6', 'Specular','6'),
            ('7', 'Roughness','7'),
            ('8', 'Roughness.Contrast','8'),
            ('9', 'Specular.Contrast','9'),
            ('10', 'Subsurface.Scale','10'),
            ('11', 'Normal.Strength','11'),
            ('12', 'Bump.Strength','12'),
            ('13', 'Bump.Distance','13'),
            ('14', 'Displacement.Height','14'),
        ],
        default = '1',
    )
    w_mgr.eye_prop = EnumProperty(
        name="skin",
        description="Eyes Adjust",
        items=[
            ('1', 'Base Color.Hue','1'),
            ('2', 'Base Color.Saturation','2'),
            ('3', 'Base Color.Value','3'),
            ('4', 'Base Color.Bright', '4'),
            ('5', 'Base Color.Contrast', '5'),
            ('6', 'Normal.Strength', '6'),
            ('7', 'Bump.Strength', '7'),
            ('8', 'Bump.Distance', '8'),
        ],
        default='1',
    )
    w_mgr.search_prop = StringProperty(
        name="",
        default="",
        description="Search_shape_keys",
        update= DtbCommands.search_morph_
    )
    w_mgr.is_eye = BoolProperty(name="eyes")
    w_mgr.ftime_prop = BoolProperty(name="ftime")
    w_mgr.br_onoff_prop = BoolProperty(name="br_onoff", default=True, update=DtbIKBones.bonerange_onoff)
    w_mgr.ifk0 = BoolProperty(name="ifk0", default=False, update=DtbIKBones.ifk_update0)
    w_mgr.ifk1 = BoolProperty(name="ifk1", default=False, update=DtbIKBones.ifk_update1)
    w_mgr.ifk2 = BoolProperty(name="ifk2", default=False, update=DtbIKBones.ifk_update2)
    w_mgr.ifk3 = BoolProperty(name="fik3", default=False, update=DtbIKBones.ifk_update3)
    w_mgr.new_morph = BoolProperty(name="_new_morph",default=False)
    w_mgr.skip_isk = BoolProperty(name = "_skip_isk",default = False)
    w_mgr.quick_heavy = BoolProperty(name="quick_heavy", default=False)
    w_mgr.combine_materials = BoolProperty(name="combine_materials", default=True)
    w_mgr.add_pose_lib = BoolProperty(name="add_pose_lib", default=True)
    figure_items = [("null" , "Choose Character", "Select which figure you wish to import")]
    w_mgr.choose_daz_figure = EnumProperty(
        name  = "Highlight for Collection",
        description = "Choose any figure in your scene to which you wish to add a pose.",
        items = figure_items,
        default = "null",
    )
    w_mgr.scene_scale = EnumProperty(
        name = "Scene Scale",
        description = "Used to change scale of imported object and scale settings",
        items = [
            ('0.01', 'Real Scale (Centimeters)', 'Daz Scale'),
            ('0.1', 'x10', '10 x Daz Scale'),
            ('1', 'x100 (Meters)', '100 x Daz Scale')
        ],
        default = '0.01'
    )
   



classes = (
    
    DtbPanels.DTB_PT_MAIN,
    DtbPanels.DTB_PT_POSE,
    DtbPanels.DTB_PT_MORPHS,
    DtbPanels.DTB_PT_MATERIAL,
    DtbPanels.DTB_PT_GENERAL,
    DtbPanels.DTB_PT_COMMANDS,
    DtbOperators.IMP_OT_POSE,
    DtbOperators.IMP_OT_FBX,
    DtbOperators.IMP_OT_ENV,
    DtbOperators.CLEAR_OT_Pose,
    DtbOperators.REFRESH_DAZ_FIGURES,
    DtbOperators.REMOVE_DAZ_OT_button,
    DtbOperators.OPTIMIZE_OT_material,
    DtbCommands.SEARCH_OT_Commands,
    IK2FK_OT_button,
    FK2IK_OT_button,
    MATERIAL_OT_up,
    MATERIAL_OT_down,
    DEFAULT_OT_material,
    TRANS_OT_Rigify,
    MATCH_OT_ikfk,
    LIMB_OT_redraw,
    EXP_OT_morph,
    SCULPT_OT_push,
   
   
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    init_props()
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__=="__main__":
    register()
