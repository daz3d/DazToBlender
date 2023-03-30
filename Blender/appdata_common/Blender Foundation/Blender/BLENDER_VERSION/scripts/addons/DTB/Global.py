import bpy
import os
import math
import json
from copy import deepcopy
from . import DataBase
from . import Versions
from . import Util

isMan = False
root = ""
isGen = False
_AMTR = ""
_BODY = ""
_EYLS = ""
_HAIR = ""
_TEAR = ""
_RGFY = ""
keep_EYLS = ""
keep_TEAR = ""
db = DataBase.DB()
updated_bone_limits = []
dtu = None

Geo_Idx = 0
now_ary = []
pst_ary = []
_BVCount = 0
_SIZE = 0
root = ""
config = ""
_ISG3 = 0
_HOMETOWN = ""
_ASSETNAME = ""
already_use_newmtl = []
_ENVROOT = ""
shape_key_custom_props = []

G3_GEOIDX = 3
#####Female#######
# 0.G8
# 1.DazGenitalA (20200525-)
# 2.DazGenitalB
# 3.G3
######Male##########
# 0.G8
# 1.DazGenitalA(20200525-)
# 2.DazGenitalB
#  G3
max_vs = [
    [
        [16556, 65806, 262514],
        [17192, 68350, 272690],
        [17292, 68450, 272790],
        [17418, 68744, 273396],
    ],
    [
        [16384, 65118, 259762],
        [17454, 69398, 276882],
        [17543, 69498, 276982],
        [17246, 68056, 270644],
    ],
]

IS_EMERGENCY = False
EYLSCOUNT = 464


def get_children(object):
    children = []
    for ob in bpy.data.objects:
        if ob.parent == object:
            children.append(ob)
    return children


def get_shape_key_custom_props():
    fig_object_name = bpy.context.window_manager.choose_daz_figure
    if fig_object_name == "null":
        return []
    if fig_object_name not in bpy.data.objects.keys():
        return []
    fig_object = bpy.data.objects[fig_object_name]
    children = get_children(fig_object)
    custom = []
    for child in children:
        if "_RNA_UI" in child.keys():
            morphs = child["_RNA_UI"].keys()
            custom.append({"mesh": child.name, "props": morphs})
    return custom


def getMyMax3():
    return max_vs[getSex()][get_geo_idx()]


def getIsG3():
    return get_geo_idx() == G3_GEOIDX


# DB 2023-Mar-27: G9 suport
def getIsG9():
    return getAmtr().data.bones.find('l_forearmtwist2') != -1

def getIsEmergency():
    return IS_EMERGENCY


def setItsEmergency():
    global IS_EMERGENCY
    IS_EMERGENCY = True


def isAcs():
    wk = bpy.context.window_manager.search_prop
    wk = wk.strip()
    wk = wk.lower()
    return wk == "#accessory"


def getSubdivLevel():
    naga = len(getBody().data.vertices)
    if naga > 200000:
        return 2
    elif naga > 60000:
        return 1
    else:
        return 0


def get_root():
    return root


def getSex():
    if getIsMan():
        return 1
    else:
        return 0


def isExistsAnimation():
    if getAmtr() is None:
        return False
    my_amtr = getAmtr()
    if my_amtr.animation_data is None:
        return False
    if my_amtr.animation_data.action is None:
        return False
    if my_amtr.animation_data.action.fcurves is None:
        return False
    if len(my_amtr.animation_data.action.fcurves) <= 0:
        return False
    return True


def orthopedic_sharp(word):
    word = word.replace(" ", "")
    word = word.lower()
    return word


def isRiggedObject(dobj):
    if dobj.type == "MESH":
        for modifier in dobj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:
                if (
                    modifier.object.name == get_Amtr_name()
                    or modifier.object.name == get_Rgfy_name()
                ):
                    return True

    return False


def isRiggedObject_when_Amtr_is_None(dobj):
    if dobj.type == "MESH":
        for modifier in dobj.modifiers:
            if modifier.type == "ARMATURE":
                return True
    return False


def store_ary(is_now):
    global now_ary
    global pst_ary
    if is_now == False:
        now_ary = []
        pst_ary = []
    for d in Util.myccobjs():
        if is_now:
            now_ary.append(d.name)
        else:
            pst_ary.append(d.name)


def what_new():
    if len(now_ary) - len(pst_ary) < 1:
        return ""
    for n in now_ary:
        hit = False
        if n not in pst_ary:
            return n
    return ""


def setOpsMode(arg):
    combi = ["POSE", "EDIT", "OBJECT", "SCULPT"]
    if arg in combi:
        if Versions.get_active_object() is not None:
            if Versions.get_active_object().mode != arg:
                bpy.ops.object.mode_set(mode=arg)


def get_Amtr_name():
    if _AMTR != "" and (_AMTR in Util.allobjs()):
        return _AMTR
    else:
        return ""


def get_Body_name():
    if _BODY != "" and (_BODY in Util.allobjs()):
        return _BODY
    else:
        return ""


def get_Eyls_name():
    if _EYLS != "" and (_EYLS in Util.allobjs()):
        return _EYLS
    else:
        return ""


def get_Tear_name():
    if _TEAR != "" and (_TEAR in Util.allobjs()):
        return _TEAR
    else:
        return ""


