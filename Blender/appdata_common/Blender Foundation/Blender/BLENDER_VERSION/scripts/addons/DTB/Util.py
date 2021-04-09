
import bpy
import os
import math
import json
from . import DataBase
from . import Versions
from . import Global
import re
from mathutils import Euler

_CURRENT_COL = ""

def colobjs(col_name):
    if col_name=="":
        col_name = "DR"
    skey = [['DP','DAZ_PUB'],['DH','DAZ_HIDE'],['DR','DAZ_ROOT']]
    for sk in skey:
        if col_name == sk[0]:
            col_name = sk[1]
            break
    col = bpy.data.collections.get(col_name)
    if col is not None:
        return col.objects
    return bpy.context.scene.collection.objects

def all_armature():
    objs =  bpy.data.objects
    armatures = []
    for obj in objs:
        if obj.type == "ARMATURE":
            armature = obj
            armatures.append(armature)
    return armatures

def allobjs():
    return bpy.data.objects

def myccobjs():
    return colobjs(cur_col_name())

def myacobjs():
    aobj = Versions.get_active_object()
    col = ""
    if aobj is not None:
        col = getUsersCollectionName(aobj)
    if col=="":
        col = cur_col_name()
    return colobjs(col)
def get_dzidx():
    ccn = cur_col_name()
    a = ccn.rfind("_")
    if a==7:
        return "-dz" + ccn[8:]
    else:
        return "err"

def cur_col_name():
    global _CURRENT_COL
    if _CURRENT_COL == "":
        _CURRENT_COL = getActiveCollection().name
        if _CURRENT_COL is None:
            _CURRENT_COL = ""
    return _CURRENT_COL


def getCurrentCollection():
    ccname = cur_col_name()
    if ccname is None or ccname == "":
        return None
    else:
        return bpy.data.collections.get(ccname)

def refresuCurrentCollection():
    col = getActiveCollection()
    global _CURRENT_COL
    _CURRENT_COL = col.name

def setCurrentCollection(col):
    global _CURRENT_COL
    _CURRENT_COL = col.name
    setCurrentCollectionByName(_CURRENT_COL)
    
def setCurrentCollectionByName(col_name):
    global _CURRENT_COL
    _CURRENT_COL = col_name
    setActiveCollectionByName(col_name)

def getUsersCollection(object):
    if object is None:
        return None
    ucols = object.users_collection
    if len(ucols)>0:
        return ucols[0]
    else:
        return None

def getUsersCollectionName(object):
    rtn = getUsersCollection(object)
    if rtn != None:
        return rtn.name
    else:
        return ""

def getCollection_old(col_name):
    if col_name=='MAIN':
        return bpy.context.view_layer.active_layer_collection
    if (col_name in bpy.data.collections) and (col_name in bpy.context.scene.collection.children.keys()):
        return bpy.data.collections.get(col_name)
    if col_name not in bpy.data.collections :
        bpy.data.collections.new(name=col_name)
    if col_name not in bpy.context.scene.collection.children.keys():
        col = bpy.data.collections.get(col_name)
        bpy.context.scene.collection.children.link(col)
    return bpy.data.collections.get(col_name)

def decideCurrentCollection(kind2):
    global _CURRENT_COL
    global _CURRENT_COL_FOR_SHADERS
    for i in range(100):
        col_name = ('DAZ_'+kind2 + '_' + str(i))
        if (col_name in bpy.data.collections)==False:
            orderCollection(col_name)
            _CURRENT_COL = col_name
            _CURRENT_COL_FOR_SHADERS = col_name
            setActiveCollectionByName(_CURRENT_COL)
            break
        else:
            objs = colobjs(col_name)
            if objs is None or len(objs)==0:
                _CURRENT_COL = col_name
                _CURRENT_COL_FOR_SHADERS = col_name
                orderCollection(_CURRENT_COL)
                setActiveCollectionByName(_CURRENT_COL)
                break

