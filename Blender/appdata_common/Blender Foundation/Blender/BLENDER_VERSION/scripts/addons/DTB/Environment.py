import bpy
import os
import json
import math
from . import Versions
from . import Global
from . import Util
from . import DtbMaterial
from . import NodeArrange
from . import Poses
from . import DataBase
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
    env_root = os.path.join(Global.getRootPath(), "ENV")
    if bpy.context.window_manager.use_custom_path:
        env_root = os.path.join(Global.get_custom_path() , "ENV")

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
        current_dir = os.getcwd()
        os.chdir(self.env_root)
        progress_bar(0)
        env_dirs = os.listdir(self.env_root)
        env_dirs = [f for f in env_dirs if os.path.isdir(os.path.join(self.env_root, f))]
        int_progress = 100/len(env_dirs)
        for i in range(len(env_dirs)):
            Global.clear_variables()
            Global.setHomeTown(os.path.join(
                                self.env_root, "ENV" + str(i)
                                ))
            Global.load_asset_name()
            Util.decideCurrentCollection('ENV')
            progress_bar(int(int_progress * i) + 5)
            ReadFbx(os.path.join(self.env_root, 'ENV' + str(i)), i, int_progress)
            Versions.active_object_none()
        progress_bar(100)
        Global.setOpsMode("OBJECT")
        wm.progress_end()
        Versions.make_sun()
        os.chdir(current_dir)
        return {"FINISHED"}

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
    my_meshs = []

    def __init__(self,dir,i,int_progress):
        self.dtu = DataBase.DtuLoader()
        self.pose = Poses.Posing(self.dtu)
        self.dtb_shaders = DtbMaterial.DtbShaders(self.dtu)
        self.adr = dir
        self.my_meshs = []
        self.index = i
        if self.read_fbx():
            progress_bar(int(i * int_progress)+int(int_progress / 2))
            self.setMaterial()
        Global.scale_settings()

    def read_fbx(self):
        self.my_meshs = []
        adr = os.path.join(self.adr, "B_ENV.fbx")
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
        # Temporaily Delete Animation Until Support is Added
        root.animation_data_clear()
        for obj in objs:
            obj.animation_data_clear()
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
        Global.change_size(Global.getEnvRoot())
        
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
                    primary_bone_axis = 'Y',
                    secondary_bone_axis = 'X',
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
                self.pose.reposition_asset(obj, amtr)
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
        
        #Fix and Check Bones to Hide
        for bone in bones:
            to_hide = self.pose.set_bone_head_tail(bone)
            if not to_hide:
                hides.append(bone.name)
                continue
            if bone.name not in vertex_group_names:
                if self.is_child_bone(amtr, bone, vertex_group_names) == False:
                    hides.append(bone.name)
                    continue
        
        Global.setOpsMode("OBJECT")
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
            
            binfo = self.pose.get_bone_limits_dict(pb.name)
            if binfo is None:
                continue
            else:
                ob = Util.allobjs().get('daz_prop')
                if ob is not None:
                    pb.custom_shape = ob
                    pb.custom_shape_scale = 0.04
                    amtr.data.bones.get(pb.name).show_wire = True
            #Apply Limits and Change Rotation Order
            self.pose.bone_limit_modify(pb)

        # Hide Bones
        for hide in hides:
            amtr.data.bones.get(hide).hide = True

        #Restore Pose.
        self.pose.restore_env_pose(amtr)
    
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
        set_transform(root,[1,1,1],"scale")
        Global.deselect()
        Versions.select(root, True)
        Versions.active_object(root)

        for i in range(3):
            root.lock_location[i] = True
            root.lock_rotation[i] = True
            root.lock_scale[i] = True
        Global.setOpsMode('OBJECT')    

    
    def setMaterial(self):
        self.dtb_shaders.make_dct()
        self.dtb_shaders.load_shader_nodes()
        for mesh in self.my_meshs:
            self.dtb_shaders.setup_materials(mesh)
            


    
