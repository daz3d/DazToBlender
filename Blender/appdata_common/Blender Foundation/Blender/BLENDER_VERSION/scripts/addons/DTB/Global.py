import bpy
import os
import math
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
_RGFY = ""
keep_EYLS = ""
db = DataBase.DB()
bone_limit_memory = []

Geo_Idx = 0
now_ary = []
pst_ary = []
_ISPRO = 0
_BVCount = 0
_SIZE = 0
root =""
_ISG3 = 0
_HOMETOWN = ""
already_use_newmtl = []
_ENVROOT = ""

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
    [[16556,65806,262514],[17192,68350,272690],[17292,68450,272790],[17418,68744,273396]],
    [[16384,65118,259762],[17454,69398,276882],[17543,69498,276982],[17246,68056,270644]],
]


IS_EMERGENCY = False
EYLSCOUNT =464

def getMyMax3():
    return max_vs[getSex()][get_geo_idx()]

def getIsPro():
    global _ISPRO
    if _ISPRO==0:
        dir = os.path.dirname(__file__)+getFileSp()+"ToHighReso.py"
        if os.path.exists(dir):
            _ISPRO = 1
        else:
            _ISPRO = -1
    return _ISPRO > 0

def getIsG3():
    return get_geo_idx()==G3_GEOIDX
    
def getIsEmergency():
    return IS_EMERGENCY

def setItsEmergency():
    global IS_EMERGENCY
    IS_EMERGENCY = True

def isAcs():
    wk = bpy.context.window_manager.search_prop
    wk = wk.strip()
    wk = wk.lower()
    return wk=='#accessory'

def getSubdivLevel():
    naga = len(getBody().data.vertices)
    if naga>200000:
        return 2
    elif naga>60000:
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
    if len(my_amtr.animation_data.action.fcurves)<=0:
        return False
    return True

def orthopedic_sharp(word):
    word = word.replace(' ', '')
    word = word.lower()
    return word

def isRiggedObject(dobj):
    if dobj.type == 'MESH':
        for modifier in dobj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:
                if modifier.object.name == get_Amtr_name() or modifier.object.name == get_Rgfy_name():
                    return True

    return False

def isRiggedObject_when_Amtr_is_None(dobj):
    if dobj.type == 'MESH':
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
    if len(now_ary)-len(pst_ary)<1:
        return ""
    for n in now_ary:
        hit = False
        if n not in pst_ary:
            return n
    return ""

def setOpsMode(arg):
    combi = ['POSE','EDIT','OBJECT','SCULPT']
    if arg in combi:
        if Versions.get_active_object() is not None:
            if Versions.get_active_object().mode != arg:
                bpy.ops.object.mode_set(mode=arg)

def add_bone_limit(line):
    bone_limit_memory.append(line)

def get_Amtr_name():
    if _AMTR!="" and (_AMTR in Util.allobjs()):
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

def get_Hair_name():
    if _HAIR != "" and (_HAIR in Util.allobjs()):
        return _HAIR
    else:
        return ""

def get_KeepEyls_name():
    return keep_EYLS

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

def getIsHair():
    return _HAIR != ""

def setEylsIsJoined():
    global _EYLS
    _EYLS = ""

def find_RGFY_all():
    for d in Util.myccobjs():
        if find_RGFY(d):
            return True
    return False

def getFileSp():
    if os.name=='nt':
        return "\\"
    else:
        return "/"

def find_RGFY(dobj):
    global _RGFY
    if dobj.type == 'ARMATURE':
        abones = dobj.data.bones
        if len(abones) > 600:
            list = ['ORG-', 'DEF-', 'MCH-', 0, 0, 0]
            for ab in abones:
                for i in range(3):
                    if ab.name.startswith(list[i]):
                        list[i + 3] += 1
            if list[3] > 100 and list[4] > 100 and list[5] > 70:
                _RGFY = dobj.name
                _AMTR = ""
                return True
    return False

