import bpy
import os
import math
import bmesh
from . import Global
from . import Versions
from . import DataBase
from . import DtbShaders
class DazRigBlend:
    notEnglish = False
    head_vgroup_index = -1
    root = ""
    buttons = []
    del_empty = []

    def __init__(self, root):
        self.root = root
        self.head_vgroup_index = -1
        self.notEnglish = False

    def convert_file(self, filepath):
        basename = os.path.basename(filepath)
        (filename, fileext) = os.path.splitext(basename)
        ext = fileext.lower()
        if os.path.isfile(filepath):
            if ext == '.fbx':
                bpy.ops.import_scene.fbx(filepath=filepath, force_connect_children=True
                                         , automatic_bone_orientation=True, primary_bone_axis='Y',
                                         secondary_bone_axis='X')

    def roop_empty(self,obj,loc,rot):
        Global.deselect()
        if len(obj.children)==0 and obj.type=='MESH':
            Versions.select(obj, True)
            Versions.active_object(obj)
            Global.setOpsMode('OBJECT')
            bpy.ops.object.parent_clear(type='CLEAR')
            for i in range(3):
                if obj.lock_location[i]:
                    obj.lock_location[i] = False
                if obj.lock_rotation[i]:
                    obj.lock_rotation[i] = False
                obj.location[i] += loc[i]
                obj.rotation_euler[i] += rot[i]
                #rint(obj.name,obj.location,obj.rotation_euler)
            self.buttons.append(obj)
        else:
            cloc = obj.location
            crot = obj.rotation_euler
            for i in range(3):
                cloc[i] += loc[i]
                crot[i] += rot[i]
            self.del_empty.append(obj)
            for c in obj.children:
                self.roop_empty(c,cloc,crot)

    def manage_empty(self,empty_objs):
        for e in empty_objs:
            self.del_empty.append(e)
            for c in e.children:
                self.roop_empty(c,e.location,e.rotation_euler)
        for de in self.del_empty:
            if de.type=='EMPTY':
                bpy.data.objects.remove(de)

    def orthopedy_everything(self):
        amtr_objs = []
        empty_objs = []
        self.buttons = []
        self.del_empty = []
        Global.deselect()
        Versions.select(Global.getAmtr(),True)
        for dobj in bpy.data.objects:
            if dobj.type == 'MESH':
                Versions.select(dobj,True)
                Versions.active_object(dobj)
                for modifier in dobj.modifiers:
                    if modifier.type == "ARMATURE":
                        if modifier.object.name == Global.get_Amtr_name():
                            if dobj.type=='MESH':
                                amtr_objs.append(dobj)
                                bpy.ops.object.parent_clear()
                Versions.select(dobj,False)
            elif dobj.type=='EMPTY':
                if dobj.parent==Global.getAmtr():
                    empty_objs.append(dobj)
        Global.deselect()
        self.manage_empty(empty_objs)
        Global.deselect()
        #max = -1
        if len(self.buttons)>0:
            for obj in self.buttons:
                Versions.select(obj,True)
                Versions.active_object(obj)
                #bpy.ops.object.join()
                #max = len(amtr_objs)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            #Versions.pivot_active_element_and_center_and_trnormal()
                amtr_objs.append(bpy.context.object)
                Global.deselect()
        Versions.select(Global.getAmtr(),True)
        Versions.active_object(Global.getAmtr())
        Versions.show_x_ray(Global.getAmtr())
        Global.setOpsMode('POSE')
        bpy.ops.pose.transforms_clear()
        Global.setOpsMode('OBJECT')
        bpy.ops.object.scale_clear()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        Global.deselect()
        for dobj in amtr_objs:
            Versions.select(dobj, True)
            Versions.active_object(dobj)
            dobj.rotation_euler.x += math.radians(90)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            for i in range(3):
                dobj.lock_location[i] = True
                dobj.lock_rotation[i] = True
                dobj.lock_scale[i] = True
            Global.deselect()
        mainbone = Global.getAmtr()
        Versions.select(mainbone,True)
        Versions.active_object(mainbone)
        for i in range(3):
            mainbone.lock_location[i] = True
            mainbone.lock_rotation[i] = True
            mainbone.lock_scale[i] = True
        Global.setOpsMode('OBJECT')

        for didx,dobj in enumerate(amtr_objs):
            Versions.select(dobj,True)
            Versions.select(mainbone, True)
            if dobj in self.buttons:#didx==max:
                bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            else:
                bpy.ops.object.parent_set(type='ARMATURE')
            Versions.select(dobj,False)
            Versions.select(mainbone,False)

    def roopFitHeadChildren(self,bone_group):
        for b in bone_group:
            if len(b.children) > 0:
                self.roopFitHeadChildren(b.children)
            else:
                ikh = [b.head[0] - b.tail[0], b.head[1] - b.tail[1], b.head[2] - b.tail[2]]
                for i in range(3):
                    b.tail[i] = b.head[i] + ikh[i] / 5

    def fitHeadChildren(self):
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode('EDIT')
        self.roopFitHeadChildren(Global.getAmtr().data.edit_bones['head'].children)
        for b in Global.getAmtr().data.edit_bones['head'].children:
            ikh = [b.head[0]-b.tail[0], b.head[1]-b.tail[1], b.head[2]-b.tail[2]]
            for i in range(3):
                b.tail[i] = b.head[i]+ikh[i]/5



    def fixGeniWeight(self, db):
        obj = Global.getBody()
        if Global.getIsMan()==False:
            if (('Futa Genitalia' in bpy.data.objects) or ('Glans' in obj.material_slots))==False:
                return
        vgs = obj.vertex_groups
        del_vgs = []
        for i, v in enumerate(obj.data.vertices):
            d2 = [False, False]
            for g in v.groups:
                if vgs[g.group].name.startswith("Shaft"):
                    d2[0] = True
                elif ('Thigh' in vgs[g.group].name):
                    d2[1] = True
                    if (g.group in del_vgs)==False:
                        del_vgs.append(g.group)
            if d2[0] and d2[1]:
                for d in del_vgs:
                    vgs[d].add([v.index], 1.0, 'SUBTRACT')

    def integrationEyelashes(self):
        Global.setOpsMode('OBJECT')
        obj1 = Global.getEyls()
        obj2 = Global.getBody()
        Versions.select(obj1,True)
        Versions.select(obj2,True)
        Versions.active_object(obj1)
        Versions.active_object(obj2)
        bpy.ops.object.join()

    def unwrapuv(self):
        Global.setOpsMode('OBJECT')
        if Global.getIsEyls():
            obj1 = Global.getEyls()
            Versions.select(obj1,True)
            Versions.active_object(obj1)
            Global.setOpsMode('EDIT')
            bpy.ops.mesh.select_all(action='TOGGLE');
            bpy.ops.uv.unwrap()
            Global.setOpsMode('OBJECT')
        obj2 = Global.getBody()
        Versions.select(obj2,True)
        Versions.active_object(obj2)
        Global.setOpsMode('EDIT')
        bpy.ops.mesh.select_all(action='TOGGLE');
        bpy.ops.uv.unwrap()
        Global.setOpsMode('OBJECT')

    def bone_limit_modify(self):
        if len(Global.get_bone_limit()) == 0:
            Global.bone_limit_modify();
        for row in Global.get_bone_limit():
            dobj = Global.getAmtr()
            pbs = dobj.pose.bones
            for pb in pbs:
                if pb.name.endswith("_IK"):
                    continue
                if pb.name == row[0]:
                    yzx3 = ['Shin', 'ThighBend', 'ShldrBend','Foot','Tnumb1','Toe']
                    hit = False
                    for yzx in yzx3:
                        if yzx  == pb.name[1:]:
                            hit = True
                            break
                    if hit:
                        pb.rotation_mode = 'YZX'
                    else:
                        pb.rotation_mode = 'XYZ'
                    pb.constraints.new('LIMIT_ROTATION')
                    lr = pb.constraints['Limit Rotation']
                    lr.owner_space = 'LOCAL'
                    lr.use_limit_x = True
                    lr.min_x = math.radians(row[2])
                    lr.max_x = math.radians(row[3])
                    lr.use_limit_y = True
                    lr.use_limit_z = True
                    lr.use_transform_limit = True
                    lr.min_y = math.radians(row[4])
                    lr.max_y = math.radians(row[5])
                    lr.min_z = math.radians(row[6])
                    lr.max_z = math.radians(row[7])
                    pb.use_ik_limit_x = True
                    pb.use_ik_limit_y = True
                    pb.use_ik_limit_z = True
                    if 'shin' in pb.name.lower():
                        pb.ik_min_x = math.radians(1)
                        pb.use_ik_limit_x = False
                    else:
                        pb.ik_min_x = math.radians(row[2])
                    pb.ik_max_x = math.radians(row[3])
                    pb.ik_min_y = math.radians(row[4])
                    pb.ik_max_y = math.radians(row[5])
                    pb.ik_min_z = math.radians(row[6])
                    pb.ik_max_z = math.radians(row[7])
                    if pb.name[1:] == 'Shin' or 'Thigh' in pb.name:
                        pb.ik_stiffness_y = 0.99
                        pb.ik_stiffness_z = 0.99
                        if 'ThighTwist' in pb.name:
                            pb.ik_stiffness_x = 0.99

    def fix_manfitbone(self, db):
        for mb in db.mbone:
            for ridx, row in enumerate(DataBase.tbl_brollfix):
                if mb[0].lower() == row[0].lower():
                    DataBase.tbl_brollfix[ridx][1] = mb[1]
                    break

    def ifitsman(self, bname, roll):
        if Global.getIsMan():
            for mb in DataBase.mbone:
                if mb[0].lower()[1:] == bname.lower()[1:]:
                    return mb[1]
        return roll

    def fitbone_roll(self):
        dobj = Global.getAmtr()
        Versions.select(dobj,True)
        Versions.active_object(dobj)
        ob = bpy.context.object
        Global.setOpsMode('EDIT')
        tbl = DataBase.tbl_brollfix
        if Global.getIsG3():
            tbl = tbl[3:]
            tbl.extend(DataBase.tbl_brollfix_g3)
        for bone in ob.data.edit_bones:
            for ridx, row in enumerate(tbl):
                if bone.name.lower() == row[0].lower():
                    bone.roll = math.radians(row[1])
                if row[0].startswith("-") and bone.name[1:].lower() == row[0][1:].lower():
                    roll = self.ifitsman(row[0], row[1])
                    if bone.name[:1].lower() == 'l':
                        bone.roll = 0 - math.radians(roll)
                    else:
                        bone.roll = math.radians(roll)

    def correct_foot_toe_orientation(self):
        foot_toe_names = [['rFoot','lFoot'],['rToe','lToe']]
        foot_toe_yx = [[0.38,0.26],[0.12,0.34]]
        for f_t_idx,foot_toe in enumerate(foot_toe_names):
            for i, ft in enumerate(foot_toe):
                bone = Global.getAmtr().data.edit_bones.get(ft)
                if bone is not None:
                    len = bone.length
                    bone.tail[2] = bone.head[2] - (len *foot_toe_yx[f_t_idx][0])
                    x_sa = len * foot_toe_yx[f_t_idx][1]
                    if i == 0:
                        x_sa = 0 - x_sa
                    bone.tail[0] = bone.head[0] + x_sa

    def makeBRotationCut(self,db):
        for pb in Global.getAmtr().pose.bones:
            for tb2 in Global.get_bone_limit():
                if pb.name==tb2[0]:
                    for i in range(3):
                        if tb2[2+i*2]==0 and tb2[2+i*2+1]==0:
                            pb.lock_rotation[i] = True
                            if i==0:
                                pb.lock_ik_x = True
                            elif i==1:
                                pb.lock_ik_y = True
                            elif i==2:
                                pb.lock_ik_z = True
                    break

    def makeRoot(self):
        dobj = Global.getAmtr()
        Versions.active_object(dobj)
        Global.setOpsMode("EDIT")
        root = dobj.data.edit_bones.new('root')
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
        poles = [dobj.data.edit_bones.new('rShin_P'), dobj.data.edit_bones.new('lShin_P')]
        lshin = dobj.data.edit_bones['lShin']
        adl = dobj.data.edit_bones['pelvis']
        yjiku = [adl.tail[2],adl.head[2]]
        yjiku[0]  = yjiku[0] + (yjiku[1]-yjiku[0])/2
        if yjiku[0]>yjiku[1]:
            wk = yjiku[0]
            yjiku[0] = yjiku[1]
            yjiku[1] = wk
        for pidx,pl in enumerate(poles):
            pl.parent = dobj.data.edit_bones['root']
            pl.use_connect = False
            pl.use_deform = False
            if pidx==0:
                pl.head[0] = 0-lshin.tail[0]#*2
            else:
                pl.head[0] = lshin.tail[0]#*2
            pl.tail[2] = yjiku[1]
            pl.head[2] = yjiku[1]
            pl.tail[0] = pl.head[0]
            pl.head[1] = 0-(lshin.head[2]*1.6)
            pl.tail[1] = pl.head[1]-(pl.head[1]/6)

    def makeIK(self):
        chain_count = [6, 6, 3, 3]
        ctl_bones = ['rHand', 'lHand', 'rShin', 'lShin']
        Global.setOpsMode('EDIT')
        amt = bpy.context.object
        for bn in amt.data.edit_bones:
            for i in range(len(ctl_bones)):
                if bn.name == ctl_bones[i]:
                    ikbone = amt.data.edit_bones.new(ctl_bones[i] + '_IK')
                    ikbone.use_connect = False
                    amt.data.edit_bones[ctl_bones[i] + "_IK"].parent = amt.data.edit_bones['root']
                    amt.data.edit_bones[ctl_bones[i] + "_IK"].use_deform = False
                    if i < 2:
                        for j in range(3):
                            ikbone.head[j] = bn.head[j]
                            ikbone.tail[j] = ikbone.head[j] - (bn.tail[j] - bn.head[j])
                            #ikbone.roll = bn.roll
                    else:
                        fts = ['rFoot','lFoot']
                        ft = amt.data.edit_bones.get(fts[i-2])
                        if ft is not None:
                            for j in range(3):
                                ikbone.head[j] = ft.head[j]
                                ikbone.tail[j] = ft.tail[j]
                                ikbone.roll =ft.roll
        Global.setOpsMode('POSE')
        amt = Global.getAmtr()
        for i in range(len(ctl_bones)):
            ikb = amt.pose.bones[ctl_bones[i]]
            c = ikb.constraints.new('IK')
            c.name = ctl_bones[i] + "_IK"
            c.target = amt
            c.subtarget = ctl_bones[i] + "_IK"
            if i>1:
                c.pole_target = amt
                c.pole_subtarget = ctl_bones[i] + "_P"
                c.pole_angle = math.radians(-90)
            c.chain_count = chain_count[i]
            if i > 1:
                c.iterations = 500
                c.use_tail = True
                c.use_stretch = False
        self.copy_rotation()

    def copy_rotation(self):
        crbones = ['rFoot','lFoot','rShin_IK','lShin_IK']
        amt = Global.getAmtr()
        for i in range(2):
            c = amt.pose.bones[crbones[i]].constraints.new('COPY_ROTATION')
            c.target = amt
            c.subtarget = crbones[i+2]
            c.target_space = 'WORLD'
            c.owner_space = 'WORLD'
            c.use_x = True
            c.use_y = True
            c.use_z = True
            c.influence = 0.0
        h_iks = ['rHand_IK','lHand_IK']
        for hik in h_iks:
            phik = amt.pose.bones.get(hik)
            if phik is not None:
                phik.lock_rotation = [True] * 3

    def pbone_limit(self):
        for b in bpy.context.object.pose.bones:
            if b.name != 'hip' and b.name!= 'root'\
            and b.name.endswith('IK') == False and b.name.endswith("_P")==False \
            and b.name.endswith("e_H")==False:
                b.lock_location = [True] * 3
            b.lock_scale = [True] * 3
            if b.name.endswith("_P"):
                b.lock_rotation = [True]*3

    def foot_finger_forg3(self):
        if Global.getIsG3()==False:
            return
        lrs = ['l','r']
        pbs = Global.getAmtr().pose.bones
        for lr in lrs:
            keys = [lr+'BigToe']
            for i in range(4):
                keys.append(lr+'SmallToe'+(str(i+1)))
            for i in range(5):
                for pb in pbs:
                    if pb.name == keys[i]:
                        cr = pb.constraints.new(type='COPY_ROTATION')
                        cr.target = Global.getAmtr()
                        cr.subtarget = lr+"Toe"
                        cr.use_x = True
                        cr.use_y = False
                        cr.use_z = False
                        Versions.mix_mode(cr)
                        cr.target_space = 'LOCAL'
                        cr.owner_space = 'LOCAL'

    def friday(self):
        hide_objs = []
        hids = ['genital', '_gens_', '_shell', 'xy', 'alegen', '_gen_', 'goldenpalace', 'breastacular']
        for dobj in bpy.data.objects:
            dnl = dobj.name.lower()
            for h in hids:
                if h in dnl:
                    if Global.get_Hair_name() !=dobj.name:
                        hide_objs.append(dobj.name)
            else:
                if Global.isRiggedObject(dobj):
                    for modifier in dobj.modifiers:
                        if modifier.type == "ARMATURE":
                            modifier.use_deform_preserve_volume = True
        if len(hide_objs) > 0:
            Versions.to_other_layer(hide_objs, 'genital_shell')
        DtbShaders.default_material()
        Versions.make_camera()
        Global.scale_environment(100)

    def finishjob(self):
        if Global.getIsPro():
            from . import ToHighReso
            thr = ToHighReso.ToHighReso()
            thr.corrective_smooth()
            thr.toCorrectVWeight1()
        Global.deselect()
        if Global.getIsG3():
            self.foot_finger_forg3()
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode('POSE')
        Versions.show_x_ray(Global.getAmtr())
        Versions.show_wire(bpy.context.object)
        for ob in bpy.data.objects:
            if Global.isRiggedObject(ob):
                for m in ob.modifiers:
                    if m.name == 'Armature':
                        m.show_on_cage = True
                        m.show_in_editmode = True
                ob.use_shape_key_edit_mode = True
        b3 = ['root','rShin_P','lShin_P','hip']
        for b in b3:
            pb = Global.getAmtr().pose.bones.get(b)
            if pb is not None:
                pb.rotation_mode = 'XYZ'
        self.eyes_correct()
        bpy.ops.pose.select_all(action='DESELECT')
        self.mesh_under_bone()
        Versions.reverse_language()
        Versions.pivot_active_element_and_center_and_trnormal()
        Global.setRenderSetting(Global.getIsPro())

    def mesh_under_bone(self):
        adr = Global.getRootPath() + "DTB.dat"
        if os.path.exists(adr):
            with open(adr) as f:
                ls = f.readlines()
            for l in ls:
                ss = l.split(",")
                if len(ss) >= 2:
                    if (ss[1].endswith("\n")):
                        ss[1] = ss[1][:len(ss[1]) - 1]
                    ss[1] += ".Shape"
                    if (ss[1] in bpy.data.objects) and (ss[0] in Global.getAmtr().pose.bones):
                        obj = bpy.data.objects.get(ss[1])
                        vgs =obj.vertex_groups
                        for vs in vgs:
                            obj.vertex_groups.remove(vs)
                        Versions.select(bpy.data.objects.get(ss[1]), True)
                        Global.getAmtr().pose.bones.get(ss[0]).bone.select = True
                        Global.getAmtr().data.bones.active = Global.getAmtr().data.bones.get(ss[0])
                        bpy.ops.object.parent_set(type='BONE')
                        Global.deselect()

    def eyes_correct(self):
        bpy.ops.pose.select_all(action='DESELECT')
        eyes = ['lEye', 'rEye']
        for eye in eyes:
            e = Global.getAmtr().pose.bones.get(eye)
            if e is not None:
                e.bone.select = True
                Versions.pose_apply()
                e.bone.select = False

    def subdiv(self):
        body = Global.getBody()
        Versions.select(body,True)
        Versions.active_object(body)
        bpy.ops.object.modifier_add(type='SUBSURF')
        Versions.set_subdiv(body)

    def layGround(self):
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.color_type = 'OBJECT'
        Versions.set_english()
        bco = bpy.context.object
        if bco != None and bco.mode != 'OBJECT':
            Global.setOpsMode('OBJECT')
            bpy.ops.view3d.snap_cursor_to_center()
            for item in bpy.context.scene.objects:
                Versions.set_link(item,False)
        for item in bpy.data.objects:
            bpy.data.objects.remove(item)
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)
        for item in bpy.data.materials:
            bpy.data.materials.remove(item)
        Versions.make_sun()
        
        
        
