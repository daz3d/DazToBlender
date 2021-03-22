import os
import sys
import math
import json
import bpy

from . import Util
from . import Versions
from . import DataBase
from . import Global

sys.path.append(os.path.dirname(__file__))


class DtbShapeKeys:
    root = Global.getRootPath()
    flg_rigify = False
    key_block_prefix = "Genesis8_1Female__"

    def __init__(self, flg_rigify):
        self.flg_rigify = flg_rigify

    def create_drivers(self):
        Global.setOpsMode('OBJECT')
        body_obj = Global.getBody()

        shape_keys = body_obj.data.shape_keys

    def make_drivers(self):
        body_obj = Global.getBody()
        if Global.isRiggedObject(body_obj):
            self.make_driver(body_obj)
        return

        for dobj in Util.myccobjs():
            if Global.isRiggedObject(dobj):
                self.make_driver(dobj)

    def delete001_sk(self):
        Global.setOpsMode('OBJECT')
        obj = Global.getBody()
        Versions.select(obj, True)
        Versions.active_object(obj)
        aobj = bpy.context.active_object
        sp = aobj.data.shape_keys
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

    def get_rigify_bone_name(self, bname):
        rtn = ""
        db = DataBase.DB()
        for trf in db.toRigify:
            if trf[0] < 2:
                continue
            ops_trf = 'r' + trf[1][1:]
            bool_ops = ops_trf == bname
            if trf[1] == bname or bool_ops:
                rtn = trf[2]
                if bool_ops:
                    rtn = rtn.replace(".L", ".R")
                break
        if rtn == '' and 'Toe' in bname and len(bname) > 4:
            rtn = bname
        elif rtn.startswith('f_') or rtn.startswith('thumb.'):
            pass
        elif ('DEF-' + rtn) in Global.getRgfyBones():
            rtn = 'DEF-' + rtn
        swap = [['DEF-shoulder.', 'shoulder.'],
                ['DEF-pelvis.L', 'tweak_spine']]
        for sp in swap:
            if sp[0] in rtn:
                rtn = rtn.replace(sp[0], sp[1])
        return rtn

    def makeOneDriver(self, db):
        cur = db.tbl_mdrive
        aobj = Global.getBody()
        if Global.getIsG3():
            cur.extend(db.tbl_mdrive_g3)
        for row in cur:
            sk_name = aobj.active_shape_key.name
            if row[0] in sk_name and sk_name.endswith(".001") == False:
                dvr = aobj.data.shape_keys.key_blocks[sk_name].driver_add(
                    'value')
                dvr.driver.type = 'SCRIPTED'
                var = dvr.driver.variables.new()
                Versions.set_debug_info(dvr)
                self.setDriverVariables(
                    var, 'val', Global.getAmtr(), row[1], row[2])
                exp = row[3]
                dvr.driver.expression = exp
                break

    def get_transform_type(self, morph_link):
        bone_name = morph_link["Bone"]
        property_name = morph_link["Property"]

        bone_limits = DataBase.get_bone_limits_dict()
        bone_order = bone_limits[bone_name][1]

        if bone_order == 'XYZ':
            if "XRotate" in property_name:
                return 'ROT_Z'
            elif "YRotate" in property_name:
                return 'ROT_X'
            elif "ZRotate" in property_name:
                return 'ROT_Y'
        elif bone_order == 'XZY':
            if "XRotate" in property_name:
                return 'ROT_Y'
            elif "YRotate" in property_name:
                return 'ROT_X'
            elif "ZRotate" in property_name:
                return 'ROT_Z'
        elif bone_order == 'YZX':
            if "XRotate" in property_name:
                return 'ROT_X'
            elif "YRotate" in property_name:
                return 'ROT_Y'
            elif "ZRotate" in property_name:
                return 'ROT_Z'
        elif bone_order == 'ZXY':
            if "XRotate" in property_name:
                return 'ROT_Y'
            elif "YRotate" in property_name:
                return 'ROT_Z'
            elif "ZRotate" in property_name:
                return 'ROT_X'
        elif bone_order == 'ZYX':
            if "XRotate" in property_name:
                return 'ROT_X'
            elif "YRotate" in property_name:
                return 'ROT_Z'
            elif "ZRotate" in property_name:
                return 'ROT_Y'

        return 'LOC_X'

    def get_var_correction(self, var_name, morph_link):
        # Check and multiply inverse correction factor to switch the property
        # sign based on the bone pointed direction
        correction_factor = 1
        bone_name = morph_link["Bone"]
        property_name = morph_link["Property"]

        # Return when controller is not a Bone
        if bone_name == "None":
            return var_name

        bone_limits = DataBase.get_bone_limits_dict()
        bone_order = bone_limits[bone_name][1]
        
        prefix = bone_name[0:1]
        post_prefix = bone_name[1:2]
        is_right = False
        if prefix == "r" and post_prefix.isupper():
            is_right = True
        is_down = False
        if bone_name in ["hip", "pelvis", "lThighBend", "rThighBend", "lThighTwist", "rThighTwist", "lShin", "rShin"]:
            is_down = True

        if bone_order == 'XYZ':
            if "XRotate" in property_name:
                correction_factor = 1
            elif "YRotate" in property_name and is_right:
                correction_factor = -1
            elif "ZRotate" in property_name and is_right:
                correction_factor = -1
        elif bone_order == 'XZY':
            if "XRotate" in property_name:
                correction_factor = -1
            elif "YRotate" in property_name and is_right:
                correction_factor = -1
            elif "ZRotate" in property_name and is_right:
                correction_factor = -1
        elif bone_order == 'YZX':
            if "XRotate" in property_name:
                correction_factor = 1
            elif "YRotate" in property_name and is_down:
                correction_factor = -1
            elif "ZRotate" in property_name and is_down:
                correction_factor = -1
        elif bone_order == 'ZXY':
            if "XRotate" in property_name:
                correction_factor = 1
            elif "YRotate" in property_name:
                correction_factor = 1
            elif "ZRotate" in property_name:
                correction_factor = 1
        elif bone_order == 'ZYX':
            if "XRotate" in property_name:
                correction_factor = -1
            elif "YRotate" in property_name:
                correction_factor = 1
            elif "ZRotate" in property_name:
                correction_factor = 1

        # Include radians to degree convesion factor
        correction_factor = math.degrees(correction_factor)

        var_name = "(" + var_name + "*" + str(correction_factor) + ")"
        return var_name

    def get_target_expression(self, var_name, morph_link, driver):
        link_type = morph_link["Type"]
        scalar = str(morph_link["Scalar"])
        addend = str(morph_link["Addend"])

        var_name = self.get_var_correction(var_name, morph_link)

        if link_type == 0:
            # ERCDeltaAdd
            return "(" + var_name + "*" + scalar + " + " + addend + ")"
        elif link_type == 1:
            # ERCDivideInto
            driver.use_self = True
            return "(" + var_name + "/self.value + " + addend + ")"
        elif link_type == 2:
            # ERCDivideBy
            driver.use_self = True
            return "(" + "self.value/" + var_name + " + " + addend + ")"
        elif link_type == 3:
            # ERCMultiply
            driver.use_self = True
            return "(" + var_name + "*self.value + " + addend + ")"
        elif link_type == 4:
            # ERCSubtract
            driver.use_self = True
            return "(" + "self.value - " + var_name + " + " + addend + ")"
        elif link_type == 5:
            # ERCAdd
            driver.use_self = True
            return "(" + "self.value + " + var_name + " + " + addend + ")"
        elif link_type == 6:
            # ERCKeyed
            # TODO: Figure out a way to represent in Blender.
            return "(" + var_name + ")"
            
        return var_name
    
    def get_morph_link_control_type(self, morph_link):
        if morph_link["Type"] == 6:
            # skip links that are 'ERCKeyed' for now
            return 'CONTROL_BY_NONE'
        elif morph_link["Bone"] == "None":
            return 'CONTROL_BY_MORPH'
        else:
            return 'CONTROL_BY_BONE'
    
    def make_bone_var(self, link_index, morph_link, driver):
        link_var = driver.variables.new()
        link_var.name = "var" + str(link_index)
        link_var.type = 'TRANSFORMS'
        
        target = link_var.targets[0]
        target.id = Global.getAmtr()
        target.bone_target = morph_link["Bone"]
        target.transform_space = 'LOCAL_SPACE'
        target.transform_type = self.get_transform_type(morph_link)
        
        return link_var

    def make_morph_var(self, link_index, morph_link, driver, shape_key):
        link_var = driver.variables.new()
        link_var.name = "var" + str(link_index)
        link_var.type = 'SINGLE_PROP'
        
        target = link_var.targets[0]
        target.id_type = 'KEY'
        target.id = shape_key
        block_id = self.key_block_prefix + morph_link["Property"]
        rna_data_path = "key_blocks[\"" + block_id + "\"].value"
        target.data_path = rna_data_path

        return link_var

    def property_in_shape_keys(self, morph_link, shape_key_blocks):
        property_name = morph_link["Property"]
        is_found = False
        for key_block in shape_key_blocks:
            if property_name == key_block.name[len(self.key_block_prefix): ]:
                is_found = True
                break
        return is_found
    
    def make_driver(self, dobj):
        shape_key = dobj.data.shape_keys
        if shape_key is None:
            return
        
        # Read all the morph links from the DTU
        for file in os.listdir(Global.getHomeTown()):
            if file.endswith(".dtu"):
                input_file = open(Global.getHomeTown() + Global.getFileSp() + file)
        dtu_content = input_file.read()
        morph_links_list = json.loads(dtu_content)["MorphLinks"]

        # Create drivers for shape key blocks
        shape_key_blocks = shape_key.key_blocks
        for key_block in shape_key_blocks:
            key_name = key_block.name[len(self.key_block_prefix): ]
            if key_name not in morph_links_list:
                continue

            driver = key_block.driver_add("value").driver
            driver.type = 'SCRIPTED'

            morph_links = morph_links_list[key_name]
            expression = ""
            var_count = 0
            for link_index, morph_link in enumerate(morph_links):
                control_type = self.get_morph_link_control_type(morph_link)
                if control_type == 'CONTROL_BY_NONE':
                    continue
                if control_type == 'CONTROL_BY_MORPH':
                    is_found = self.property_in_shape_keys(morph_link, shape_key_blocks)
                    if not is_found:
                        # If the controller morph is not in listed shape keys
                        continue
                    var = self.make_morph_var(link_index, morph_link, driver, shape_key)
                    var_count += 1
                elif control_type == 'CONTROL_BY_BONE':
                    var = self.make_bone_var(link_index, morph_link, driver)
                    var_count += 1

                expression += self.get_target_expression(var.name, morph_link, driver) + "+"
            
            # Delete the driver and continue if there are no variables
            if var_count == 0:
                key_block.driver_remove("value")
                continue
            
            if expression.endswith("+"):
                expression = expression[:-1]
            driver.expression = expression

        # TODO: Create drivers for bone trasnforms

    def toRgfyXyz(self, xyz, bname):
        zy_switch = ['chest', 'hips']
        for zy in zy_switch:
            if bname == zy:
                if xyz == 1:
                    return 2
                elif xyz == 2:
                    return 1
        return xyz

    def getRgfyExp(self, exp, target_bone, sk_name):
        exp = exp.replace(' ', '')
        exp_kind = [
            ['upper_arm', '', ''],
            ['forearm', '', ''],
            ['hand', '', ''],
            ['hip', '', ''],
            ['tweak_spine', '', ''],
            ['toe', '', ''],
            ['chest', '', 'Side'],
            ['DEF-spine', 'spine', 'pJCMAbdomenFwd_35']
        ]
        for ek in exp_kind:
            if(ek[0] in target_bone) and target_bone.endswith(ek[1]) and (ek[2] in sk_name):
                exp = self.invert_exp(exp)
                break
        return exp

    def setDriverVariables(self, var, varname, target_id, bone_target, xyz):
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

    def invert_exp(self, exp):
        flg_ToMs = ('val-' in exp) or ('*-' in exp) == False  # In case of Plus
        if flg_ToMs:
            if ('val-' in exp):
                exp = exp.replace("val-", "val+")
            if ('*-' in exp) == False:
                exp = exp.replace("*", "*-")
        else:
            if ('val+' in exp):
                exp = exp.replace("val+", "val-")
            if ('*-' in exp):
                exp = exp.replace("*-", "*")
        return exp

    def toHeadMorphMs(self, db):
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
                        if kb.name.lower() == row.lower():
                            kb.slider_min = -1

    def add_sk(self, dobj):
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        for mesh in bpy.data.meshes:
            if mesh.name == dobj.data.name:
                bpy.ops.object.shape_key_add(from_mix=False)
                kblen = len(mesh.shape_keys.key_blocks)
                bpy.context.active_object.active_shape_key_index = kblen-1

    def toshortkey(self):
        keys = [
                    Global.get_Amtr_name(),
                    'head',
                    '_',
                    '_',
                    'eCTRL',
                    'PHM'
                ]
        for shape_key in bpy.data.shape_keys:
            for key_block in shape_key.key_blocks:
                continue
                # Strip pJCM suffix
                suff_idx = key_block.name.find("__pJCM")
                if suff_idx > 2:
                    key_block.name = key_block.name[suff_idx:]

                for sidx, s in enumerate(keys):
                    if key_block.name.startswith(s):
                        wk = key_block.name[len(s):]
                        if sidx == 0:
                            wk = "D" + wk
                        elif sidx == 4:
                            wk = "H-" + wk
                        key_block.name = wk

    def deleteExtraSkey(self):
        dels = []
        for k in bpy.data.shape_keys:
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
        body_obj = Global.getBody()
        Versions.select(body_obj, True)
        Versions.active_object(body_obj)

        eyls_name = Global.get_KeepEyls_name()
        if eyls_name.endswith(".Shape"):
            eyls_name = eyls_name[:len(eyls_name)-6]

        shape_keys = body_obj.data.shape_keys
        if shape_keys is not None and eyls_name != "":
            max = len(shape_keys.key_blocks)
            i = 0
            for notouch in range(max):
                body_obj.active_shape_key_index = i
                if (eyls_name in body_obj.active_shape_key.name):
                    bpy.ops.object.shape_key_remove(all=False)
                    max = max-1
                else:
                    i = i + 1

    def delete_old_vgroup(self, db):
        dobj = Global.getBody()
        for fv in db.fvgroup:
            for vg in dobj.vertex_groups:
                if vg.name == fv:
                    if vg.name in dobj.vertex_groups:
                        dobj.vertex_groups.remove(vg)
                        break

    def swap_fvgroup(self, db):
        dobj = Global.getBody()
        for z in range(2):
            for _fs in db.fvgroup_swap:
                fs = [_fs[0], _fs[1]]
                if z == 1:
                    if fs[1].startswith("l") and fs[1].startswith("lower") == False:
                        fs[1] = "r" + fs[1][1:]
                        fs[0] = fs[0].replace(".L", ".R")
                    else:
                        continue
                vgs = dobj.vertex_groups
                for vg in vgs:
                    if vg.name == fs[1]:
                        vg.name = fs[0]

    def delete_oneobj_sk_from_command(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        aobj = Versions.get_active_object()
        if aobj is None:
            return
        self.delete_oneobj_sk(0, 100, 0, aobj, wm)
        wm.progress_end()

    def delete_oneobj_sk(self, min, onesa, oidx, obj, wm):
        v = min + onesa * oidx
        wm.progress_update(int(v))
        Versions.active_object(obj)
        if obj.data.shape_keys is None:
            return
        kbs = obj.data.shape_keys.key_blocks
        root_kb = [d.co[0]
                   for didx, d in enumerate(kbs[0].data) if didx % 4 == 0]
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
                    if root_kb == [d.co[0] for didx, d in enumerate(kb.data) if didx % 4 == 0]:
                        z0_same_idx_ary.append(i)
                    old_dv = dv
            else:
                if z0_same_idx_ary == []:
                    break
                decisa = onesa / (2.0 * len(z0_same_idx_ary))
                old_dv = v
                root_kb_yz = [[d.co[1], d.co[2]]
                              for didx, d in enumerate(kbs[0].data) if didx % 4 == 0]
                for i in z0_same_idx_ary:
                    dv = int(v + onesa / 2.0 + decisa * i)
                    if old_dv != dv:
                        wm.progress_update(dv)
                    kb = kbs[i]
                    if root_kb_yz == [[d.co[1], d.co[2]] for didx, d in enumerate(kb.data) if didx % 4 == 0]:
                        dels.append(i)
                    old_dv = dv
            dels.sort(reverse=True)
            for d in dels:
                Versions.get_active_object().active_shape_key_index = d
                bpy.ops.object.shape_key_remove(all=False)

    def delete_all_extra_sk(self, min, max, wm):
        objs = []
        for obj in Util.myccobjs():
            if obj.type == 'MESH':
                objs.append(obj)
        allsa = max-min
        onesa = allsa/len(objs)
        for oidx, obj in enumerate(objs):
            self.delete_oneobj_sk(min, onesa, oidx, obj, wm)
