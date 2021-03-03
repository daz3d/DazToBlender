import bpy
import os
import math
import mathutils
from . import Versions
from . import Global
from . import Util
from . import DtbMaterial
from . import NodeArrange
import re


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
    _pose_ary = None
    bone_head_tail_dict = None
    ss_ary = []
    asc_ary = []
    my_meshs = []

    def __init__(self,dir,i,int_progress):
        self.adr = dir
        self.my_meshs = []
        self.index = i
        self.ss_ary = []
        self._pose_ary = None
        self.bone_head_tail_dict = None
        self.asc_ary = []
        if self.read_fbx():
            progress_bar(int(i*int_progress)+int(int_progress/2))
            self.readAsc()
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
    #Currently not setting bones as expected.
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
            # bone.head[0] = float(binfo[1])
            # bone.head[1] = -float(binfo[3])
            # bone.head[2] = float(binfo[2])
            
            # set tail
            # bone.tail[0] = float(binfo[4])
            # bone.tail[1] = -float(binfo[6])
            # bone.tail[2] = float(binfo[5])

            # calculate roll aligning bone towards a vector
            # align_axis_vec = mathutils.Vector((
            #                     float(binfo[7]),
            #                     -float(binfo[9]),
            #                     float(binfo[8])
            #                     ))
            # bone.align_roll(align_axis_vec)
            
        # Freeze Transforms
        Global.setOpsMode('OBJECT')
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        Global.deselect()

        for obj in objs:
            Versions.select(obj, True)
            Versions.active_object(obj)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            Versions.select(obj,False)

        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Global.setOpsMode("POSE")
        amtr.show_in_front = True

        #Apply Custom Shape and Limits
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

        for i in range(3):
            root.scale[i] = 1
        Global.deselect()
        
        root_pose = self.get_pose(root)

        for obj in objs:
            if obj is None or obj==root:
                continue
            Versions.select(obj, True)
            Versions.active_object(obj)
            pose = self.get_pose(obj)
            for i in range(3):
                obj.scale[i] = 1

            if obj.type == 'EMPTY':
                for i in range(3):
                    obj.scale[i] = float(pose[i+9])
                    obj.rotation_euler[i] = 0

            elif obj.type == 'LIGHT' or obj.type == 'CAMERA':
                for i in range(3):
                    print(obj.name, obj.type, "#####", pose[i+3])
                    obj.lock_location[i] = False
                    obj.location[i] = float(pose[i+3]) + float(root_pose[i+3])
                    self.before_edit_prop()
                    obj.rotation_euler[i] = math.radians(float(pose[i+6]))
                    obj.scale[i] = 1

            for i in range(3):
                obj.lock_location[i] = True
                obj.lock_rotation[i] = True
                obj.lock_scale[i] = True

            Global.deselect()
        Versions.select(root, True)
        Versions.active_object(root)

        for i in range(3):
            root.lock_location[i] = True
            root.lock_rotation[i] = True
            root.lock_scale[i] = True
        Global.setOpsMode('OBJECT')


    #TODO: SET UP DICTIONARY ON EXPORT
    def get_pose(self,obj):
        obj_name = obj.name.split(".00")[0]
        a = obj_name.find(".Shape")
        if a > 0:
            obj_name = obj_name[0:a]
        if self.ss_ary == []:
            if self._pose_ary is None:
                with open(self.adr+"ENV.csv") as f:
                    self._pose_ary = f.readlines()
            if self._pose_ary is None:
                return None
            num = 2
            for p in self._pose_ary:
                if p.endswith("\n"):
                    p = p[0:len(p)-1]
                ss = p.split(',')
                #manage [_dup_] files
                if ss[0] != ss[1]:
                    ss[0] = ss[1] + "_dup_" + str(num)
                    num += 1
                self.ss_ary.append(ss)
        for ss in self.ss_ary:
            if ss[1] == obj_name:
                if ss[2] == obj.type:
                    return ss
        return [obj_name,obj_name,"?",0,0,0,0,0,0,1,1,1]


    def readAsc(self):
        adr = self.adr + "A_ENV.fbx"
        if os.path.exists(adr) == False:
            return
        with open(adr) as f:
            ls= f.readlines()
        max = len(ls)
        args = ['Material','Texture','Model']#,'Pose']
        for idx,l in enumerate(ls):
            l = l.replace('"','')
            if l.endswith("\n"):
                l = l[0:len(l)-1]
            for pidx,arg in enumerate(args):
                pt = "^\s+" + arg + ":\s\d+,\s" + arg + "::[\w\s]+,[\w\s]+\{"
                rep = re.compile(pt)
                result = rep.search(l)
                if result:
                    a = l.rfind("::")
                    b = l.rfind(',')
                    if b<a:
                        continue
                    title = l[a+2:b]
                    hani = [30,15,30]
                    for i in range(hani[pidx]):
                        if (i+idx)>=max:
                            break
                        getp = ls[idx+i].strip()
                        if pidx==0 and ("}" in getp):
                            break
                        yoko = []
                        if pidx==1:
                            if getp.startswith("FileName: "):
                                getp = getp[10:]
                                getp = getp.replace('"', '')
                                yoko = [getp]
                        else:
                            if getp.startswith("P: "):
                                getp = getp[3:]
                                getp = getp.replace('"",','"-",')
                                getp = getp.replace('"','')
                                getp = getp.replace(" ","")
                                yoko = getp.split(",")
                        if len(yoko)>0:
                            yoko.insert(0,title)
                            if pidx==2:
                                yoko.insert(0, "B")
                            else:
                                yoko.insert(0, arg[0:1])
                            self.asc_ary.append(yoko)
                            if pidx>0:
                                break
        #for aa in self.asc_ary:
        #    print(aa)

    def setMaterial(self):
        dtb_shaders = DtbMaterial.DtbShaders()
        dtb_shaders.make_dct()
        dtb_shaders.load_shader_nodes()
        for mesh in self.my_meshs:
            dtb_shaders.env_textures(mesh)
            

    def before_edit_prop(self):
        BV = 2.83
        if BV < 2.80:
            for space in bpy.context.area.spaces:
                if space.type == 'VIEW_3D':
                    space.pivot_point = 'BOUNDING_BOX_CENTER'
                    space.cursor_location = (0.0, 0.0, 0.0)
            bpy.context.space_data.transform_orientation = 'GLOBAL'
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'ROTATE'}
        else:
            bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
            bpy.ops.view3d.snap_cursor_to_center()
            for s in bpy.context.scene.transform_orientation_slots:
                s.type = 'GLOBAL'

    def import_one(self,single):
        for i in range(3):
            single.scale[i] = 1
        if single.type=='LIGHT':
            pose = self.get_pose(single)
            single.location[0] = float(pose[0 + 3])
            single.location[1] = 0-float(pose[2 + 3])
            single.location[2] = float(pose[1 + 3])

    
