bl_info = {
    "name": "DazToBlender",
    "author": "Daz 3D | https://www.daz3d.com",
    "version": (2, 0,0),
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
from . import DtbMaterial
from . import FitBone
from . import CustomBones
from . import Util
from . import WCmd
from . import Octane
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
num_bones = [6, 6, 3, 3]
ik_name = ['rHand_IK', 'lHand_IK', 'rShin_IK', 'lShin_IK']
bone_name = ['rHand', 'lHand', 'rShin', 'lShin']
bone_name_rigify = ['MCH-upper_arm_ik.R','MCH-upper_arm_ik.L','MCH-thigh_ik.R','MCH-thigh_ik.L']
fbx_exsported = ""
obj_exsported = ""
mute_bones = []
ik_access_ban = False
ds = DtbMaterial.DtbShaders()
region = 'UI'
BV = Versions.getBV()

def get_influece_data_path(bname):
    amtr = Global.getAmtr()
    if amtr is None:
        return
    if bname in amtr.pose.bones:
        pbn = amtr.pose.bones[bname]
        for c in pbn.constraints:
            if bname + '_IK' in c.name:
                return [c, 'influence']
    return None

def get_ik_influence(data_path):
    return eval("data_path[0].%s" % data_path[1])

def set_ik_influence(data_path, val):
    exec("data_path[0].%s = %f" % (data_path[1], val))

def set_ik(data_path):
    set_ik_influence(data_path, 1.0)

def set_fk(data_path):
    set_ik_influence(data_path, 0.0)

def set_translation(matrix, loc):
    trs = matrix.decompose()
    rot = trs[1].to_matrix().to_4x4()
    scale = mathutils.Matrix.Scale(1, 4, trs[2])
    if BV<2.80:
        return mathutils.Matrix.Translation(loc) * (rot * scale)
    else:
        return mathutils.Matrix.Translation(loc) @ (rot @ scale)

class DTB_PT_Main(bpy.types.Panel):
    bl_label = "DazToBlender"
    bl_space_type = 'VIEW_3D'
    bl_region_type = region
    if BV <2.80:
        bl_category = "Tools"
    else:
        bl_category = "DazToBlender"
    t_non = None
    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        row = box.row(align=True)
        row.prop(w_mgr, "quick_heavy", text="Quick But Heavy", toggle=False)
        row.prop(w_mgr, "size_100", text="Size * 100", toggle=False)
        box.operator('import.fbx', icon='POSE_HLT')
        box.operator('import.env', icon='WORLD')
        if context.object and context.active_object:
            cobj = context.active_object
            if Global.get_Body_name() == "" and Global.get_Rgfy_name() == "" and Global.get_Amtr_name() == "":
                Global.clear_variables()
                Global.decide_HERO()
            if context.object.type == 'ARMATURE' and Global.getRgfy() is None and Global.getAmtr() is None:
                Global.clear_variables()
                Global.find_AMTR(cobj)
                Global.find_RGFY(cobj)
            if context.object.type == 'MESH' and Global.getBody() is None:
                Global.clear_variables()
                Global.find_BODY(cobj)
            if cobj.mode == 'POSE':
                if Global.get_Amtr_name() != cobj.name and len(cobj.data.bones) > 90 and len(cobj.data.bones) < 200:
                    Global.clear_variables()
                    Global.find_Both(cobj)
                if Global.get_Rgfy_name() != cobj.name and len(cobj.data.bones) > 600:
                    Global.clear_variables()
                    Global.find_Both(cobj)
            elif context.object.type == 'MESH':
                if Global.get_Body_name() != "" and Global.get_Body_name() != cobj.name and len(
                        cobj.vertex_groups) > 163 \
                        and len(cobj.data.vertices) >= 16384 \
                        and len(cobj.vertex_groups) < 500 and len(cobj.data.vertices) < 321309:
                    Global.clear_variables()
                    Global.find_Both(cobj)
            if ik_access_ban == False and context.active_object.mode == 'POSE':
                l.separator()
                if Global.amIAmtr(context.object):
                    col = l.column(align=True)
                    r = col.row(align=True)
                    for i in range(len(ik_name)):
                        if i == 2:
                            r = col.row(align=True)
                        influence_data_path = get_influece_data_path(bone_name[i])
                        if influence_data_path is not None:
                            r.prop(w_mgr, 'ifk' + str(i), text=ik_name[i], toggle=True)
                    col.operator('limb.redraw',icon='LINE_DATA')
                    l.separator()
                elif Global.amIRigfy(context.object):
                    if BV<2.81:
                        row = l.row(align=True)
                        row.alignment = 'EXPAND'
                        row.operator('my.iktofk', icon="MESH_CIRCLE")
                        row.operator('my.fktoik', icon="MESH_CUBE")
                if Global.amIAmtr(context.object):
                    l.operator('to.rigify', icon='ARMATURE_DATA')
                if Global.amIRigfy(context.object):
                    if BV<2.81:
                        row = l.row(align=True)
                        row.alignment = 'EXPAND'
                        row.operator('match.ikfk')
                        row.prop(w_mgr, "br_onoff_prop", text="Joint Range", toggle=True)
                    else:
                        l.prop(w_mgr, "br_onoff_prop", text="Joint Range", toggle=True)
                l.separator()
                l.operator('my.clear')
            if Global.amIBody(context.object) and bpy.context.scene.render.engine !='octane':
                col = l.column(align=True)
                box = col.box()
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(w_mgr, "is_eye", text="Eye")
                row.prop(w_mgr, "ftime_prop", text="x 4")
                if w_mgr.is_eye:
                    box.prop(w_mgr, "eye_prop", text="")
                else:
                    box.prop(w_mgr, "skin_prop", text="")
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.operator('material.up', icon="TRIA_UP")
                row.operator('material.down', icon="TRIA_DOWN")
                box.operator('df.material')
            if context.object.type == 'MESH':
                if Global.isRiggedObject(context.object):
                    if Versions.get_active_object().mode == 'OBJECT':
                        l.prop(w_mgr, 'new_morph', text="Make New Morph")
                    row = l.row(align=True)
                    row.operator('exsport.morph', icon="TRIA_LEFT")
                    row.operator('to.sculpt', icon="MONKEY")
                    if obj_exsported != "":
                        l.label(text=obj_exsported)
                l.separator()
            row = l.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(w_mgr, "search_prop")
            if context.object.type == 'MESH':
                row.operator('search.morph', icon='VIEWZOOM')
            else:
                row.operator('search.morph', icon='HAND')
        else:
            l.prop(w_mgr, "search_prop")
        l.operator('remove.alldaz', icon='BOIDS')


class IMP_OT_FBX(bpy.types.Operator):
    bl_idname = "import.fbx"
    bl_label = " Import New Genesis 3/8"
    bl_options = {'REGISTER', 'UNDO'}
    root = Global.getRootPath()

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def finish_obj(self):
        Versions.reverse_language()
        Versions.pivot_active_element_and_center_and_trnormal()
        Global.setRenderSetting(Global.getIsPro())

    def layGround(self):
        wm = bpy.context.window_manager
        wk = bpy.context.window_manager.search_prop
        wk = wk.replace(" ","")
        wk = wk.lower()
        bpy.context.window_manager.search_prop = wk
        bpy.context.preferences.inputs.use_mouse_depth_navigate = True
        Util.deleteEmptyDazCollection()
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.color_type = 'OBJECT'
        bpy.context.space_data.shading.show_shadows = False
        Versions.set_english()
        bco = bpy.context.object
        if bco != None and bco.mode != 'OBJECT':
            Global.setOpsMode('OBJECT')
        bpy.ops.view3d.snap_cursor_to_center()

    def pbar(self,v,wm):
        wm.progress_update(v)

    def import_one(self,fbx_adr):
        Versions.active_object_none()
        Util.decideCurrentCollection('FIG')
        Util.clear_dzidx_material_and_nodegroup()
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        Global.clear_variables()
        ik_access_ban = True
        drb = DazRigBlend.DazRigBlend()
        self.pbar(5,wm)
        drb.convert_file(filepath=fbx_adr)
        self.pbar(10, wm)
        db = DataBase.DB()
        Global.decide_HERO()
        self.pbar(15, wm)
        if Global.getAmtr() is not None and Global.getBody() is not None:
            Global.deselect()
            drb.clear_pose()
            drb.mub_ary_A()
            drb.orthopedy_empty()
            self.pbar(18, wm)
            drb.orthopedy_everything()
            Global.deselect()
            self.pbar(20, wm)
            drb.fitHeadChildren()
            Global.deselect()
            FitBone.FitBone(True)
            self.pbar(25, wm)
            drb.bone_limit_modify()
            drb.fitbone_roll()
            Global.meipe_bone()
            Global.deselect()
            self.pbar(30, wm)
            drb.unwrapuv()
            Global.deselect()
            if Global.getIsEyls():
                drb.integrationEyelashes()
                Global.deselect()
            ds.makeDct()

            DtbMaterial.McySkin()
            DtbMaterial.McyEyeWet()
            DtbMaterial.McyEyeDry()
            ds.bodyTexture()
            self.pbar(35, wm)
            ds.propTexture()
            self.pbar(40, wm)
            Octane.Octane()
            if Global.getIsGen():
                drb.fixGeniWeight(db)
            Global.deselect()
            self.pbar(45, wm)
            Global.setOpsMode('OBJECT')
            Global.deselect()
            dsk = DtbShapeKeys.DtbShapeKeys(False)
            dsk.deleteEyelashes()
            self.pbar(50, wm)
            dsk.toshortkey()
            dsk.deleteExtraSkey()
            dsk.toHeadMorphMs(db)
            wm.progress_update(55)
            if wm.quick_heavy==False:
                dsk.delete_all_extra_sk(55, 75, wm)
            self.pbar(75,wm)
            dsk.makeDrives(db)
            Global.deselect()
            self.pbar(80,wm)
            drb.makeRoot()
            drb.makePole()
            drb.makeIK()
            drb.pbone_limit()
            drb.mub_ary_Z()
            Global.setOpsMode("OBJECT")
            CustomBones.CBones()
            Global.setOpsMode('OBJECT')
            Global.deselect()
            self.pbar(90,wm)
            dsk.delete001_sk()
            amt = Global.getAmtr()
            for bname in bone_name:
                bone = amt.pose.bones[bname]
                for bc in bone.constraints:
                    if bc.name == bname + "_IK":
                        pbik = amt.pose.bones.get(bname + "_IK")
                        amt.pose.bones[bname].constraints[bname + '_IK'].influence = 0
            drb.makeBRotationCut(db)
            Global.deselect()
            DtbMaterial.forbitMinus()
            self.pbar(95,wm)
            Global.deselect()
            Versions.active_object(Global.getAmtr())
            Global.setOpsMode("POSE")
            drb.mub_ary_Z()
            Global.setOpsMode("OBJECT")
            drb.finishjob()
            Global.setOpsMode("OBJECT")
            Util.Posing().setpose()
            bone_disp(-1, True)
            self.pbar(100,wm)
            ik_access_ban = False
            self.report({"INFO"}, "Success")
        else:
            self.show_error()
        wm.progress_end()
        ik_access_ban = False

    def execute(self, context):
        global ik_access_ban

        if self.root == "":
            self.report({"ERROR"}, "Appropriate FBX does not exist!")
            return {'FINISHED'}
        self.layGround()
        for i in range(10):
            fbx_adr = self.root + "FIG/FIG" + str(i) + "/B_FIG.fbx"
            if os.path.exists(fbx_adr)==False:
                break
            Global.setHomeTown(self.root+"FIG/FIG" + str(i))
            self.import_one(fbx_adr)
        self.finish_obj()
        return {'FINISHED'}

    def show_error(self):
        Global.setOpsMode("OBJECT")
        for b in Util.myacobjs():
            bpy.data.objects.remove(b)
        filepath = os.path.dirname(__file__) + Global.getFileSp()+"img" + Global.getFileSp() + "Error.fbx"
        if os.path.exists(filepath):
            bpy.ops.import_scene.fbx(filepath=filepath)
            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.color_type = 'TEXTURE'
        if Global.want_real():
            for b in Util.myacobjs():
                for i in range(3):
                    b.scale[i] = 0.01
            Global.my_region_3d(1)
        else:
            Global.my_region_3d(0)

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

class CLEAR_OT_Pose(bpy.types.Operator):
    bl_idname = "my.clear"
    bl_label = 'CLEAR ALL POSE'

    def execute(self, context):
        clear_pose()
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
        adjust_shin_y(2, False)
        adjust_shin_y(3, False)
        trf.toRigify(db, self)
        return {'FINISHED'}

class DEFAULT_OT_material(bpy.types.Operator):
    bl_idname = "df.material"
    bl_label = 'CLEAR MATERIAL'
    def execute(self, context):
        Util.active_object_to_current_collection()
        default_material(context)
        return {'FINISHED'}

def default_material(context):
    w_mgr = context.window_manager
    if w_mgr.is_eye:
        #DtbShaders.toEyeDryDefault(bpy.data.node_groups.get(DtbShaders.getGroupNode(DtbShaders.EDRY)))
        DtbMaterial.toEyeDryDefault(DtbMaterial.getGroupNodeTree(DtbMaterial.ngroup3(DtbMaterial.EDRY)))
        DtbMaterial.toEyeWetDefault(DtbMaterial.getGroupNodeTree(DtbMaterial.ngroup3(DtbMaterial.EWET)))
    else:
        DtbMaterial.toSkinDefault(DtbMaterial.getGroupNodeTree(DtbMaterial.ngroup3(DtbMaterial.SKIN)))

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

class SEARCH_OT_morph(bpy.types.Operator):
    bl_idname = "search.morph"
    bl_label = 'Command'

    def execute(self, context):
        search_morph(context)
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
            bone_disp(-1, False)
            global mute_bones
            mute_bones.append('NG')
            for i in range(len(bone_name)):
                fktoik(i)
                adjust_shin_y(i, True)
            mute_bones = []
        return {'FINISHED'}

class IMP_OT_ENV(bpy.types.Operator):
    bl_idname = "import.env"
    bl_label = "Import New Env/Prop"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        from . import Environment
        Environment.EnvProp()
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
            bone_disp(-1, True)
            global mute_bones
            mute_bones.append('NG')
            for i in range(len(bone_name)):
                iktofk(i)
                adjust_shin_y(i, False)
            mute_bones = []
        return {'FINISHED'}


class REMOVE_DAZ_OT_button(bpy.types.Operator):
    bl_idname = "remove.alldaz"
    bl_label = "Remove All Daz"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self,context,event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        col = bpy.data.collections.get('DAZ_ROOT')
        if col is not None:
            for c in col.children:
                for obj in c.objects:
                    bpy.data.objects.remove(obj)
                bpy.data.collections.remove(c)
        return {'FINISHED'}

class LIMB_OT_redraw(bpy.types.Operator):
    bl_idname = "limb.redraw"
    bl_label = "ReDisplay Subtle FK/IK"

    def execute(self, context):
        if Global.getAmtr() is None:
            return
        w_mgr = bpy.context.window_manager
        for i in range(4):
            ik_value = get_ik_influence(get_influece_data_path(bone_name[i]))
            flg_ik = ik_value >= 0.5
            bone_disp(i, flg_ik == False)
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

def manageKeyFrame(index, flg_to_ik, switch):
    global mute_bones
    amt = Global.getAmtr()
    if index ==1000:
        return
    if amt is None:
        return
    if 'NG' in mute_bones:
        return
    if amt.animation_data is None:
        return
    act = amt.animation_data.action
    if act is None:
        return
    ckey = bpy.context.scene.frame_current
    if switch<0:
        mute_bones = []
        my_bone = amt.pose.bones[bone_name[index]]
        num = num_bones[index]
        for i in range(num):
            mute_bones.append(my_bone.name)
            my_bone = my_bone.parent
        mute_bones.append(ik_name[index])
        if index>1:
            poles = ['', '', 'rShin_P', 'lShin_P']
            foots = ['', '', 'rFoot', 'lFoot']
            mute_bones.append(poles[index])
            mute_bones.append(foots[index])
        if flg_to_ik:
            mute_bones.append("hip")
    if switch < 0:
        first_cr = bpy.context.scene.frame_start
        first_ik = first_cr
        prev_cr = -999
        fkp_ik = Find_KeyFrame_Point(act.fcurves, mute_bones, ['influence',ik_name[index],bone_name[index]], ckey)
        prev_ik = fkp_ik.previous
        first_ik = fkp_ik.skip_first(first_ik)
        if index > 1:
            foots = ['', '', 'rFoot', 'lFoot']
            fkp_cr = Find_KeyFrame_Point(act.fcurves, mute_bones, ['influence', 'Copy Rotation',foots[index]], ckey)
            prev_cr = fkp_cr.previous
            first_cr= fkp_cr.skip_first(first_cr)
        if first_cr >= prev_cr:
            first_cr = -999
        if first_ik >= prev_ik:
            first_ik = -999
        for b in mute_bones:
            for c in amt.pose.bones.get(b).constraints:
                if (index > 1 and c.name == 'Copy Rotation' and b[1:]=='Foot'):
                    if first_cr > -1:
                        c.keyframe_insert(data_path='influence', frame=first_cr)
                    if prev_cr > -1:
                        c.keyframe_insert(data_path='influence', frame=prev_cr)
                if c.name==ik_name[index]:
                    if first_ik >-1:
                        c.keyframe_insert(data_path='influence', frame=first_ik)
                    if prev_ik > -1:
                        c.keyframe_insert(data_path='influence', frame=prev_ik)
    if switch==0:
        for b in mute_bones:
            if flg_to_ik==False:
                if (b.endswith("_IK") or b.endswith("_P"))==False:
                    amt.pose.bones[b].keyframe_insert(data_path='rotation_euler', frame=ckey)
            else:
                if (b.endswith("_IK") or b.endswith("_P")):

                    amt.pose.bones[b].keyframe_insert(data_path='location', frame=ckey)
                    if index > 1 and b.endswith("_IK"):
                        amt.pose.bones[b].keyframe_insert(data_path='rotation_euler', frame=ckey)

            for c in amt.pose.bones.get(b).constraints:
                if (index > 1 and c.name == 'Copy Rotation') or c.name == ik_name[index]:
                    c.keyframe_insert(data_path='influence', frame=ckey)
    else:
        for fcu in act.fcurves:
            if switch > 0 and fcu.mute:
                fcu.mute = False
            else:
                name = fcu.data_path.split(sep='"', maxsplit=2)[1]
                if name in  mute_bones:
                    if switch < 0:
                        fcu.mute = True
    if switch==1:
        mute_bones = []

class Find_KeyFrame_Point():
    find_collection = []
    skip_collection = []
    previous = -999

    def skip_first(self,now_first):
        if len(self.skip_collection)>1:
            wk = self.skip_collection[len(self.skip_collection)-1]
            if wk == now_first:
                return -999
            else:
                return now_first
        else:
            return now_first

    def __init__(self,fcurves,find_keys,skip_keys,now_posision):
        self.find_collection = []
        self.skip_collection = []
        self.previous = -999
        for fc in fcurves:
            for fk in find_keys:
                if (fk in fc.data_path):
                    for point in fc.keyframe_points:
                        if point.co[0] < now_posision and (point.co[0] in self.find_collection) == False:
                            self.find_collection.append(point.co[0])
            err = False
            for sk in skip_keys:
                if (sk in fc.data_path)==False:
                    err = True
                    break
            if err ==False:
                for point in fc.keyframe_points:
                    if point.co[0] < now_posision and (point.co[0] in self.skip_collection)==False:
                        self.skip_collection.append(point.co[0])
        self.find_collection.sort()
        self.find_collection.reverse()
        self.skip_collection.sort()
        self.skip_collection.reverse()
        if len(self.find_collection)<=0:
            self.previous =  -999
        elif len(self.skip_collection)<=0 or self.skip_collection[0] < self.find_collection[0]:
            self.previous = self.find_collection[0]
        else:
            self.previous =  -999

def fktoik(index):
    manageKeyFrame(index, True, -1)
    amt = Global.getAmtr()
    adjust_shin_y(index, True)
    my_bone = amt.pose.bones[bone_name[index]]
    ik_bone = amt.pose.bones[ik_name[index]]
    set_fk(get_influece_data_path(bone_name[index]))
    Global.setOpsMode('OBJECT')
    Global.setOpsMode('POSE')
    ik_bone.matrix = set_translation(ik_bone.matrix, my_bone.tail)
    set_ik(get_influece_data_path(bone_name[index]))
    if index>1:
        rot3 = Global.getFootAngle(index-2)
        for ridx,rot in enumerate(rot3):
            ik_bone.rotation_euler[ridx] = math.radians(rot)
        toFootCopyRotate(index,True)
    manageKeyFrame(index, True, 0)
    if index == 0:
        t = threading.Thread(target=my_srv0_1)
        t.start()
    if index == 1:
        t = threading.Thread(target=my_srv1_1)
        t.start()
    if index == 2:
        t = threading.Thread(target=my_srv2_1)
        t.start()
    if index == 3:
        t = threading.Thread(target=my_srv3_1)
        t.start()

def toFootCopyRotate(index,flg_ik):
    copy_r = ['','','rFoot', 'lFoot']
    pbone = Global.getAmtr().pose.bones
    if pbone is None:
        return
    for c in pbone.get(copy_r[index]).constraints:
        if 'Copy Rotation' == c.name:
            if flg_ik:
                c.influence = 1.0
            else:
                c.influence = 0.0

def my_service(index,flg_to_ik):
    time.sleep(2)
    manageKeyFrame(index, flg_to_ik, 1)

def my_srv0_1():
    my_service(0,True)
def my_srv1_1():
    my_service(1,True)
def my_srv2_1():
    my_service(2,True)
def my_srv3_1():
    my_service(3,True)
def my_srv0_0():
    my_service(0,False)
def my_srv1_0():
    my_service(1,False)
def my_srv2_0():
    my_service(2,False)
def my_srv3_0():
    my_service(3,False)

def iktofk(index):
    manageKeyFrame(index, False, -1)
    adjust_shin_y(index, False)
    amt = Global.getAmtr()
    ik_bone = amt.pose.bones[ik_name[index]]
    my_bone = amt.pose.bones[bone_name[index]]
    set_ik(get_influece_data_path(bone_name[index]))
    Global.setOpsMode('OBJECT')
    Global.setOpsMode('POSE')
    ik_bone_matrixes = []
    if my_bone.name=='lShin':
        my_bone = amt.pose.bones.get('lFoot')
    elif my_bone.name == 'rShin':
        my_bone = amt.pose.bones.get('rFoot')
    it = my_bone
    for i in range(num_bones[index]+1):
        if it == None:
            continue
        mx = deepcopy(it.matrix)
        ik_bone_matrixes.append(mx)
        it = it.parent
    set_fk(get_influece_data_path(bone_name[index]))
    if index >1:
        toFootCopyRotate(index,False)
    it = my_bone
    for i in range(num_bones[index] + 1):
        if it == None:
            continue
        it.matrix = deepcopy(ik_bone_matrixes[i])
        it = it.parent
    manageKeyFrame(index, False, 0)
    if index == 0:
        t = threading.Thread(target=my_srv0_0)
        t.start()
    if index == 1:
        t = threading.Thread(target=my_srv1_0)
        t.start()
    if index == 2:
        t = threading.Thread(target=my_srv2_0)
        t.start()
    if index == 3:
        t = threading.Thread(target=my_srv3_0)
        t.start()

def bone_disp2(idx,pose_bone,amt_bone,flg_hide):
    hfp = CustomBones.hikfikpole
    scales = [hfp[0],hfp[0],hfp[1],hfp[1],hfp[2],hfp[2]]
    if amt_bone is None or pose_bone is None:
        return
    isAnim = Global.isExistsAnimation()
    if flg_hide and isAnim:
        pose_bone.custom_shape_scale = scales[idx] * 0.4
    else:
        pose_bone.custom_shape_scale = scales[idx]
    if isAnim:
        amt_bone.hide = False
    else:
        amt_bone.hide = flg_hide

def bone_disp(idx, flg_hide):
    if idx < 0 or idx > 3:
        for i in range(4):
            bone_disp(i, flg_hide)
        return
    abones = Global.getAmtrBones()
    pbones = Global.getAmtr().pose.bones
    if ik_name[idx] in abones:
        bone_disp2(idx, pbones.get(ik_name[idx]),abones.get(ik_name[idx]), flg_hide)
    if idx>1:
        pole = ik_name[idx][0:len(ik_name[idx])-2]
        pole = pole + 'P'
        if pole in abones:
            bone_disp2(idx+2, pbones.get(pole), abones.get(pole),flg_hide)

def search_morph_(self, context):
    search_morph(context)

def search_morph(context):
    w_mgr = context.window_manager
    key = w_mgr.search_prop
    nozero = False
    if key.startswith("!"):
        nozero = True
        key = key[1:]
    if len(key) < 2:
        return
    if key.startswith("#"):
        WCmd.Command(key[1:], context)
        return
    cobj = bpy.context.object
    mesh = cobj.data
    for z in range(2):
        find = False
        max = len(mesh.shape_keys.key_blocks)
        for kidx, kb in enumerate(mesh.shape_keys.key_blocks):
            if kidx <= Versions.get_active_object().active_shape_key_index:
                continue
            if nozero and kb.value == 0.0:
                continue
            if (key.lower() in kb.name.lower()):
                Versions.get_active_object().active_shape_key_index = kidx
                find = True
                break
        if z == 0 and find == False:
            if max > 1:
                Versions.get_active_object().active_shape_key_index = 1
        else:
            break

def bonerange_onoff(self):
    bonerange_onoff(self,bpy.contxt)
    
def bonerange_onoff(self,context):
    flg_on = context.window_manager.br_onoff_prop
    Global.boneRotation_onoff(context, flg_on)

def ifk_update0(self, context):
    ifk_update(context, 0)

def ifk_update1(self, context):
    ifk_update(context, 1)

def ifk_update2(self, context):
    ifk_update(context, 2)

def ifk_update3(self, context):
    ifk_update(context, 3)

def ifk_update(context, idx):
    if Global.get_Amtr_name() == "" or ik_access_ban == True:
        return {'FINISHED'}
    if idx >= 0 and idx <= 3:
        ik_force = (get_ik_influence(get_influece_data_path(bone_name[idx])) > 0.5)
        gui_force = eval('context.window_manager.ifk' + str(idx))
        if ik_force != gui_force:
            if ik_force == False:
                bone_disp(idx, False)
                fktoik(idx)
            else:
                bone_disp(idx, True)
                iktofk(idx)
    return {'FINISHED'}

def adjust_shin_y(idx, flg_ik):
    if Global.getAmtr() is None or idx < 2:
        return
    idx = idx - 2
    bns = ['rShin', 'lShin']
    Global.setOpsMode('EDIT')
    mobj = Global.getBody()
    if mobj is None:
        Global.find_Both(Global.getAmtr())
        return
    vgs = mobj.data.vertices
    fm_ikfk = [[4708 ,3418],[4428,3217]]
    vidx = 0
    if Global.getIsMan():
        if flg_ik:
            vidx = fm_ikfk[1][0]
        else:
            vidx = fm_ikfk[1][1]
    else:
        if flg_ik:
            vidx = fm_ikfk[0][0]
        else:
            vidx = fm_ikfk[0][1]
    if Global.getIsGen():
        vidx = Global.toGeniVIndex(vidx)
    Global.getAmtr().data.edit_bones[bns[idx]].head[1] = vgs[vidx].co[1]
    Global.setOpsMode('POSE')
    if flg_ik:
        for i in range(2):
            s = Global.getAmtr().pose.bones.get(bns[i])
            if s is not None:
                if s.rotation_euler[0] <= 0.0:
                    s.rotation_euler[0] = 0.1

def gorl_update(self, context):
    w_mgr = context.window_manager
    gorl = w_mgr.gorl_prop
    if gorl == False:
        for i, bn in enumerate(bone_name):
            v = get_ik_influence(get_influece_data_path(bn))
            if i == 0:
                w_mgr.ifk0 = v > 0.5
            elif i == 1:
                w_mgr.ifk1 = v > 0.5
            elif i == 2:
                w_mgr.ifk2 = v > 0.5
            elif i == 3:
                w_mgr.ifk3 = v > 0.5

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
        update=search_morph_
    )
    w_mgr.is_eye = BoolProperty(name="eyes")
    w_mgr.ftime_prop = BoolProperty(name="ftime")
    w_mgr.br_onoff_prop = BoolProperty(name="br_onoff", default=True, update=bonerange_onoff)
    w_mgr.ifk0 = BoolProperty(name="ifk0", default=False, update=ifk_update0)
    w_mgr.ifk1 = BoolProperty(name="ifk1", default=False, update=ifk_update1)
    w_mgr.ifk2 = BoolProperty(name="ifk2", default=False, update=ifk_update2)
    w_mgr.ifk3 = BoolProperty(name="fik3", default=False, update=ifk_update3)
    w_mgr.new_morph = BoolProperty(name="_new_morph",default=False)
    w_mgr.skip_isk = BoolProperty(name = "_skip_isk",default = False)
    w_mgr.quick_heavy = BoolProperty(name="quick_heavy", default=False)
    w_mgr.size_100 = BoolProperty(name="size_100", default=False)



classes = (
    DTB_PT_Main,
    IMP_OT_FBX,
    IK2FK_OT_button,
    FK2IK_OT_button,
    CLEAR_OT_Pose,
    MATERIAL_OT_up,
    MATERIAL_OT_down,
    DEFAULT_OT_material,
    SEARCH_OT_morph,
    TRANS_OT_Rigify,
    MATCH_OT_ikfk,
    LIMB_OT_redraw,
    EXP_OT_morph,
    SCULPT_OT_push,
    IMP_OT_ENV,
    REMOVE_DAZ_OT_button,


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