def deleteEmptyDazCollection():
    orderCollection('DAZ_ROOT')
    col_root = getLayerCollection(bpy.context.view_layer.layer_collection,'DAZ_ROOT')
    for c in col_root.children:
        objs = colobjs(c.name)
        if objs is None:
            bpy.data.collections.remove(bpy.data.collections.get(c.name))

def orderCollection(cur_col_name):
    col_names = ['DAZ_ROOT', 'DAZ_FIG_\d{1,2}',  'DAZ_ENV_\d{1,2}','DAZ_HIDE','DAZ_PUB']
    last_col = None
    rtn = None
    for i, col_name in enumerate(col_names):
        if i ==1 or i==2:
            rep = re.compile(col_name)
            if not rep.search(cur_col_name):
                continue
            col_name = cur_col_name
        if (col_name in bpy.data.collections) == False:
            bpy.data.collections.new(name=col_name)
        col = bpy.data.collections.get(col_name)
        if i == 0:
            if col_name not in bpy.context.scene.collection.children.keys():
                bpy.context.scene.collection.children.link(col)
        else:
            if i>1:
                last_col = bpy.data.collections.get(col_names[0])
            if last_col is not None:
                prtname = get_parent_name(col_name)
                if prtname is not None and prtname !=last_col.name:
                    bpy.data.collections.get(prtname).children.unlink(col)
                if col_name not in last_col.children.keys():
                    last_col.children.link(col)
        if i==3:
            col.hide_render = True
            col.hide_viewport = True
        last_col = col
        if col_name == cur_col_name:
            rtn = col
    if rtn is None:
        return last_col
    else:
        return rtn

def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)

def to_other_collection_byname(objnames,dist_col_name,src_col_name):
    if dist_col_name==src_col_name:
        return
    objs  = []
    for objname in objnames:
        obj = allobjs().get(objname)
        if obj is not None:
            objs.append(obj)
    to_other_collection(objs,dist_col_name,src_col_name)

def to_other_collection(objs,dist_col_name,src_col_name):
    if objs is None:
        return
    dst_col = bpy.data.collections.get(dist_col_name)
    src_col = bpy.data.collections.get(src_col_name)
    if dst_col==src_col:
        return
    if dst_col is None:
        return
    for obj in objs:
        if obj is None:
            continue
        if src_col is not None and (obj.name in bpy.data.collections.get(src_col_name).objects):
            bpy.data.collections.get(src_col_name).objects.unlink(obj)
        if obj.name not in dst_col.objects:
            dst_col.objects.link(obj)

coll_parents={}

def get_parent_name(col_name):
    global coll_parents
    if len(coll_parents)==0:
        for coll in traverse_tree(bpy.context.scene.collection):
            for c in coll.children.keys():
                coll_parents.setdefault(c, coll.name)
    print("coll_parents.length()=",len(coll_parents))
    return coll_parents.get(col_name)

def getActiveCollection():
    return bpy.context.view_layer.active_layer_collection

def toHome():
    setActiveCollectionByName(cur_col_name())

def setActiveCollectionByName(col_name):
    if col_name=='MAIN':
        Versions.to_main_layer_active()
    else:
        col = getLayerCollection(bpy.context.view_layer.layer_collection,col_name)
        if col is not None:
            bpy.context.view_layer.active_layer_collection = col

def active_object_to_current_collection():
    col = getUsersCollection(Versions.get_active_object())
    if col is not None:
        setCurrentCollection(col)

def getLayerCollection(layerColl, schName):
    found = None
    if (layerColl.name == schName):
        return layerColl
    for layer in layerColl.children:
        found = getLayerCollection(layer, schName)
        if found:
            return found

def getMatName(src_name):
    key = src_name
    find = False
    for i in range(100):
        for mat in bpy.data.materials:
            if mat.name == src_name:
                find = True
        if find==False:
            break
    