def get_Hair_name():
    if _HAIR != "" and (_HAIR in Util.allobjs()):
        return _HAIR
    else:
        return ""


def get_KeepEyls_name():
    return keep_EYLS


def get_KeepTear_name():
    return keep_TEAR


def get_Rgfy_name():
    if _RGFY != "" and (_RGFY in Util.allobjs()):
        return _RGFY
    else:
        return ""


def getIsMan():
    return isMan


def getIsGen():
    return isGen


def getIsEyls():
    return _EYLS != ""


def getIsTEAR():
    return _TEAR != ""


def getIsHair():
    return _HAIR != ""


def setEylsIsJoined():
    global _EYLS
    _EYLS = ""


def setTearIsJoined():
    global _TEAR
    _TEAR = ""


def find_RGFY_all():
    for d in Util.myccobjs():
        if find_RGFY(d):
            return True
    return False


def getFileSp():
    if os.name == "nt":
        return "\\"
    else:
        return "/"


def find_RGFY(dobj):
    global _RGFY
    if dobj.type == "ARMATURE":
        abones = dobj.data.bones
        if len(abones) > 600:
            list = ["ORG-", "DEF-", "MCH-", 0, 0, 0]
            for ab in abones:
                for i in range(3):
                    if ab.name.startswith(list[i]):
                        list[i + 3] += 1
            if list[3] > 100 and list[4] > 100 and list[5] > 70:
                _RGFY = dobj.name
                _AMTR = ""
                return True
    return False


# TODO: Find a method to get Armature Necessary when Rigify is Ran
def find_AMTR(dobj):
    global _AMTR
    if dobj.type == "ARMATURE" and "Genesis" in dobj.name:
        _AMTR = dobj.name
        return True
    return False


def find_amtr(dobj):
    global dtu
    import_name = dtu.get_import_name()
    global _AMTR
    if dobj.type == "ARMATURE" and import_name in dobj.name:
        _AMTR = dobj.name
        return True
    return False


def find_BODY(dobj):
    global _BODY
    if dobj.type == "MESH":
        if Versions.isHide(dobj):
            return False
        for modifier in dobj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:

                if modifier.object.name == _AMTR or modifier.object.name == _RGFY:
                    figure_name = dobj.name.replace(".Shape", "")
                    figure_name = figure_name.split(".")[0]
                    if figure_name in DataBase.get_figure_list():
                        _BODY = dobj.name
                        return True

    return False


def load_dtu(dtu_to_load):
    global dtu
    dtu = dtu_to_load


# new find body used for importing
def find_body(dobj):
    global dtu
    import_name = dtu.get_import_name()
    global _BODY
    if dobj.type == "MESH":
        if Versions.isHide(dobj):
            return False
        for modifier in dobj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:
                if modifier.object.name == _AMTR or modifier.object.name == _RGFY:
                    figure_name = dobj.name.replace(".Shape", "")
                    figure_name = figure_name.split(".")[0]
                    if figure_name == import_name:
                        _BODY = dobj.name
                        return True

    return False


def get_children(obj):
    children = []
    col = Util.getUsersCollection(obj)
    for ob in Util.colobjs(col.name):
        if ob.parent == obj:
            children.append(ob)
    return children


def find_Both(obj):
    if obj.type == "MESH":
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:
                if find_AMTR(modifier.object) == False:
                    if find_RGFY(modifier.object) == False:
                        return False
        return find_BODY(obj)
    elif obj.type == "ARMATURE":
        if find_AMTR(obj) or find_RGFY(obj):
            kids = get_children(obj)
            for k in kids:
                if find_BODY(k):
                    return True
            return False
    return False


# TODO: Fix Logic of Combination of Tears
def find_EYLS(dobj):
    global _EYLS
    global keep_EYLS
    if isRiggedObject(dobj):
        if "Eyelashes" in dobj.name:
            _EYLS = dobj.name
            keep_EYLS = deepcopy(dobj.name)
            return True
    return False


def find_TEAR(dobj):
    global _TEAR
    global keep_TEAR
    if "Tear" in dobj.name:
        _TEAR = dobj.name
        keep_TEAR = deepcopy(dobj.name)
        return True
    return False


def find_HAIR(dobj):
    global _HAIR
    if isRiggedObject(dobj):
        if ("brow" in dobj.name.lower()) == False:
            hi = 0
            count = [0, 0]
            if getBody() is not None:
                cnt = 0
                hi = getBody().dimensions[2]
                if hi < getBody().dimensions[1]:
                    hi = getBody().dimensions[1]

            vgs = dobj.vertex_groups
            for v in dobj.data.vertices:
                if v.co[1] >= hi or v.co[2] >= hi:
                    count[0] += 1
                for gp in v.groups:
                    vgname = vgs[gp.group].name.lower()
                    if "head" in vgname:
                        count[1] += 1
                    elif ("abdomen" in vgname) or ("forearm" in vgname):
                        count[1] -= 1
            if count[0] > 10 and count[1] > 10:
                _HAIR = dobj.name
                return True
    return False


