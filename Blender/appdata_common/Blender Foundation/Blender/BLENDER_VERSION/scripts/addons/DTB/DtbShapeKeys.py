import bpy
import sys
import os
sys.path.append(os.path.dirname(__file__))
from . import Global
from . import DataBase
from . import Versions
from . import Util
class DtbShapeKeys:
    root = Global.getRootPath()
    flg_rigify = False

    def __init__(self, flg_rigify):
        self.flg_rigify = flg_rigify

    def makeDrives(self,db):
        for dobj in Util.myccobjs():
            if Global.isRiggedObject(dobj):
                self.makeDrive(dobj,db)

    def delete001_sk(self):
        Global.setOpsMode('OBJECT')
        obj = Global.getBody()
        Versions.select(obj, True)
        Versions.active_object(obj)
        aobj = bpy.context.active_object
        sp =  aobj.data.shape_keys
        if sp is not None:
            max = len(sp.key_blocks)
            i = 0
            for notouch in range(max):
                aobj.active_shape_key_index = i
                if aobj.active_shape_key.name.endswith(".001"):
                    bpy.ops.object.shape_key_remove(all=False)
                    max = max-1
                else:
                    i = i + 1

    def get_rigify_bone_name(self,bname):
        rtn = ""
        db = DataBase.DB()
        for trf in db.toRigify:
            if trf[0] < 2:
                continue
            ops_trf = 'r' + trf[1][1:]
            bool_ops = ops_trf==bname
            if trf[1]==bname or bool_ops:
                rtn = trf[2]
                if bool_ops:
                    rtn = rtn.replace(".L",".R")
                break
        if rtn=='' and 'Toe' in bname and len(bname)>4:
            rtn = bname
        elif rtn.startswith('f_') or rtn.startswith('thumb.'):
            pass
        elif ('DEF-' + rtn) in Global.getRgfyBones():
            rtn = 'DEF-' + rtn
        swap = [['DEF-shoulder.','shoulder.'],['DEF-pelvis.L','tweak_spine']]
        for sp in swap:
            if sp[0] in rtn:
                rtn = rtn.replace(sp[0],sp[1])
        return rtn

    def makeOneDriver(self,db):
        cur = db.tbl_mdrive
        aobj = Global.getBody()
        if Global.getIsG3():
            cur.extend(db.tbl_mdrive_g3)
        for row in cur:
            sk_name =aobj.active_shape_key.name
            if row[0] in sk_name and sk_name.endswith(".001") == False:
                dvr = aobj.data.shape_keys.key_blocks[sk_name].driver_add('value')
                dvr.driver.type = 'SCRIPTED'
                var = dvr.driver.variables.new()
                Versions.set_debug_info(dvr)
                self.setDriverVariables(var, 'val', Global.getAmtr(), row[1], row[2])
                exp = row[3]
                dvr.driver.expression = exp
                break

    def makeDrive(self,dobj,db):
        mesh_name = dobj.data.name
        Versions.active_object(dobj)
        aobj = bpy.context.active_object
        if bpy.data.meshes[mesh_name].shape_keys is None:
            return
        ridx = 0
        cur = db.tbl_mdrive
        if Global.getIsG3():
            cur.extend(db.tbl_mdrive_g3)
        while ridx  < len(cur):
            max = len(bpy.data.meshes[mesh_name].shape_keys.key_blocks)
            row = cur[ridx]
            for i in range(max):
                if aobj is None:
                    continue
                aobj.active_shape_key_index = i
                if aobj.active_shape_key is None:
                    continue
                sk_name = aobj.active_shape_key.name
                if row[0] in sk_name and sk_name.endswith(".001")==False:
                    dvr = aobj.data.shape_keys.key_blocks[sk_name].driver_add('value')
                    dvr.driver.type = 'SCRIPTED'
                    var = dvr.driver.variables.new()
                    Versions.set_debug_info(dvr)
                    if self.flg_rigify:
                        target_bone =  self.get_rigify_bone_name(row[1])
                        xyz = self.toRgfyXyz(row[2],target_bone)
                        self.setDriverVariables(var, 'val', Global.getRgfy(), target_bone, xyz)
                        exp = self.getRgfyExp(row[3],target_bone,row[0])
                        if ridx < len(cur) - 1 and cur[ridx + 1][0] in sk_name:
                            row2 = cur[ridx + 1]
                            target_bone2 = self.get_rigify_bone_name(row2[1])
                            var2 = dvr.driver.variables.new()
                            xyz2 = self.toRgfyXyz(row2[2],target_bone2)
                            self.setDriverVariables(var2, 'val2', Global.getRgfy(), target_bone2, xyz2)
                            exp2 = self.getRgfyExp(row2[3], target_bone2, row2[0])
                            exp += '+' + exp2
                            ridx = ridx + 1
                        dvr.driver.expression = exp
                    else:
                        self.setDriverVariables(var, 'val', Global.getAmtr(), row[1], row[2])
                        exp = row[3]
                        if ridx < len(cur)-1 and cur[ridx+1][0] in sk_name:
                            row2 = cur[ridx+1]
                            var2 = dvr.driver.variables.new()
                            self.setDriverVariables(var2, 'val2', Global.getAmtr(), row2[1], row2[2])
                            exp += '+' + row2[3]
                            ridx = ridx + 1
                        dvr.driver.expression = exp
                    break
            ridx = ridx + 1

    def toRgfyXyz(self,xyz,bname):
        zy_switch = ['chest','hips']
        for zy in zy_switch:
            if bname==zy:
                if xyz==1:
                    return 2
                elif xyz==2:
                    return 1
        return xyz

    def getRgfyExp(self,exp,target_bone,sk_name):
        exp = exp.replace(' ', '')
        exp_kind = [
            ['upper_arm', '', '' ],
            ['forearm', '', ''],
            ['hand', '', ''],
            ['hip','',''],
            ['tweak_spine','',''],
            ['toe','',''],
            ['chest','','Side'],
            ['DEF-spine','spine','pJCMAbdomenFwd_35']
        ]
        for ek in exp_kind:
            if(ek[0] in target_bone) and target_bone.endswith(ek[1]) and (ek[2] in sk_name):
                exp = self.invert_exp(exp)
                break
        return exp

    def setDriverVariables(self,var,varname,target_id,bone_target,xyz):
        var.name = varname
        var.type = 'TRANSFORMS'
        target = var.targets[0]
        target.id = target_id
        target.bone_target = bone_target
        target.transform_space = 'LOCAL_SPACE'
        if xyz == 0:
            target.transform_type = 'ROT_X'
        elif xyz == 1:
            target.transform_type = 'ROT_Y'
        elif xyz == 2:
            target.transform_type = 'ROT_Z'

    def invert_exp(self,exp):
        flg_ToMs =  ('val-' in exp) or ('*-' in exp)==False#In case of Plus
        if flg_ToMs:
            if ('val-' in exp):
                exp = exp.replace("val-", "val+")
            if ('*-' in exp)==False:
                exp = exp.replace("*", "*-")
        else:
            if ('val+' in exp):
                exp = exp.replace("val+", "val-")
            if ('*-' in exp):
                    exp = exp.replace("*-", "*")
        return exp

    def toHeadMorphMs(self,db):
        dobj = Global.getBody()
        Versions.select(dobj, True)
        cur = db.tbl_facems
        Versions.active_object(dobj)
        for mesh in bpy.data.meshes:
            if mesh.name == dobj.data.name:
                if mesh.shape_keys is None:
                    continue
                for kb in mesh.shape_keys.key_blocks:
                    for row in cur:
                        if kb.name.lower()==row.lower():
                            kb.slider_min =-1

    def add_sk(self,dobj):
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        for mesh in bpy.data.meshes:
            if mesh.name == dobj.data.name:
                bpy.ops.object.shape_key_add(from_mix = False)
                kblen = len(mesh.shape_keys.key_blocks)
                bpy.context.active_object.active_shape_key_index = kblen-1

    def toshortkey(self):
        for k in bpy.data.shape_keys:
            for b in k.key_blocks:
                a = b.name.find("__pJCM");
                if a > 2:
                    bpy.data.shape_keys[k.name].key_blocks[b.name].name = b.name[a:]
                keys = [Global.get_Amtr_name(),'head','_','_','eCTRL','PHM']
                for sidx,s in enumerate(keys):
                    if b.name.startswith(s):
                        wk = b.name[len(s):]
                        if sidx==0:
                            wk = "D"+ wk
                        elif sidx==4:
                            wk = "H-" + wk
                        bpy.data.shape_keys[k.name].key_blocks[b.name].name = wk

    def deleteExtraSkey(self):
        for k in bpy.data.shape_keys:
            dels = []
            for aidx, a in enumerate(k.key_blocks):
                if ('eCTRL' in a.name) and a.name.startswith("D"):
                    for bidx, b in enumerate(k.key_blocks):
                        if aidx == bidx:
                            continue
                        if b.name.startswith("H-"):
                            astart = a.name.find('eCTRL')
                            if a.name[astart + 5:] == b.name[2:]:
                                if not (aidx in dels):
                                    dels.append(aidx)
        dels.sort()
        ms = 0
        for d in dels:
            Global.getBody().active_shape_key_index = d - ms
            bpy.ops.object.shape_key_remove(all=False)
            ms += 1

    def deleteEyelashes(self):
        Global.setOpsMode('OBJECT')
        dobj = Global.getBody()
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        sp =  dobj.data.shape_keys
        eylsname = Global.get_KeepEyls_name()
        if eylsname.endswith(".Shape"):
            eylsname = eylsname[:len(eylsname)-6]
        if sp is not None and eylsname!="":
            max = len(sp.key_blocks)
            i = 0
            for notouch in range(max):
                dobj.active_shape_key_index = i
                if  (eylsname in dobj.active_shape_key.name):
                    bpy.ops.object.shape_key_remove(all=False)
                    max = max-1
                else:
                    i = i + 1

    def delete_old_vgroup(self,db):
        dobj = Global.getBody()
        for fv in db.fvgroup:
            for vg in dobj.vertex_groups:
                if vg.name == fv:
                    if vg.name in dobj.vertex_groups:
                        dobj.vertex_groups.remove(vg)
                        break

    def swap_fvgroup(self,db):
        dobj = Global.getBody()
        for z in range(2):
            for _fs in db.fvgroup_swap:
                fs = [_fs[0],_fs[1]]
                if z==1:
                    if fs[1].startswith("l") and fs[1].startswith("lower")==False:
                        fs[1] = "r" + fs[1][1:]
                        fs[0] = fs[0].replace(".L",".R")
                    else:
                        continue
                vgs = dobj.vertex_groups
                for vg in vgs:
                    if vg.name==fs[1]:
                        vg.name = fs[0]

    def delete_oneobj_sk_from_command(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        aobj = Versions.get_active_object()
        if aobj is None:
            return
        self.delete_oneobj_sk(0,100, 0,aobj, wm)
        wm.progress_end()

    def delete_oneobj_sk(self,min,onesa,oidx,obj,wm):
        v = min + onesa * oidx
        wm.progress_update(int(v))
        Versions.active_object(obj)
        if obj.data.shape_keys is None:
            return
        kbs = obj.data.shape_keys.key_blocks
        root_kb = [d.co[0] for didx,d in enumerate(kbs[0].data) if didx%4==0]
        max = len(kbs)
        z0_same_idx_ary = []
        dels = []
        for z in range(2):
            if z == 0:
                decisa = onesa / (2.0 * max)
                old_dv = v
                for i in range(1, max):
                    dv = int(v + decisa * i)
                    if old_dv != dv:
                        wm.progress_update(dv)
                    kb = kbs[i]
                    if root_kb == [d.co[0] for didx,d in enumerate(kb.data) if didx%4==0 ]:
                        z0_same_idx_ary.append(i)
                    old_dv = dv
            else:
                decisa = onesa / (2.0 * len(z0_same_idx_ary))
                old_dv = v
                if z0_same_idx_ary == []:
                    break
                root_kb_yz = [[d.co[1], d.co[2]] for didx,d in enumerate(kbs[0].data) if didx%4==0]
                for i in z0_same_idx_ary:
                    dv = int(v + onesa / 2.0 + decisa * i)
                    if old_dv != dv:
                        wm.progress_update(dv)
                    kb = kbs[i]
                    if root_kb_yz == [[d.co[1], d.co[2]] for didx,d in enumerate(kb.data) if didx%4==0]:
                        dels.append(i)
                    old_dv = dv
            dels.sort(reverse=True)
            for d in dels:
                Versions.get_active_object().active_shape_key_index = d
                bpy.ops.object.shape_key_remove(all=False)

    def delete_all_extra_sk(self, min, max, wm):
        objs = []
        for obj in Util.myccobjs():
            if obj.type=='MESH':
                objs.append(obj)
        allsa = max-min
        onesa = allsa/len(objs)
        for oidx,obj in enumerate(objs):
            self.delete_oneobj_sk(min,onesa,oidx,obj,wm)
