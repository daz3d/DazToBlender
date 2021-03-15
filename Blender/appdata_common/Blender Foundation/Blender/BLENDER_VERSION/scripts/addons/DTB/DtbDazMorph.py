import sys
import os
sys.path.append(os.path.dirname(__file__))
import bpy
from . import Versions
from . import Global
import datetime

class DtbDazMorph():
    KWORD = 'to_daz_morph'
    basic_faces = []
    human_max = 0
    now_edit_object_name = ""
    now_edit_object = None
    flg_human = False
    
    def __init__(self):
        self.basic_faces = []
        self.human_max = 0
        self.now_edit_object = None
        self.now_edit_object_name = ""
        self.flg_human = False

    def get_moment(self):
        return datetime.datetime.today().strftime("%Y%m%d_%H%M%S")[2:]

    def make_it_old(self, kb):
        kb.name = kb.name + "_end_" + self.get_moment()

    def select_to_daz_morph(self, is_new_morph):
        aobj = Versions.get_active_object()
        if aobj is None:
            return
        self.now_edit_object = aobj
        mesh = aobj.data
        self.now_edit_object_name = aobj.name
        find = False
        if mesh.shape_keys is None:
            self.add_sk()
        sk_idx = aobj.active_shape_key_index
        kblen = len(mesh.shape_keys.key_blocks)
        if kblen > sk_idx:
            kb = mesh.shape_keys.key_blocks[sk_idx]
            if kb.name == self.KWORD:

                if is_new_morph:
                    self.make_it_old(kb)
                else:
                    kb.value = 1.0
                    find = True
        if find == False:
            for kidx, kb in enumerate(mesh.shape_keys.key_blocks):
                if (self.KWORD == kb.name):
                    if is_new_morph:
                        self.make_it_old(kb)
                    else:
                        aobj.active_shape_key_index = kidx
                        find = True
                        kb.value = 1.0
                    break
        if find == False:
            self.make_to_daz_morph()

    def make_to_daz_morph(self):
        self.add_sk()
        mesh = self.now_edit_object.data
        kb = mesh.shape_keys.key_blocks[-1]
        kb.name = self.KWORD
        kb.value = 1.0
        kblen = len(mesh.shape_keys.key_blocks)
        if kblen > 0:
            bpy.context.active_object.active_shape_key_index = kblen - 1

    def add_sk(self):
        mesh = self.now_edit_object.data
        bpy.ops.object.shape_key_add(from_mix=False)
        if mesh.shape_keys != None:
            kblen = len(mesh.shape_keys.key_blocks)
            if kblen > 0:
                bpy.context.active_object.active_shape_key_index = kblen - 1
##########export################################################################################
    def top_exsport(self):
        dobj = Versions.get_active_object()
        if Global.isRiggedObject(dobj)==False:
            return
        self.basicfaces()
        objname = dobj.name
        if objname.endswith(".Shape"):
            objname =objname[0:len(objname)-6]
        path = os.path.join(Global.getRootPath(), self.KWORD, objname + "_" + self.get_moment())
        root = Global.getRootPath() + self.KWORD
        if (os.path.exists(path) and os.path.isdir(path))==False:
            os.makedirs(path)
        flg_ok = self.exsport_1morph(dobj.name,path)
        if flg_ok:
            import subprocess
            if os.name == 'nt':
                subprocess.Popen(['explorer', root])
            else:
                subprocess.call(["open", "-R",root])
            return True
        else:
            return False

    def exsport_1morph(self, objname, path):
        self.flg_human = objname == Global.get_Body_name()
        dobj = bpy.data.objects.get(objname)
        mesh = dobj.data
        flg_stop = True
        if mesh.shape_keys is None:
            if self.flg_human:
                self.add_sk()
                flg_stop = False
            else:
                return
        elif self.flg_human == False:
            for kb in mesh.shape_keys.key_blocks:
                if kb.name.startswith(self.KWORD):
                    flg_stop = False
                    break
        else:
            flg_stop = False
        if flg_stop:
            return
        flg_executed = False
        for kidx, kb in enumerate(mesh.shape_keys.key_blocks):
            if (kb.name.startswith(self.KWORD)):
                path_w = os.path.join(path, kb.name + ".obj")
                with open(path_w, mode='w') as f:
                    for idx, v in enumerate(kb.data):
                        if self.flg_human and idx >= self.human_max:
                            break
                        sc = 1.0
                        f.write(
                            "v " + str(v.co[0] / sc) + " " + str(v.co[2] / sc) + " " + str(0 - v.co[1] / sc) + "\n")

                    for lcnt, l in enumerate(self.basicfaces()):
                        f.write(l)
                    flg_executed = True
        if flg_executed == False and self.flg_human:
            path_w = os.path.join(path, "Basic.obj")
            with open(path_w, mode='w') as f:
                for v in mesh.vertices:
                    if v.index >= self.human_max:
                        break
                    sc = 1.0
                    f.write("v " + str(v.co[0] / sc) + " " + str(v.co[2] / sc) + " " + str(0 - v.co[1] / sc) + "\n")
                for lcnt, l in enumerate(self.basicfaces()):
                    f.write(l)
            flg_executed = True
        return flg_executed

    def before_execute(self,isbody):
        self.basic_faces = []
        if isbody:
            max3 = Global.getMyMax3()
            now_lev = Global.getSubdivLevel()
            self.human_max = max3[now_lev]
        self.basicfaces()

    def basicfaces(self):
        if len(self.basic_faces)==0:
            if self.flg_human:
                mesh = Global.getBody().data
            else:
                mesh = Versions.get_active_object().data
            for pl in mesh.polygons:
                line = 'f'
                for vi in pl.vertices:
                    if self.flg_human and vi > self.human_max:
                        line = "break"
                        break
                    line = line + ' ' + str(vi+1)
                if line == "break":
                    continue
                self.basic_faces.append(line+"\n")
        return self.basic_faces