def find_AMTR(dobj):
    global _AMTR
    global _ISG3
    _ISG3 = 0
    if dobj.type == 'ARMATURE':
        abones = dobj.data.bones
        point = 0
        if('lHeel' in abones) or ('rHeel' in abones):#G3
            _ISG3 = 1
        if len(abones) > 160:
            for bn in db.tbl_basic_bones:
                for pb in abones:
                    if bn[0] == pb.name:
                        point += 1
        if point > 150:
            _AMTR = dobj.name
            _RGFY = ""
            if _ISG3==1:
                _ISG3 = 2
            return True
    return False

def find_BODY(dobj):
    global _BODY
    if dobj.type == 'MESH':
        if Versions.isHide(dobj):
            return False
        for modifier in dobj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:
                if modifier.object.name == _AMTR or modifier.object.name == _RGFY:

                    if len(dobj.vertex_groups) > 163 and len(dobj.data.vertices) >= 16384:  # Female 16556 Male 16384
                        mtls = ['Torso', 'Face', 'Lips', 'Teeth', 'Ears', 'Legs', 'EyeSocket', 'Mouth', 'Arms',
                                'Pupils', 'EyeMoisture', 'Fingernails', 'Cornea', 'Irises', 'Sclera', 'Toenails','EylsMoisture']
                        point = len(mtls)
                        for slot in dobj.material_slots:
                            for m in mtls:
                                if m in slot.name:
                                    point -= 1;
                                    break
                        if point < 5:
                            _BODY = dobj.name
                            return True
    return False

def getChildren(obj):
    children = []
    col = Util.getUsersCollection(obj)
    for ob in Util.colobjs(col.name):
        if ob.parent == obj:
            children.append(ob)
    return children

def find_Both(obj):
    if obj.type=='MESH':
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object is not None:
                if find_AMTR(modifier.object)==False:
                    if find_RGFY(modifier.object)==False:
                        return False
        return find_BODY(obj)
    elif obj.type=='ARMATURE':
        if find_AMTR(obj) or find_RGFY(obj):
            kids = getChildren(obj)
            for k in kids:
                if find_BODY(k):
                    return True
            return False
    return False



def find_EYLS(dobj):
    global _EYLS
    global keep_EYLS
    if isRiggedObject(dobj):
        if len(dobj.vertex_groups) == 16 and len(dobj.data.vertices) == 464:
            miss = 0
            for vg in dobj.vertex_groups:
                if ('head' == vg.name.lower()) == False and ('eyelid' in vg.name.lower()) == False:
                    miss += 1
            if miss < 3:
                _EYLS = dobj.name
                keep_EYLS = deepcopy(dobj.name)
                return True
    return False

def find_HAIR(dobj):
    global _HAIR
    if isRiggedObject(dobj):
        if ('brow' in dobj.name.lower())==False:
            hi = 0
            count = [0,0]
            if getBody() is not None:
                cnt = 0
                hi = getBody().dimensions[2]
                if hi < getBody().dimensions[1]:
                    hi = getBody().dimensions[1]

            vgs = dobj.vertex_groups
            for v in dobj.data.vertices:
                if v.co[1] >=hi or v.co[2] >= hi :
                    count[0]+= 1
                for gp in v.groups:
                    vgname = vgs[gp.group].name.lower()
                    if ('head' in vgname):
                        count[1] += 1
                    elif ('abdomen' in vgname) or ('forearm' in vgname):
                        count[1] -=1
            if count[0]>10 and count[1]>10:
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
    if fromtop[0]!=frombtm[0]:
        return
    if fromtop[0].type=='ARMATURE' or fromtop[0].type=='EMPTY':
        _ENVROOT = fromtop[0].name

def getEnvRoot():
    if _ENVROOT !="" and (_ENVROOT in Util.allobjs()):
        return Util.allobjs().get(_ENVROOT)