def find_ENVROOT(dobj):
    fromtop = []
    frombtm = []
    cname = Util.getUsersCollectionName(dobj)
    objs = Util.colobjs(cname)
    global _ENVROOT
    if len(objs) == 1:
        _ENVROOT = objs[0].name
        return
    for obj in objs:
        find = False
        while obj.parent is not None:
            find = True
            obj = obj.parent
        if find == False:
            fromtop.append(obj)
        else:
            if not (obj in frombtm):
                frombtm.append(obj)
    if (len(fromtop) == 1 and len(frombtm) == 1) == False:
        return
    if fromtop[0] != frombtm[0]:
        return
    if fromtop[0].type == "ARMATURE" or fromtop[0].type == "EMPTY":
        _ENVROOT = fromtop[0].name


def getEnvRoot():
    if _ENVROOT != "" and (_ENVROOT in Util.allobjs()):
        return Util.allobjs().get(_ENVROOT)


def decide_HERO():
    global _AMTR
    global _RGFY
    global _BODY
    global _EYLS
    global _TEAR
    global _HAIR
    global isMan
    global isGen
    global _BVCount
    global _ISG3
    global Geo_Idx
    global _SIZE

    clear_variables()

    active_col_objs = Util.myacobjs()
    # Find Armatures
    exists = {"_AMTR": False, "_RGFY": False, "_BODY": False}
    for dobj in active_col_objs:
        if exists["_AMTR"] == False:
            exists["_AMTR"] = find_AMTR(dobj)
            if exists["_AMTR"]:
                continue
        if exists["_RGFY"] == False:
            exists["_RGFY"] = find_RGFY(dobj)
            if exists["_RGFY"]:
                continue

    # Needs to be Seperated as Rigify changes Order
    for dobj in active_col_objs:
        if exists["_BODY"] == False:
            exists["_BODY"] = find_BODY(dobj)
            if exists["_BODY"]:
                continue

    if "Male" in _BODY:
        isMan = True

    # Removed until found necessary

    # if find_EYLS(dobj):
    #     continue
    # if find_HAIR(dobj):
    #     continue
    # if find_TEAR(dobj):
    #     continue


def store_variables():
    global _AMTR
    global _RGFY
    global _BODY
    global _EYLS
    global _TEAR
    global _HAIR
    global isMan
    global isGen
    global _BVCount
    global _ISG3
    global Geo_Idx
    global _SIZE

    clear_variables()

    active_col_objs = Util.myacobjs()
    # Find Armatures
    exists = {"_AMTR": False, "_RGFY": False, "_BODY": False}
    for dobj in active_col_objs:
        if exists["_AMTR"] == False:
            exists["_AMTR"] = find_amtr(dobj)
            if exists["_AMTR"]:
                continue
        if exists["_RGFY"] == False:
            exists["_RGFY"] = find_RGFY(dobj)
            if exists["_RGFY"]:
                continue

    # Needs to be Seperated as Rigify changes Order
    for dobj in active_col_objs:
        if exists["_BODY"] == False:
            exists["_BODY"] = find_body(dobj)
            if exists["_BODY"]:
                continue

    if "Male" in _BODY:
        isMan = True

    # Removed until found necessary

    # if find_EYLS(dobj):
    #     continue
    # if find_HAIR(dobj):
    #     continue
    # if find_TEAR(dobj):
    #     continue


def addG3Database(isman):
    sql = ""
    if isman == False and len(DataBase.f_geni) == G3_GEOIDX - 1:
        sql = "select SRC,DST from G3F order by SRC"
    elif isman and len(DataBase.m_geni) == G3_GEOIDX - 1:
        sql = "select SRC,DST from G3M order by SRC"
    if sql == "":
        return
    con = getCon()
    cur = con.cursor()
    cur.execute(sql)
    addtbl = []
    for row in cur:
        addtbl.append([row[0], row[1]])
    if isman:
        DataBase.m_geni.append(addtbl)
    else:
        DataBase.f_geni.append(addtbl)
    cur.close()
    con.close()


def getMf():
    global Geo_Idx
    global isMan
    if getBody() is None:
        return
    rtn = [False, False, False]
    verts = getBody().data.vertices
    if getAmtr() is not None:
        xr = getAmtr().rotation_euler[0]
    else:
        xr = 0
    is_fst = xr > math.radians(88) and xr < math.radians(92)
    if is_fst:
        hi = getBody().dimensions[1]
        hi = (hi * 9) / 10
    else:
        hi = getBody().dimensions[2]
        hi = (hi * 8) / 10
    tops = [[5358, 69, 3958, 79, 5534, 3], [5054, 69, 3733, 78, 5230, 3]]  # 5345,5041,
    for sex in range(2):
        isMan = sex == 1
        Geo_Idx = 0
        if is_fst and ("Male" in getBody().name) and sex == 0:
            continue
        max = len(DataBase.f_geni) + 1
        if isMan:
            max = len(DataBase.m_geni) + 1
        for i in range(max):
            point = 0
            tpast = 0
            max3 = max_vs[sex][i]
            # if (len(getBody().data.vertices) in max3)==False:
            #     continue
            for tidx, t in enumerate(tops[sex]):
                v = verts[t]
                src_t = t
                Geo_Idx = i
                if i > 0:
                    t = toGeniVIndex(t)
                    v = verts[t]
                vpast = verts[tpast]
                if is_fst:
                    if v.co[1] > hi and v.co[0] < 0.3 and v.co[0] > -0.3:
                        if tidx == 0 or (tidx > 0 and v.co[2] > vpast.co[2]):
                            point += 1
                else:
                    if v.co[2] > hi and v.co[0] < 0.3 and v.co[0] > -0.3:
                        if tidx == 0 or (tidx > 0 and v.co[1] < vpast.co[1]):
                            point += 1
                tpast = t
            if point == 6:
                rtn[0] = sex == 1
                rtn[1] = i > 0
                rtn[2] = True
                return rtn
    Geo_Idx = 0
    return rtn


