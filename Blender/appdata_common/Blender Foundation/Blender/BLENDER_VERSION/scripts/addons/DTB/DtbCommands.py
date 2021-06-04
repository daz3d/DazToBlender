import bpy
import os
import sys
sys.path.append(os.path.dirname(__file__))
from . import DataBase
from . import Versions
from . import MatDct
from . import DtbMaterial
from . import Util
from . import Global
from . import Poses
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator


class SEARCH_OT_Commands(bpy.types.Operator):
    bl_idname = "command.search"
    bl_label = 'Command'

    def execute(self, context):
        search_morph(context)
        return {'FINISHED'}


def search_morph_(self, context):
    search_morph(context)

def search_morph(context):
    w_mgr = context.window_manager
    key = w_mgr.search_prop
    nozero = False
    if key.startswith("!"):
        nozero = True
        key = key[1:]
    if len(key) < 2:
        return
    if key.startswith("#"):
        WCmd.Command(key[1:], context)
        return
    cobj = bpy.context.object
    mesh = cobj.data
    for z in range(2):
        find = False
        max = len(mesh.shape_keys.key_blocks)
        for kidx, kb in enumerate(mesh.shape_keys.key_blocks):
            if kidx <= Versions.get_active_object().active_shape_key_index:
                continue
            if nozero and kb.value == 0.0:
                continue
            if (key.lower() in kb.name.lower()):
                Versions.get_active_object().active_shape_key_index = kidx
                find = True
                break
        if z == 0 and find == False:
            if max > 1:
                Versions.get_active_object().active_shape_key_index = 1
        else:
            break


get_obj_name = ""
class ImportFilesCollection(bpy.types.PropertyGroup):
    name : StringProperty(
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

    filepath : StringProperty(
            name="input file",
            subtype= 'DIR_PATH'
            )
    filename_ext : StringProperty(
            default="",#*.png;*.jpg;*.bmp;*.exr;*.jpeg;*.tif;*.gif",
            options={'HIDDEN'},
            )
    filter_glob :  StringProperty(
            default="",#*.png;*.jpg;*.bmp;*.exr;*.jpeg;*.tif;*.gif",
            options={'HIDDEN'},
            )

    def execute(self, context):
        if os.path.isfile(self.filepath):
            self.filepath = os.path.dirname(self.filepath)
        md = MatDct.MatDct()
        if self.filepath.endswith("\\"):
            self.filepath = self.filepath[0:len(self.filepath)-1]
        md.make_dct_from_directory(self.filepath)
        dct = md.get_dct()
        DtbMaterial.readImages(dct)
        return{'FINISHED'}

bpy.utils.register_class(IMP_OT_dir)

class IMP_OT_object(Operator, ImportHelper):
    bl_idname = "imp.object"
    bl_label = "Import Daz G8 Object"
    filename_ext : StringProperty(
        default=".obj",
        options={'HIDDEN'},
    )
    filter_glob : StringProperty(
        default="*.obj",
        options={'HIDDEN'},
    )
    files : bpy.props.CollectionProperty(type=ImportFilesCollection)

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)
        for i, f in enumerate(self.files, 1):
            print("f===",f)
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
    filename_ext : StringProperty(
        default=".duf",
        options={'HIDDEN'},
    )
    filter_glob : StringProperty(
        default="*.duf",
        options={'HIDDEN'},
    )
    files : bpy.props.CollectionProperty(type=ImportFilesCollection)

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)
        for i, f in enumerate(self.files, 1):
            durPath = (os.path.join(dirname, f.name))
            up = Poses.Posing("POSE")
            up.pose_copy(durPath)
        return {'FINISHED'}

bpy.utils.register_class(IMP_OT_dazG8_pose)

class Command:
    def __init__(self,key,context):
        key = Global.orthopedic_sharp(key)
        Util.active_object_to_current_collection()
        not_erace = ['getpose', 'accessory']
        kwd = ['getface', 'getbody', 'gethand', 'rentface', 'rentbody', 'renthand', "getleg", "rentleg"]
        flg_morph = False
        for kw in kwd:
            if key.startswith(kw):
                if Global.getAmtr() is None and Global.getRgfy() is not None:
                    Versions.msg("This feature does not work in Rigify mode", "I'm sorry", "INFO")
                    w_mgr = context.window_manager
                    w_mgr.search_prop = ""
                    flg_morph = False
                else:
                    flg_morph = True
                break
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
            Global.changeSize(1,[])
            Global.scale_environment()
        elif key=='gettexture':
            bpy.ops.imp.material('INVOKE_DEFAULT')
        elif key=='clearextrabones':
            Global.deselect()
            Versions.active_object_none()
            for obj in Util.myacobjs():
                if obj.type != 'ARMATURE':
                    continue
                Versions.select(obj, True)
                Versions.active_object(obj)
                Global.setOpsMode("EDIT")
                db = DataBase.DB()
                dels = []
                for eb in obj.data.edit_bones:
                    for bb in db.tbl_basic_bones:
                        if eb.name.startswith(bb[0] + ".00"):
                            dels.append(eb)
                            break
                for d in dels:
                    obj.data.edit_bones.remove(d)
                Global.deselect()
                Global.setOpsMode("POSE")
        elif key=='geograft':
            print("IsMan",Global.getIsMan(),"--GetIdx",Global.get_geo_idx())
        elif key=='spliteyelash' and Global.getIsG3()==False:
            Global.deselect()
            Global.setOpsMode("OBJECT")
            Versions.select(Global.getBody(),True)
            Versions.active_object(Global.getBody())
            removeEyelash()
            Global.setOpsMode("OBJECT")
        elif key=='realskin':
            DtbMaterial.skin_levl(True)
        elif key=='easyskin':
            DtbMaterial.skin_levl(False)
        elif key=='myheros':
            print(Global.getAmtr(),Global.getRgfy(),Global.getBody(),Global.getEnvRoot(),Global.getSize(),Util.cur_col_name(),
                  "*",Global.get_Amtr_name(),Global.get_Rgfy_name(),Global.get_Body_name())
        elif key=='onedrive':
            db = DataBase.DB()
            from . import DtbShapeKeys
            sk = DtbShapeKeys.DtbShapeKeys(False)
            sk.makeOneDriver(db)
        elif key=='clearmorph':
            from . import DtbShapeKeys
            sk = DtbShapeKeys.DtbShapeKeys(False)
            sk.delete_oneobj_sk_from_command()
        elif flg_morph:
            global get_obj_name
            Versions.active_object(Global.getBody())
            Global.setOpsMode("OBJECT")
            get_obj_name = key
            bpy.ops.imp.object('INVOKE_DEFAULT')
        elif key in not_erace:
            pass
        else:
            Versions.msg("Invalid Command","Message")
        if key not in not_erace:
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
            if self._EYLS in Util.myccobjs():
                return Util.myccobjs().get(self._EYLS)
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
                    new_obj = Util.myccobjs().get(new_obj_name)
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
                Versions.set_link(now_eyls_obj,True,'DAZ_HIDE')
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
                Util.allobjs().remove(body)
                continue
            Versions.select(body,True)
            Versions.select(Global.getBody(),True)
            Versions.active_object(Global.getBody())
            bpy.ops.object.join_shapes()
            self.toMsGen()
            Util.allobjs().remove(body)
            Global.deselect()
        if self.eyls() is not None:
            Util.allobjs().remove(self.eyls())

    def toMsGen(self):
        mesh = Global.getBody().data
        max = len(mesh.shape_keys.key_blocks)
        kb = mesh.shape_keys.key_blocks[max-1]
        kb.slider_min = -1