def decide_HERO():
    global _AMTR
    global _RGFY
    global _BODY
    global _EYLS
    global _HAIR
    global isMan
    global isGen
    global _BVCount
    global _ISG3
    global Geo_Idx
    global _SIZE
    bool_amtr = [False, False]
    clear_variables()
    for dobj in Util.myacobjs():
        if find_AMTR(dobj):
            bool_amtr[0] = True
            break
        if find_RGFY(dobj):
            bool_amtr[1] = True
            break
    if bool_amtr[0] == False:
        _AMTR = ""
    if bool_amtr[1] == False:
        _RGFY = ""
    if _AMTR == "" and _RGFY == "":
        return
    mf = 0
    bool_body = [False, False, False]

    for z in range(2):
        for dobj in Util.myccobjs():
            if z==0 and find_BODY(dobj):
                bool_body[0] = True
                lon = len(dobj.data.vertices)
                _BVCount = lon
                for i in range(2):
                    for vc in max_vs[i][0]:
                        if lon==vc or lon==vc+EYLSCOUNT:
                            mf = (1 if i == 1 else 2)
                            isGen = False
                            break
                    for vc in max_vs[i][G3_GEOIDX]:
                        if lon == vc:
                            if getIsPro() == False:
                                bool_body[0] = False
                                break
                            elif _ISG3 == 2:
                                _ISG3 = 0
                                mf = (1 if i == 1 else 2)
                                isMan = mf==1
                                addG3Database(isMan)
                                Geo_Idx = G3_GEOIDX
                                isGen = True
                                break
                break
            elif z>0 and bool_body[1]==False and find_EYLS(dobj):
                bool_body[1] = True
            elif z>0 and bool_body[2]==False and find_HAIR(dobj):
                bool_body[2] = True
    if bool_body[0] == False:
        _BODY = ""
    if bool_body[1] == False:
        _EYLS = "";
    if bool_body[2] == False:
        _HAIR = "";
    if _BODY == "":
        return
    if mf == 0:
        getmf = getMf()
        if getmf[2]==False:
            _BODY = ""
        else:
            isMan = getmf[0]
            isGen = getmf[1]
    else:
        isMan = mf==1
        
        
def addG3Database(isman):
    sql = ""
    if isman==False and len(DataBase.f_geni)==G3_GEOIDX-1:
        sql = "select SRC,DST from G3F order by SRC"
    elif isman and len(DataBase.m_geni)==G3_GEOIDX -1:
        sql = "select SRC,DST from G3M order by SRC"
    if sql=="":
        return
    con = getCon()
    cur = con.cursor()
    cur.execute(sql)
    addtbl = []
    for row in cur:
        addtbl.append([row[0],row[1]])
    if isman:
        DataBase.m_geni.append(addtbl)
    else:
        DataBase.f_geni.append(addtbl)
    cur.close()
    con.close()

def meipe_bone():
    if getIsMan() or Geo_Idx!=2:
        return
    bones = ["labia","rectum","vagina","clitoris","labium"]
    dobj = getAmtr()
    Versions.select(dobj,True)
    Versions.active_object(dobj)
    ob = bpy.context.object
    setOpsMode('EDIT')
    for bone in ob.data.edit_bones:
        for bn in bones:
            if bn in bone.name.lower():
                bone.tail[2] = bone.head[2]-2
        #if bone.name.endswith("_end"):
        #    dobj.data.edit_bones.remove(bone)

