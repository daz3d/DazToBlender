import bpy
import os
import json
import math
import mathutils
from . import Versions
from . import Global
from . import Util
from . import DtbMaterial
from . import NodeArrange
import re

def set_transform(obj,data,type):
    if type == "scale":
        transform = obj.scale
    if type == "rotate":
        transform = obj.rotation_euler
        for i in range(len(data)):
            data[i] = math.radians(data[i])
    if type == "translate":
        transform = obj.location
    for i in range(3):
        transform[i] = float(data[i])    
def progress_bar(percent):
    bpy.context.window_manager.progress_update(percent)


class EnvProp:
    env_root = Global.getRootPath() + "ENV" + Global.getFileSp()

    def __init__(self):
        Util.deleteEmptyDazCollection() # Remove Empty Collections
        self.execute()

    def execute(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        Versions.active_object_none() # deselect all
        self.set_default_settings()
        if os.path.exists(self.env_root)==False:
            return
        progress_bar(0)
        env_dirs = os.listdir(self.env_root)
        env_dirs = [f for f in env_dirs if os.path.isdir(os.path.join(self.env_root, f))]
        
        int_progress = 100/len(env_dirs)
        for i in range(len(env_dirs)):
            Global.clear_variables()
            Global.setHomeTown(
                                Global.getRootPath() + Global.getFileSp() + "ENV" + 
                                Global.getFileSp() + "ENV" + str(i)
                                )
            Util.decideCurrentCollection('ENV')
            progress_bar(int(int_progress * i) + 5)
            ReadFbx(self.env_root + 'ENV' + str(i) + Global.getFileSp(), i, int_progress)
            Versions.active_object_none()
        progress_bar(100)
        Global.setOpsMode("OBJECT")
        wm.progress_end()
        Versions.make_sun()

    def set_default_settings(self):
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.color_type = 'OBJECT'
        bpy.context.space_data.shading.show_shadows = False
        bco = bpy.context.object
        if bco != None and bco.mode != 'OBJECT':
            Global.setOpsMode('OBJECT')
        bpy.ops.view3d.snap_cursor_to_center()

class ReadFbx:
    adr = ""
    index = 0
    bone_head_tail_dict = None
    pose_data = {}
    my_meshs = []

    def __init__(self,dir,i,int_progress):
        self.adr = dir
        self.my_meshs = []
        self.index = i
        self.pose_data = {}
        self.bone_head_tail_dict = None
        if self.read_fbx():
            progress_bar(int(i*int_progress)+int(int_progress/2))
            self.setMaterial()
        Global.scale_environment()

    def read_fbx(self):
        self.my_meshs = []
        adr = self.adr + "B_ENV.fbx"
        if os.path.exists(adr) == False:
            return
        objs = self.convert_file(adr)
        for obj in objs:
            if obj.type == 'MESH':
                self.my_meshs.append(obj)
        if objs is None or len(objs) == 0:
            return
        Global.find_ENVROOT(objs[0])
        root = Global.getEnvRoot()
        if len(objs) > 1:
            if root is None:
                return
            else:
                objs.remove(root)
        else:
            root = objs[0]
        Versions.active_object(root)
        Global.deselect()
        if root.type == 'ARMATURE':
            self.import_as_armature(objs, root)
        #TODO: Remove Groups with no MESH   
        elif root.type == 'EMPTY':
            no_empty = False
            for o in objs:
                if o.type != 'EMPTY':
                    no_empty = True
                    break
            if no_empty == False:
                for o in objs:
                    bpy.data.objects.remove(o)
                return False
            else:
                self.import_empty(objs, Global.getEnvRoot())
        if Global.want_real():
            Global.changeSize(1,[])
        return True
            
    
    def convert_file(self, filepath):
        Global.store_ary(False) #Gets all objects before.
        basename = os.path.basename(filepath)
        (filename, fileext) = os.path.splitext(basename)
        ext = fileext.lower()
        if os.path.isfile(filepath):
            if ext == '.fbx':
                bpy.ops.import_scene.fbx(
                    filepath = filepath,
                    use_manual_orientation = False,
                    bake_space_transform = False,
                    use_image_search = True,
                    use_anim = True,
                    anim_offset = 0,
                    ignore_leaf_bones = False,
                    force_connect_children = False,
                    automatic_bone_orientation = False,
                    use_prepost_rot = False
                    )
        Global.store_ary(True) #Gets all objects after.
        return self.new_objects()

    def new_objects(self):
        rtn = []
        if len(Global.now_ary) == len(Global.pst_ary):
            return ""
        rtn = [bpy.data.objects[n] for n in Global.now_ary if not n in Global.pst_ary]
        return rtn
    
    #TODO: combine shared code with figure import
    def import_as_armature(self, objs, amtr):
        Global.deselect()
        self.create_controller()
        vertex_group_names = []
        empty_objs = []
        amtr_objs = []
        
        for i in range(3):
            amtr.scale[i] = 1
        
        #Apply Armature Modifer if it does not exist
        for obj in objs:
            if obj.type == 'MESH':
                amtr_objs.append(obj)
                vgs = obj.vertex_groups
                if len(vgs) > 0:
                    vertex_group_names = [vg.name for vg in vgs]
                    if self.is_armature_modified(obj) == False:
                        amod = obj.modifiers.new(type='ARMATURE', name="ama" + obj.name)
                        amod.object = amtr
            elif obj.type == 'EMPTY':
                if obj.parent == amtr:
                    empty_objs.append(obj)
        Global.deselect()
        
        #Apply rest pose        
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Global.setOpsMode("POSE")
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.pose.select_all(action='DESELECT')
        Global.setOpsMode("EDIT")
        
        hides = []
        bones = amtr.data.edit_bones
        bcnt = len(bones)
        notbuilding = bcnt > 30  #Use DTU to check Asset Type
        
        #Fix and Check Bones to Hide
        for bone in bones:
            binfo = self.get_bone_info(bone.name)
            if binfo is None:
                hides.append(bone.name)
                continue
            if bone.name not in vertex_group_names:
                if self.is_child_bone(amtr, bone, vertex_group_names) == False:
                    hides.append(bone.name)
                    continue
            
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
            
        for obj in objs:
            Versions.select(obj, True)
            Versions.active_object(obj)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            Versions.select(obj,False)

        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Global.setOpsMode("POSE")
        amtr.show_in_front = True

        #Apply Custom Shape
        for pb in amtr.pose.bones:
            binfo = self.get_bone_info(pb.name)
            if binfo is None:
                continue
            else:
                ob = Util.allobjs().get('daz_prop')
                if ob is not None:
                    pb.custom_shape = ob
                    pb.custom_shape_scale = 0.04
                    amtr.data.bones.get(pb.name).show_wire = True
            #Apply Limits 
            #TODO: Clean up to be more readible
            lrs = [False, False, False]
            for i in range(3):
                for j in range(3):
                    if binfo[10 + (i * 3) + j] == '0':
                        if i == 0 and lrs[i] == False:
                            lrs[i] = True
                            lim = pb.constraints.new(type='LIMIT_LOCATION')
                            lim.owner_space = 'LOCAL'
                        elif i == 1 and lrs[i] == False:
                            lim = pb.constraints.new(type='LIMIT_ROTATION')
                            lim.owner_space = 'LOCAL'
                            lrs[i] = True
                        elif i == 2 and lrs[i] == False:
                            lrs[i] = True
                            lim = pb.constraints.new(type='LIMIT_SCALE')
                            lim.owner_space = 'LOCAL'
                        if j == 0:
                            if i == 1:
                                lim.use_limit_x = True
                                lim.use_limit_x = True
                            else:
                                lim.use_min_x = True
                                lim.use_max_x = True
                        elif j == 1:
                            if i == 1:
                                lim.use_limit_y = True
                                lim.use_limit_y = True
                            else:
                                lim.use_min_y = True
                                lim.use_max_y = True
                        elif j == 2:
                            if i == 1:
                                lim.use_limit_z = True
                                lim.use_limit_z = True
                            else:
                                lim.use_min_z = True
                                lim.use_max_z = True
                        if i == 2:
                            lim.min_x = 1
                            lim.min_y = 1
                            lim.min_z = 1
                            lim.max_x = 1
                            lim.max_y = 1
                            lim.max_z = 1

        # Hide Bones
        for hide in hides:
            amtr.data.bones.get(hide).hide = True

    
    def create_controller(self):
        if 'daz_prop' in Util.colobjs('DAZ_HIDE'):
            return
        Global.setOpsMode('OBJECT')
        bpy.ops.mesh.primitive_circle_add()
        Global.setOpsMode('EDIT')
        args = [(0, 0, math.radians(90)), (math.radians(90), 0, 0), (0, math.radians(90), 0)]
        for i in range(3):
            bpy.ops.mesh.primitive_circle_add(
                rotation=args[i]
            )
        Global.setOpsMode('OBJECT')
        bpy.context.object.name = 'daz_prop'
        Util.to_other_collection([bpy.context.object],'DAZ_HIDE',Util.cur_col_name())

    
    def is_armature_modified(self,dobj):
        if dobj.type == 'MESH':
            for modifier in dobj.modifiers:
                if modifier.type=='ARMATURE' and modifier.object is not None:
                    return True
        return False


    #Bone property
    def get_bone_info(self,bname):
        bname = bname.split(".00")[0] # To deal with Duplicates
        if self.bone_head_tail_dict is None:
            self.get_bone_head_tail_data()
        if bname in self.bone_head_tail_dict.keys():
            return self.bone_head_tail_dict[bname]
        return None

    
    def get_bone_head_tail_data(self):
        input_file = open(self.adr + "ENV_boneHeadTail.csv", "r")
        lines = input_file.readlines()
        input_file.close()
        self.bone_head_tail_dict = dict()
        for line in lines:
            line_split = line.split(",")
            self.bone_head_tail_dict[line_split[0]] = line_split


    def is_child_bone(self,amtr,bone,vertex_groups):
        rtn = self.has_child(amtr,bone)
        if rtn is None or len(rtn) == 0:
            return False
        for r in rtn:
            if r not in vertex_groups:
                return False
        return True

    def has_child(self,amtr,vertex_groups):
        rtn = []
        for bone in amtr.data.edit_bones:
            if bone.parent == vertex_groups:
                rtn.append(bone.name)
        return rtn
    
    def import_empty(self, objs, root):
        # Load an instance of the pose info
        self.load_pose_data()
        set_transform(root,[1,1,1],"scale")
        Global.deselect()
        
        root_pose = self.get_pose(root)
        #Organize List
        objs = sorted(objs, key = lambda obj: obj.name)
        for obj in objs:
            if obj is None or obj == root:
                continue
            Versions.select(obj, True)
            Versions.active_object(obj)
            pose = self.get_pose(obj)
            if pose != {}:
                if obj.type == pose["Object Type"]:
                    # Set Position of Shape
                    #bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    #set_transform(obj, [0, obj.location[1], 0], "translate")
                    # Delete data to speed up next object
                    del self.pose_data[pose['Label']]
                # for i in range(3):
                    # obj.lock_location[i] = True
                    # obj.lock_rotation[i] = True
                    # obj.lock_scale[i] = True
                Global.deselect()
            else:
                print(obj.name)
        Versions.select(root, True)
        Versions.active_object(root)

        for i in range(3):
            root.lock_location[i] = True
            root.lock_rotation[i] = True
            root.lock_scale[i] = True
        Global.setOpsMode('OBJECT')


    def load_pose_data(self):
        with open(self.adr+"ENV.transforms") as f:
            self.pose_data = json.load(f)
    
 
    def get_pose(self,obj):
        obj_name = obj.name.replace(".Shape", "")
        if obj_name in self.pose_data:
            return self.pose_data[obj_name]

        for key in self.pose_data:
            if obj_name == key:
                return self.pose_data[obj_name]
            elif obj_name.replace("_dup_", " ") == key:
                return self.pose_data[key]
            elif len(obj_name.split(".00")) > 1:
                temp_name = obj_name.split(".00")[0] + " " + str(int(obj_name.split(".00")[1]) + 1)
                if temp_name == key:
                    return self.pose_data[key] 
            elif self.pose_data[key]["Name"] == obj_name:
                return self.pose_data[key]
        return {}

    def setMaterial(self):
        dtb_shaders = DtbMaterial.DtbShaders()
        dtb_shaders.make_dct()
        dtb_shaders.load_shader_nodes()
        for mesh in self.my_meshs:
            dtb_shaders.env_textures(mesh)
            


    
