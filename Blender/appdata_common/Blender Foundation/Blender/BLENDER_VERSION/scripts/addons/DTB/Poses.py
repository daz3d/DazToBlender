import bpy
import os
import math
import json
import mathutils
import gzip
import urllib.parse
from . import DataBase
from . import Versions
from . import Global
import re


class Posing:
    
    bone_head_tail_dict = {}
    bone_limits_dict = {}
    pose_data_dict = {}
    skeleton_data_dict = {}
    fig_object = ""
    fig_object_name = "" 

    def __init__(self, dtu):
        if isinstance(dtu, str):
            self.select_figure()
            Global.setOpsMode("POSE")
        else:
            self.bone_limits_dict = dtu.get_bone_limits_dict()
            self.skeleton_data_dict = dtu.get_skeleton_data_dict()
            self.pose_data_dict = dtu.get_pose_data_dict()
            self.bone_head_tail_dict = dtu.get_bone_head_tail_dict()
            
    def is_json(self, myjson):
        try:
            json_object = json.load(myjson)
        except ValueError as e:
            return False
        return True    


    def load_duf(self, input_duf):
        with open(input_duf, "r") as file:
            string = file
            if self.is_json(string):
                with open(input_duf, "r") as file:
                    return json.load(file)
            else:
                data =  gzip.open(input_duf, "rb")
                return json.load(data)

    def select_figure(self):
        fig_object_name = bpy.context.window_manager.choose_daz_figure
        Global.deselect()
        bpy.context.view_layer.objects.active = bpy.data.objects[fig_object_name]
        
   
    def add_skeleton_data(self):
        self.fig_object_name = bpy.context.window_manager.choose_daz_figure
        if self.fig_object_name == "null":
            return
        self.fig_object  = bpy.data.objects[self.fig_object_name]
        skeleton_data = self.skeleton_data_dict
        # Add to properties
        for key in skeleton_data:
           self.fig_object[key] =  float(skeleton_data[key][1])


    def get_scale(self):
        self.fig_object_name = bpy.context.window_manager.choose_daz_figure
        if self.fig_object_name == "null":
            return 1
        self.fig_object  = bpy.data.objects[self.fig_object_name]
        return float(self.fig_object["skeletonScale"])

   
    def get_offset(self):
        self.fig_object_name = bpy.context.window_manager.choose_daz_figure
        if self.fig_object_name == "null":
            return 0
        self.fig_object  = bpy.data.objects[self.fig_object_name]
        return float(self.fig_object["offset"])

   
    # Bone property
    def get_bone_head_tail_data(self, bname):
        bname = bname.split(".00")[0] # To deal with Duplicates
        if bname in self.bone_head_tail_dict.keys():
            return self.bone_head_tail_dict[bname]
        return None
    
    # Taken from DazRigBlend and Adjusted for Environments
    def reposition_asset(self, dobj, amtr):
        self.del_empty = []
        Global.deselect()
        # Cycles through the objects and unparents the meshes from the figure.
        if dobj.type == "MESH":
            if dobj.parent == amtr:
                Versions.select(dobj, True)
                Versions.active_object(dobj)
                bpy.ops.object.transform_apply(
                    location=True, rotation=True, scale=True
                )
                bpy.ops.object.parent_clear()
                Versions.select(dobj, False)
        Global.deselect()

        # Zero out the transforms on the Armature
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Versions.show_x_ray(amtr)
        Global.setOpsMode("POSE")
        bpy.ops.pose.transforms_clear()
        Global.setOpsMode("OBJECT")
        bpy.ops.object.scale_clear()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        Global.deselect()

        # Reposition Object
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        dobj.rotation_euler.x += math.radians(90)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for i in range(3):
            dobj.lock_location[i] = True
            dobj.lock_rotation[i] = True
            dobj.lock_scale[i] = True
        Global.deselect()

        # Reparent to Armature
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Global.setOpsMode("OBJECT")
        Versions.select(dobj, True)
        Versions.select(amtr, True)
        bpy.ops.object.parent_set(type="ARMATURE")
        Versions.select(dobj, False)
        Versions.select(amtr, False)

    # TODO: Combine with Animation Version
    def set_bone_head_tail(self, bone):
        binfo = self.get_bone_head_tail_data(bone.name)
        
        if binfo is None:
            return False
        else:

            # set head
            bone.head[0] = float(binfo[0])
            bone.head[1] = -float(binfo[2])
            bone.head[2] = float(binfo[1])
            
            # set tail
            bone.tail[0] = float(binfo[3])
            bone.tail[1] = -float(binfo[5])
            bone.tail[2] = float(binfo[4])

            # calculate roll aligning bone towards a vector
            align_axis_vec = mathutils.Vector((
                                float(binfo[6]),
                                -float(binfo[8]),
                                float(binfo[7])
                                ))
            bone.align_roll(align_axis_vec)
            
            return True


    def get_bone_limits_dict(self, bname):
        bname = bname.split(".00")[0] # To deal with Duplicates
        if bname in self.bone_limits_dict.keys():
            return self.bone_limits_dict[bname]
        
    # TODO: Combine with Figure Version
    def bone_limit_modify(self, bone):
        bone_limit = self.get_bone_limits_dict(bone.name)
        order = bone_limit[1]
        new_bone_limit = self.reorder_limits(order, bone_limit, bone.name)
        new_order = self.get_rotation_order(order)
        bone["Daz Rotation Order"] = bone_limit[1]
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

        # TODO: Check how to convert it.
        elif rotation_order == "YXZ":
            return limits
        return limits


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


    def pose_copy(self,dur):
        self.pose_data_dict = {}
        if os.path.exists(dur) == False:
            return
        pose_data = self.load_duf(dur)
        self.pose_data_dict["Asset Name"] = pose_data["asset_info"]["id"].split("/")[-1].replace("%20"," ").replace(".duf","")
        for info in pose_data["scene"]["animations"]:
            url = info["url"]
            keys = info["keys"]
            sep = url.split("/")
            # To Deal with Shape_keys info
            if "#" in sep[2]:
                continue

            # To Deal with Root Bone
            if "?" in sep[2]:
                bone = "root"
                transform = sep[2].split("?")[1]
                axis = sep[3]
            else:
                bone = sep[3].split(":?")[0]
                transform = sep[3].split(":?")[1]
                axis = sep[4]

            value = keys[0][1]
            if bone not in self.pose_data_dict.keys():
                self.pose_data_dict[bone] = {}
            if "Position" not in self.pose_data_dict[bone].keys():
                self.pose_data_dict[bone]["Position"] = [0, 0, 0]
            if "Rotation" not in self.pose_data_dict[bone].keys():
                self.pose_data_dict[bone]["Rotation"] = [0, 0, 0]
            if axis == "x":
                index = 0
            if axis == "y":
                index = 1
            if axis == "z":
                index = 2
            if transform == "translation":
                trans_key = "Position"
            if transform == "rotation":
                trans_key = "Rotation"
            self.pose_data_dict[bone][trans_key][index] = value

        self.make_pose()

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
            rotations[1] = rotations[2]
            rotations[2] = temp

            # X invert (-X)
            rotations[0] = -rotations[0]

        elif rotation_order == "YXZ":
            return rotations
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
        elif order == "YXZ":
            return 'ZYX'
    
    
    def update_scale(self):
        Global.setOpsMode("POSE")
        self.fig_object_name = bpy.context.window_manager.choose_daz_figure
        if self.fig_object_name == "null":
            return
        self.fig_object  = bpy.data.objects[self.fig_object_name]
        pbs = self.fig_object.pose.bones
        root_bone = pbs[0]
        root_name = root_bone.name
        scale = self.get_scale()
        pbs[root_name].scale[0] = scale
        pbs[root_name].scale[1] = scale
        pbs[root_name].scale[2] = scale

    
    def make_pose(self, use="FIG", armature=None):
        Global.setOpsMode("POSE")
        bone_limits = self.bone_limits_dict
        transform_data = self.pose_data_dict
        if use == "FIG":
            self.fig_object_name = bpy.context.window_manager.choose_daz_figure
            if self.fig_object_name == "null":
                return
            self.fig_object  = bpy.data.objects[self.fig_object_name]
            pbs = self.fig_object.pose.bones
        else:
            pbs = armature.pose.bones
        for pb in pbs:
            if pb.name == "root":
                bname = pb.name
                order = "YXZ"
                new_order = self.get_rotation_order(order)
                pb.rotation_mode = new_order
                
                if "root" in transform_data.keys():
                    position = transform_data[bname]["Position"]
                    rotation = transform_data[bname]["Rotation"]
                    for i in range(len(position)):
                        position[i] = position[i] * Global.get_size()

                    pbs[bname].location[0] = float(position[0])
                    # Y invert (-Y) and Flip with Z
                    pbs[bname].location[1] = -float(position[2])
                    # Z invert (-Z) and Flip with Y
                    pbs[bname].location[2] = float(position[1])
                    
                    # Rotation
                    fixed_rotation = self.reorder_rotation(new_order,rotation,bname)
                    pbs[bname].rotation_mode = order
                    for i in range(len(rotation)):      
                        pbs[bname].rotation_euler[i] = math.radians(float(fixed_rotation[i]))
                    pbs[bname].rotation_mode = new_order
            if "Daz Rotation Order" in pb.keys():
                order = pb["Daz Rotation Order"]
                bname = pb.name
                new_order = self.get_rotation_order(order)
                if bname in transform_data.keys():
                    
                    position = transform_data[bname]["Position"]
                    rotation = transform_data[bname]["Rotation"]
                    # Position
                    if bname == "hip":
                        if self.get_offset() != 0:
                            position[1] = position[1] - self.get_offset()
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
                    
        if (bpy.context.window_manager.add_pose_lib):
            if use == "FIG":
                if self.pose_lib_check():
                    self.add_pose(transform_data)
                    num = ""
                    if ".0" in self.fig_object_name:
                        num = " " + self.fig_object_name[-1]
                    bpy.ops.pose.select_all(action="SELECT")
                    bpy.ops.poselib.pose_add(frame=0, name=str(self.fig_object["Asset Name"] + " Pose"))
                    action = bpy.data.actions["PoseLib"]
                    action.name = self.fig_object["Asset Name"] + num + " Pose Library"
                    bpy.ops.pose.select_all(action="DESELECT")

        
    def pose_lib_check(self):
        if ".0" in self.fig_object_name:
            num = " " + self.fig_object_name[-1]
            name = self.fig_object["Asset Name"] + num + " Pose Library"
        else:
            name = self.fig_object["Asset Name"] + " Pose Library"
        if name in bpy.data.actions.keys():  
            return True

    
    # Add Pose to Library
    def add_pose(self,transform_data):
        if ".0" in self.fig_object_name:
                num = ""
                if ".0" in self.fig_object_name:
                    num = " " + self.fig_object_name[-1]
                    name = self.fig_object["Asset Name"] + num + " Pose Library"
        else:
            name = self.fig_object["Asset Name"] + " Pose Library"
        action = bpy.data.actions[name]
        frame_count = len(action.pose_markers) + 1
        
        if "Asset Name" in transform_data.keys():
            pose_name = transform_data["Asset Name"]
        else:
            pose_name = frame_count

        bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.poselib.pose_add(frame=frame_count, name=str(pose_name))
        bpy.ops.pose.select_all(action="DESELECT")
       
    
    def restore_pose(self):
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode("POSE")
        self.make_pose()

    def restore_env_pose(self, amtr):
        Versions.active_object(amtr)
        Global.setOpsMode("POSE")
        self.make_pose("ENV", amtr)