def getMf():
    global Geo_Idx
    global isMan
    if getBody() is None:
        return
    rtn = [False, False, False]
    verts = getBody().data.vertices
    if getAmtr() is not None:
        xr =  getAmtr().rotation_euler[0]
    else:
        xr = 0
    is_fst =  xr> math.radians(88) and xr < math.radians(92)
    if is_fst:
        hi = getBody().dimensions[1]
        hi = (hi * 9) / 10
    else:
        hi = getBody().dimensions[2]
        hi = (hi * 8) / 10
    tops = [[5358,69,3958,79,5534,3],[5054,69,3733,78,5230,3]]#5345,5041,
    for sex in range(2):
        isMan = sex == 1
        Geo_Idx = 0
        if is_fst and ('Male' in getBody().name) and sex==0:
            continue
        max = len(DataBase.f_geni)+1
        if isMan:
            max = len(DataBase.m_geni)+1
        for i in range(max):
            point = 0
            tpast = 0
            max3 = max_vs[sex][i]
            # if (len(getBody().data.vertices) in max3)==False:
            #     continue
            for tidx,t in enumerate(tops[sex]):
                v = verts[t]
                src_t = t
                Geo_Idx = i
                if i > 0:
                    t = toGeniVIndex(t)
                    v = verts[t]
                vpast = verts[tpast]
                if is_fst:
                    if v.co[1] > hi and v.co[0] < 0.3 and v.co[0] > -0.3:
                        if tidx==0 or (tidx > 0 and v.co[2] > vpast.co[2]):
                            point += 1
                else:
                    if v.co[2] > hi and v.co[0] < 0.3 and v.co[0] > -0.3:
                        if tidx==0 or (tidx > 0 and v.co[1] < vpast.co[1]):
                            point += 1
                tpast = t
            if point == 6:
                rtn[0] = sex==1
                rtn[1] = i > 0
                rtn[2] = True
                return rtn
    Geo_Idx = 0
    return rtn

def boneRotation_onoff(context,flg_on):
    rig = context.active_object
    if rig is None or rig.type!='ARMATURE':
        return
    for pb in rig.pose.bones:
        for c in pb.constraints:
            if c.name == 'Limit Rotation':
                c.mute = flg_on == False

def getRootPath():
    global root
    if root == "":
        if os.name == 'nt':
            hdir = os.path.expanduser('~')
        else:
            hdir = os.environ['HOME']
        fname = "DTB"
        hdir += getFileSp() + "Documents" + getFileSp() + "DTB" + getFileSp()
        if os.path.exists(hdir)==False or os.path.isdir(hdir) == False:
            if os.name == 'nt':
                hdir = "C:\\Documents\\DTB\\"
            else:
                hdir = "/Documents/DTB/"
        if os.path.exists(hdir):
            root = hdir
        else:
            root = ""
    return root

def clear_already_use_newmtl():
    global already_use_newmtl
    already_use_newmtl = []

def set_already_use_newmtl(newmtl):
    global already_use_newmtl
    already_use_newmtl.append(newmtl)

def is_already_use_newmtl(newmtl):
    is_in = (newmtl in already_use_newmtl)
    print("@@@",is_in,newmtl,already_use_newmtl)
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
    _BVCount  = 0
    now_ary = []
    pst_ary = []
    #for scene in bpy.data.scenes:
    #    scene.unit_settings.scale_length = 1
    
def amIRigfy(cobj):
    if cobj.type=='ARMATURE' and _RGFY==cobj.name:
        return True
    return False

def amIAmtr(cobj):
    if cobj.type=='ARMATURE' and _AMTR==cobj.name:
        return True
    return False
def amIBody(cobj):
    if cobj.type=='MESH' and _BODY == cobj.name:
        return True
    return False

def getHair():
    for dobj in Util.allobjs():
        if dobj.type == 'MESH' and dobj.name == _HAIR:
            return dobj
    return None

def getBody():
    for dobj in Util.allobjs():
        if dobj.type == 'MESH' and dobj.name == _BODY:
            return dobj
    return None

def getEyls():
    for dobj in Util.allobjs():
        if dobj.type == 'MESH' and dobj.name == _EYLS:
            return dobj
    return None

def getRgfyBones():
    rig = getRgfy()
    if rig is not None:
        return rig.data.bones
    return None

def getRgfy():
    for dobj in Util.allobjs():
        if dobj.type == 'ARMATURE' and dobj.name == _RGFY:
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
        if dobj.type == 'ARMATURE' and dobj.name == _AMTR:
            return dobj
    return None

def getAmtrConstraint(bone_name,const_name):
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
        Versions.select(obj,False)