def boneRotation_onoff(context, flg_on):
    rig = context.active_object
    if rig is None or rig.type != "ARMATURE":
        return
    for pb in rig.pose.bones:
        for c in pb.constraints:
            if c.name == "Limit Rotation":
                c.mute = flg_on == False

import platform
def getHomeDir():
    if (platform.system() == "Windows"):
        try:
            import ctypes.wintypes
            csidl=5 # My Documents Folder (CSIDL_PERSONAL)
            access_token=None # Current User
            flags=0 # Current Value (SHGFP_TYPE_CURRENT)
            buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            result = ctypes.windll.shell32.SHGetFolderPathW(0, csidl, access_token, flags, buffer)
            if result != 0:
                if result < 0:
                    result += 2**32
                print("ERROR: SHGetFolderPathW() returned error code=[" + str(hex(result)) + "]")
                del buffer
                raise Exception()
            HOME_DIR = buffer.value
        except:
            HOME_DIR = os.path.expanduser("~").replace("\\","/") + "/Documents"
            print("Unable to query the correct Documents path for Windows, failing back to user folder=\"" + str(HOME_DIR) + "\".")
    elif (platform.system() == "Darwin"):
        HOME_DIR = os.path.expanduser("~") + "/Documents"
    else:
        HOME_DIR = os.path.expanduser("~")
    return HOME_DIR

def getRootPath():
    global root

    HOME_DIR = getHomeDir()
    root = os.path.join(HOME_DIR, "DAZ 3D", "Bridges", "Daz To Blender", "Exports").replace("\\", "/")

    return root


def get_custom_path():
    return bpy.context.scene.dtb_custom_path.path.replace("\\", "/")


def get_config_path():
    global config
    if config == "":
        hdir = getHomeDir()
        hdir = os.path.join(
            hdir, "DAZ 3D", "Bridges", "Daz To Blender", "Config"
        )
        if os.path.exists(hdir):
            config = hdir
        else:
            try:
                if os.path.isabs(hdir):
                    os.makedirs(hdir)
                    config = hdir
            except:
                print("ERROR: Unable to create config path:\"" + str(hdir) + "\".")
                config = ""
    return config


def load_asset_name():
    global _ASSETNAME
    for file in os.listdir(getHomeTown()):
        if file.endswith(".dtu"):
            dtu = os.path.join(getHomeTown(), file)
            break
    with open(dtu, "r") as file:
        _ASSETNAME = json.load(file)["Asset Name"]


def get_asset_name():
    return _ASSETNAME


def clear_already_use_newmtl():
    global already_use_newmtl
    already_use_newmtl = []


def set_already_use_newmtl(newmtl):
    global already_use_newmtl
    already_use_newmtl.append(newmtl)


def is_already_use_newmtl(newmtl):
    is_in = newmtl in already_use_newmtl
    print("@@@", is_in, newmtl, already_use_newmtl)
    return is_in


def setHomeTown(htown):
    global _HOMETOWN
    _HOMETOWN = htown


def getHomeTown():
    return _HOMETOWN


def clear_variables():
    global isMan
    global isGen
    global _AMTR
    global _BODY
    global _EYLS
    global _TEAR
    global _HAIR
    global _RGFY
    global keep_EYLS
    global Geo_Idx
    global _ISG3
    global _SIZE
    global IS_EMERGENCY
    global _BVCount
    global now_ary
    global pst_ary
    global _ENVROOT
    global shape_key_custom_props
    isMan = False
    isGen = False
    _AMTR = ""
    _BODY = ""
    _EYLS = ""
    _HAIR = ""
    _RGFY = ""
    keep_EYLS = ""
    Geo_Idx = 0
    _ISG3 = 0
    _SIZE = 0
    _ENVROOT = ""
    IS_EMERGENCY = False
    _BVCount = 0
    now_ary = []
    pst_ary = []
    shape_key_custom_props = []
    # for scene in bpy.data.scenes:
    #    scene.unit_settings.scale_length = 1


def amIRigfy(cobj):
    if cobj.type == "ARMATURE" and _RGFY == cobj.name:
        return True
    return False


def amIAmtr(cobj):
    if cobj.type == "ARMATURE" and _AMTR == cobj.name:
        return True
    return False


def amIBody(cobj):
    if cobj.type == "MESH" and _BODY == cobj.name:
        return True
    return False


def getHair():
    for dobj in Util.allobjs():
        if dobj.type == "MESH" and dobj.name == _HAIR:
            return dobj
    return None


def getBody():
    for dobj in Util.allobjs():
        if dobj.type == "MESH" and dobj.name == _BODY:
            return dobj
    return None


