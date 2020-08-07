import bpy
import os
import math
import sys
sys.path.append(os.path.dirname(__file__))
from . import DataBase
from . import Versions
from . import MatDct
from . import DtbShaders
from pathlib import Path
from . import Global
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

get_obj_name = ""
class ImportFilesCollection(bpy.types.PropertyGroup):
    name = StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

bpy.utils.register_class(ImportFilesCollection)
class IMP_OT_dir(bpy.types.Operator, ImportHelper):
    bl_idname = "imp.material"
    bl_label = "Import material"
    bl_description = 'processing select directry'
    bl_label = "Select Directory"

    filepath = StringProperty(
            name="input file",
            subtype= 'DIR_PATH'
            )
    filename_ext = ""#*.png;*.jpg;*.bmp;*.exr;*.jpeg;*.tif;*.gif"
    filter_glob =  StringProperty(
            default="",#*.png;*.jpg;*.bmp;*.exr;*.jpeg;*.tif;*.gif",
            options={'HIDDEN'},
            )

    def execute(self, context):
        if os.path.isfile(self.filepath):
            self.filepath = os.path.dirname(self.filepath)
        md = MatDct.MatDct()
        if self.filepath.endswith("\\"):
            self.filepath = self.filepath[0:len(self.filepath)-1]
        md.makeDctFromDirectory(self.filepath)
        dct = md.getResult()
        DtbShaders.readImages(dct)
        return{'FINISHED'}

bpy.utils.register_class(IMP_OT_dir)

class IMP_OT_object(Operator, ImportHelper):
    bl_idname = "imp.object"
    bl_label = "Import Daz G8 Object"
    filename_ext = ".obj"
    filter_glob = StringProperty(
        default="*.obj",
        options={'HIDDEN'},
    )
    files = bpy.props.CollectionProperty(type=ImportFilesCollection)

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)
        for i, f in enumerate(self.files, 1):
            durPath = (os.path.join(dirname, f.name))
            from . import ToHighReso
            tgm = ToHighReso.get_Morph(durPath, get_obj_name)
            if ('face' in get_obj_name):
                tgm.get_face_or_body('face')
            elif ('body' in get_obj_name):
                tgm.get_face_or_body('body')
            else:
                rls = ['r','l']
                for rl in rls:
                    if ('hand' in get_obj_name):
                        tgm.get_face_or_body(rl + 'hand')
                    elif ('leg' in get_obj_name):
                        tgm.get_face_or_body(rl + 'knee')
            break
        return {'FINISHED'}

bpy.utils.register_class(IMP_OT_object)

class IMP_OT_dazG8_pose(Operator, ImportHelper):
    bl_idname = "import_daz_g8.pose"
    bl_label = "Import Daz G8 Pose"
    filename_ext = ".duf"
    filter_glob = StringProperty(
        default="*.duf",
        options={'HIDDEN'},
    )
    files = bpy.props.CollectionProperty(type=ImportFilesCollection)

    def execute(self, context):

        dirname = os.path.dirname(self.filepath)
        for i, f in enumerate(self.files, 1):
            durPath = (os.path.join(dirname, f.name))
            self.pose_copy(durPath)
        return {'FINISHED'}

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

    def make_pose(self,v3ary):
        db = DataBase.DB()
        cur = db.g8_blimit
        pbs = Global.getAmtr().pose.bones
        cur.append(['hip', 'YZX'])
        for rows in cur:
            odr = rows[1]
            bname = rows[0]
            for v3 in v3ary:
                if v3[0] !=bname:
                    continue
                flg_zi = False
                z_invert = ['neckUpper','chestUpper','chestLower','neckLower','abdomenUpper','abdomenLower']
                for zi in z_invert:
                    if zi==v3[0]:
                        flg_zi = True
                        break
                if (odr == 'YZX' or odr == 'XYZ') and flg_zi==False:
                    if v3[1]==2:
                        v3[2] = 0-v3[2]
                xy_invert = ['rCollar', 'rShldrBend', 'rForearmBend', 'rForearmTwist', 'rShldrTwist', 'rThumb2', 'rThumb3',
                             'rThumb1', 'rHand','rThighTwist','lThighTwist']
                for xyi in xy_invert:
                    if bname == xyi:
                        if v3[1] !=2:
                            v3[2] = 0-v3[2]
                if odr == 'XZY' or odr == 'XYZ':
                    if v3[1]==0:
                        v3[1] = 1
                    elif v3[1]==1:
                        v3[1] = 0
                if odr == 'ZYX':  # YZ switch
                    if v3[1] == 1:
                        v3[1] = 2
                    elif v3[1] == 2:
                        v3[1] = 1
                x_invert = ['rIndex', 'rMid', 'rPinky', 'rRing']
                for xi in x_invert:
                    if xi in bname:
                        if v3[1] == 0:
                            v3[2] = 0 - v3[2]
                if bname=='hip':
                    if v3[1] == 1:
                        v3[1] = 2
                    elif v3[1] == 2:
                        v3[1] = 1
                y_invert = ['Shin']
                for yi in y_invert:
                    if yi in bname:
                        if v3[1] == 1:
                            v3[2] = 0 - v3[2]

                z_invert2 = ['Foot','lThumb1']
                for zi in z_invert2:
                    if zi in bname:
                        if v3[1] == 2:
                            v3[2] = 0 - v3[2]
                if v3[0] in pbs:
                    pbs[v3[0]].rotation_euler[v3[1]] = math.radians(v3[2])