def toGeniVIndex(vidx):
    old = 0
    if Geo_Idx <= 0 or Geo_Idx >= 10:
        return vidx
    if getIsMan() == False:
        for ridx, r in enumerate(DataBase.f_geni[Geo_Idx-1]):
            if vidx < r[0] and ridx > 0:
                vidx -= old;
                break
            old = r[1]
    else:
        for ridx, r in enumerate(DataBase.m_geni[Geo_Idx-1]):
            if vidx < r[0] and ridx > 0:
                vidx -= old;
                break
            old = r[1]
    return vidx

def get_geo_idx():
    return Geo_Idx
    
def get_bone_limit():
    if bone_limit_memory is None or len(bone_limit_memory)==0:
        bone_limit_modify()
    return bone_limit_memory

def getRig_id():
    rig = getRgfy()
    for d in rig.data:
        if d.name=='rig_id':
            return d.data['rig_id']
            
def bone_limit_modify():

    cur = db.g8_blimit
    if getIsG3():
        cur = cur[4:]
        cur.extend(db.g3_blimit)
    for rows in cur:
        if len(rows)==2:
            continue
        odr = rows[1]
        row = [rows[0], ""]
        for i in range(2, len(rows)):
            row.append(rows[i])
        # Z_INVERT
        if odr == 'YZX' or odr == 'XYZ':
            if row[0] != '*rCollar':
                work = 0 - row[7]
                row[7] = 0 - row[6]
                row[6] = work
        xy_invert =['rCollar','rShldrBend','rForearmBend','rForearmTwist','rShldrTwist','rThumb2','rThumb3','rThumb1','rHand']
        #Y_INVERT and X_INVERT
        for xyi in xy_invert:   
            if row[0]==xyi:
                for i in range(2):
                    work = row[2+i*2]
                    row[2+i*2] = 0-row[2+i*2+1]
                    row[2+i*2+1] = 0-work
        # XY switch
        if odr == 'XZY' or odr == 'XYZ': 
            for i in range(2):
                work = row[2 + i]
                row[2 + i] = row[4 + i]
                row[4 + i] = work
        # YZ switch
        if odr == 'ZYX':  
            for i in range(2):
                work = row[4 + i]
                row[4 + i] = row[6 + i]
                row[6 + i] = work
        if row[0][1:] == 'Foot':
            work = 0 - row[7]
            row[7] = 0 - row[6]
            row[6] = work
        add_bone_limit(row)

def toMergeWeight(dobj, ruler_idx, slave_idxs):
    setOpsMode('OBJECT')
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
                    vgs[ruler_idx].add(list, (1.0 - other_weight), 'ADD')
                else:
                    vgs[ruler_idx].add(list, 1.0, 'ADD')
                    
def toMergeWeight2(dobj, ruler_idx, slave_idxs,flg_half):
    setOpsMode('OBJECT')
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
                        if vw[0]==vidx:
                            vw[1] += wt
                            wt = 0
                    if wt>0:
                        vw_ary.append([vidx,wt])
                    vgs[g.group].remove(list)
    for vw in vw_ary:
        vgs[ruler_idx].add([vw[0]], vw[1], 'ADD')

def toMergeWeight_str(dobj, ruler_name, slave_names,flg_head,flg_half):
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
            toMergeWeight2(dobj, ruler, slave,flg_half)
        else:
            toMergeWeight(dobj, ruler, slave)

