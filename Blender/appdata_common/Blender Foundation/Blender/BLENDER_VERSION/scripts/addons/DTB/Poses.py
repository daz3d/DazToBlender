import bpy
import os
import math
import json
import mathutils
from . import DataBase
from . import Versions
from . import Global
import re

#TODO: Figure out a way to use for Figure and Prop
class Posing:
    
    bone_head_tail_dict = {}
    bone_limits_dict = {}
    pose_data_dict = {}
    
    def __init__(self, asset):
        if asset == "FIG":
            self.bone_limits = DataBase.get_bone_limits_dict()
            self.get_pose_data(asset)

        if asset == "ENV":
            self.load_bone_limits(asset)
            self.load_bone_head_tail_data(asset)
            self.get_pose_data(asset)
        
    
    def load_bone_head_tail_data(self, asset):
        input_file = open(os.path.join(Global.getHomeTown(), asset + "_boneHeadTail.csv"), "r")
        lines = input_file.readlines()
        input_file.close()
        self.bone_head_tail_dict = dict()
        for line in lines:
            line_split = line.split(",")
            self.bone_head_tail_dict[line_split[0]] = line_split
    

    #Bone property
    def get_bone_head_tail_data(self, bname):
        bname = bname.split(".00")[0] # To deal with Duplicates
        if self.bone_head_tail_dict is None:
            self.get_bone_head_tail_data()
        if bname in self.bone_head_tail_dict.keys():
            return self.bone_head_tail_dict[bname]
        return None
    

    def set_bone_head_tail(self, bone):
        binfo = self.get_bone_head_tail_data(bone.name)
        if binfo is None:
            return False
        else:
            # set head
            bone.head[0] = float(binfo[1])
            bone.head[1] = -float(binfo[3])
            bone.head[2] = float(binfo[2])
            
            # set tail
            bone.tail[0] = float(binfo[4])
            bone.tail[1] = -float(binfo[6])
            bone.tail[2] = float(binfo[5])

            # calculate roll aligning bone towards a vector
            align_axis_vec = mathutils.Vector((
                                float(binfo[7]),
                                -float(binfo[9]),
                                float(binfo[8])
                                ))
            bone.align_roll(align_axis_vec)
            
            return True


    def load_bone_limits(self, asset):
        input_file = open(os.path.join(Global.getHomeTown(), asset + "_boneLimits.csv"), "r")
        lines = input_file.readlines()
        input_file.close()

        for line in lines:
            line_split = line.split(',')
            bone_limit = []
            
            bone_limit.append(line_split[0])
            bone_limit.append(line_split[1])
            bone_limit.append(float(line_split[2]))
            bone_limit.append(float(line_split[3]))
            bone_limit.append(float(line_split[4]))
            bone_limit.append(float(line_split[5]))
            bone_limit.append(float(line_split[6]))
            bone_limit.append(float(line_split[7]))
            self.bone_limits_dict[bone_limit[0]] = bone_limit
    

    def get_bone_limits_dict(self, bname):
        bname = bname.split(".00")[0] # To deal with Duplicates
        if len(self.bone_limits_dict.keys()) == 0:
            self.load_bone_limits()
        if bname in self.bone_limits_dict.keys():
            return self.bone_limits_dict[bname]
        
    def bone_limit_modify(self, bone):
        bone_limit = self.get_bone_limits_dict(bone.name)
        order = bone_limit[1]
        new_bone_limit = self.reorder_limits(order, bone_limit, bone.name)
        new_order = self.get_rotation_order(order)
        bone.rotation_mode = new_order
        bone.constraints.new('LIMIT_ROTATION')
        rot_limit = bone.constraints['Limit Rotation']
        rot_limit.owner_space = 'LOCAL'
        rot_limit.use_transform_limit = True
        rot_limit.use_limit_x = True
        rot_limit.min_x = math.radians(new_bone_limit[2])
        rot_limit.max_x = math.radians(new_bone_limit[3])
        rot_limit.use_limit_y = True
        rot_limit.min_y = math.radians(new_bone_limit[4])
        rot_limit.max_y = math.radians(new_bone_limit[5])
        rot_limit.use_limit_z = True
        rot_limit.min_z = math.radians(new_bone_limit[6])
        rot_limit.max_z = math.radians(new_bone_limit[7])

        bone.use_ik_limit_x = True
        bone.use_ik_limit_y = True
        bone.use_ik_limit_z = True
        if 'shin' in bone.name.lower():
            bone.ik_min_x = math.radians(1)
            bone.use_ik_limit_x = False
        else:
            bone.ik_min_x = math.radians(new_bone_limit[2])
        bone.ik_max_x = math.radians(new_bone_limit[3])
        bone.ik_min_y = math.radians(new_bone_limit[4])
        bone.ik_max_y = math.radians(new_bone_limit[5])
        bone.ik_min_z = math.radians(new_bone_limit[6])
        bone.ik_max_z = math.radians(bone_limit[7])

        if bone.name[1:] == 'Shin' or 'Thigh' in bone.name:
            bone.ik_stiffness_y = 0.99
            bone.ik_stiffness_z = 0.99
            if 'ThighTwist' in bone.name:
                bone.ik_stiffness_x = 0.99

    def reorder_limits(self, rotation_order, limits, name):
        if rotation_order == 'XYZ':
            # YZ switch (Y <-> Z)
            temp1 = limits[4]
            temp2 = limits[5]
            limits[4] = limits[6]
            limits[5] = limits[7]
            limits[6] = temp1
            limits[7] = temp2

            # XY switch (X <-> Y)
            temp1 = limits[2]
            temp2 = limits[3]
            limits[2] = limits[4]
            limits[3] = limits[5]
            limits[4] = temp1
            limits[5] = temp2

            if "right" in name.lower():
                # Y invert (-Y)
                limits[4] = -limits[4]
                limits[5] = -limits[5]
                # Z invert (-Z)
                limits[6] = -limits[6]
                limits[7] = -limits[7]

        elif rotation_order == 'XZY':
            # XY switch (X <-> Y)
            temp1 = limits[2]
            temp2 = limits[3]
            limits[2] = limits[4]
            limits[3] = limits[5]
            limits[4] = temp1
            limits[5] = temp2

            # X invert (-X)
            limits[2] = -limits[2]
            limits[3] = -limits[3]

            if "right" in name.lower():
                # Y invert (-Y)
                limits[4] = -limits[4]
                limits[5] = -limits[5]
                # Z invert (-Z)
                limits[6] = -limits[6]
                limits[7] = -limits[7]

        elif rotation_order == "ZXY":
            # XY switch (X <-> Y)
            temp1 = limits[2]
            temp2 = limits[3]
            limits[2] = limits[4]
            limits[3] = limits[5]
            limits[4] = temp1
            limits[5] = temp2

            # YZ switch (Y <-> Z)
            temp1 = limits[4]
            temp2 = limits[5]
            limits[4] = limits[6]
            limits[5] = limits[7]
            limits[6] = temp1
            limits[7] = temp2

        elif rotation_order == "ZYX":
             # YZ switch (Y <-> Z)
            temp1 = limits[4]
            temp2 = limits[5]
            limits[4] = limits[6]
            limits[5] = limits[7]
            limits[6] = temp1
            limits[7] = temp2

            # X invert (-X)
            limits[2] = -limits[2]
            limits[3] = -limits[3]

        return limits

    def get_pose_data(self, asset):
        hometown = Global.getHomeTown()

        padr = os.path.join(hometown, asset + ".transforms")
        if os.path.exists(padr) == False:
            return
        with open(padr, errors='ignore', encoding='utf-8') as f:
            data = json.load(f)

        # Rename the root bone
        for key in data:
            if key.startswith('Genesis'):
                new_key = 'root'
                data[key]["Name"] = new_key
                data[key]["Object Type"] = 'BONE'
                data[new_key] = data.pop(key)

        self.pose_data_dict = data


    def get_objects_pose(self,obj):
        obj_name = obj.name.replace(".Shape", "")
        if obj_name in self.pose_data_dict:
            return self.pose_data_dict[obj_name]

        for key in self.pose_data_dict:
            if obj_name == key:
                return self.pose_data_dict[obj_name]
            elif obj_name.replace("_dup_", " ") == key:
                return self.pose_data_dict[key]
            elif len(obj_name.split(".00")) > 1:
                temp_name = obj_name.split(".00")[0] + " " + str(int(obj_name.split(".00")[1]) + 1)
                if temp_name == key:
                    return self.pose_data_dict[key] 
            elif self.pose_data_dict[key]["Name"] == obj_name:
                return self.pose_data_dict[key]
        return {}


    def clear_pose(self):
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Versions.show_x_ray(Global.getAmtr())
        Global.setOpsMode('POSE')
        bpy.ops.pose.transforms_clear()
        Global.setOpsMode('OBJECT')

    #TODO Refactor and update to Reenable
    def pose_copy(self,dur):
        if os.path.exists(dur) == False:
            return
        with open(dur, errors='ignore', encoding='utf-8') as f:
            ls = f.readlines()
        ptn = ['"url" : ','"keys" : ']
        xyz = ["/x/value","/y/value","/z/value"]
        v3ary = []
        v3 = []
        for l in ls:
            for i in range(2):
                f = l.find(ptn[i])
                if f >=0:
                    l = l[f+len(ptn[i]):]
                else:
                    continue
                if '#' in l:
                    continue
                if i == 0:
                    k = "@selection/"
                    f = l.find(k)
                    if f >= 0:
                        l = l[f+len(k):]
                        f = l.find("rotation")
                        if f>=0:
                            v3 = []
                            v3.append(l[:f-2])
                            for kidx,k in enumerate(xyz):
                                if k in l:
                                    v3.append(kidx)
                                    break
                elif i == 1 and len(v3) == 2:
                    a = l.find(",")
                    if a > 0:
                        l = l[a+1:]
                        a = l.find("]")
                        if a > 0:
                            l = l[:a]
                            v3.append(float(l.strip()))
                            v3ary.append(v3)
        self.make_pose(v3ary)

    def reorder_rotation(self,rotation_order,rotations,name):
        if rotation_order == 'XYZ':
            # YZ switch (Y <-> Z)
            temp = rotations[1]
            rotations[1] = rotations[2]
            rotations[2] = temp

            # XY switch (X <-> Y)
            temp = rotations[0]
            rotations[0] = rotations[1]
            rotations[1] = temp
            if(name.startswith("r")):
                # Y invert (-Y)
                rotations[1] = -rotations[1]
                # Z invert (-Z)
                rotations[2] = -rotations[2]

        elif rotation_order == 'XZY':
            # XY switch (X <-> Y)
            temp = rotations[0]
            rotations[0] =rotations[1]
            rotations[1] = temp

            # X invert (-X)
            rotations[0] = -rotations[0]

            if(name.startswith("r")):
                # Y invert (-Y)
                rotations[1] = -rotations[1]

                # Z invert (-Z)
                rotations[2] = -rotations[-2]

        elif rotation_order == "YZX":
        # Bones that are pointed down with YZX order
        # TODO: remove hardcoding
            if name in ["hip", "pelvis", "lThighBend", "rThighBend", "lThighTwist", "rThighTwist", "lShin", "rShin"]:
                # Y invert (-Y)
                rotations[1] = -rotations[1]

                # Z invert (-Z)
                rotations[2] = -rotations[2]

        elif rotation_order == "ZXY":
            # XY switch (X <-> Y)
            temp =  rotations[0]
            rotations[0] = rotations[1]
            rotations[1] = temp

            # YZ switch (Y <-> Z)
            temp = rotations[1]
            rotations[1] = rotations[2]
            rotations[2] = temp

        elif rotation_order == "ZYX":
            # YZ switch (Y <-> Z)
            temp = rotations[1]
            rotations[2] = rotations[1]

            # X invert (-X)
            rotations[0] = -rotations[0]

        return rotations

    def get_rotation_order(self,order):
        if order == 'XYZ':
            return 'ZXY'
        elif order == 'XZY':
            return 'YZX'
        elif order == 'YZX':
            return 'YZX'
        elif order == 'ZXY':
            return 'XYZ'
        elif order == 'ZYX':
            return 'YZX'

    
    def make_pose(self):
        bone_limits = self.bone_limits_dict
        transform_data = self.pose_data_dict

        pbs = Global.getAmtr().pose.bones
        for bone_limit_key in bone_limits:
            bone_limit = bone_limits[bone_limit_key]
            order = bone_limit[1]
            new_order = self.get_rotation_order(order)
            bname = bone_limit[0]
            if bname in transform_data.keys():
                if bname in pbs:
                    position = transform_data[bname]["Position"]
                    rotation = transform_data[bname]["Rotation"]
                    
                    # Position
                    for i in range(len(position)):   
                        position[i] = position[i] * Global.get_size()

                    pbs[bname].location[0] = float(position[0])
                    # Y invert (-Y)
                    pbs[bname].location[1] = -float(position[1])
                    # Z invert (-Z)
                    pbs[bname].location[2] = -float(position[2])
                    
                    
                    # Rotation
                    fixed_rotation = self.reorder_rotation(order,rotation,bname)
                    pbs[bname].rotation_mode = order
                    for i in range(len(rotation)):      
                        pbs[bname].rotation_euler[i] = math.radians(float(fixed_rotation[i]))
                    pbs[bname].rotation_mode = new_order
                    
                    #Add Pose to Libary
                    bpy.ops.pose.select_all(action="TOGGLE")
                    bpy.ops.poselib.pose_add(frame=0, name=str(Global.get_asset_name() + " Pose"))
                    for action in bpy.data.actions:
                        if action.name == "PoseLib":
                            action.name = Global.get_asset_name() + " Pose Library"
                    bpy.ops.pose.select_all(action="DESELECT")

    
    def restore_pose(self):
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode("POSE")
        self.make_pose()
