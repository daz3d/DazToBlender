import bpy
import bmesh
from .import Global
from . import Versions
class ToHighReso:
    max3 = []
    def __init__(self):
        pass
    def toCorrectVWeight1(self):
        self.max3 = Global.getMyMax3()
        lev = Global.getSubdivLevel()
        for i in range(4):
            if lev == 0:
                break
            if lev == 1 and i<2:
                continue
            self.toCorrectVWeight2(i)

    def get_yuko_verts(self,bv0,mesh,z):
        rtn_vs = []
        for eidx,edge in enumerate(bv0.link_edges):
            bv = edge.other_vert(bv0)
            if z>1:
                mv = mesh.vertices[bv.index]
                if (mv in rtn_vs)==False:
                    if len(mv.groups) > 0:
                        rtn_vs.append([mv,eidx])
            else:
                for edge2 in bv.link_edges:
                    bv2 = edge2.other_vert(bv)
                    mv = mesh.vertices[bv2.index]
                    if (mv in rtn_vs) == False:
                        if len(mv.groups) > 0:
                            rtn_vs.append([mv, eidx])
        return rtn_vs



    def toCorrectVWeight2(self,z):
        file_ary = []
        Global.setOpsMode('OBJECT')
        Versions.select(Global.getBody(),True)
        Versions.active_object(Global.getBody())
        bpy.ops.object.mode_set(mode='EDIT')
        obj = Global.getBody()
        vgs = obj.vertex_groups
        mesh = obj.data
        all_avg_ary = []
        bm = bmesh.from_edit_mesh(mesh)
        for v in bm.verts:
            if v.index < self.max3[0]:
                continue
            if z<2:
                if v.index >= self.max3[1]:
                    break
            avg_ary = []

            if len(mesh.vertices[v.index].groups) > 0:
                continue
            fline = str(v.index)+","
            yuko_vs = self.get_yuko_verts(v,mesh,z)
            for yuko in yuko_vs:
                pvs = yuko[0]
                eidx = yuko[1]
                for g in pvs.groups:
                    gidx = g.group
                    weight = g.weight
                    if gidx < len(vgs):
                        find = False
                        for aidx, aa in enumerate(avg_ary):
                            if aa[0] == gidx:
                                avg_ary[aidx][eidx + 1] = weight
                                find = True
                                break
                        max = len(avg_ary)
                        if find == False:
                            avg = [gidx, -1, -1, -1, -1]
                            avg[eidx + 1] = weight
                            avg_ary.append(avg)
                            for i in range(max):
                                if avg_ary[i][eidx+1]<0:
                                    avg_ary[i][eidx + 1] = 0.0
            file_ary.append(fline)
            for avg in avg_ary:
                max = 0
                sum = 0
                for i in range(4):
                    if avg[i + 1] > -1:
                        max += 1
                        sum = sum + avg[i + 1]
                if max % 2 == 1:
                    max += 1
                all_avg_ary.append([avg[0], v.index, sum / max,vgs[avg[0]].name])
        bpy.ops.object.mode_set(mode='OBJECT')
        for a in all_avg_ary:
            vgs[a[0]].add([a[1]], a[2], 'ADD')


    def armpit(self):
        con  = Global.getCon()
        cur = con.cursor()
        vgs = Global.getBody().vertex_groups
        vgs.new(name='armpit')
        fm = ['f','m']
        sx = fm[Global.getSex()]
        sql = "select VID,WEIGHT from armpit_" + sx + " order by VID"

        max3 = Global.getMyMax3()
        cur.execute(sql)
        leng = Global.getMyMax3()[Global.getSubdivLevel()]
        for row in cur:
            if row[0]<leng:
                vid = row[0]
                if Global.get_geo_idx()>0:
                    vid = Global.toGeniVIndex(vid)
                if max3[0]<=vid:
                    continue
                vgs[len(vgs)-1].add([vid], row[1], 'ADD')
            else:
                break
        cur.close()
        con.close()

    def corrective_smooth(self):
        self.armpit()
        body = Global.getBody()
        Versions.select(body,True)
        Versions.active_object(body)
        bpy.ops.object.modifier_add(type='CORRECTIVE_SMOOTH')
        Versions.set_csmooth(body,1.0,10,'armpit')