def getFootAngle(r_l):
    bones = ['hip','pelvis','ThighBend','ThighTwist','Shin','Foot']
    kakudo3 = [[0,0,0,-1,0,0],[1,2,2,-1,2,1],[2,1,-1,1,1,2]]
    minus3 = [[1],[0,2,4],[0]]
    ans = [0,0,0]
    flip_xyz = [0.0,0.0,0.0]
    flip_value = 0.0
    for i in range(3):
        for bidx,bname in enumerate(bones):
            if bidx>=2:
                if r_l==0:
                    bname = 'r' + bname
                else:
                    bname = 'l' + bname
            if kakudo3[i][bidx]<0:
                continue
            pb = getAmtr().pose.bones.get(bname)
            if pb is None:
                continue
            rot =  pb.rotation_euler[kakudo3[i][bidx]]*57.3
            for ms in minus3[i]:
                if bidx == ms:
                    rot = 0 - rot
            r = 0.0
            #ThighBend
            if bidx==2:
                #Fwd
                if i==0 and rot<0:
                    r = math.fabs(rot)
                    if math.fabs(r) > 90:
                        r = 90
                #Side
                elif i==1:
                    r = rot
                flip_xyz[i] = r/90.0
            #ThighTwist  Y
            if bidx==3 and i==2:
                flip_value = rot
            ans[i] = ans[i] + rot
        #Fwd
        x = flip_value * flip_xyz[0]
        if x < 0 and (math.fabs(ans[2]%360) - x) >= 355:
            x = -360 + ans[2] + 5
        ans[2] -= x
        ans[1] += x
        #Side
        y = flip_value * flip_xyz[1]
        ans[0] += y
    return ans

def ifNeedToSnapKnee(r_l):
    poles = [getAmtr().pose.bones.get('rShin_P'), getAmtr().pose.bones.get('lShin_P')]
    iks = [getAmtr().pose.bones.get('rShin_IK'),getAmtr().pose.bones.get('lShin_IK')]
    k = iks[r_l].head[2] + iks[r_l].location[2]
    return iks[r_l].head[2] > poles[r_l].head[2]


def judgeSize():
    max = 0
    for z in range(2):
        if z>0 and max>0:
            break
        for obj in Util.myacobjs():
            for i in range(3):
                if z == 0:
                    if obj.dimensions[i]>max:
                        max = obj.dimensions[i]
                else:
                    if obj.location[i] > max:
                        max = obj.location[i]
    if max==0:
        if bpy.context.window_manager.size_100:
            max = 71
    global _SIZE
    if max <70:
        _SIZE = 1
    else:
        _SIZE= 100

def want_real():
    return bpy.context.window_manager.size_100==False

def getSize():
    if _SIZE==0:
        judgeSize()
    return _SIZE

def scale_environment():
    for scene in bpy.data.scenes:
        scene.tool_settings.use_keyframe_insert_auto = False
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.scale_length = 1.0/getSize()
    lens = [0.01*getSize(),1000*getSize(),50.0+math.floor(0.3*getSize())]
    bpy.context.space_data.clip_start = lens[0]
    bpy.context.space_data.clip_end = lens[1]
    bpy.context.space_data.lens = lens[2]
    size_1_100 =  [[(0.2721, -0.2184, 0.9022),(-0.7137, -0.5870, -0.2612,-0.2790),3],
                   [(7.15, -4.35, 100.0),(-0.7150, -0.5860, -0.2601, -0.2788) ,430]]
    idx = 0 if getSize()==1 else 1
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            rv3d = area.spaces[0].region_3d
            if rv3d is not None:
                rv3d.view_location = size_1_100[idx][0]
                rv3d.view_rotation = size_1_100[idx][1]
                rv3d.view_distance = size_1_100[idx][2]
                rv3d.view_camera_zoom = 0
    bpy.context.preferences.inputs.use_mouse_depth_navigate = True
    normal_and_bump_to_size()

def normal_and_bump_to_size():
    objs = Util.myacobjs()
    for obj in objs:
        if obj==getBody():
            continue
        for slot in obj.material_slots:
            mat = bpy.data.materials.get(slot.name)
            if mat is None or mat.node_tree is None:
                print(mat,mat.node_tree)
                continue
            ROOT = mat.node_tree.nodes

            for n in ROOT:
                if n.type=='BUMP':
                    n.inputs['Strength'].default_value = 0.01 * getSize()
                    n.inputs['Distance'].default_value = 0.01 * getSize()
                elif n.type=='NORMAL_MAP':
                    n.inputs['Strength'].default_value = 0.01 * getSize()