def getEyls():
    for dobj in Util.allobjs():
        if dobj.type == "MESH" and dobj.name == _EYLS:
            return dobj
    return None


def getTear():
    for dobj in Util.allobjs():
        if dobj.type == "MESH" and dobj.name == _TEAR:
            return dobj
    return None


def getRgfyBones():
    rig = getRgfy()
    if rig is not None:
        return rig.data.bones
    return None


def getRgfy():
    for dobj in Util.allobjs():
        if dobj.type == "ARMATURE" and dobj.name == _RGFY:
            return dobj
    return None


def setRgfy_name(newname):
    global _RGFY
    if getRgfy() is None:
        return
    getRgfy().name = newname
    _RGFY = newname


def getAmtrBones():
    rig = getAmtr()
    if rig is not None:
        return rig.data.bones
    return None


def getAmtr():
    for dobj in Util.allobjs():
        if dobj.type == "ARMATURE" and dobj.name == _AMTR:
            return dobj
    return None


def getAmtrConstraint(bone_name, const_name):
    if getAmtr is None:
        return
    pbone = getAmtr().pose.bones.get(bone_name)
    if pbone is None:
        return
    for c in pbone.constraints:
        if c.name == const_name:
            return c
    return None


def deselect():
    for obj in Util.allobjs():
        Versions.select(obj, False)


def toGeniVIndex(vidx):
    old = 0
    if Geo_Idx <= 0 or Geo_Idx >= 10:
        return vidx
    if getIsMan() == False:
        for ridx, r in enumerate(DataBase.f_geni[Geo_Idx - 1]):
            if vidx < r[0] and ridx > 0:
                vidx -= old
                break
            old = r[1]
    else:
        for ridx, r in enumerate(DataBase.m_geni[Geo_Idx - 1]):
            if vidx < r[0] and ridx > 0:
                vidx -= old
                break
            old = r[1]
    return vidx


def get_geo_idx():
    return Geo_Idx


def getRig_id():
    rig = getRgfy()
    for d in rig.data:
        if d.name == "rig_id":
            return d.data["rig_id"]


def bone_limit_modify(bone_limits):
    for bone_limit_key in bone_limits:
        bone_limit = bone_limits[bone_limit_key]
        name = bone_limit[0]
        order = bone_limit[1]

        prefix = name[0:1]
        post_prefix = name[1:2]
        bone_type = "none"
        if prefix == "l" and post_prefix.isupper():
            bone_type = "left"
        elif prefix == "r" and post_prefix.isupper():
            bone_type = "right"
        else:
            bone_type = "center"

        do_conversion = True

        if do_conversion and order == "XYZ":
            # YZ switch (Y <-> Z)
            for i in range(2):
                temp = bone_limit[4 + i]
                bone_limit[4 + i] = bone_limit[6 + i]
                bone_limit[6 + i] = temp

            # XY switch (X <-> Y)
            for i in range(2):
                temp = bone_limit[2 + i]
                bone_limit[2 + i] = bone_limit[4 + i]
                bone_limit[4 + i] = temp

            if bone_type == "right":
                # Y invert (-Y)
                temp = 0 - bone_limit[5]
                bone_limit[5] = 0 - bone_limit[4]
                bone_limit[4] = temp

                # Z invert (-Z)
                temp = 0 - bone_limit[7]
                bone_limit[7] = 0 - bone_limit[6]
                bone_limit[6] = temp

        elif do_conversion and order == "XZY":
            # XY switch (X <-> Y)
            for i in range(2):
                temp = bone_limit[2 + i]
                bone_limit[2 + i] = bone_limit[4 + i]
                bone_limit[4 + i] = temp

            # X invert (-X)
            temp = 0 - bone_limit[3]
            bone_limit[3] = 0 - bone_limit[2]
            bone_limit[2] = temp

            if bone_type == "right":
                # Y invert (-Y)
                temp = 0 - bone_limit[5]
                bone_limit[5] = 0 - bone_limit[4]
                bone_limit[4] = temp

                # Z invert (-Z)
                temp = 0 - bone_limit[7]
                bone_limit[7] = 0 - bone_limit[6]
                bone_limit[6] = temp

        elif do_conversion and order == "YZX":
            # Bones that are pointed down with YZX order
            lower_extremities_to_flip = DataBase.get_lower_extremities_to_flip()
            if name in lower_extremities_to_flip:
                # Y invert (-Y)
                temp = 0 - bone_limit[5]
                bone_limit[5] = 0 - bone_limit[4]
                bone_limit[4] = temp

                # Z invert (-Z)
                temp = 0 - bone_limit[7]
                bone_limit[7] = 0 - bone_limit[6]
                bone_limit[6] = temp

        elif do_conversion and order == "ZXY":
            # XY switch (X <-> Y)
            for i in range(2):
                temp = bone_limit[2 + i]
                bone_limit[2 + i] = bone_limit[4 + i]
                bone_limit[4 + i] = temp

            # YZ switch (Y <-> Z)
            for i in range(2):
                temp = bone_limit[4 + i]
                bone_limit[4 + i] = bone_limit[6 + i]
                bone_limit[6 + i] = temp

        elif do_conversion and order == "ZYX":
            # YZ switch (Y <-> Z)
            for i in range(2):
                temp = bone_limit[4 + i]
                bone_limit[4 + i] = bone_limit[6 + i]
                bone_limit[6 + i] = temp

            # X invert (-X)
            temp = 0 - bone_limit[3]
            bone_limit[3] = 0 - bone_limit[2]
            bone_limit[2] = temp
    store_bone_limits(bone_limits)
    return bone_limits