bpy.utils.register_class(IMP_OT_dazG8_pose)

class Command:
    def __init__(self,key,context):
        key = Global.orthopedic_sharp(key)
        if key=='getpose':
            if Global.getAmtr() is None:
                Versions.msg("Invalid Command", "Message")
                return
            Global.deselect()
            Versions.select(Global.getAmtr(),True)
            Versions.active_object(Global.getAmtr())
            Global.setOpsMode("POSE")
            bpy.ops.import_daz_g8.pose('INVOKE_DEFAULT')
        elif key=='getgenital':
            Get_Genital()
        elif key=='finger' and Global.getAmtr() is not None:
            Global.finger(0)
        elif key=='realsize':
            if Global.getAmtr() is None:
                Versions.msg("This function is effective only in the basic mode", "Message", 'INFO')
                return
            if Global.getSize() == 1:
                Versions.msg("Already Real Size", "Message", 'INFO')
                return
            Global.changeSize(1)
        elif key=='symmetry':
            pass
        elif key=='gettexture':
            bpy.ops.imp.material('INVOKE_DEFAULT')
        elif key=='clearextrabones':
            Global.deselect()
            Versions.select(Global.getAmtr(),True)
            Versions.active_object(Global.getAmtr())
            Global.setOpsMode("EDIT")
            db = DataBase.DB()
            dels = []
            for eb in Global.getAmtr().data.edit_bones:
                for bb in db.tbl_basic_bones:
                    if eb.name.startswith(bb[0]+".00"):
                        dels.append(eb)
                        break
            for d in dels:
                Global.getAmtr().data.edit_bones.remove(d)
            Global.deselect()
            Global.setOpsMode("POSE")
        elif key=='geograft':
            print("IsMan",Global.getIsMan(),"--GetIdx",Global.get_geo_idx())
        elif key=='spliteyelash' and Global.getIsG3()==False:
            #from . import ToHighReso
            Global.deselect()
            Global.setOpsMode("OBJECT")
            Versions.select(Global.getBody(),True)
            Versions.active_object(Global.getBody())
            removeEyelash()
            Global.setOpsMode("OBJECT")
        elif Global.getIsPro():
            kwd = ['getface','getbody','gethand','rentface','rentbody','renthand',"getleg","rentleg"]
            flg_morph = False
            for kw in kwd:
                if key.startswith(kw):
                    flg_morph = True
                    break
            if flg_morph:
                if Global.getAmtr() is None and Global.getRgfy() is not None:
                    Versions.msg("This feature does not work in Rigify mode","I'm sorry","INFO")
                    w_mgr = context.window_manager
                    w_mgr.search_prop = ""
                    flg_morph = False
                    return
            if flg_morph:
                global get_obj_name
                Versions.active_object(Global.getBody())
                Global.setOpsMode("OBJECT")
                get_obj_name = key
                bpy.ops.imp.object('INVOKE_DEFAULT')
            elif key=='fitbone':
                from . import FitBone
                FitBone.FitBone(False)
            else:
                Versions.msg("Invalid Command","Message")
        if key!='getpose':
            w_mgr = context.window_manager
            w_mgr.search_prop = ""