def changeSize(size, mub_ary):
    global _SIZE
    if _SIZE==0:
        getSize()
    flg_env = False
    if getAmtr() is not None and (get_Amtr_name() in Util.myacobjs()):
        armature = getAmtr()
    elif getRgfy() is not None and (get_Rgfy_name() in Util.myacobjs()):
        armature = getRgfy()
    elif getEnvRoot() is not None and (_ENVROOT in Util.myacobjs()):
        armature = getEnvRoot()
        flg_env = True
    else:
        return
    change_size = 1 if size == 100 else 0.01
    setOpsMode("OBJECT")
    for i in range(3):
        if armature.scale[i]!=change_size:
            armature.scale[i] = change_size
    deselect()
    if mub_ary !=[]:
        for obj in Util.myacobjs():
            if obj.name in mub_ary:
                Versions.active_object(obj)
                Versions.select(obj, True)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                Versions.active_object_none()
                Versions.select(obj, False)
    if flg_env==False:
        Versions.active_object(armature)
        Versions.select(armature, True)
        bpy.ops.object.transform_apply(scale=True)
    deselect()
    if flg_env==False:
        for obj in Util.myacobjs():
            if isRiggedObject(obj):
                Versions.select(obj,True)
                Versions.active_object(obj)
                bpy.ops.object.transform_apply(scale=True)
            elif obj.type=='LIGHT' or obj.type=='CAMERA':
                for i in range(3):
                    if obj.scale[i] != change_size:
                        obj.scale[i] = change_size
                Versions.select(obj, True)
                Versions.active_object(obj)
                bpy.ops.object.transform_apply(scale=True)
            deselect()
    find = False
    for d in Util.colobjs('DP'):
        if d.type=='CAMERA' or d.type=='LIGHT':
            find = True
            for i in range(3):
                if d.scale[i] !=change_size:
                    d.location[i] = d.location[i]*change_size
                    d.scale[i] = change_size
    _SIZE = size
    if getBody() is not None:
        Versions.select(getBody(), True)
        from . import DtbMaterial
        DtbMaterial.default_material()

    #scale_environment(size)
    deselect()
    # Versions.select(armature,True)
    # Versions.active_object(armature)
    # setOpsMode("POSE")
    #Versions.view_from_camera()

def heigou_vgroup():
    vgs = getBody().vertex_groups
    setOpsMode('OBJECT')
    Versions.active_object(getBody())
    vidx = 0
    max = len(vgs)
    for vg in vgs:
        if vg.name=='upperTeeth':
            vg.name = 'upperJaw'
        elif vg.name=='LipLowerMiddle':
            bpy.context.object.vertex_groups.active_index = vidx
            bpy.context.object.vertex_groups[vidx].name = 'lLipLowerMiddle'
            bpy.ops.object.vertex_group_copy()
            bpy.context.object.vertex_groups[max].name = 'rLipLowerMiddle'
            max += 1
        elif vg.name == 'CenterBrow':
            bpy.context.object.vertex_groups.active_index = vidx
            bpy.context.object.vertex_groups[vidx].name = 'lCenterBrow'
            bpy.ops.object.vertex_group_copy()
            bpy.context.object.vertex_groups[max].name = 'rCenterBrow'
            max += 1
        vidx += 1
    half_liplower=[
        ['lLipLowerInner', ['lLipLowerMiddle']],
        ['rLipLowerInner', ['rLipLowerMiddle']],
    ]
    for hl in half_liplower:
        toMergeWeight_str(getBody(), hl[0], hl[1], True,True)

    slave_rulers = [
        ['lowerJaw', ['lowerTeeth']],
        ['tongue03', ['tongue04']],
        ['lSquintInner', ['lNasolabialMiddle','lNasolabialUpper']],
        ['lNasolabialMouthCorner',['lLipNasolabialCrease']],
        ['lLipLowerOuter', ['lLipCorner']],
    ]
    for sidx,sr in enumerate(slave_rulers):
        toMergeWeight_str(getBody(),sr[0],sr[1],True,False)
        if sidx>0 and sr[0].startswith("l"):
            sr[0] = 'r' + sr[0][1:]
            for i in range(len(sr[1])):
                sr[1][i] = 'r' + sr[1][i][1:]
            toMergeWeight_str(getBody(), sr[0], sr[1],True,False)

