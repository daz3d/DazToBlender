import bpy
import os
import math
from . import Versions
from . import Global
from . import Util
from . import DtbMaterial
from . import NodeArrange
import re


def pbar(v):
    bpy.context.window_manager.progress_update(v)

class EnvProp:
    bmeshs = []
    bamtr = []
    env_root = Global.getRootPath() + "ENV"+Global.getFileSp()

    def __init__(self):
        Util.deleteEmptyDazCollection()
        self.bstart()

    def bstart(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        Versions.active_object_none()
        self.layGround()
        if os.path.exists(self.env_root)==False:
            return
        pbar(0)
        files = os.listdir(self.env_root)
        files = [f for f in files if os.path.isdir(os.path.join(self.env_root, f))]
        max = len(files)
        one = 100/max
        for i in range(max):
            Global.clear_variables()
            Global.setHomeTown("ENV" + str(i))
            Util.decideCurrentCollection('ENV')
            pbar(int(one * i)+5)
            ReadFbx(self.env_root + 'ENV' + str(i) + Global.getFileSp(), i,one)
            Versions.active_object_none()
        pbar(100)
        Versions.reverse_language()
        Global.setOpsMode("OBJECT")
        wm.progress_end()
        Versions.make_sun()

    def layGround(self):
        Versions.set_english()
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

class ReadFbx:
    adr = ""
    index = 0
    _pose_ary = None
    _bone_ary = None
    ss_ary = []
    asc_ary = []
    my_meshs = []

    def __init__(self,dir,i,one):
        self.adr = dir
        self.my_meshs = []
        self.index = i
        self.ss_ary = []
        self._pose_ary = None
        self._bone_ary = None
        self.asc_ary = []
        if self.readFbx():
            pbar(int(i*one)+int(one/2))
            self.readAsc()
            self.setMaterial()
        Global.scale_environment()

    def readFbx(self):
        self.my_meshs = []
        adr = self.adr + "B_ENV.fbx"
        if os.path.exists(adr)==False:
            return
        objs = self.convert_file(adr)
        for obj in objs:
            if obj.type=='MESH':
                self.my_meshs.append(obj)
        if objs is None or len(objs)==0:
            return
        Global.find_ENVROOT(objs[0])
        root = Global.getEnvRoot()
        if len(objs)>1:
            if root is None:
                return
            else:
                objs.remove(root)
        else:
            root = objs[0]
        Versions.active_object(root)
        Global.deselect()
        if root.type=='ARMATURE':
            self.orthopedy_armature(objs, root)
        elif root.type=='EMPTY':
            no_empty = False
            for o in objs:
                if o.type != 'EMPTY':
                    no_empty = True
                    break
            if no_empty==False:
                for o in objs:
                    bpy.data.objects.remove(o)
                return False
            else:
                self.orthopedy_empty(objs, Global.getEnvRoot())
        if Global.want_real():
            Global.changeSize(1,[])
        return True

    #Bone property
    def get_bone_info(self,bname):
        if self._bone_ary is None:
            with open(self.adr + "ENV.bon") as f:
                self._bone_ary = f.readlines()
        if self._bone_ary is None:
            return None
        for p in self._bone_ary:
            if p.endswith("\n"):
                p = p[0:len(p) - 1]
            ss = p.split(',')
            if ss[0]==bname:
                return ss
            for i in range(1,10):
                if bname==ss[0]+".00" + str(i):
                    return ss
        return None

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

    def Maru(self):
        if 'daz_door' in Util.colobjs('DAZ_HIDE'):
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
        bpy.context.object.name = 'daz_door'
        Util.to_other_collection([bpy.context.object],'DAZ_HIDE',Util.cur_col_name())

    def is_armature_modified(self,dobj):
        if dobj.type == 'MESH':
            for modifier in dobj.modifiers:
                if modifier.type=='ARMATURE' and modifier.object is not None:
                    return True
        return False

    def is_yukobone(self,amtr,myebone,vgroups):
        rtn = self.has_child(amtr,myebone)
        if rtn is None or len(rtn) == 0:
            return False
        for r in rtn:
            if r not in vgroups:
                return False
        return True

    def has_child(self,amtr,myebone):
        rtn = []
        for eb in amtr.data.edit_bones:
            if eb.parent == myebone:
                rtn.append(eb.name)
        return rtn

    def orthopedy_armature(self, objs, amtr):
        Global.deselect()
        self.Maru()
        vgroups = []
        empty_objs = []
        amtr_objs = []

        for i in range(3):
            amtr.scale[i] = 1
        for obj in objs:
            if obj.type == 'MESH':
                amtr_objs.append(obj)
                vgs = obj.vertex_groups
                flg_vg = False
                for vg in vgs:
                    flg_vg = True
                    vgroups.append(vg.name)
                if flg_vg:
                    if self.is_armature_modified(obj) == False:
                        amod = obj.modifiers.new(type='ARMATURE', name="ama" + obj.name)
                        amod.object = amtr
            elif obj.type == 'EMPTY':
                if obj.parent == amtr:
                    empty_objs.append(obj)
        Global.deselect()
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Global.setOpsMode("POSE")
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.pose.select_all(action='DESELECT')
        Global.setOpsMode("EDIT")
        hides = []
        ebones = amtr.data.edit_bones
        bcnt = 0
        for eb in ebones:
            bcnt += 1
        notbuilding = bcnt > 30
        for eb in ebones:
            binfo = self.get_bone_info(eb.name)
            if binfo is None:
                hides.append(eb.name)
                continue
            if eb.name not in vgroups:
                if self.is_yukobone(amtr, eb,vgroups) == False:
                    hides.append(eb.name)
                    continue
                if '1' not in binfo[7:]:
                    hides.append(eb.name)
                    continue
            else:
                if '1' not in binfo[7:]:
                    hides.append(eb.name)

                    # for bidx,bi in enumerate(binfo):
                    #     if bidx>6:
                    #         binfo[bidx] = 1
            if notbuilding:
                for i in range(3):
                    eb.tail[i] = float(binfo[4 + i])

            else:
                len = 100
                eb.roll = 0
                for i in range(3):
                    if i == 1:
                        eb.tail[i] = float(eb.head[i]) + len
                    else:
                        eb.tail[i] = float(eb.head[i])

        Global.setOpsMode('OBJECT')
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        Global.deselect()
        for obj in objs:
            Versions.select(obj, True)
            Versions.active_object(obj)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            for i in range(3):
                obj.location[i] = 0
            Versions.select(obj,False)
        Versions.select(amtr, True)
        Versions.active_object(amtr)
        Global.setOpsMode("POSE")
        amtr.show_in_front = True
        for pb in amtr.pose.bones:
            binfo = self.get_bone_info(pb.name)
            if binfo is None:
                continue
            else:
                if notbuilding==False:
                    ob = Util.allobjs().get('daz_door')
                    if ob is not None:
                        pb.custom_shape = ob
                        pb.custom_shape_scale = 0.4
                        amtr.data.bones.get(pb.name).show_wire = True
            lrs = [False, False, False]
            for i in range(3):
                for j in range(3):
                    if binfo[7 + (i * 3) + j] == '0':
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
        for hide in hides:
            amtr.data.bones.get(hide).hide = True

    def convert_file(self, filepath):
        Global.store_ary(False)
        basename = os.path.basename(filepath)
        (filename, fileext) = os.path.splitext(basename)
        ext = fileext.lower()
        if os.path.isfile(filepath):
            if ext == '.fbx':
                bpy.ops.import_scene.fbx(filepath=filepath, use_manual_orientation = False,
                                         #global_scale=(1 if Global.want_real() else 0.01),
                                         #global_scale=0.01,
                                         bake_space_transform=False,
                                         use_image_search=True,  use_anim=False,
                                         ignore_leaf_bones=False,force_connect_children=False,
                                         automatic_bone_orientation=False,
                                         use_prepost_rot=False, )
        Global.store_ary(True)
        return self.what_news()

    def what_news(self):
        rtn = []
        if len(Global.now_ary) - len(Global.pst_ary) < 1:
            return ""
        for n in Global.now_ary:
            hit = False
            for p in Global.pst_ary:
                if n == p:
                    hit = True
                    break
            if hit == False:
                rtn.append(bpy.data.objects[n])
        return rtn

    def setMaterial(self):
        for mesh in self.my_meshs:
            for slot in mesh.material_slots:
                if slot.name in bpy.data.materials:
                    mat = bpy.data.materials[slot.name]
                    normal = None
                    ROOT = mat.node_tree.nodes
                    LINK = mat.node_tree.links
                    for node in ROOT:
                        if node.name=='Normal Map':
                            normal = node
                            break
                    for mainNode in ROOT:
                        if mainNode.name=='Principled BSDF':
                            mainNode.inputs['Metallic'].default_value = 0.0
                            mainNode.inputs['Specular'].default_value = 0.2
                            mainNode.inputs['Roughness'].default_value = 0.5
                            root_bump = DtbMaterial.insertBumpMap(ROOT, LINK)
                            ROOT = root_bump[0]
                            bumpNode = root_bump[1]
                            bcolor_by_asc = ""
                            for asc in self.asc_ary:
                                if  (asc[1] == mat.name or mat.name.startswith(asc[1]+".00")):
                                    if asc[0] == 'M':
                                        kind = asc[2]
                                        if len(asc)==9:
                                            if kind.startswith('Diffuse'):
                                                mainNode.inputs['Base Color'].default_value =(float(asc[6]),float(asc[7]),float(asc[8]),1)
                                            elif kind=='TransparentColor':
                                                mainNode.inputs['Alpha'].default_value = float(asc[6])
                                        elif len(asc)==7:
                                            if kind=='Specular':
                                                mainNode.inputs['Specular'].default_value = float(asc[6])
                                    elif asc[0]=='T':
                                        bcolor_by_asc = asc[2]
                            if mainNode.inputs.get('Base Color') is not None:
                                lnks = mainNode.inputs['Base Color'].links
                                for lnk in lnks:
                                    node = lnk.from_node
                                    if node.name.startswith('Image Texture'):
                                        bcolor_by_asc = node.image.filepath
                                        break
                            if bcolor_by_asc !="":
                                from . import MatDct
                                mm = MatDct.MatDct()
                                ts = mm.cloth_dct_0(bcolor_by_asc)
                                for t in ts:
                                    SNTIMG = ROOT.new(type='ShaderNodeTexImage')
                                    img = bpy.data.images.load(filepath=t[1])
                                    SNTIMG.image = img
                                    Versions.to_color_space_non(SNTIMG)

                                    if t[0].endswith("-n"):
                                        if normal is not None:
                                            LINK.new(SNTIMG.outputs['Color'],normal.inputs['Color'])
                                        else:
                                            normal = ROOT.new(type='ShaderNodeNormalMap')
                                            LINK.new(SNTIMG.outputs['Color'], normal.inputs['Color'])
                                            LINK.new(mainNode.inputs['Normal'], normal.outputs['Normal'])
                                    elif t[0].endswith("-d"):
                                        if mainNode.inputs['Base Color'].links ==0:
                                            LINK.new(mainNode.inputs['Base Color'], SNTIMG.outputs['Color'])
                                    elif t[0].endswith("-r"):
                                        LINK.new(mainNode.inputs['Roughness'],SNTIMG.outputs['Color'])
                                    elif t[0].endswith("-s"):
                                        LINK.new(mainNode.inputs['Specular'],SNTIMG.outputs['Color'])
                                    elif t[0].endswith("-b"):
                                        if bumpNode is not None:
                                            LINK.new(SNTIMG.outputs['Color'],bumpNode.inputs['Height'])
                                    elif t[0].endswith("-t"):
                                        if len(t[0])>5:
                                            if mainNode.inputs['Alpha'].links == 0:
                                                LINK.new(mainNode.inputs['Alpha'],SNTIMG.outputs['Color'])
                    NodeArrange.toNodeArrange(ROOT)


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

    def orthopedy_one(self,single):
        for i in range(3):
            single.scale[i] = 1
        if single.type=='LIGHT':
            pose = self.get_pose(single)
            single.location[0] = float(pose[0 + 3])
            single.location[1] = 0-float(pose[2 + 3])
            single.location[2] = float(pose[1 + 3])

    def orthopedy_empty(self, objs, root):
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

            if obj.type=='EMPTY':
                for i in range(3):
                    obj.scale[i] = float(pose[i+9])
                    obj.rotation_euler[i] = 0
            elif obj.type=='LIGHT' or obj.type=='CAMERA':
                for i in range(3):
                    obj.location[i] = float(pose[i+3]) + float(root_pose[i+3])
                    self.before_edit_prop()
                    obj.rotation_euler[i] = math.radians(float(pose[i+6]))
                    obj.scale[i] = 100
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

    def get_pose(self,obj):
        obj_name = obj.name
        for i in range(5):
            if obj_name.endswith(".00"+str(i)):
                obj_name = obj_name[0:len(obj_name)-4]
        a = obj_name.find(".Shape")
        if a > 0:
            obj_name = obj_name[0:a]
        if self.ss_ary==[]:
            if self._pose_ary is None:
                with open(self.adr+"ENV.csv") as f:
                    self._pose_ary = f.readlines()
            if self._pose_ary is None:
                return None
            for p in self._pose_ary:
                if p.endswith("\n"):
                    p = p[0:len(p)-1]
                ss = p.split(',')
                #manage [_dup_] files
                for i in range(2,20):
                    if ss[0].endswith(" (" + str(i) + ")"):
                        if not ss[1].endswith("_dup_" + str(i)):
                            ss[1] = ss[1] + "_dup_" + str(i)
                        break
                self.ss_ary.append(ss)
        for ss in self.ss_ary:
            if ss[1] == obj_name:
                if ss[2]=='E' and obj.type=='EMPTY' or \
                        ss[2]=='M' and obj.type=='MESH' or \
                        ss[2]=='L' and obj.type=='LIGHT' or \
                        ss[2]=='C' and obj.type=='CAMERA':
                    return ss
        return [obj_name,obj_name,"?",0,0,0,0,0,0,1,1,1]