def store_bone_limits(bone_limits):
    global updated_bone_limits
    updated_bone_limits = bone_limits


def get_bone_limit():
    return updated_bone_limits


def toMergeWeight(dobj, ruler_idx, slave_idxs):
    setOpsMode("OBJECT")
    Versions.active_object(dobj)
    vgs = dobj.vertex_groups
    for i, v in enumerate(dobj.data.vertices):
        find = False
        other_weight = 0.0
        for s in slave_idxs:
            if s < 0:
                continue
            for g in v.groups:
                if g.group == s:
                    list = [i]
                    vgs[g.group].remove(list)
                    find = True
                elif g.group != ruler_idx:
                    other_weight += g.weight
            if find == True:
                list = [i]
                if other_weight > 0.0 and other_weight < 1.0:
                    vgs[ruler_idx].add(list, (1.0 - other_weight), "ADD")
                else:
                    vgs[ruler_idx].add(list, 1.0, "ADD")


def toMergeWeight2(dobj, ruler_idx, slave_idxs, flg_half):
    setOpsMode("OBJECT")
    Versions.active_object(dobj)
    vgs = dobj.vertex_groups
    vw_ary = []
    for vidx, v in enumerate(dobj.data.vertices):
        for s in slave_idxs:
            if s < 0:
                continue
            for g in v.groups:
                wt = g.weight
                if flg_half:
                    wt = wt / 2.0
                if g.group == s:
                    list = [vidx]
                    for vw in vw_ary:
                        if vw[0] == vidx:
                            vw[1] += wt
                            wt = 0
                    if wt > 0:
                        vw_ary.append([vidx, wt])
                    vgs[g.group].remove(list)
    for vw in vw_ary:
        vgs[ruler_idx].add([vw[0]], vw[1], "ADD")


def toMergeWeight_str(dobj, ruler_name, slave_names, flg_head, flg_half):
    Versions.select(dobj, True)
    Versions.active_object(dobj)
    ruler = -1
    slave = []
    vgs = dobj.vertex_groups
    for vi, vg in enumerate(vgs):
        if ruler_name == vg.name:
            ruler = vi
        else:
            for sn in slave_names:
                if sn in vg.name:
                    slave.append(vi)
                    break
    if ruler >= 0 and len(slave) > 0:
        if flg_head:
            toMergeWeight2(dobj, ruler, slave, flg_half)
        else:
            toMergeWeight(dobj, ruler, slave)

def getFootAngle_matrix(r_l):
    bones = ["hip", "pelvis", "ThighBend", "ThighTwist", "Shin", "Foot"]
    if getIsG9():
        bones = ["hip", "pelvis", "_thigh", "", "_shin", "_foot"]
    bone_name = "l" + bones[-1]
    if r_l == 0:
        bone_name = "r" + bones[-1]
    pose_bone = getAmtr().pose.bones.get(bone_name)
    if pose_bone is None:
        return [0, 0, 0]
    return_matrix = pose_bone.matrix
    return return_matrix


def getFootAngle(r_l):
    bones = ["hip", "pelvis", "ThighBend", "ThighTwist", "Shin", "Foot"]
    kakudo3 = [[0, 0, 0, -1, 0, 0], [1, 2, 2, -1, 2, 1], [2, 1, -1, 1, 1, 2]]
    minus3 = [[1], [0, 2, 4], [0]]
    ans = [0, 0, 0]
    flip_xyz = [0.0, 0.0, 0.0]
    flip_value = 0.0
    for i in range(3):
        for bidx, bname in enumerate(bones):
            if bidx >= 2:
                if r_l == 0:
                    bname = "r" + bname
                else:
                    bname = "l" + bname
            if kakudo3[i][bidx] < 0:
                continue
            pb = getAmtr().pose.bones.get(bname)
            if pb is None:
                continue
            rot = pb.rotation_euler[kakudo3[i][bidx]] * 57.3
            for ms in minus3[i]:
                if bidx == ms:
                    rot = 0 - rot
            r = 0.0
            # ThighBend
            if bidx == 2:
                # Fwd
                if i == 0 and rot < 0:
                    r = math.fabs(rot)
                    if math.fabs(r) > 90:
                        r = 90
                # Side
                elif i == 1:
                    r = rot
                flip_xyz[i] = r / 90.0
            # ThighTwist  Y
            if bidx == 3 and i == 2:
                flip_value = rot
            ans[i] = ans[i] + rot
        # Fwd
        x = flip_value * flip_xyz[0]
        if x < 0 and (math.fabs(ans[2] % 360) - x) >= 355:
            x = -360 + ans[2] + 5
        ans[2] -= x
        ans[1] += x
        # Side
        y = flip_value * flip_xyz[1]
        ans[0] += y
    return ans


