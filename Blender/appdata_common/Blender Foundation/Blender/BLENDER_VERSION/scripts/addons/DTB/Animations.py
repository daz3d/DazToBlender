import bpy
import mathutils
from . import Poses
from . import Global
from . import Versions
from . import DataBase

class Animations:
    total_key_count = 0
    def __init__(self, dtu):
        self.skeleton_data = dtu.get_skeleton_data_dict()

        
    def update_total_key_count(self,key_count):
        if key_count > self.total_key_count:
            self.total_key_count = key_count


    def reset_total_key_count(self):
        self.total_key_count = 0

    
    def has_keyframe(self, ob):
        anim = ob.animation_data
        if anim is not None and anim.action is not None:
            return True
        return False


    def get_or_create_fcurve(self, action, data_path, array_index=-1, group=None):
        for fc in action.fcurves:
            if fc.data_path == data_path and (array_index < 0 or fc.array_index == array_index):
                return fc

        fc = action.fcurves.new(data_path, index=array_index)
        fc.group = group
        return fc


    def add_keyframe_euler(self, action, euler, frame, bone_prefix, group):
        for i in range(len(euler)):
            fc = self.get_or_create_fcurve(
                    action, bone_prefix + "rotation_euler",
                    i,
                    group
                    )
            pos = len(fc.keyframe_points)
            fc.keyframe_points.add(1)
            fc.keyframe_points[pos].co = [frame, euler[i]]
            fc.update()


    def fcurves_group(self, action, data_path):
        for fc in action.fcurves:
            if fc.data_path == data_path and fc.group is not None:
                return fc.group
        return None


    def frames_matching(self, action, data_path):
        frames = set()
        for fc in action.fcurves:
            if fc.data_path == data_path:
                fri = [kp.co[0] for kp in fc.keyframe_points]
                frames.update(fri)
        return frames


    def convert_quaternion_to_euler(self, action, obj):
        # Get all the bones with quaternion animation data
        bone_prefixes = set()
        for fcurve in action.fcurves:
            if fcurve.data_path == "rotation_quaternion" or fcurve.data_path[-20:] == ".rotation_quaternion":
                bone_prefixes.add(fcurve.data_path[:-19])

        for bone_prefix in bone_prefixes:
            if (bone_prefix == ""):
                bone = obj
            else:
                # get the bone using the data path prefix
                bone = eval("obj." + bone_prefix[:-1])

            data_path = bone_prefix + "rotation_quaternion"
            frames = self.frames_matching(action, data_path)
            group = self.fcurves_group(action, data_path)
            
            for fr in frames:
                # Get quaternion keyframe value
                quat = bone.rotation_quaternion.copy()
                for fcurve in action.fcurves:
                    if fcurve.data_path == data_path:
                        quat[fcurve.array_index] = fcurve.evaluate(fr)

                # Calculate euler equivalent for the quaternion
                order = self.get_rotation_order(bone.name)
                euler = quat.to_euler(order)

                # Add euler keyframe and set correct rotation order
                self.add_keyframe_euler(action, euler, fr, bone_prefix, group)
                bone.rotation_mode = order
        
        # delete all the curves with quaternion data
        quat_fcurves = []
        for fcurve in action.fcurves:
            if fcurve.data_path[-20:] == ".rotation_quaternion":
                quat_fcurves.append(fcurve)
        for fcurve in quat_fcurves:
            action.fcurves.remove(fcurve)    


    def get_rotation_order(self, node_name):
        bone_limits = Global.get_bone_limit()
        if node_name in bone_limits.keys():
            return bone_limits[node_name][1]
        return "XYZ"


    def convert_rotation_orders(self):
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode('POSE')
        for bone in Global.getAmtr().pose.bones:
            order = bone.rotation_mode
            if order == 'XYZ':
                bone.rotation_mode = 'ZXY'
            elif order == 'XZY':
                bone.rotation_mode = 'YZX'
            elif order == 'YZX':
                bone.rotation_mode = 'YZX'
            elif order == 'ZXY':
                bone.rotation_mode = 'XYZ'
            elif order == 'ZYX':
                bone.rotation_mode = 'YZX'


    def clean_animations(self):
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode('POSE')
        scene_size = Global.get_size()
        root_scale = float(self.skeleton_data["skeletonScale"][1])
        #Choose Action
        armature = Global.getAmtr()
        action = armature.animation_data.action
            
        # Convert rotation animation data from quaternion to euler angles
        self.convert_quaternion_to_euler(action, Global.getAmtr())

        # Convert animation data from Studio to Blender
        curve_count = len(action.fcurves)
        index = 0
        while index < curve_count:
            fcurve = action.fcurves[index]
            start_index = fcurve.data_path.find('[')
            end_index = fcurve.data_path.find(']')
            if (start_index == -1 or end_index == -1):
                # Convert Figure root bone animation data
                if "Genesis" in action.name:
                    if fcurve.data_path == "rotation_euler":
                        for point in fcurve.keyframe_points:
                            point.co[1] = 0
                    if fcurve.data_path == "scale":
                        for point in fcurve.keyframe_points:
                            point.co[1] = root_scale
                # Convert non Figure root bone animation data
                else:
                    if fcurve.data_path == "location":
                        fcurve_x = action.fcurves[index + 0]
                        fcurve_y = action.fcurves[index + 1]
                        fcurve_z = action.fcurves[index + 2]
                        point_count = len(fcurve_x.keyframe_points)

                        for i in range(point_count):
                            # Y invert (-Y)
                            fcurve_y.keyframe_points[i].co[1] = -fcurve_y.keyframe_points[i].co[1]

                            # Z invert (-Z)
                            fcurve_z.keyframe_points[i].co[1] = -fcurve_z.keyframe_points[i].co[1]
                        
                        index += 2
            else:
                node_name = fcurve.data_path[start_index + 2 : end_index - 1]
                property_name = fcurve.data_path[end_index + 2 :]
                rotation_order = self.get_rotation_order(node_name)

                # Convert location animation data for all the non root bones
                if property_name == "location":
                    fcurve_x = action.fcurves[index + 0]
                    fcurve_y = action.fcurves[index + 1]
                    fcurve_z = action.fcurves[index + 2]
                    point_count = len(fcurve_x.keyframe_points)
                    self.update_total_key_count(point_count)

                    for i in range(point_count):
                        # Y invert (-Y)
                        fcurve_y.keyframe_points[i].co[1] = -fcurve_y.keyframe_points[i].co[1]

                        # Z invert (-Z)
                        fcurve_z.keyframe_points[i].co[1] = -fcurve_z.keyframe_points[i].co[1]

                    # Get skeleton scale and set to location animation data
                    root_scale *= scene_size # To match armature scale
                    for i in range(point_count):
                        fcurve_x.keyframe_points[i].co[1] *= root_scale 
                        fcurve_y.keyframe_points[i].co[1] *= root_scale
                        fcurve_z.keyframe_points[i].co[1] *= root_scale

                    index += 2

                # Convert rotation animation data for all the non root bones
                if property_name == "rotation_euler":
                    fcurve_x = action.fcurves[index + 0]
                    fcurve_y = action.fcurves[index + 1]
                    fcurve_z = action.fcurves[index + 2]
                    point_count = len(fcurve_x.keyframe_points)
                    self.update_total_key_count(point_count)

                    if rotation_order == 'XYZ':
                        for i in range(point_count):
                            # YZ switch (Y <-> Z)
                            temp = fcurve_y.keyframe_points[i].co[1]
                            fcurve_y.keyframe_points[i].co[1] = fcurve_z.keyframe_points[i].co[1]
                            fcurve_z.keyframe_points[i].co[1] = temp

                            # XY switch (X <-> Y)
                            temp = fcurve_x.keyframe_points[i].co[1]
                            fcurve_x.keyframe_points[i].co[1] = fcurve_y.keyframe_points[i].co[1]
                            fcurve_y.keyframe_points[i].co[1] = temp

                            if(node_name.startswith("r")):
                                # Y invert (-Y)
                                fcurve_y.keyframe_points[i].co[1] = -fcurve_y.keyframe_points[i].co[1]

                                # Z invert (-Z)
                                fcurve_z.keyframe_points[i].co[1] = -fcurve_z.keyframe_points[i].co[1]

                    elif rotation_order == 'XZY':
                        for i in range(point_count):
                            # XY switch (X <-> Y)
                            temp = fcurve_x.keyframe_points[i].co[1]
                            fcurve_x.keyframe_points[i].co[1] = fcurve_y.keyframe_points[i].co[1]
                            fcurve_y.keyframe_points[i].co[1] = temp

                            # X invert (-X)
                            fcurve_x.keyframe_points[i].co[1] = -fcurve_x.keyframe_points[i].co[1]

                            if(node_name.startswith("r")):
                                # Y invert (-Y)
                                fcurve_y.keyframe_points[i].co[1] = -fcurve_y.keyframe_points[i].co[1]

                                # Z invert (-Z)
                                fcurve_z.keyframe_points[i].co[1] = -fcurve_z.keyframe_points[i].co[1]

                    elif rotation_order == "YZX":
                        # Bones that are pointed down with YZX order
                        # TODO: remove hardcoding
                        lower_extremities_to_flip = DataBase.get_lower_extremities_to_flip()
                        if node_name in lower_extremities_to_flip:
                            for i in range(point_count):
                                # Y invert (-Y)
                                fcurve_y.keyframe_points[i].co[1] = -fcurve_y.keyframe_points[i].co[1]

                                # Z invert (-Z)
                                fcurve_z.keyframe_points[i].co[1] = -fcurve_z.keyframe_points[i].co[1]

                    elif rotation_order == "ZXY":
                        for i in range(point_count):
                            # XY switch (X <-> Y)
                            temp = fcurve_x.keyframe_points[i].co[1]
                            fcurve_x.keyframe_points[i].co[1] = fcurve_y.keyframe_points[i].co[1]
                            fcurve_y.keyframe_points[i].co[1] = temp

                            # YZ switch (Y <-> Z)
                            temp = fcurve_y.keyframe_points[i].co[1]
                            fcurve_y.keyframe_points[i].co[1] = fcurve_z.keyframe_points[i].co[1]
                            fcurve_z.keyframe_points[i].co[1] = temp

                    elif rotation_order == "ZYX":
                        for i in range(point_count):
                            # YZ switch (Y <-> Z)
                            temp = fcurve_y.keyframe_points[i].co[1]
                            fcurve_y.keyframe_points[i].co[1] = fcurve_z.keyframe_points[i].co[1]
                            fcurve_z.keyframe_points[i].co[1] = temp

                            # X invert (-X)
                            fcurve_x.keyframe_points[i].co[1] = -fcurve_x.keyframe_points[i].co[1]
                    
                    index += 2

            index += 1

        self.convert_rotation_orders()

        # Update Name
        action.name = "{0} Animation".format(Global.get_asset_name())