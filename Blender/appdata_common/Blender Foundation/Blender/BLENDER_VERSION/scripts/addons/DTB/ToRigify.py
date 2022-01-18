from re import T
import re
import bpy
import os
import math
import bmesh
from . import Global
from . import DtbShapeKeys
from . import Versions
from . import DataBase
from . import Util


class ToRigify:
    notEnglish = False
    amtr_objs = []
    METARIG = None
    RIG = None
    chest_upper_tail = []
    neck_lower_head = []

    def __init__(self, dtu):
        self.dtu = dtu

    def find_amtr_objs(self):
        for d in Util.myccobjs():
            if d.type == "MESH":
                for modifier in d.modifiers:
                    if modifier.type == "ARMATURE":
                        if modifier.object.name == Global.get_Amtr_name():
                            self.amtr_objs.append(d.name)

    def del_eyesdriver(self):
        dobj = Global.getBody()
        sks = dobj.data.shape_keys
        if sks is None:
            return
        for didx, dvr in enumerate(sks.animation_data.drivers):
            d = dvr.driver
            dp = dvr.data_path
            if len(dp) > 24:
                dp = dp[12:]
                dp = dp[: len(dp) - 8]
                if dp == "EyesUpDown" or dp == "EyesSideSide":
                    dobj.data.shape_keys.key_blocks[dp].driver_remove("value")

    def prepare_scene(self):
        self.chest_upper_tail = []
        self.neck_lower_head = []
        self.amtr_objs = []
        self.RIG = None
        self.METARIG = None
        Versions.set_english()
        for scene in bpy.data.scenes:
            if scene.name == "Scene":
                scene.tool_settings.use_keyframe_insert_auto = False

    def check_if_possible(self):
        if Global.find_RGFY_all():  # Check if Rigify ran
            return True
        if Global.getBody() is None:
            return True
        if Global.getAmtr() is None:
            return True

    def prepare_bone_list(self, dobj):
        blist = []
        for bone in dobj.data.edit_bones:
            if bone.name.lower() == "chestupper":
                for i in range(3):
                    self.chest_upper_tail.append(bone.tail[i])
            elif bone.name.lower() == "necklower":
                for i in range(3):
                    self.neck_lower_head.append(bone.head[i])
            b10 = [
                bone.name,
                bone.head[0],
                bone.head[1],
                bone.head[2],
                bone.tail[0],
                bone.tail[1],
                bone.tail[2],
                bone.roll,
                bone.use_connect,
            ]
            blist.append(b10)
        Versions.do_chest_upper(blist, self.neck_lower_head)
        return blist

    def toRigify(self, db, main):
        # Prepare for Rigify
        self.prepare_scene()
        bpy.ops.mesh.primitive_circle_add()
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        Global.decide_HERO()
        self.find_amtr_objs()
        Global.setOpsMode("OBJECT")
        Versions.pivot_active_element_and_center_and_trnormal()
        if self.check_if_possible():
            return
        Global.convert_vgroups()  # Updates VertexGroups
        if len(Global.get_bone_limit()) == 0:  # Seems not Necessary
            Global.bone_limit_modify()
        wm.progress_update(5)
        dobj = Global.getAmtr()
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        Global.setOpsMode("EDIT")
        blist = []
        blist = self.prepare_bone_list(dobj)
        Global.setOpsMode("OBJECT")
        wm.progress_update(10)

        # Create Rig
        rtn = self.make_metarig()
        if rtn != "":
            main.report({"ERROR"}, rtn)
            return
        wm.progress_update(15)
        Global.setOpsMode("EDIT")
        self.fit2Rig(blist, db, 0)
        self.fitMetaFace(db)
        wm.progress_update(20)
        Global.setOpsMode("OBJECT")

        rtn = self.generate_rig()
        if rtn != "":
            main.report({"ERROR"}, rtn)
            return

        Global.setOpsMode("EDIT")

        wm.progress_update(30)
        self.all_rigity_bone(db)

        wm.progress_update(40)
        Global.setOpsMode("EDIT")
        self.fit2Rig(blist, db, 2)

        wm.progress_update(50)
        self.adjust_tweak()
        wm.progress_update(55)
        Global.setOpsMode("OBJECT")
        for oname in self.amtr_objs:
            self.toToeWeight1(Util.myccobjs().get(oname))
            Global.deselect()
        wm.progress_update(60)
        for ao in self.amtr_objs:
            cobj = Util.myccobjs().get(ao)
            Versions.select(cobj, True)
            washide = False
            if Versions.is_hide_view(cobj):
                washide = True
                Versions.hide_view(cobj, False)
            Versions.active_object(cobj)
            bpy.ops.object.parent_clear(type="CLEAR")
            if washide:
                Versions.hide_view(cobj, True)
            Global.deselect()
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        self.omit_g8(db)
        Util.allobjs().remove(self.METARIG)
        wm.progress_update(70)
        Global.deselect()
        amtr = self.RIG
        for ao in self.amtr_objs:
            if ao in Util.myccobjs():
                d = Util.myccobjs().get(ao)
                Versions.select(d, True)
                Versions.select(amtr, True)
                Versions.active_object(amtr)
                bpy.ops.object.parent_set(type="ARMATURE")
                Versions.select(d, False)
        wm.progress_update(75)
        Global.decide_HERO()
        Versions.select(Global.getBody(), True)
        Versions.active_object(Global.getBody())
        dsk = DtbShapeKeys.DtbShapeKeys(True, self.dtu)
        self.swap_morph_driver(db, dsk)
        wm.progress_update(80)
        dsk.swap_fvgroup(db, self.amtr_objs)
        wm.progress_update(90)
        Global.deselect()
        Versions.select(Global.getRgfy(), True)
        wm.progress_update(95)
        Versions.active_object(Global.getRgfy())
        self.finish_job()
        wm.progress_update(100)
        self.hide_finger_tool()

    def omit_g8(self, db):
        dobj = Global.getAmtr()
        Global.setOpsMode("EDIT")
        dobjname = dobj.name
        othbns = ["lShin_IK", "lHand_IK", "lShin_P", "lEye_H", "mainEye_H"]
        parent_combis = []
        for eb in dobj.data.edit_bones:
            if eb.parent is not None:
                parent_combis.append([eb.name, eb.parent.name])
        for eb in dobj.data.edit_bones:
            ebname = eb.name
            for dbn in db.tbl_basic_bones:
                if (("Toe" in dbn[0]) and len(dbn[0]) > 4) == False:
                    if dbn[0] == ebname:
                        dobj.data.edit_bones.remove(eb)
            for ob in othbns:
                if (("Toe" in dbn[0]) and len(dbn[0]) > 4) == False:
                    if ob == ebname or ("r" + ob[1:]) == ebname:
                        dobj.data.edit_bones.remove(eb)
        dbones = ["sight", "root"]
        for dbs in dbones:
            if dobj.data.edit_bones.get(dbs) is not None:
                dobj.data.edit_bones.remove(dobj.data.edit_bones[dbs])
        bnum = len(dobj.data.edit_bones)
        Global.setOpsMode("OBJECT")
        if bnum < 2:
            Versions.active_object(dobj)
            bpy.ops.object.delete(use_global=False)
        else:
            Global.deselect()
            aobj = Util.myccobjs().get(dobjname)
            amtr_bones = []
            for b in aobj.data.bones:
                amtr_bones.append(b.name)
            Versions.select(aobj, True)
            robj = self.RIG
            Versions.select(robj, True)
            Versions.active_object(robj)
            bpy.ops.object.join()
            Global.setOpsMode("EDIT")
            for eb in robj.data.edit_bones:
                if eb.name in amtr_bones and eb.parent is None:
                    find = False
                    if "Toe" in eb.name:
                        if eb.name.startswith("r"):
                            eb.parent = robj.data.edit_bones["toe.R"]
                            self.to_layer(eb, 18)
                        else:
                            eb.parent = robj.data.edit_bones["toe.L"]
                            self.to_layer(eb, 15)
                        find = True
                    else:
                        for combi in parent_combis:
                            if find == True:
                                break
                            if eb.name == combi[0]:
                                mparent = combi[1]
                                for torigify in db.toRigify:
                                    if torigify[0] >= 2:
                                        ops_torigify = "r" + torigify[1][1:]
                                        nparent = ""
                                        if mparent == ops_torigify:
                                            nparent = "DEF-" + torigify[2].replace(
                                                ".L", ".R"
                                            )
                                        elif mparent == torigify[1]:
                                            nparent = "DEF-" + torigify[2]
                                        if (
                                            nparent != ""
                                            and nparent in robj.data.edit_bones
                                        ):
                                            eb.parent = robj.data.edit_bones.get(
                                                nparent
                                            )
                                            self.to_layer(eb, 3)
                                            find = True
                                            break
                    if find == False:
                        eb.parent = robj.data.edit_bones["torso"]
                        self.to_layer(eb, 3)

    def to_layer(self, ebone, lnum):
        ebone.layers[lnum] = True
        for i in range(32):
            if i != lnum:
                ebone.layers[i] = False

    def toToeWeight1(self, dobj):
        Versions.active_object(dobj)
        Global.toMergeWeight_str(dobj, "lMetatarsals", ["lFoot"], True, False)
        Global.toMergeWeight_str(dobj, "rMetatarsals", ["rFoot"], True, False)

    def swap_morph_driver(self, db, dsk):
        for ao in self.amtr_objs:
            if (ao in Util.myccobjs()) == False:
                continue
            dobj = Util.myccobjs().get(ao)
            self.changeVgroup(dobj, db)
            sks = dobj.data.shape_keys
            if sks is None:
                continue
            if sks.animation_data is None:
                continue
            for didx, dvr in enumerate(sks.animation_data.drivers):
                d = dvr.driver
                dp = dvr.data_path
                if len(dp) > 24:
                    dp = dp[12:]
                    dp = dp[: len(dp) - 8]
                    if dp in dobj.data.shape_keys.key_blocks:
                        dobj.data.shape_keys.key_blocks[dp].driver_remove("value")
            dsk.makeDrive(dobj, db)
            for modifier in Util.myccobjs().get(ao).modifiers:
                if modifier.type == "ARMATURE":
                    modifier.use_deform_preserve_volume = True

    def finish_job(self):
        Global.setOpsMode("POSE")
        for ob in Util.myccobjs():
            if Global.isRiggedObject(ob):
                for m in ob.modifiers:
                    if m.name == "Armature":
                        m.show_on_cage = True
                        m.show_in_editmode = True
                ob.use_shape_key_edit_mode = True
        rig = Global.getRgfy()
        iks = ["thigh_parent", "upper_arm_parent", "MCH-thigh_ik", "MCH-upper_arm"]
        lrs = [".L", ".R"]
        for ik in iks:
            for lr in lrs:
                for pb in rig.pose.bones:
                    if pb.name == ik + lr:
                        pb["IK_Stretch"] = 0
        Versions.show_x_ray(Global.getRgfy())
        bs = ["DEF-pelvis.R", "head", "tweak_spine", "WGT-rig_breast.R"]
        if bs[0] in Global.getRgfyBones():
            Global.getRgfyBones()[bs[0]].hide = True
        if bs[1] in Global.getRgfyBones():
            Global.getRgfyBones()[bs[1]].hide = True
        if bs[2] in Global.getRgfyBones():
            pbs = Global.getRgfy().pose.bones
            if bs[2] in pbs:
                pbs[bs[2]].custom_shape = Util.allobjs().get(bs[3])
                #blender 3.0 break change
                Versions.handle_custom_shape_scale(pbs[bs[2]], 6.0)
            Global.getRgfyBones()[bs[2]].layers[3] = True
            Global.getRgfyBones()[bs[2]].layers[4] = False
            for i in range(3):
                Global.getRgfy().pose.bones[bs[2]].lock_rotation[i] = False
        Global.setRgfy_name("rig" + Util.get_dzidx())

        Versions.reverse_language()

        nper = ["tweak_spine.003", "tweak_spine.002"]
        for i in range(2):
            add = 1
            if i == 1:
                add = -1
            add = add * (0.01 * Global.get_size())
            Global.getRgfy().pose.bones[nper[i]].location[1] += add
        Versions.rigify_finger()
        self.finish_toes()

    def finish_toes(self):
        pbones = Global.getRgfy().pose.bones
        for pb in pbones:
            if ("Toe" in pb.name) and len(pb.name) > 4:
                wtg = Util.allobjs().get("Circle")
                if wtg is not None:
                    pb.custom_shape = wtg
                    #blender 3.0 break change
                    Versions.handle_custom_shape_scale(pb, 0.2)

    def delete001_sk(self):
        Global.setOpsMode("OBJECT")
        obj = Global.getBody()
        Versions.select(obj, True)
        Versions.active_object(obj)
        sp = obj.data.shape_keys
        if sp is not None:
            max = len(sp.key_blocks)
            i = 0
            for notouch in range(max):
                obj.active_shape_key_index = i
                if obj.active_shape_key.name.endswith(".001"):
                    bpy.ops.object.shape_key_remove(all=False)
                    max = max - 1
                else:
                    i = i + 1

    def avg_pos(self, vlist, all_vs, db):
        pos3 = [0, 0, 0]
        sum = len(vlist) - 2
        for i, v in enumerate(vlist):
            if i < 2:
                continue
            if Global.getIsGen():
                v = Global.toGeniVIndex(v)
            for j in range(3):
                pos3[j] += all_vs[v].co[j]
        for j in range(3):
            pos3[j] = pos3[j] / sum
        return pos3

    def fitMetaFace(self, db):
        bobj = Global.getBody()
        all_vs = bobj.data.vertices
        amtr = Util.myccobjs().get("metarig")
        tbl = None
        if Global.getIsMan():
            tbl = db.tometaface_m
        else:
            tbl = db.tometaface_f
        for b in amtr.data.edit_bones:
            bname = b.name
            for dbn in tbl:
                ops_dbn = dbn[1].replace(".L", ".R")
                bool_ops = bname == ops_dbn
                if bname == dbn[1] or bool_ops:
                    pos3 = self.avg_pos(dbn, all_vs, db)
                    if bool_ops:
                        pos3[0] = 0 - pos3[0]
                    if dbn[0] == 0:
                        b.tail = pos3
                    else:
                        b.head = pos3
        clist = []
        for z in range(2):
            for b in amtr.data.edit_bones:
                bname = b.name
                ops_bname = bname.replace(".R", ".L")
                for tfc in db.tometaface_couple:
                    if z == 0 and bname == tfc[1]:
                        clist.append(
                            [
                                b.name,
                                [b.tail[0], b.tail[1], b.tail[2]],
                                [b.head[0], b.head[1], b.head[2]],
                            ]
                        )
                    if z == 1 and (bname == tfc[2] or ops_bname == tfc[2]):
                        bool_ops = ops_bname == tfc[2] and bname != tfc[2]
                        for cl in clist:
                            # five is tail to head
                            if cl[0] == tfc[1]:
                                if tfc[0] == 0:
                                    b.tail = cl[1]
                                elif tfc[0] == 1:
                                    b.head = cl[2]
                                elif tfc[0] == 5:
                                    b.tail = cl[2]
                                elif tfc[0] == 9:
                                    b.head = cl[1]
                                break
                        if bool_ops:
                            if tfc[0] == 0 or tfc[0] == 5:
                                b.tail[0] = 0 - b.tail[0]
                            else:
                                b.head[0] = 0 - b.head[0]

    def getPlainRol(self, db, plainbone):
        for r in DataBase.tbl_brollfix:
            if r[0] == plainbone or (
                r[0].startswith("-") and r[0][1:] == plainbone[1:]
            ):
                roll = r[1]
                if r[0].startswith("-") and plainbone.startswith("l"):
                    roll = 0 - roll
                return roll
        return 0

    def hide_finger_tool(self):
        bs = Global.getRgfy().data
        ls = ["f_index", "thumb", "f_middle", "f_ring", "f_pinky"]
        rs = [".01_master.L", ".01_master.R"]
        for l in ls:
            for r in rs:
                if bs.bones.get(l + r) is not None:
                    bs.bones.get(l + r).hide = True

    def all_rigity_bone(self, db):
        rig = bpy.context.active_object
        Global.setOpsMode("EDIT")
        b5 = [
            ["thigh", "Thigh", "ThighBend"],
            ["shin", "Shin", "Shin"],
            ["upper_arm", "Shldr", "ShldrBend"],
            ["forearm", "Forearm", "ForearmBend"],
            ["foot", "Foot", "Foot"],
            ["hand", "Hand", "Hand"],
        ]
        lr2 = ["L", "R"]
        find = False
        miss = ""
        get = ""
        for bone in rig.data.edit_bones:
            if "arm" in bone.name or "hand" in bone.name:
                r = bone.roll
                if r < 0:
                    r = r - math.radians(30)
                else:
                    r = r + math.radians(30)
                bone.roll = r
                continue
            if "thigh" in bone.name:
                if ".L" in bone.name:
                    if bone.name == "MCH-thigh_ik_target.L":
                        bone.roll = math.radians(-94)
                    else:
                        bone.roll = math.radians(-11)
                else:
                    if bone.name == "MCH-thigh_ik_target.R":
                        bone.roll = math.radians(94)
                    else:
                        bone.roll = math.radians(11)
                mch_ti = ["MCH-thigh_ik.L", "MCH-thigh_ik.R"]
                for mt in mch_ti:
                    if bone.name == mt:
                        if bone.head[1] > 0:
                            bone.head[1] = 0
                continue
            if "shin" in bone.name:
                mch_ti = ["MCH-shin_ik.L", "MCH-shin_ik.R"]
                for mt in mch_ti:
                    if bone.name == mt:
                        if bone.head[1] > -0.002 * Global.get_size():
                            bone.head[1] = -0.002 * Global.get_size()
                if ".L" in bone.name:
                    bone.roll = math.radians(-8)
                else:
                    bone.roll = math.radians(8)
                continue
            if bone.name.startswith("DEF-foot"):
                if ".L" in bone.name:
                    bone.roll = math.radians(-84)
                else:
                    bone.roll = math.radians(84)
                continue
            if "breast" in bone.name:
                if ".L" in bone.name:
                    bone.roll = math.radians(-50)
                else:
                    bone.roll = math.radians(50)
            if bone.name.startswith("DEF-breast."):
                if "DEF-spine.002" in self.RIG.data.bones:
                    bone.parent = self.RIG.data.edit_bones["DEF-spine.002"]
            oeyes = [
                "ORG-eye.L",
                "ORG-eye.R",
                "ORG-teeth.T",
                "ORG-teeth.B",
                "ear.L",
                "ear.R",
            ]
            for oe in oeyes:
                if bone.name == oe:
                    bone.use_deform = True
        find = False
        Global.setOpsMode("POSE")
        for pb in rig.pose.bones:
            find = False
            mix = [0, 0, 0, 0, 0, 0]
            if (
                (
                    ("fk." in pb.name)
                    and pb.name.startswith("MCH-") == False
                    and ("hand" in pb.name) == False
                    and ("upper_arm." in pb.name) == False
                )
                or pb.name[0 : len(pb.name) - 1] == "thumb.01."
                or pb.name[0 : len(pb.name) - 1] == "toe."
            ):
                pb.rotation_mode = "YZX"
            else:
                pb.rotation_mode = "XYZ"
            for b in b5:
                if b[0] in pb.name:
                    for lr in lr2:
                        for i, k9 in enumerate(db.kind9(b[0], lr)):
                            if i > 0 and i != 2 and i != 3:
                                continue
                            if pb.name == k9:
                                b1 = b[1]
                                if k9.startswith("MCH-thigh_ik."):
                                    b1 = "Shin"
                                lr = lr.lower()
                                mix = db.mix_range(lr + b1)
                                find = True
                                break
                        if find:
                            break
                    if find:
                        break
            if find == False:
                for tbr in db.tbl_blimit_rgfy:
                    if tbr[0] == pb.name:
                        mix = tbr[1]
                        find = True
                        break
            if find == False:
                for tbl in db.toRigify:
                    if tbl[0] < 2:
                        continue
                    ops_tbl = [tbl[0], "r" + tbl[1][1:], tbl[2].replace(".L", ".R")]
                    bool_ops = (".L" in tbl[2]) and pb.name == ops_tbl[2]
                    if pb.name == tbl[2] or bool_ops:
                        for gbl in Global.get_bone_limit():
                            if (gbl[0] == tbl[1] and bool_ops == False) or (
                                bool_ops and gbl[0] == ops_tbl[1]
                            ):
                                line = ""
                                for i in range(6):
                                    mix[i] = gbl[2 + i]
                                    line = line + str(gbl[2 + i]) + ","
                                find = True
                                break
                    if find == True:
                        break
            if find == True:
                if "arm" in pb.name:
                    for i in range(3):
                        if i == 1:
                            continue
                        wk = mix[i * 2]
                        mix[i * 2] = 0 - mix[i * 2 + 1]
                        mix[i * 2 + 1] = 0 - wk
                if "toe" in pb.name:
                    for i in range(3):
                        wk = mix[i * 2]
                        mix[i * 2] = 0 - mix[i * 2 + 1]
                        mix[i * 2 + 1] = 0 - wk
                skips = [
                    "foot_ik.L",
                    "foot_ik.R",
                    "hand_ik.L",
                    "hand_ik.R",
                    "ORG-hand.L",
                    "ORG-hand.R",
                ]
                skip_ik = False
                for skip in skips:
                    if pb.name == skip:
                        skip_ik = True
                        break
                if skip_ik == False:
                    lr = pb.constraints.new("LIMIT_ROTATION")
                    lr.owner_space = "LOCAL"
                    lr.use_limit_x = True
                    lr.min_x = math.radians(mix[0])
                    lr.max_x = math.radians(mix[1])
                    lr.use_limit_y = True
                    lr.min_y = math.radians(mix[2])
                    lr.max_y = math.radians(mix[3])
                    lr.use_limit_z = True
                    lr.min_z = math.radians(mix[4])
                    lr.max_z = math.radians(mix[5])
                    lr.use_transform_limit = True
            self.adjust_pose_bones(pb)

    def adjust_pose_bones(self, pb):
        if pb.name.startswith("f_") and (
            pb.name.endswith(".L") or pb.name.endswith(".R")
        ):
            for c in pb.constraints:
                if c.name == "Copy Rotation":
                    c.use_x = False
                    c.use_z = True
        if pb.name.startswith("DEF-breast.") and len(pb.name) == 12:
            cr = pb.constraints.new("COPY_TRANSFORMS")
            cr.target = self.RIG  # Util.myccobjs().get('rig')
            if pb.name.endswith("L"):
                cr.subtarget = "breast.L"
            else:
                cr.subtarget = "breast.R"
            cr.target_space = "WORLD"
            cr.owner_space = "WORLD"
            cr.influence = 0.4
            cr.head_tail = 0.1
            pb.scale[0] = 0.9
            if Versions.getBV() > 2.80:
                pb.scale[1] = 0.90
            else:
                pb.scale[1] = 0.95
            pb.scale[2] = 0.9
        if pb.name == "head":
            cr = pb.constraints.new("COPY_ROTATION")
            cr.target = self.RIG  # Util.myccobjs().get('rig')
            cr.subtarget = "neck"
            cr.use_x = True
            cr.use_y = True
            cr.use_z = True
            cr.target_space = "LOCAL"
            cr.owner_space = "LOCAL"
            pb.lock_rotation = [True] * 3
        if pb.name == "DEF-spine.002":
            for c in pb.constraints:
                if c.name == "Stretch To":
                    c.mute = True
                elif c.name == "Copy Transforms":
                    c.head_tail = Versions.get_defspine002_heatail()
                elif c.name == "Damped Track":
                    c.head_tail = 0.5
        if pb.name == "torso":
            pb["head_follow"] = 0.8
            pb["neck_follow"] = 0.8
        if pb.name == "DEF-shin.L" or pb.name == "DEF-shin.R":
            for c in pb.constraints:
                if c.name == "Copy Transforms":
                    c.mute = True
        back_reverses = [
            ["upper_arm_tweak", "upper_arm_fk"],
            ["thigh_tweak", "thigh_fk"],
            ["forearm_tweak", "forearm_fk"],
        ]
        lrs = [".L", ".R"]
        idx = 0
        influ = [1.0, 0.75, 0.5]
        for br in back_reverses:
            for lr in lrs:
                if pb.name == br[0] + lr:
                    cr = pb.constraints.new("COPY_ROTATION")
                    cr.target = self.RIG  # Util.myccobjs().get('rig')
                    cr.subtarget = br[1] + lr
                    cr.use_x = False
                    cr.use_y = True
                    cr.invert_y = True
                    cr.use_z = False
                    cr.influence = influ[idx]
                    cr.target_space = "LOCAL"
                    cr.owner_space = "LOCAL"
            idx = idx + 1

    def ik2fk(self, idx):
        rig_id = Global.getRgfy().data["rig_id"]
        parents = ["thigh_parent", "upper_arm_parent"]
        len11 = [
            ["thigh_fk", "thigh_fk"],
            ["shin_fk", "shin_fk"],
            ["mfoot_fk", "MCH-foot_fk"],
            ["foot_fk", "foot_fk"],
            ["thigh_ik", "thigh_ik"],
            ["shin_ik", "MCH-thigh_ik"],
            ["foot_ik", "foot_ik"],
            ["footroll", "foot_heel_ik"],
            ["pole", "thigh_ik_target"],
            ["mfoot_ik", "MCH-thigh_ik_target"],
            ["main_parent", "thigh_parent"],
        ]
        arm8 = [
            ["uarm_fk", "upper_arm_fk"],
            ["farm_fk", "forearm_fk"],
            ["hand_fk", "hand_fk"],
            ["uarm_ik", "upper_arm_ik"],
            ["farm_ik", "MCH-upper_arm_ik"],
            ["hand_ik", "hand_ik"],
            ["pole", "upper_arm_ik_target"],
            ["main_parent", "upper_arm_parent"],
        ]
        lr = [".R", ".L"]
        for i in range(2):
            leg_ik2fk = "bpy.ops.pose.rigify_leg_ik2fk_" + rig_id + "("
            for l in len11:
                leg_ik2fk += l[0] + " = '" + l[1] + lr[i] + "',"
            leg_ik2fk += ")"
            arm_ik2fk = "bpy.ops.pose.rigify_arm_ik2fk_" + rig_id + "("
            for l in arm8:
                arm_ik2fk += l[0] + " = '" + l[1] + lr[i] + "',"
            arm_ik2fk += ")"
            if idx < 0 or i == idx:
                exec(arm_ik2fk)
            if idx < 0 or idx == i + 2:
                exec(leg_ik2fk)
            if idx < 0:
                Global.getRgfy().pose.bones[parents[0] + lr[i]]["IK_FK"] = 0
                Global.getRgfy().pose.bones[parents[1] + lr[i]]["IK_FK"] = 0

    def match_ikfk(self, influence4):
        for i, inf in enumerate(influence4):
            if inf > 0.5:
                self.ik2fk(i)
            else:
                self.fk2ik(i)

    def fk2ik(self, idx):
        rig_id = Global.getRgfy().data["rig_id"]
        arm6 = [
            ["uarm_fk", "upper_arm_fk"],
            ["farm_fk", "forearm_fk"],
            ["hand_fk", "hand_fk"],
            ["uarm_ik", "upper_arm_ik"],
            ["farm_ik", "MCH-upper_arm_ik"],
            ["hand_ik", "hand_ik"],
        ]
        leg8 = [
            ["thigh_fk", "thigh_fk"],
            ["shin_fk", "shin_fk"],
            ["foot_fk", "foot_fk"],
            ["mfoot_fk", "MCH-foot_fk"],
            ["thigh_ik", "thigh_ik"],
            ["shin_ik", "MCH-thigh_ik"],
            ["foot_ik", "MCH-thigh_ik_target"],
            ["mfoot_ik", "MCH-thigh_ik_target"],
        ]
        lr = [".R", ".L"]
        parents = ["thigh_parent", "upper_arm_parent"]
        for i in range(2):
            leg_fk2ik = "bpy.ops.pose.rigify_leg_fk2ik_" + rig_id + "("
            for l in leg8:
                leg_fk2ik += l[0] + " = '" + l[1] + lr[i] + "',"
            leg_fk2ik += ")"
            arm_fk2ik = "bpy.ops.pose.rigify_arm_fk2ik_" + rig_id + "("
            for l in arm6:
                arm_fk2ik += l[0] + " = '" + l[1] + lr[i] + "',"
            arm_fk2ik += ")"

            if idx < 0 or idx == i:
                exec(arm_fk2ik)
            if idx < 0 or idx == i + 2:
                exec(leg_fk2ik)
            if idx < 0:
                Global.getRgfy().pose.bones[parents[0] + lr[i]]["IK_FK"] = 1
                Global.getRgfy().pose.bones[parents[1] + lr[i]]["IK_FK"] = 1

    def ik_stretch_mute(self, flg_mute):
        strech_iks = ["thigh_ik", "MCH-thigh_ik", "upper_arm_ik", "MCH-upper_arm_ik"]
        lr = [".L", ".R"]
        rig = Global.getRgfy()
        for pb in rig.pose.bones:
            for c in pb.constraints:
                if c.name == "IK":
                    c.use_stretch = flg_mute == False
                    break
            for i in range(len(lr)):
                for siks in strech_iks:
                    if pb.name == (siks + lr[i]):
                        if flg_mute:
                            pb.ik_stretch = 0
                        else:
                            pb.ik_stretch = 0.1
                        break

    def generate_rig(self):
        Global.setOpsMode("OBJECT")
        try:
            bpy.ops.pose.rigify_generate()
        except:
            return "Generate Rig Error"
        rig = bpy.context.active_object
        self.RIG = rig
        Versions.select(rig, True)
        return ""

    def fit2Rig(self, blist, db, sw):

        rig = None
        if sw == 0:
            rig = self.METARIG
        else:
            rig = self.RIG
        for meb in rig.data.edit_bones:
            for dmr in db.toRigify:
                if (sw < 2 and dmr[0] >= 6) or (sw == 2 and dmr[0] < 2):
                    continue
                key = dmr[2]
                keep_key = key
                if sw == 1:
                    key = "ORG-" + key
                elif sw == 2:
                    key = "DEF-" + key
                ops_key = key.replace(".L", ".R")
                bool_ops = (".L" in key) and (ops_key == meb.name)
                ops_keep_key = keep_key.replace(".L", ".R")
                bool_keep_ops = (".L" in keep_key) and (ops_keep_key == meb.name)
                if key == meb.name or bool_ops:
                    for b8 in blist:
                        if (bool_ops == False and b8[0] == dmr[1]) or (
                            bool_ops
                            and dmr[1].startswith("l")
                            and b8[0] == "r" + dmr[1][1:]
                        ):
                            if (
                                sw > 0
                                and (dmr[0] > 0 and dmr[0] != 6)
                                and ("Toe" in dmr[1]) == False
                            ):
                                meb.use_connect = b8[8]
                            for i in range(3):
                                if dmr[0] != 4:
                                    if dmr[0] >= 2 or dmr[0] == 1 or dmr[0] == 7:
                                        if dmr[0] != 6:
                                            meb.head[i] = b8[1 + i]
                                    if dmr[0] >= 2 or dmr[0] == 0 or dmr[0] == 6:
                                        if dmr[0] != 7:
                                            meb.tail[i] = b8[4 + i]
                                    if sw == 0:
                                        meb.roll = b8[7]
                elif keep_key.startswith("f_") and (
                    keep_key.endswith(".R") or keep_key.endswith(".L")
                ):
                    if keep_key == meb.name or bool_keep_ops:
                        for b8 in blist:
                            if (bool_keep_ops == False and b8[0] == dmr[1]) or (
                                bool_keep_ops
                                and dmr[1].startswith("l")
                                and b8[0] == "r" + dmr[1][1:]
                            ):
                                meb.roll = b8[7]
                if len(meb.name) == 22 and meb.name.startswith("MCH-upper_arm_parent."):
                    meb.roll = 0.0

    def adjust_tweak(self):
        deb = self.RIG.data.edit_bones
        at = [
            ["tweak_spine.003", "DEF-spine.002"],
            ["tweak_spine.004", "DEF-spine.004"],
        ]
        for a in at:
            if (a[0] in deb) and (a[1] in deb):
                deb[a[0]].tail[1] = deb[a[1]].tail[1]
                deb[a[0]].head[1] = deb[a[1]].tail[1]
        at1 = [
            ["DEF-spine.003", "tweak_spine.003"],
            ["ORG-spine.003", "tweak_spine.003"],
        ]
        for a in at1:
            if (a[0] in deb) and (a[1] in deb):
                deb[a[0]].head[1] = deb[a[1]].head[1]
        at2 = [
            ["tweak_spine.005", "DEF-spine.005", "DEF-spine.004"],
            ["shin_tweak.L", "DEF-thigh.L.001", "DEF-shin.L"],
            ["shin_tweak.R", "DEF-thigh.R.001", "DEF-shin.R"],
        ]
        for a in at2:
            if (a[0] in deb) and (a[1] in deb) and (a[2] in deb):
                deb[a[0]].tail[1] = (deb[a[1]].tail[1] + deb[a[2]].tail[1]) / 2
                deb[a[0]].head[1] = (deb[a[1]].tail[1] + deb[a[2]].tail[1]) / 2
        at3 = ["DEF-spine.002", "tweak_spine.002"]
        if (at3[0] in deb) and (at3[1] in deb):
            deb[at3[0]].use_connect = False
            h = deb[at3[1]].head
            t = deb[at3[1]].tail
            y = int((t[2] - h[2]) / 6)
            h[2] = h[2] + y
            h[1] = h[1] + int(y / 2)
            deb[at3[0]].head = h
        at4 = ["shin_tweak.R", "shin_tweak.L"]
        knees = [["DEF-thigh.R.001", "DEF-shin.R"], ["DEF-thigh.L.001", "DEF-shin.L"]]
        for aidx, a in enumerate(at4):
            if a in deb:
                deb[a].roll = 0
                z = -1
                for kidx, k in enumerate(knees[aidx]):
                    if k in deb:
                        if kidx == 0:
                            z = deb.get(k).tail[2]
                        elif kidx == 1:
                            z += deb.get(k).head[2]
                z = z / 2
                deb.get(a).head[2] = z
        at5 = ["thigh_tweak.R.001", "thigh_tweak.L.001"]
        for i, a in enumerate(at5):
            if a in deb:
                deb[a].roll = math.radians(20 + (-40 * i))
        arm_d = ["DEF-forearm.L", "DEF-forearm.R"]
        for a in arm_d:
            if a in deb:
                deb[a].use_connect = False
                for i in range(3):
                    deb[a].head[i] = (
                        deb[a].head[i] + (deb[a].tail[i] - deb[a].head[i]) / 6
                    )

    def make_metarig(self):
        error = ""
        try:
            bpy.ops.object.armature_human_metarig_add()
        except AttributeError:
            error = "Missing Addon: 'Rigify'"
        except:
            error = (
                "Rigify: Broken... Something's wrong with Rigify. Please report this"
            )
        if ("metarig" in Util.myccobjs()) == False:
            error = "Missing Addon: 'Rigify'"
        if error != "":
            return error
        self.METARIG = bpy.context.active_object

        Versions.select(self.METARIG, True)
        for i in range(3):
            self.METARIG.scale[i] = Global.get_size()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        return ""

    def changeVgroup(self, dobj, db):
        for vname in dobj.vertex_groups.keys():
            for dbone in db.toRigify:
                if dbone[0] < 2 or dbone[0] == 4:
                    continue
                ops_dbone1 = "r" + dbone[1][1:]
                bool_ops = ops_dbone1 == vname
                if dbone[1] == vname or bool_ops:
                    if bool_ops:
                        dobj.vertex_groups[vname].name = "DEF-" + dbone[2].replace(
                            ".L", ".R"
                        )
                    else:
                        dobj.vertex_groups[vname].name = "DEF-" + dbone[2]
                    break