def removeEyelash():
    import bmesh
    Global.deselect()
    Versions.select(Global.getBody(), True)
    Versions.active_object(Global.getBody())
    Global.setOpsMode("EDIT")
    find = False
    bpy.ops.mesh.select_all(action='DESELECT')
    for sidx, slot in enumerate(Global.getBody().material_slots):
        if slot.name.startswith("drb_EylsMoisture") or slot.name.startswith("drb_Eyelashes"):
            Global.getBody().active_material_index = sidx
            bpy.ops.object.material_slot_select()
            find = True
    bm = bmesh.from_edit_mesh(Global.getBody().data)
    bm.verts.ensure_lookup_table()
    cnt = 0
    for i in range(1,60):
        if bm.verts[len(bm.verts)-i].select:
            cnt += 1
    if cnt>50 and find:
        bpy.ops.mesh.separate(type='SELECTED')
        sobjs = bpy.context.selected_objects
        for sobj in sobjs:
            if sobj !=Global.getBody():
                sobj.name = 'EyeLash'
    Global.deselect()
    Global.setOpsMode('OBJECT')
    Versions.active_object(Global.getBody())
    Global.setOpsMode('OBJECT')

class Get_Genital:
    _EYLS = ""
    def eyls(self):
        if self._EYLS!="":
            if self._EYLS in bpy.data.objects:
                return bpy.data.objects[self._EYLS]
        return None

    def __init__(self):
        if Global.getBody() is None:
            return
        self.exec_()

    def check_eyls(self,dir):
        ey_dir = dir + "EYELASH" + Global.getFileSp()
        if os.path.exists(ey_dir):
            ey_list = os.listdir(ey_dir)
            for el in ey_list:
                if el[len(el) - 4:] == '.obj':
                    Versions.import_obj(ey_dir + el)
                    new_obj_name = Global.what_new()
                    new_obj = bpy.data.objects[new_obj_name]
                    Versions.select(new_obj,True)
                    Versions.active_object(new_obj)
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                    self._EYLS = new_obj_name

    def exec_(self):
        dir = Global.getRootPath()+"GEN" +Global.getFileSp()
        if os.path.exists(dir)==False:
            return
        self.check_eyls(dir)
        Global.deselect()
        list = os.listdir(dir)
        for lidx,l in enumerate(list):
            if l[len(l)-4:].lower() !='.obj':
                continue
            now_eyls_obj = None
            if self.eyls() is not None:
                Versions.active_object(self.eyls())
                now_eyls_obj = bpy.data.objects.new('EYELASH' + str(lidx), self.eyls().data)
                Versions.set_link(now_eyls_obj,True)
            body = Versions.import_obj(dir+l)
            if body is None:
                continue
            Versions.active_object(body)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            oname = l[0:len(l)-4]
            if (oname in body.name):
                if now_eyls_obj is not None:
                    Versions.select(body, True)
                    Versions.select(now_eyls_obj,True)
                    Versions.active_object(body)
                    bpy.ops.object.join()
                Versions.active_object(body)
            else:
                continue
            if len(body.data.vertices) != len(Global.getBody().data.vertices):
                bpy.data.objects.remove(body)
                continue
            Versions.select(body,True)
            Versions.select(Global.getBody(),True)
            Versions.active_object(Global.getBody())
            bpy.ops.object.join_shapes()
            self.toMsGen()
            bpy.data.objects.remove(body)
            Global.deselect()
        if self.eyls() is not None:
            bpy.data.objects.remove(self.eyls())

    def toMsGen(self):
        mesh = Global.getBody().data
        max = len(mesh.shape_keys.key_blocks)
        kb = mesh.shape_keys.key_blocks[max-1]
        kb.slider_min = -1


