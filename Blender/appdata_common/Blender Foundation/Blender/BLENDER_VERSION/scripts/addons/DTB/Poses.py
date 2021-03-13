import bpy
import os
import math
import json
from . import DataBase
from . import Versions
from . import Global
import re


class Posing:
    #TODO Refactor and update to Reenable
    def clear_pose(self):
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Versions.show_x_ray(Global.getAmtr())
        Global.setOpsMode('POSE')
        bpy.ops.pose.transforms_clear()
        Global.setOpsMode('OBJECT')

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

    
    def make_pose(self, transform_data):
        bone_limits = DataBase.get_bone_limits_dict()
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
                    # Y invert (-z)
                    pbs[bname].location[2] = -float(position[2])
                    
                    
                    # Rotation
                    fixed_rotation = self.reorder_rotation(order,rotation,bname)
                    pbs[bname].rotation_mode = order
                    for i in range(len(rotation)):      
                        pbs[bname].rotation_euler[i] = math.radians(float(fixed_rotation[i]))
                    pbs[bname].rotation_mode = new_order
                    
                    #Add Pose to Libary
                    bpy.ops.pose.select_all(action="TOGGLE")
                    bpy.ops.poselib.pose_add(frame=0, name=str("Pose At Import"))
                    bpy.ops.pose.select_all(action="DESELECT")


    def restore_pose(self):
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode("POSE")
        hometown = Global.getHomeTown()

        padr = hometown+ "/FIG.transforms"
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

        self.make_pose(data)
