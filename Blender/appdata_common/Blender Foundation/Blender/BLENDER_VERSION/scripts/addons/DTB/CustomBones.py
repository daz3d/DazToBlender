import bpy
from . import Global
from . import Versions
from . import Util
hikfikpole=[0.7,1.7,0.3]
class CBones:
    face_bones = []
    limb_bones = []
    unconnect = 'tongue'
    hide = ['upperfacerig','lowerfacerig']
    shapes = ['triang_up', 'triang_down', 'triang_yoko','rhombus1', 'rhombus2',
              'pentagon',
              'octagon1','octagon2','square1','square2','rect1','rect2']
              
    def __init__(self):
        self.face_bones = []
        self.limb_bones = []
        if len(self.shapes) > 12:
            self.shapes = self.shapes[0:12]
        Global.setOpsMode("EDIT")
        self.makeRootBone()
        Global.deselect()
        self.makeMesh()
        Global.setOpsMode('OBJECT')
        Global.deselect()
        self.makeCustomBone()
        Global.setOpsMode('OBJECT')
        Global.deselect()
        self.makeIkBone()
        Global.setOpsMode('OBJECT')
        Global.deselect()
        self.makeEyes()
        Util.to_other_collection_byname(self.shapes,'DAZ_HIDE',Util.cur_col_name())

    def makeMesh(self):
        vertss = [
            [[-1, 0, -1], [0, 0, 1], [1, 0, -1]],
            [[-1, 0, 1], [0, 0, -1], [1, 0, 1]],
            [[-1, 0, 0], [1, 0, 1], [1, 0, -1]],
            [[1, 0, 0], [0, 0, -1], [-1, 0, 0], [0, 0, 1]],
            [[1, 0, 0], [0, 0, -1], [-1, 0, 0], [0, 0, 1]],
            [[0.6, 0, -1], [1, 0, 0.2], [0, 0,0.9], [-1, 0, 0.2], [-0.6, 0, -1]],
            [[-0.5, 0, -1], [-1, 0, -0.5], [-1, 0, 0.5], [-0.5, 0, 1], [0.5, 0, 1], [1, 0, 0.5], [1, 0, -0.5],[0.5, 0, -1]],
            [[-0.5, 0, -1], [-1, 0, -0.5], [-1, 0, 0.5], [-0.5, 0, 1], [0.5, 0, 1], [1, 0, 0.5], [1, 0, -0.5],[0.5, 0, -1]],
            [[1, 0, 1], [-1, 0, 1], [-1, 0, -1], [1, 0, -1]],
            [[-0.5, 0.5, 0], [0.5, 0.5, 0], [0.5, -0.5, 0], [-0.5, -0.5, 0]],
            [[-0.1, 2, 0], [0.1, 2, 0], [0.1, -2, 0], [-0.1, -2, 0]],
            [[-0.1, 2, 0], [0.1, 2, 0], [0.1, -2, 0], [-0.1, -2, 0]]
        ]
        for sidx,sp in enumerate(self.shapes):
            if sp in Util.colobjs('DAZ_HIDE'):
                continue
            me = bpy.data.meshes.new(sp+'_mesh')
            ob = Util.allobjs().new(sp, me)
            ob.show_name = True

            edges = []
            e2 = []
            for i in range(len(vertss[sidx])-1):
                e2.append([i, i+1])
            e2.append([len(vertss[sidx])-1,0])
            edges.extend(e2)
            nowvs = []
            plus = 1
            if sidx<2:
                plus = 20
            elif sp == 'triang_yoko':
                plus = 10
            elif sp == 'rect1':
                plus = 4
            elif sp == 'rect2':
                plus = 5
            elif sp == 'square2':
                plus = 3
            elif sp == 'square1':
                plus = 0
            elif sp == 'maru2':
                plus = -1
            elif sp == 'octagon1':
                plus = 1.5
            elif sp == 'octagon2':
                plus = -2
            for vs in vertss[sidx]:
                if sidx>=9:
                    wk = vs[0]
                    vs[0] = vs[2]
                    vs[2] = wk
                if sp == 'rhombus2':
                    wk = vs[1]
                    vs[1] = vs[2]
                    vs[2] = wk
                nowvs.append((vs[0],vs[1]+plus,vs[2]))
            me.from_pydata(nowvs, edges, [])
            me.update()
        Global.setOpsMode('OBJECT')
        f2 = ['cube1', 'cube2']
        for i in range(2):
            if f2[i] in Util.colobjs('DAZ_HIDE'):
                continue
            bpy.ops.mesh.primitive_cube_add()
            Global.setOpsMode('EDIT')
            bpy.ops.transform.resize(value=(0.5, 0.5, 0.01))
            Global.setOpsMode('OBJECT')
            bpy.context.object.name = f2[i]
            self.shapes.append(f2[i])
        for i in range(4):
            Global.deselect()
            name = 'maru' + str(i+1)
            if name in Util.colobjs('DAZ_HIDE'):
                continue
            bpy.ops.mesh.primitive_circle_add()
            bpy.context.object.name = 'maru'+str(i+1)
            Global.setOpsMode('EDIT')
            Versions.orientation_to_global()
            if i<3:
                Versions.rotate(90,'x')
            if i==0:
                bpy.ops.transform.translate(value=(0, 4, 0))
            elif i==1:
                bpy.ops.transform.translate(value=(0, 2, 0))
            else:
                bpy.ops.transform.translate(value=(0, 0, 0))

            if i == 1:
                bpy.ops.transform.resize(value=(1, 0.5, 1))
            Global.setOpsMode('OBJECT')
            self.shapes.append('maru'+str(i+1))

    def limit_location(self,pbone):
        lr = pbone.constraints.new(type='LIMIT_LOCATION')
        lr.owner_space = 'LOCAL'
        lr.use_min_x = True
        lr.use_max_x = True
        lr.use_min_y = True
        lr.use_max_y = True
        lr.use_min_z = True
        lr.use_max_z = True
        max = 2
        min = -2
        plower = pbone.name.lower()
        if plower.endswith("eye") or plower.endswith("teeth") or plower == 'lowerfacerig':
            max = 0.2
            min = -0.2
        lr.min_x = min
        lr.max_x = max
        lr.min_y = min
        lr.max_y = max
        lr.min_z = min
        lr.max_z = max

    def makeCustomBone(self):
        Global.deselect()
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Versions.bone_display_type(Global.getAmtr())
        self.find_bone('head')
        limb4 = ['rHand','rFoot','lHand','lFoot']
        for lb in limb4:
            self.find_bone(lb)
        Global.setOpsMode('POSE')
        Global.getAmtr().data.show_bone_custom_shapes = True
        end_bones = []
        for fb in self.face_bones:
            if ( fb in bpy.context.object.pose.bones) == False:
                continue
            pbone = Global.getAmtr().pose.bones[fb]
            bai = 0.06
            if Global.getAmtr().data.bones[fb].parent.name =='lowerFaceRig':
                ob = Util.allobjs()['rhombus2']
            elif 'tongue' in fb:
                ob = Util.allobjs()['rect2']
                bai = 0.2
            else:
                ob = Util.allobjs()['rhombus1']
            if 'ear' in fb.lower():
                if Global.getIsMan():
                    ob = Util.allobjs()['octagon1']
                    bai = 1.2
                else:
                    ob = Util.allobjs()['octagon2']
                    bai = 1.5
            end_bones.append(fb)
            if ('eyelidinner' in fb.lower()) or ('eyelidouter' in fb.lower()):
                ob = Util.allobjs()['triang_yoko']
                bai = 0.08
            elif 'eyelid' in fb.lower():
                if 'lower' in fb.lower():
                    ob = Util.allobjs()['triang_down']
                else:
                    ob = Util.allobjs()['triang_up']
                bai = 0.05
            elif fb.lower()== 'lowerjaw':
                ob = Util.allobjs()['octagon2']
                bai = 3
            self.limit_location(pbone)
            pbone.custom_shape = ob
            pbone.custom_shape_scale = bai
            pbone.lock_location=[False]*3
            pbone.lock_rotation = [False]*3
        for lb in self.limb_bones:
            if ( lb in bpy.context.object.pose.bones) == False:
                continue
            end_bones.append(lb)
            ob = Util.allobjs()['octagon1']
            pbone = bpy.context.object.pose.bones[lb]
            bai = 0.34
            if ('carpal' in lb.lower()) or lb.lower().endswith('thumb1'):
                ob = Util.allobjs()['rect2']
                bai = 0.1
                if lb.lower().endswith('thumb1'):
                    bai = 0.12
            elif 'metatarsals' in lb.lower():
                ob = Util.allobjs()['rect1']
                bai = 0.1
            elif lb.endswith("1") and ('toe' in lb.lower())==False:
                bai = 0.18
            elif lb.lower().endswith("toe") and len(lb)==4:
                ob = Util.allobjs()['octagon2']
            pbone.custom_shape = ob
            pbone.custom_shape_scale = bai
        for lb in limb4:
            if ( lb in bpy.context.object.pose.bones) == False:
                continue
            end_bones.append(lb)
            ob = Util.allobjs()['maru3']
            pbone = bpy.context.object.pose.bones[lb]
            pbone.custom_shape = ob
            bai = 0.5
            pbone.custom_shape_scale = bai
        for pb in Global.getAmtr().pose.bones:
            plower = pb.name.lower()
            if plower == 'lowerfacerig' or plower=='upperfacerig':
                Global.getAmtr().data.bones.get(pb.name).hide = True
            if 'twist' in plower:
                pb.custom_shape = Util.allobjs()['pentagon']
                pb.custom_shape_scale = 0.3
            elif 'collar' in plower:
                pb.custom_shape = Util.allobjs().get('rect1')
                pb.custom_shape_scale = 0.15
            elif plower == 'hip':
                pb.custom_shape = Util.allobjs().get('square1')
                pb.custom_shape_scale = 1.1
            elif 'breast' in plower:
                pb.custom_shape = Util.allobjs()['octagon1']
                pb.custom_shape_scale = 0.2
            elif 'areola' in plower:
                pb.custom_shape = Util.allobjs()['octagon1']
                pb.use_custom_shape_bone_size = False
                pb.custom_shape_scale = 2
            elif 'nipple' in plower:
                pb.custom_shape = Util.allobjs()['pentagon']
                pb.use_custom_shape_bone_size = False
                pb.custom_shape_scale = 1.1
            elif pb.custom_shape is None:
                if ('shin' in plower) or ('bend' in plower):
                    pb.custom_shape = Util.allobjs().get('octagon1')
                    if 'shin' in plower:
                        pb.custom_shape_scale = 0.15
                    else:
                        pb.custom_shape_scale = 0.3
                else:
                    pb.custom_shape = Util.allobjs().get('maru2')
                    if 'pectoral' in plower:
                        pb.custom_shape = Util.allobjs().get('maru1')
                        pb.custom_shape_scale = 0.2
                    elif 'neck' in plower:
                        pb.custom_shape = Util.allobjs().get('maru3')
                        pb.custom_shape_scale = 0.5
                    else:
                        if 'abdomen' in plower:
                            pb.custom_shape_scale = 0.5
                        else:
                            pb.custom_shape_scale = 0.3
            if pb.custom_shape is not None:
                pb.use_custom_shape_bone_size = True
                if pb.custom_shape_scale == 1.0:
                    pb.custom_shape_scale = 0.3
            pb.custom_shape_transform = pb
    def find_bone_roop(self,bone_group,rootbone):
        for b in bone_group:
            if len(b.children) > 0:
                self.find_bone_roop(b.children,rootbone)
            if rootbone=='head':
                self.face_bones.append(b.name)
            elif ('hand' in rootbone.lower()) or ('foot' in rootbone.lower()):
                self.limb_bones.append(b.name)

    def find_bone(self,rootbone):
        Global.setOpsMode('OBJECT')
        self.find_bone_roop(Global.getAmtr().data.bones[rootbone].children,rootbone)

    def makeIkBone(self):
        if 'hako' not in Util.allobjs():
            bpy.ops.mesh.primitive_cube_add()
            bpy.context.object.name = "hako"
        foots = ['rfoot_cube','lfoot_cube']
        for i in range(2):
            if (foots[i]  in Util.allobjs()):
                continue
            bpy.ops.mesh.primitive_cube_add()
            Global.setOpsMode('EDIT')
            bpy.ops.transform.resize(value=(0.8, 1.5, 0.2))
            bpy.ops.transform.translate(value = (0.2-(i*0.4),1.0,0.8))
            Versions.foot_ikbone_rotate(i)
            Global.setOpsMode('OBJECT')
            bpy.context.object.name = foots[i]
        if 'Icosphere' not in Util.allobjs():
            bpy.ops.mesh.primitive_ico_sphere_add()
        hobjs = ['hako', 'Icosphere','root.shape','lfoot_cube','rfoot_cube']
        Versions.select(Global.getAmtr(), True)
        Versions.active_object(Global.getAmtr())
        Global.setOpsMode('POSE')
        Global.getAmtr().data.show_bone_custom_shapes = True
        ctl_bones = ['rShin_P','lShin_P','root']
        for i in range(len(ctl_bones)):
            if (ctl_bones[i] in bpy.context.object.pose.bones)==False:
                continue
            bai = 2
            shape = 'root.shape'
            if i<2:
                bai = hikfikpole[2]
                shape = 'Icosphere'
            if (shape in Util.allobjs()):
                ob = Util.allobjs()[shape]
                bpy.context.object.pose.bones[ctl_bones[i]].custom_shape = ob
                bpy.context.object.pose.bones[ctl_bones[i]].custom_shape_scale = bai
            bpy.context.object.data.bones[ctl_bones[i]].show_wire = True
        ik_bones = ['rHand', 'lHand', 'rShin', 'lShin']
        ikshapes = ['hako', 'hako', 'rfoot_cube', 'lfoot_cube']
        for i in range(len(ik_bones)):
            if ((ik_bones[i]+"_IK") in bpy.context.object.pose.bones)==False:
                continue
            bai = hikfikpole[1]
            if i > 1:
                bai = hikfikpole[0]
            bpy.context.object.pose.bones[ik_bones[i] + "_IK"].custom_shape = Util.allobjs().get(ikshapes[i])
            bpy.context.object.pose.bones[ik_bones[i] + "_IK"].custom_shape_scale = bai
            bpy.context.object.pose.bones[ik_bones[i] + "_IK"].rotation_mode = 'XYZ'
            bpy.context.object.data.bones[ik_bones[i] + "_IK"].show_wire = True
            if i<2:
                bpy.context.object.pose.bones[ik_bones[i] + "_IK"].use_custom_shape_bone_size = True
        self.shapes.extend(foots)
        self.shapes.extend(ikshapes)
        self.shapes.extend(hobjs)

    def makeRootBone(self):
        dobj = Global.getAmtr()
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        Global.setOpsMode('EDIT')
        if 'root.shape' not in Util.allobjs():
            me = bpy.data.meshes.new('root_mesh')
            ob = Util.allobjs().new('root.shape', me)
            ob.show_name = True
            Versions.set_link(ob,True,'DAZ_HIDE')
            edges = []
            e2 = []
            list =  [1, 5, 9, 13, 33, 41, 46, 40, 32, 12, 8, 4, 0, 24, 20, 16, 28, 36, 44, 38, 30, 18, 22, 26, 2, 6, 10,
             14, 34, 42, 47, 43, 35, 15, 11, 7, 3, 27, 23, 19, 31, 39, 45, 37, 29,17, 21, 25, 1]
            for i in range(len(list)-1):
                e2.append([list[i],list[i+1]])
            edges.extend(e2)
            from . import DataBase
            db = DataBase.DB()
            me.from_pydata(db.root_verts, edges, [])
            me.update()
        dobj.data.edit_bones['hip'].parent = dobj.data.edit_bones.get('root')
        Global.setOpsMode("OBJECT")

    #TODO : Redo the logic so it doesn't rely on naming conventions of bones
    def makeEyes(self):
        Global.setOpsMode("EDIT")
        mihon3 = ['MidNoseBridge','rEye','lEye']
        newbname3 = ['mainEye_H','rEye_H','lEye_H']
        for bidx,nbname in enumerate(newbname3):
            if not mihon3[bidx] in bpy.context.object.data.edit_bones.keys():
                return
        for bidx,nbname in enumerate(newbname3):
            nbone = bpy.context.object.data.edit_bones.new(nbname)
            mihon = bpy.context.object.data.edit_bones[mihon3[bidx]]
            nbone.use_deform = False
            for i in range(3):
                nbone.head[i] = mihon.head[i]
                nbone.tail[i] = mihon.tail[i]
                if i==1:
                    nbone.head[i] -= 10
                    nbone.tail[i] -= 10
            if bidx==0:
                nbone.parent = Global.getAmtr().data.edit_bones.get('upperFaceRig')
            else:
                nbone.parent = Global.getAmtr().data.edit_bones.get(newbname3[0])
        Global.setOpsMode('POSE')

        for nidx,nb in enumerate(newbname3):
            pb = Global.getAmtr().pose.bones.get(nb)
            pb.rotation_mode = 'XYZ'
            if nidx==0:
                pb.custom_shape = Util.allobjs().get('rhombus1')
                pb.custom_shape_scale = 0.6
            else:
                if Global.getIsMan():
                    pb.custom_shape = Util.allobjs().get('maru3')
                else:
                    pb.custom_shape = Util.allobjs().get('maru3')
                pb.custom_shape_scale = 3
            for i in range(3):
                if i==1:
                    pb.lock_location[i] = True
                else:
                    pb.lock_location[i] = False
                pb.lock_rotation[i] = True
        for i in range(1,3):
            pb = Global.getAmtr().pose.bones.get(mihon3[i])
            cs = pb.constraints.new(type='DAMPED_TRACK')
            cs.target = Global.getAmtr()
            cs.subtarget = newbname3[i]
            if Global.getIsMan():
                cs.track_axis = 'TRACK_Y'
            else:
                cs.track_axis = 'TRACK_Y'
            cs.influence = 1