def mslot_to_vgroup(obj):
    material_names = []
    for index, slot in enumerate(obj.material_slots):
        if not slot.material:
            continue
        verts = [v for f in obj.data.polygons
                if f.material_index == index for v in f.vertices]
        if len(verts):
            vg = obj.vertex_groups.get(slot.material.name)
            if vg is None:
                vg = obj.vertex_groups.new(name=slot.material.name)
                material_names.append(slot.material.name)
            vg.add(verts, 1.0, 'ADD')
    return material_names

def finger(zindex):
    keys = [['Ring', 'Mid', 'Pinky', 'Index', 'Thumb'],['f_ring','f_middle','f_pinky','f_index','thumb']]
    if zindex==0:
        allbones = getAmtr().pose.bones
    else:
        allbones = getRgfy().pose.bones
    for pb in allbones:
        for k in keys[zindex]:
            if (zindex==0 and pb.name[1:].startswith(k) and len(pb.name) == len(k) + 2 and (
                pb.name.endswith("2") or pb.name.endswith("3"))
            )or(
                zindex==1 and pb.name.startswith(k) and len(pb.name)==len(k)+5 and
                (('.02.' in pb.name) or ('.03.' in pb.name))
            ):
                find = False
                for c in pb.constraints:
                    if c.name=='Copy Rotation':
                        mt = c.mute
                        c.mute = mt==False
                        find = True
                        break
                if find:
                    break
                cr = pb.constraints.new(type='COPY_ROTATION')
                if zindex==0:
                    cr.target = getAmtr()
                    length = len(pb.name)
                    starget = pb.name[:length - 1]
                    if pb.name.endswith("3"):
                        starget += "2"
                    else:
                        starget += "1"
                else:
                    cr.target = getRgfy()
                    if '.03.' in pb.name:
                        starget = pb.name.replace('3', '2')
                    elif '.02.' in pb.name:
                        starget = pb.name.replace('2', '1')
                cr.subtarget = starget
                cr.use_x = k.lower() == 'thumb'
                cr.use_y = False
                cr.use_z = k.lower() != 'thumb'
                Versions.mix_mode(cr)
                cr.target_space = 'LOCAL'
                cr.owner_space = 'LOCAL'


def getCon():
    import sqlite3
    cadr = os.path.dirname(__file__) + getFileSp() + "img" + getFileSp() + "dtb.sqlite"
    con = sqlite3.connect(cadr)
    return con

def get_symmetry(vidx,want_left):
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
        sql = "select left from "+tblName+" where right = " + str(vidx)
    else:
        sql = "select right from "+tblName+" where left = " + str(vidx)
    cur.execute(sql)
    rtn = vidx
    for row in cur:
        rtn = row[0]
    cur.close()
    return rtn

def setRenderSetting(flg_high):
    args = [[1,12,16,260,'EXPERIMENTAL'],[2,8,2,80,'SUPPORTED']]
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
    def __init__(self,rootbone):
        self.bones = []
        self.vweights = []
        self.find_bone_roop(getAmtr().data.bones[rootbone].children,rootbone)
    def find_bone_roop(self,bone_group,rootbone):
        for b in bone_group:
            if len(b.children) > 0:
                self.find_bone_roop(b.children,rootbone)
            self.bones.append(b.name)
    def getResultBones(self):
        return self.bones
    def getResultVertices(self):
        vgs = getBody().vertex_groups
        verts = getBody().data.vertices
        for v in verts:
            for g in v.groups:
                if vgs[g.group].name in self.bones:
                    self.vweights.append([v.index,g.group,vgs[g.group].name,g.weight])
        self.vweights.sort()
        old_v = -1
        sum = 0.0
        rtn = []
        for vw in self.vweights:
            if old_v!=vw[0]:
                rtn.append([old_v, sum])
                sum = 0.0
            sum = sum + vw[3]
            old_v = vw[0]
        if sum>0.0:
            rtn.append([old_v, sum])
        return rtn