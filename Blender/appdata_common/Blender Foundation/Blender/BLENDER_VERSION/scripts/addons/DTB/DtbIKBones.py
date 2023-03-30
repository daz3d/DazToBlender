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
from bpy.props import EnumProperty
from bpy.props import BoolProperty
from bpy.props import StringProperty
import threading
import time

BV = Versions.getBV()
num_bones = [6, 6, 3, 3]
# G9 support
num_bones_G9 = [4, 4, 2, 2]
ik_name = ['rHand_IK', 'lHand_IK', 'rShin_IK', 'lShin_IK']
bone_name = ['rHand', 'lHand', 'rShin', 'lShin']
bone_name_rigify = ['MCH-upper_arm_ik.R','MCH-upper_arm_ik.L','MCH-thigh_ik.R','MCH-thigh_ik.L']
mute_bones = []
ik_access_ban = False
obj_exported = ""

def get_num_bones(index):
    if index is None:
        return get_num_bones_array()
    if Global.getIsG9():
        return num_bones_G9[index]
    return num_bones[index]

def get_num_bones_array():
    if Global.getIsG9():
        return num_bones_G9
    return num_bones

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

#TODO: Get intergate the setting into the import setup
def set_scene_settings(key_count):
    scene = bpy.context.scene
    

    # Set start and end playable range for the animations.
    scene.frame_start = 0
    scene.frame_end = key_count - 1
    scene.frame_current = 0

    # Set armature display settings
    Global.setOpsMode('POSE')
    armature = Global.getAmtr().data
    armature.display_type = 'OCTAHEDRAL'
    armature.show_names = False
    armature.show_axes = False
    armature.show_bone_custom_shapes = True


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
        num = get_num_bones(index)
        for i in range(num):
            mute_bones.append(my_bone.name)
            my_bone = my_bone.parent
        mute_bones.append(ik_name[index])
        if index>1:
            poles = ['', '', 'rShin_P', 'lShin_P']
            poles = DataBase.translate_bonenames(poles)
            foots = ['', '', 'rFoot', 'lFoot']
            foots = DataBase.translate_bonenames(foots)
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
            foots = DataBase.translate_bonenames(foots)
            fkp_cr = Find_KeyFrame_Point(act.fcurves, mute_bones, ['influence', 'Copy Rotation',foots[index]], ckey)
            prev_cr = fkp_cr.previous
            first_cr= fkp_cr.skip_first(first_cr)
        if first_cr >= prev_cr:
            first_cr = -999
        if first_ik >= prev_ik:
            first_ik = -999
        for b in mute_bones:
            for c in amt.pose.bones.get(b).constraints:
                # G9 support
                if (index > 1 and c.name == 'Copy Rotation'
                    and (b[1:]=='Foot' or b[1:]=='_foot') ):
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
                names = fcu.data_path.split(sep='"', maxsplit=2)
                if len(names) < 2:
                    continue
                name = names[1]
                if name in  mute_bones and switch < 0:
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
        rot_matrix = Global.getFootAngle_matrix(index-2)
        ik_bone.matrix = rot_matrix
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
    copy_r = DataBase.translate_bonenames(copy_r)
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
    if my_bone.name == DataBase.translate_bonenames('lShin'):
        my_bone = amt.pose.bones.get(DataBase.translate_bonenames('lFoot'))
    elif my_bone.name == DataBase.translate_bonenames('rShin'):
        my_bone = amt.pose.bones.get(DataBase.translate_bonenames('rFoot'))
    it = my_bone
    for i in range(get_num_bones(index)+1):
        if it == None:
            continue
        mx = deepcopy(it.matrix)
        ik_bone_matrixes.append(mx)
        it = it.parent
    set_fk(get_influece_data_path(bone_name[index]))
    if index >1:
        toFootCopyRotate(index,False)
    it = my_bone
    for i in range(get_num_bones(index) + 1):
        if it == None:
            continue
        it.matrix = deepcopy(ik_bone_matrixes[i])
        # print("\nDEBUG: DEEP_COPY VERIFICATION: iktofk(): it.name = " + it.name  + "\nit.matrix =\n" + str(it.matrix) + "\nmx =\n" + str(ik_bone_matrixes[i]) )
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
    # custom G9 override for foot(shin) IK scale
    if Global.getIsG9():
        hfp[1] = 0.7
    scales = [hfp[0],hfp[0],hfp[1],hfp[1],hfp[2],hfp[2]]
    if amt_bone is None or pose_bone is None:
        return
    isAnim = Global.isExistsAnimation()
    # blender 3.0 break change:
    # Replaced PoseBone.custom_shape_scale scalar with a PoseBone.custom_shape_scale_xyz vector
    if flg_hide and isAnim:
        Versions.handle_custom_shape_scale(pose_bone, scales[idx] * 0.4)
    else:
        Versions.handle_custom_shape_scale(pose_bone, scales[idx])

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

def reset_pole(idx):
    if idx < 0 or idx >= len(ik_name):
        return
    pole = ik_name[idx][0:len(ik_name[idx])-2]
    pole = pole + 'P'
    pole_bone = Global.getAmtr().pose.bones.get(pole)
    if pole_bone is None:
        return
    pole_bone.location = [0, 0, 0]
    pole_bone.rotation_quaternion = [1, 0, 0, 0]


# def bonerange_onoff(self):
#     bonerange_onoff(self,bpy.contxt)
    
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
    bns = DataBase.translate_bonenames(bns)
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
    if Global.getIsG9():
        return
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