class get_Morph:
    dst_obj = None
    flg_base = False
    flg_manualed = False
    is_manualed = False
    con = None
    cur = None
    kword = ""
    my_vscount = 0
    myfloat = 1.0
    def __init__(self,adr,kwd):
        self.my_vscount = 0
        self.kword = kwd
        Global.decide_HERO()
        if Global.getAmtr() is None:
            Versions.msg("This feature is not available in Rigify mode.","Only Basic Mode", "ERROR")
            return
        self.flg_base = kwd.startswith("get")
        self.dst_obj = Versions.import_obj(adr)

        if self.judge_is_correct_vcount()==False:
            bpy.data.objects.remove(self.dst_obj)
            Versions.msg("Wrong .OBJ file","Wrong .OBJ", "ERROR")
            self.dst_obj = None
        else:
            if (Global.getBody().dimensions[0] *50)< self.dst_obj.dimensions[0]:
                for i in range(3):
                    self.dst_obj.scale[i] = self.dst_obj.scale[i] * 0.01
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            if self.flg_base:
                a = kwd.find('0.')
                if a>5:
                    f = float(kwd[a:])
                    if f>0.0 and f<1.0:
                        self.myfloat = f

    def judge_is_correct_vcount(self):
        your_vscount = len(self.dst_obj.data.vertices)
        max3 = Global.getMyMax3()
        self.my_vscount = max3[Global.getSubdivLevel()]
        if (your_vscount in max3) and your_vscount >= self.my_vscount:
            return True
        else:
            return False
    def get_face_or_body(self,b_name):
        if self.dst_obj is None:
            Versions.msg("Geometry does not match or there are not enough vertices.","ERROR","ERROR")
            return
        kjns = [[[57,101],[7915,7908],[10681,8303]],[[57,93],[7538,7532],[10132,9576]]]
        #3930,3705
        kjns_index = 0
        if b_name.endswith("hand"):
            kjns_index = 1
        elif b_name.endswith("knee"):
            kjns_index = 2
        kjn = kjns[Global.getSex()][kjns_index]
        if kjns_index%2==1 and b_name.startswith("l"):
            for i in range(2):
                kjn[i] = Global.get_symmetry(kjn[i],True)
        if Global.get_geo_idx()>0:
            for i in range(len(kjn)):
                kjn[i] = Global.toGeniVIndex(kjn[i])
        bm = None

        src_verts = Global.getBody().data.vertices
        dst_verts = self.dst_obj.data.vertices
        dst_xyz = []
        src_xyz = []
        sa_xyz = []
        for i in range(3):
            dst_xyz.append((dst_verts[kjn[0]].co[i]+dst_verts[kjn[1]].co[i])/2)
            src_xyz.append((src_verts[kjn[0]].co[i]+src_verts[kjn[1]].co[i])/2)
            sa_xyz.append(dst_xyz[i]-src_xyz[i])

        Versions.active_object(Global.getBody())
        if self.flg_base == False:
            bpy.ops.object.shape_key_add(from_mix=False)
            kb = Global.getBody().data.shape_keys.key_blocks[-1]
            kb.value = 1.0
            kb.name  = self.dst_obj.name
        else:
            Versions.select(Global.getBody(),True)
            bpy.context.active_object.active_shape_key_index = 0
            Global.setOpsMode("EDIT")

            bm = bmesh.from_edit_mesh(Global.getBody().data)
            bm.verts.ensure_lookup_table()
        if b_name.endswith('hand'):
            if b_name.startswith("r"):
                br = Global.BoneRoop('rHand')
            else:
                br = Global.BoneRoop('lHand')
        elif b_name.endswith("knee"):
            if b_name.startswith("r"):
                br = Global.BoneRoop('rThighBend')
            else:
                br = Global.BoneRoop('lThighBend')
        else:
            br = Global.BoneRoop('neckLower')
        fary = br.getResultVertices()
        bary = []
        if b_name == 'body':
            max = self.my_vscount
            for i in range(max):
                weight = 1.0
                for fa in fary:
                    if i==fa[0]:
                        weight =1.0-fa[1]
                        break
                if weight>0.0:
                    bary.append([i,weight])
            fary = []
            fary.extend(bary)

        for fa in fary:
            vidx = fa[0]
            dvidx = vidx
            if vidx>=self.my_vscount:
                continue
            dst_vs = self.dst_obj.data.vertices[dvidx]
            for i in range(3):
                if self.flg_base:
                    sa = dst_vs.co[i] - bm.verts[vidx].co[i]
                else:
                    sa = dst_vs.co[i] - kb.data[vidx].co[i]

                fvalue = float(fa[1])
                if fvalue<1.0:
                    sa = sa * fvalue
                    sa = sa - sa_xyz[i]*fvalue
                else:
                    sa = sa - sa_xyz[i]

                if self.flg_base:
                    sa = sa * self.myfloat
                    bm.verts[vidx].co[i]+=sa
                else:
                    kb.data[vidx].co[i] +=sa
        if self.flg_base:
            bmesh.update_edit_mesh(Global.getBody().data)
            Global.setOpsMode("OBJECT")
        if b_name[:1]!='r':
            bpy.data.objects.remove(self.dst_obj)

def removeEyelash():
    Global.deselect()
    Versions.select(Global.getBody(), True)
    Versions.active_object(Global.getBody())
    Global.setOpsMode("EDIT")
    find = False
    bpy.ops.mesh.select_all(action='DESELECT')
    for sidx, slot in enumerate(Global.getBody().material_slots):
        if slot.name.startswith("drb_EylsMoisture") or slot.name.startswith("drb_Eyelashes"):
            Global.getBody().active_material_index = sidx
            bpy.ops.object.material_slot_select()
            find = True
    bm = bmesh.from_edit_mesh(Global.getBody().data)
    bm.verts.ensure_lookup_table()
    cnt = 0
    for i in range(1,60):
        if bm.verts[len(bm.verts)-i].select:
            cnt += 1
    if cnt>50 and find:
        bpy.ops.mesh.separate(type='SELECTED')
        sobjs = bpy.context.selected_objects
        for sobj in sobjs:
            if sobj !=Global.getBody():
                sobj.name = 'EyeLash'
    Global.deselect()
    Global.setOpsMode('OBJECT')
    Versions.active_object(Global.getBody())
    Global.setOpsMode('OBJECT')