def ifNeedToSnapKnee(r_l):
    poles = [getAmtr().pose.bones.get("rShin_P"), getAmtr().pose.bones.get("lShin_P")]
    iks = [getAmtr().pose.bones.get("rShin_IK"), getAmtr().pose.bones.get("lShin_IK")]
    k = iks[r_l].head[2] + iks[r_l].location[2]
    return iks[r_l].head[2] > poles[r_l].head[2]


def get_size():
    return float(bpy.context.window_manager.scene_scale)


def change_size(root):
    if get_size() < 1:
        # Scale Import
        for i in range(3):
            og_scale = root.scale[i]
            root.scale[i] = og_scale * get_size()
        setOpsMode("OBJECT")
        Versions.active_object(root)
        Versions.select(root, True)
        bpy.ops.object.transform_apply(scale=True)
        deselect()

        for obj in Util.myacobjs():
            if obj.type == "MESH":
                if obj.parent == root:
                    Versions.select(obj, True)
                    Versions.active_object(obj)
                    bpy.ops.object.transform_apply(
                        location=True, rotation=True, scale=True
                    )
                    deselect()
            elif obj.type == "LIGHT" or obj.type == "CAMERA":
                for i in range(3):
                    og_scale = obj.scale[i]
                    obj.scale[i] = og_scale * get_size()
                Versions.select(obj, True)
                Versions.active_object(obj)
                bpy.ops.object.transform_apply(scale=True)
                deselect()
        # Scale Daz_Pub
        for d in Util.colobjs("DP"):
            if d.type == "CAMERA" or d.type == "LIGHT":
                og_location = (140, 100, 150)
                for i in range(3):
                    d.location[i] = og_location[i] * get_size()
                Versions.select(obj, True)
                Versions.active_object(obj)
                bpy.ops.object.transform_apply(scale=True)
                deselect()


def float_by_size(float):
    return float * get_size()


def scale_settings():
    scene = bpy.context.scene
    scene.tool_settings.use_keyframe_insert_auto = False
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    if get_size() == 0.01:
        scene.unit_settings.length_unit = "CENTIMETERS"
    else:
        scene.unit_settings.length_unit = "METERS"

    # Change View Clipping
    bpy.context.space_data.clip_start = get_size()
    bpy.context.space_data.clip_end = 10000.00 * get_size()
    bpy.context.space_data.lens = 50

    location = [float_by_size(7.15), float_by_size(-4.35), float_by_size(100.0)]
    rotation = [0.6888, 0.6246, 0.2473, 0.2727]
    distance = float_by_size(430)
    cam_ob = bpy.context.scene.camera

    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            rv3d = area.spaces[0].region_3d
            if rv3d is not None:
                rv3d.view_location = location
                rv3d.view_rotation = rotation
                rv3d.view_distance = distance
                rv3d.view_camera_zoom = 0
            rv3d.update()
            viewport_data = rv3d

    if cam_ob != None:
        # Set Camera Position
        cam_ob.matrix_world = viewport_data.view_matrix
        cam_ob.matrix_world.invert()
        # Set Camera Clipping
        cam_ob.data.sensor_width = 64
        cam_ob.data.clip_start = bpy.context.space_data.clip_start
        cam_ob.data.clip_end = bpy.context.space_data.clip_end
        bpy.context.preferences.inputs.use_mouse_depth_navigate = True


# Destroy old hierachy of the vertex groups
def convert_vgroups():
    vgs = getBody().vertex_groups
    setOpsMode("OBJECT")
    Versions.active_object(getBody())
    vidx = 0
    total_vgs = len(vgs)
    for vg in vgs:
        if vg.name == "upperTeeth":
            vg.name = "upperJaw"
        elif vg.name == "LipLowerMiddle":
            bpy.context.object.vertex_groups.active_index = vidx
            bpy.context.object.vertex_groups[vidx].name = "lLipLowerMiddle"
            bpy.ops.object.vertex_group_copy()
            bpy.context.object.vertex_groups[total_vgs].name = "rLipLowerMiddle"
            total_vgs += 1
        elif vg.name == "CenterBrow":
            bpy.context.object.vertex_groups.active_index = vidx
            bpy.context.object.vertex_groups[vidx].name = "lCenterBrow"
            bpy.ops.object.vertex_group_copy()
            bpy.context.object.vertex_groups[total_vgs].name = "rCenterBrow"
            total_vgs += 1
        vidx += 1
    half_liplower = [
        ["lLipLowerInner", ["lLipLowerMiddle"]],
        ["rLipLowerInner", ["rLipLowerMiddle"]],
    ]
    for hl in half_liplower:
        toMergeWeight_str(getBody(), hl[0], hl[1], True, True)

    slave_rulers = [
        ["lowerJaw", ["lowerTeeth"]],
        ["tongue03", ["tongue04"]],
        ["lSquintInner", ["lNasolabialMiddle", "lNasolabialUpper"]],
        ["lNasolabialMouthCorner", ["lLipNasolabialCrease"]],
        ["lLipLowerOuter", ["lLipCorner"]],
    ]
    for index, slave_ruler in enumerate(slave_rulers):
        toMergeWeight_str(getBody(), slave_ruler[0], slave_ruler[1], True, False)
        prefix = slave_ruler[0][0:1]
        post_prefix = slave_ruler[0][1:2]
        bone_type = "center"
        if prefix == "l" and post_prefix.isupper():
            bone_type = "left"
        if bone_type == "left":
            slave_ruler[0] = "r" + slave_ruler[0][1:]
            for i in range(len(slave_ruler[1])):
                slave_ruler[1][i] = "r" + slave_ruler[1][i][1:]
            toMergeWeight_str(getBody(), slave_ruler[0], slave_ruler[1], True, False)


