import os
import math
import bpy
import mathutils

from . import Global
from . import Versions
from . import DataBase
from . import DtbMaterial
from . import Util
from . import DtbImports


class DazRigBlend:
    notEnglish = False
    head_vgroup_index = -1
    root = Global.getRootPath()
    buttons = []
    del_empty = []
    mub_ary = []
    bone_head_tail_dict = dict()
    bone_limits = dict()
    skeleton_data_dict = dict()

    def __init__(self, dtu):
        self.head_vgroup_index = -1
        self.notEnglish = False
        self.bone_limits = dtu.get_bone_limits_dict()
        self.bone_limits = Global.bone_limit_modify(self.bone_limits)
        self.bone_head_tail_dict = dtu.get_bone_head_tail_dict()
        self.skeleton_data_dict = dtu.get_skeleton_data_dict()

    def convert_file(self, filepath):
        isacs = Global.isAcs()
        basename = os.path.basename(filepath)
        (filename, fileext) = os.path.splitext(basename)
        ext = fileext.lower()
        if os.path.isfile(filepath):
            if ext == ".fbx":
                DtbImports.fbx_catched_error(filepath)

    def roop_empty(self, obj):
        Global.deselect()
        Versions.active_object(obj)
        Versions.select(obj, True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        Versions.select(obj, False)
        Versions.active_object_none()
        Global.deselect()
        if len(obj.children) == 0 or obj.type == "MESH":
            # check scale
            if Global.getAmtr().scale[0] < 0.015:
                for i in range(3):
                    obj.location[i] = obj.location[i] * 100
                    obj.scale[i] = 100
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            if self.is_mub(obj):
                pass
            else:
                self.buttons.append(obj)
            max = len(self.del_empty)
            ms = 0
            # delete empty
            for i in range(max):
                Util.allobjs().remove(self.del_empty.pop(i - ms))
                ms += 1
                max -= 1
        else:
            if obj.type == "EMPTY":
                self.del_empty.append(obj)
            for c in obj.children:
                self.roop_empty(c)

    def orthopedy_empty(self):
        self.buttons = []
        self.add_amtr_objs = []
        for dobj in Util.allobjs():
            if dobj.type == "EMPTY":
                if dobj.parent == Global.getAmtr():
                    self.del_empty = []
                    self.roop_empty(dobj)
                    Global.deselect()
                    Versions.active_object_none()

    def orthopedy_everything(self):
        amtr_objs = []
        self.del_empty = []
        Global.deselect()
        # Cycles through the objects and unparents the meshes from the figure.
        for dobj in Util.myacobjs():
            if dobj.type == "MESH":
                if dobj.parent == Global.getAmtr():
                    Versions.select(dobj, True)
                    Versions.active_object(dobj)
                    bpy.ops.object.transform_apply(
                        location=True, rotation=True, scale=True
                    )
                    amtr_objs.append(dobj)
                    bpy.ops.object.parent_clear()
                    Versions.select(dobj, False)
        Global.deselect()

        # Zero out the transforms on the Armature
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Versions.show_x_ray(Global.getAmtr())
        Global.setOpsMode("POSE")
        bpy.ops.pose.transforms_clear()
        Global.setOpsMode("OBJECT")
        bpy.ops.object.scale_clear()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        Global.deselect()

        # Reposition Objects
        for dobj in amtr_objs:
            Versions.select(dobj, True)
            Versions.active_object(dobj)
            dobj.rotation_euler.x += math.radians(90)
            # for i in range(3):
            #     dobj.scale[i] *= self.skeleton_data_dict["skeletonScale"][1]
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            for i in range(3):
                dobj.lock_location[i] = True
                dobj.lock_rotation[i] = True

                dobj.lock_scale[i] = True
            Global.deselect()

        mainbone = Global.getAmtr()
        Versions.select(mainbone, True)
        Versions.active_object(mainbone)
        for i in range(3):
            mainbone.lock_location[i] = True
            mainbone.lock_rotation[i] = True
            mainbone.lock_scale[i] = True

        # Reparent to Armature
        Global.setOpsMode("OBJECT")
        for btn in self.buttons:
            Versions.select(btn, True)
            Versions.select(mainbone, True)
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
            Versions.select(btn, False)
            Versions.select(mainbone, False)
        for didx, dobj in enumerate(amtr_objs):
            Versions.select(dobj, True)
            Versions.select(mainbone, True)
            bpy.ops.object.parent_set(type="ARMATURE")
            Versions.select(dobj, False)
            Versions.select(mainbone, False)

    def fixGeniWeight(self, db):
        obj = Global.getBody()
        if Global.getIsMan() == False:
            if (
                ("Futa Genitalia" in Util.myccobjs()) or ("Glans" in obj.material_slots)
            ) == False:
                return
        vgs = obj.vertex_groups
        del_vgs = []
        for i, v in enumerate(obj.data.vertices):
            d2 = [False, False]
            for g in v.groups:
                if vgs[g.group].name.startswith("Shaft"):
                    d2[0] = True
                elif "Thigh" in vgs[g.group].name:
                    d2[1] = True
                    if (g.group in del_vgs) == False:
                        del_vgs.append(g.group)
            if d2[0] and d2[1]:
                for d in del_vgs:
                    vgs[d].add([v.index], 1.0, "SUBTRACT")

    def integrationEyelashes(self):
        Global.setOpsMode("OBJECT")
        obj1 = Global.getEyls()
        obj2 = Global.getBody()
        Versions.select(obj1, True)
        Versions.select(obj2, True)
        Versions.active_object(obj1)
        Versions.active_object(obj2)
        bpy.ops.object.join()

    def integrationTear(self):
        Global.setOpsMode("OBJECT")
        obj1 = Global.getTear()
        obj2 = Global.getBody()
        Versions.select(obj1, True)
        Versions.select(obj2, True)
        Versions.active_object(obj1)
        Versions.active_object(obj2)
        bpy.ops.object.join()

    def unwrapuv(self):
        Global.setOpsMode("OBJECT")
        if Global.getIsEyls():
            obj1 = Global.getEyls()
            Versions.select(obj1, True)
            Versions.active_object(obj1)
            Global.setOpsMode("EDIT")
            bpy.ops.mesh.select_all(action="TOGGLE")
            bpy.ops.uv.unwrap()
            Global.setOpsMode("OBJECT")
        obj2 = Global.getBody()
        Versions.select(obj2, True)
        Versions.active_object(obj2)
        Global.setOpsMode("EDIT")
        bpy.ops.mesh.select_all(action="TOGGLE")
        bpy.ops.uv.unwrap()
        Global.setOpsMode("OBJECT")

    def bone_limit_modify(self):
        for bone in Global.getAmtr().pose.bones:
            if bone.name.endswith("_IK") or bone.name not in self.bone_limits.keys():
                continue

            bone_limit = self.bone_limits[bone.name]

            # Store Custom Properties
            bone["Daz Rotation Order"] = bone_limit[1]
            bone["min x"] = bone_limit[2]
            bone["max x"] = bone_limit[3]
            bone["min y"] = bone_limit[4]
            bone["max y"] = bone_limit[5]
            bone["min z"] = bone_limit[6]
            bone["max z"] = bone_limit[7]

            bone.constraints.new("LIMIT_ROTATION")
            rot_limit = bone.constraints["Limit Rotation"]
            rot_limit.owner_space = "LOCAL"
            rot_limit.use_transform_limit = True
            rot_limit.use_limit_x = True
            rot_limit.min_x = math.radians(bone_limit[2])
            rot_limit.max_x = math.radians(bone_limit[3])
            rot_limit.use_limit_y = True
            rot_limit.min_y = math.radians(bone_limit[4])
            rot_limit.max_y = math.radians(bone_limit[5])
            rot_limit.use_limit_z = True
            rot_limit.min_z = math.radians(bone_limit[6])
            rot_limit.max_z = math.radians(bone_limit[7])

            bone.use_ik_limit_x = True
            bone.use_ik_limit_y = True
            bone.use_ik_limit_z = True
            if "shin" in bone.name.lower():
                bone.ik_min_x = math.radians(1)
                bone.use_ik_limit_x = False
            else:
                bone.ik_min_x = math.radians(bone_limit[2])
            bone.ik_max_x = math.radians(bone_limit[3])
            bone.ik_min_y = math.radians(bone_limit[4])
            bone.ik_max_y = math.radians(bone_limit[5])
            bone.ik_min_z = math.radians(bone_limit[6])
            bone.ik_max_z = math.radians(bone_limit[7])

            if bone.name[1:] == "Shin" or "Thigh" in bone.name:
                bone.ik_stiffness_y = 0.99
                bone.ik_stiffness_z = 0.99
                if "ThighTwist" in bone.name:
                    bone.ik_stiffness_x = 0.99
            # name changes for Genesis 9
            elif bone.name[2:] == "shin" or "thigh" in bone.name:
                bone.ik_stiffness_y = 0.99
                bone.ik_stiffness_z = 0.99
                if "twist" in bone.name:
                    bone.ik_stiffness_x = 0.99

    def ifitsman(self, bname, roll):
        if Global.getIsMan():
            if Global.getIsG3():
                tbl = DataBase.mbone_g3
            else:
                tbl = DataBase.mbone
            for mb in tbl:
                if mb[0].lower()[1:] == bname.lower()[1:]:
                    return mb[1]
        return roll

    # To Do fix, roll as it is being incorrectly calculated in Shoulders and Arms
    def set_bone_head_tail(self):
        # Switch to Edit mode
        armature_obj = Global.getAmtr()
        Versions.select(armature_obj, True)
        Versions.active_object(armature_obj)
        ob = bpy.context.object
        Global.setOpsMode("EDIT")

        # Set head, tail and roll values for all the bones
        for bone in ob.data.edit_bones:
            if bone.name in self.bone_head_tail_dict.keys():
                head_and_tail = self.bone_head_tail_dict[bone.name]

                bone.use_connect = False

                # set head
                bone.head[0] = float(head_and_tail[0])
                bone.head[1] = -float(head_and_tail[2])
                bone.head[2] = float(head_and_tail[1])

                # set tail
                bone.tail[0] = float(head_and_tail[3])
                bone.tail[1] = -float(head_and_tail[5])
                bone.tail[2] = float(head_and_tail[4])

                # calculate roll aligning bone towards a vector
                align_axis_vec = mathutils.Vector(
                    (
                        float(head_and_tail[6]),
                        -float(head_and_tail[8]),
                        float(head_and_tail[7]),
                    )
                )
                bone.align_roll(align_axis_vec)

    def makeBRotationCut(self, db):

        for bone in Global.getAmtr().pose.bones:
            if bone.name not in self.bone_limits.keys():
                continue
            bone_limit = self.bone_limits[bone.name]
            for i in range(3):
                if bone_limit[2 + i * 2] == 0 and bone_limit[2 + i * 2 + 1] == 0:
                    bone.lock_rotation[i] = True
                    if i == 0:
                        bone.lock_ik_x = True
                    elif i == 1:
                        bone.lock_ik_y = True
                    elif i == 2:
                        bone.lock_ik_z = True

    def makeRoot(self):
        dobj = Global.getAmtr()
        Versions.active_object(dobj)
        Global.setOpsMode("EDIT")
        root = dobj.data.edit_bones.new("root")
        root.use_deform = False
        for i in range(3):
            if i == 1:
                root.head[i] = -20
                root.tail[i] = 20
            else:
                root.head[i] = 0
                root.tail[i] = 0

    def makePole(self):
        dobj = Global.getAmtr()
        pole_bones = ["lShin", "pelvis", "root"]
        pole_bones = DataBase.translate_bonenames(pole_bones)
        make_pole = 0
        for bone in dobj.data.edit_bones.keys():
            if bone in pole_bones:
                make_pole += 1
        if make_pole == 3:
            poles = [
                dobj.data.edit_bones.new(DataBase.translate_bonenames("rShin_P")),
                dobj.data.edit_bones.new(DataBase.translate_bonenames("lShin_P")),
            ]
            lshin = dobj.data.edit_bones[DataBase.translate_bonenames("lShin")]
            adl = dobj.data.edit_bones["pelvis"]
            yjiku = [adl.tail[2], adl.head[2]]
            yjiku[0] = yjiku[0] + (yjiku[1] - yjiku[0]) / 2
            if yjiku[0] > yjiku[1]:
                wk = yjiku[0]
                yjiku[0] = yjiku[1]
                yjiku[1] = wk
            for pidx, pl in enumerate(poles):
                pl.parent = dobj.data.edit_bones["root"]
                pl.use_connect = False
                pl.use_deform = False
                if pidx == 0:
                    pl.head[0] = 0 - lshin.tail[0]  # *2
                else:
                    pl.head[0] = lshin.tail[0]  # *2
                pl.tail[2] = yjiku[1]
                pl.head[2] = yjiku[1]
                pl.tail[0] = pl.head[0]
                pl.head[1] = 0 - (lshin.head[2] * 1.6)
                pl.tail[1] = pl.head[1] - (pl.head[1] / 6)

    def makeIK(self):
        chain_count = [6, 6, 3, 3]
        if Global.getIsG9():
            chain_count = [4, 4, 2, 2]
        ctl_bones = ["rHand", "lHand", "rShin", "lShin"]
        ctl_bones = DataBase.translate_bonenames(ctl_bones)

        make_ik = 0
        Global.setOpsMode("EDIT")
        amt = bpy.context.object
        for bn in amt.pose.bones.keys():
            if bn in ctl_bones:
                make_ik += 1
        if make_ik == 4:
            for bn in amt.data.edit_bones:
                for i in range(len(ctl_bones)):
                    if bn.name == ctl_bones[i]:
                        ikbone = amt.data.edit_bones.new(ctl_bones[i] + "_IK")
                        ikbone.use_connect = False
                        amt.data.edit_bones[
                            ctl_bones[i] + "_IK"
                        ].parent = amt.data.edit_bones["root"]
                        amt.data.edit_bones[ctl_bones[i] + "_IK"].use_deform = False
                        if i < 2:
                            for j in range(3):
                                ikbone.head[j] = bn.head[j]
                                ikbone.tail[j] = ikbone.head[j] - (
                                    bn.tail[j] - bn.head[j]
                                )
                                # ikbone.roll = bn.roll
                        else:
                            fts = ["rFoot", "lFoot"]
                            fts = DataBase.translate_bonenames(fts)
                            ft = amt.data.edit_bones.get(fts[i - 2])
                            if ft is not None:
                                for j in range(3):
                                    ikbone.head[j] = ft.head[j]
                                    ikbone.tail[j] = ft.tail[j]
                                    ikbone.roll = ft.roll
            Global.setOpsMode("POSE")
            amt = Global.getAmtr()
            for i in range(len(ctl_bones)):

                ikb = amt.pose.bones[ctl_bones[i]]
                c = ikb.constraints.new("IK")
                c.name = ctl_bones[i] + "_IK"
                c.target = amt
                c.subtarget = ctl_bones[i] + "_IK"
                if i > 1:
                    c.pole_target = amt
                    c.pole_subtarget = ctl_bones[i] + "_P"
                    c.pole_angle = math.radians(-90)
                c.chain_count = chain_count[i]
                if i > 1:
                    c.iterations = 500
                    c.use_tail = True
                    c.use_stretch = False
            self.copy_rotation()
            Util.to_other_collection_byname(ctl_bones, "DAZ_HIDE", Util.cur_col_name())

    def copy_rotation(self):
        crbones = ["rFoot", "lFoot", "rShin_IK", "lShin_IK"]
        crbones = DataBase.translate_bonenames(crbones)
        amt = Global.getAmtr()
        for i in range(2):
            c = amt.pose.bones[crbones[i]].constraints.new("COPY_ROTATION")
            c.target = amt
            c.subtarget = crbones[i + 2]
            c.target_space = "WORLD"
            c.owner_space = "WORLD"
            c.use_x = True
            c.use_y = True
            c.use_z = True
            c.influence = 0.0
        h_iks = ["rHand_IK", "lHand_IK"]
        h_iks = DataBase.translate_bonenames(h_iks)
        for hik in h_iks:
            phik = amt.pose.bones.get(hik)
            if phik is not None:
                phik.lock_rotation = [True] * 3

    def pbone_limit(self):
        for b in bpy.context.object.pose.bones:
            if (
                b.name != "hip"
                and b.name != "root"
                and b.name.endswith("IK") == False
                and b.name.endswith("_P") == False
                and b.name.endswith("e_H") == False
            ):
                b.lock_location = [True] * 3
            b.lock_scale = [True] * 3
            if b.name.endswith("_P"):
                b.lock_rotation = [True] * 3

    def foot_finger_forg3(self):
        if Global.getIsG3() == False:
            return
        lrs = ["l", "r"]
        pbs = Global.getAmtr().pose.bones
        for lr in lrs:
            keys = [lr + "BigToe"]
            for i in range(4):
                keys.append(lr + "SmallToe" + (str(i + 1)))
            for i in range(5):
                for pb in pbs:
                    if pb.name == keys[i]:
                        cr = pb.constraints.new(type="COPY_ROTATION")
                        cr.target = Global.getAmtr()
                        cr.subtarget = lr + "Toe"
                        cr.use_x = True
                        cr.use_y = False
                        cr.use_z = False
                        Versions.mix_mode(cr)
                        cr.target_space = "LOCAL"
                        cr.owner_space = "LOCAL"

    # TODO: Split up logic
    def finishjob(self):
        DtbMaterial.default_material()
        Versions.make_sun()
        from . import ToHighReso

        thr = ToHighReso.ToHighReso()
        thr.toCorrectVWeight1()
        self.subdiv()
        Global.deselect()
        if Global.getIsG3():
            self.foot_finger_forg3()
            Global.deselect()
        Versions.active_object_none()
        Global.change_size(Global.getAmtr())
        if bpy.context.window_manager.update_viewport:
            Global.scale_settings()
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode("POSE")
        Versions.show_x_ray(Global.getAmtr())
        Versions.show_wire(bpy.context.object)
        for ob in Util.myccobjs():
            if Global.isRiggedObject(ob):
                for m in ob.modifiers:
                    if m.name == "Armature":
                        m.show_on_cage = True
                        m.show_in_editmode = True
                        m.use_deform_preserve_volume = True
                ob.use_shape_key_edit_mode = True
        b3 = ["root", "rShin_P", "lShin_P"]
        b3 = DataBase.translate_bonenames(b3)
        for b in b3:
            pb = Global.getAmtr().pose.bones.get(b)
            if pb is not None:
                pb.rotation_mode = "XYZ"
        self.eyes_correct()
        Global.setOpsMode("OBJECT")
        self.fix_mub()
        Global.setOpsMode("POSE")
        bpy.ops.pose.select_all(action="DESELECT")

    # [mub --means-->  Mesh Under Bone]
    def fix_mub(self):
        for obj in Util.myacobjs():
            if obj.name in [mb[1] for mb in self.mub_ary]:
                for i in range(3):
                    obj.location[i] = 0

    def mub_ary_A(self):
        adr = os.path.join(Global.getHomeTown(), "FIG.dat")
        if os.path.exists(adr):
            with open(adr) as f:
                ls = f.readlines()
            for l in ls:
                ss = l.split(",")
                if len(ss) >= 2:
                    if ss[1].endswith("\n"):
                        ss[1] = ss[1][: len(ss[1]) - 1]
                    self.mub_ary.append(ss)
                    ss[1] += ".Shape"
                    self.mub_ary.append(ss)

    def is_mub(self, obj):
        for ss in self.mub_ary:
            if ss[1] == obj.name:
                return True
        return False

    def mub_ary_Z(self):
        for ss in self.mub_ary:
            if (ss[1] in Util.myacobjs()) and (ss[0] in Global.getAmtr().pose.bones):
                obj = Util.myacobjs().get(ss[1])
                if obj.type != "MESH":
                    continue
                vgs = obj.vertex_groups
                for vs in vgs:
                    obj.vertex_groups.remove(vs)
                Versions.select(Util.myacobjs().get(ss[1]), True)
                Global.getAmtr().pose.bones.get(ss[0]).bone.select = True
                Global.getAmtr().data.bones.active = Global.getAmtr().data.bones.get(
                    ss[0]
                )
                bpy.ops.object.parent_set(type="BONE")
                Global.deselect()

    def eyes_correct(self):
        bpy.ops.pose.select_all(action="DESELECT")
        eyes = ["lEye", "rEye"]
        eyes = DataBase.translate_bonenames(eyes)
        for eye in eyes:
            e = Global.getAmtr().pose.bones.get(eye)
            if e is not None:
                e.bone.select = True
                Versions.pose_apply()
                e.bone.select = False

    def subdiv(self):
        body = Global.getBody()
        Versions.select(body, True)
        Versions.active_object(body)
        bpy.ops.object.modifier_add(type="SUBSURF")
        Versions.set_subdiv(body)