def mslot_to_vgroup(obj):
    material_names = []
    for index, slot in enumerate(obj.material_slots):
        if not slot.material:
            continue
        verts = [
            v
            for f in obj.data.polygons
            if f.material_index == index
            for v in f.vertices
        ]
        if len(verts):
            vg = obj.vertex_groups.get(slot.material.name)
            if vg is None:
                vg = obj.vertex_groups.new(name=slot.material.name)
                material_names.append(slot.material.name)
            vg.add(verts, 1.0, "ADD")
    return material_names


def finger(zindex):
    keys = [
        ["Ring", "Mid", "Pinky", "Index", "Thumb"],
        ["f_ring", "f_middle", "f_pinky", "f_index", "thumb"],
    ]
    if zindex == 0:
        allbones = getAmtr().pose.bones
    else:
        allbones = getRgfy().pose.bones
    for pb in allbones:
        for k in keys[zindex]:
            if (
                zindex == 0
                and pb.name[1:].startswith(k)
                and len(pb.name) == len(k) + 2
                and (pb.name.endswith("2") or pb.name.endswith("3"))
            ) or (
                zindex == 1
                and pb.name.startswith(k)
                and len(pb.name) == len(k) + 5
                and ((".02." in pb.name) or (".03." in pb.name))
            ):
                find = False
                for c in pb.constraints:
                    if c.name == "Copy Rotation":
                        mt = c.mute
                        c.mute = mt == False
                        find = True
                        break
                if find:
                    break
                cr = pb.constraints.new(type="COPY_ROTATION")
                if zindex == 0:
                    cr.target = getAmtr()
                    length = len(pb.name)
                    starget = pb.name[: length - 1]
                    if pb.name.endswith("3"):
                        starget += "2"
                    else:
                        starget += "1"
                else:
                    cr.target = getRgfy()
                    if ".03." in pb.name:
                        starget = pb.name.replace("3", "2")
                    elif ".02." in pb.name:
                        starget = pb.name.replace("2", "1")
                cr.subtarget = starget
                cr.use_x = k.lower() == "thumb"
                cr.use_y = False
                cr.use_z = k.lower() != "thumb"
                Versions.mix_mode(cr)
                cr.target_space = "LOCAL"
                cr.owner_space = "LOCAL"


def getCon():
    import sqlite3

    cadr = os.path.join(os.path.dirname(__file__), "img", "dtb.sqlite")
    con = sqlite3.connect(cadr)
    return con


def get_symmetry(vidx, want_left):
    if vidx <= 0:
        return 0
    tblName = "symmetry_"
    if getIsMan():
        tblName += "m"
    else:
        tblName += "f"

    con = getCon()
    cur = con.cursor()
    if want_left:
        sql = "select left from " + tblName + " where right = " + str(vidx)
    else:
        sql = "select right from " + tblName + " where left = " + str(vidx)
    cur.execute(sql)
    rtn = vidx
    for row in cur:
        rtn = row[0]
    cur.close()
    return rtn


def setRenderSetting(flg_high):
    args = [[1, 12, 16, 260, "EXPERIMENTAL"], [2, 8, 2, 80, "SUPPORTED"]]
    idx = 0 if flg_high else 1
    bpy.context.scene.cycles.dicing_rate = args[idx][0]
    bpy.context.scene.cycles.preview_dicing_rate = 8
    bpy.context.scene.cycles.offscreen_dicing_scale = args[idx][1]
    bpy.context.scene.cycles.max_subdivisions = args[idx][2]
    bpy.context.scene.cycles.samples = args[idx][3]
    bpy.context.scene.cycles.feature_set = args[idx][4]


class BoneRoop:
    bones = []
    vweights = []

    def __init__(self, rootbone):
        self.bones = []
        self.vweights = []
        self.find_bone_roop(getAmtr().data.bones[rootbone].children, rootbone)

    def find_bone_roop(self, bone_group, rootbone):
        for b in bone_group:
            if len(b.children) > 0:
                self.find_bone_roop(b.children, rootbone)
            self.bones.append(b.name)

    def getResultBones(self):
        return self.bones

    def getResultVertices(self):
        vgs = getBody().vertex_groups
        verts = getBody().data.vertices
        for v in verts:
            for g in v.groups:
                if vgs[g.group].name in self.bones:
                    self.vweights.append(
                        [v.index, g.group, vgs[g.group].name, g.weight]
                    )
        self.vweights.sort()
        old_v = -1
        sum = 0.0
        rtn = []
        for vw in self.vweights:
            if old_v != vw[0]:
                rtn.append([old_v, sum])
                sum = 0.0
            sum = sum + vw[3]
            old_v = vw[0]
        if sum > 0.0:
            rtn.append([old_v, sum])
        return rtn
