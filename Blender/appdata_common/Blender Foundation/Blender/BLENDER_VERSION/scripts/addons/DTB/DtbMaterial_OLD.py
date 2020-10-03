import os
import bpy
from . import Global
from . import NodeArrange
from . import Versions
from . import MatDct
from . import Util
NGROUP3 = ['mcy_skin','mcy_eyewet','mcy_eyedry']
SKIN = 0
EWET = 1
EDRY = 2

def ngroup3(idx):
    return NGROUP3[idx] + Util.get_dzidx()

mtable = [
    ["Torso", 2],
    ["Face", 1],
    ["Lips", 1],
    ["Teeth", 5],
    ["Ears", 1],
    ["Legs", 3],
    ["EyeSocket", 1],
    ["Mouth", 5],
    ["Arms", 4],
    ["Pupils", 7],
    ["Fingernails", 4],
    ["Cornea", 8],
    ["Irises", 7],
    ["Sclera", 7],
    ["Toenails", 3],
    ["EyeMoisture", 8],
    ["EyeMoisture.00", 8],
    ["Eyelashes", 0],
    ["EylsMoisture", 8],
    ["Genitalia", 2],
    ["anus", 9], ["labia", 9], ["clitoris", 9], ["vagina", 9], ["glans", 9], ["shaft", 9], ["testicles", 9],
    ["rectum", 9],
]
ftable = [["d","Diffuse"],
          ["b","Bump"],
          ["s","Specular"],
          ["r","Roughness"],
          ["z","Subsurface"],
          ["n","Normal"]]
class DtbShaders:
    dct ={}
    evaluate = -1

    def makeDct(self):
        self.dct = []
        md = MatDct.MatDct()
        md.makeDctFromMtl()
        self.dct =md.getResult()
        self.evaluate = md.getEvaluate()

    def __init__(self):
        pass

    def eyelash(self,ROOT,LINK,cyclesOUT,eeveeOUT,mname):
        adr = ""
        ALF = ROOT.new(type='ShaderNodeBsdfTransparent')
        if "0t" in self.dct.keys():
            adr = self.dct["0t"]
        if os.path.exists(adr) == False:
            LINK.new(ALF.outputs['BSDF'], cyclesOUT.inputs[0])
            LINK.new(ALF.outputs['BSDF'], eeveeOUT.inputs[0])
            return
        SNTIMG = ROOT.new(type='ShaderNodeTexImage')
        SNTIMG.name = Global.img_format(mname, "t")
        img = bpy.data.images.load(filepath=adr)
        SNTIMG.image = img
        MIX = ROOT.new(type='ShaderNodeMixShader')
        DIF = ROOT.new(type='ShaderNodeBsdfDiffuse')
        IVT = ROOT.new(type='ShaderNodeInvert')
        DIF.inputs['Color'].default_value = (0.1,0.1,0.1,1)
        DIF.inputs['Roughness'].default_value = 0.2
        nodemap = [
        [IVT.inputs['Color'], SNTIMG.outputs['Color']],
        [ MIX.inputs[0], IVT.outputs['Color']],
        [MIX.inputs[2], ALF.outputs['BSDF']],
        [MIX.inputs[1],DIF.outputs['BSDF']],
        [MIX.outputs[0], cyclesOUT.inputs[0]],
        [MIX.outputs[0], eeveeOUT.inputs[0]]
        ]
        for n in nodemap:
            LINK.new(n[0],n[1])

    def bodyTexture(self):
        moisture_count = 0
        for slot in Global.getBody().material_slots:
            for midx in range(len(mtable)):
                m_name = mtable[midx][0]
                mban = mtable[midx][1]
                if m_name.lower() in slot.name.lower():
                    mname = "drb_" + m_name + Util.get_dzidx()
                    if "Moisture" in slot.name:
                        moisture_count += 1
                        if moisture_count>1 and ('.0' in slot.name):
                            mname = 'drb_EylsMoisture' + Util.get_dzidx()
                    if mname not in bpy.data.materials:
                        mat = bpy.data.materials.new(name=mname)
                    else:
                        mat = bpy.data.materials.get(mname)
                    mname = mat.name
                    bpy.data.materials[mname].use_nodes = True
                    ROOT = bpy.data.materials[mname].node_tree.nodes
                    LINK = bpy.data.materials[mname].node_tree.links
                    dels = ['Material Output','Diffuse BSDF', 'Principled BSDF']
                    for r in ROOT:
                        for d in dels:
                            if r.name == d:
                                ROOT.remove(ROOT[d])
                                break
                    cyclesOUT = ROOT.new(type="ShaderNodeOutputMaterial")
                    cyclesOUT.target = 'CYCLES'
                    eeveeOUT = ROOT.new(type="ShaderNodeOutputMaterial")
                    eeveeOUT.target = 'EEVEE'
                    SNBP = ROOT.new(type='ShaderNodeGroup')
                    if mban==8:
                        SNBP.node_tree = bpy.data.node_groups[ngroup3(EWET)]
                    elif mban==7:
                        SNBP.node_tree = bpy.data.node_groups[ngroup3(EDRY)]
                    elif mban==0:
                        Versions.eevee_alpha(mat, 'BLEND', 0)
                        ROOT.remove(SNBP)
                        self.eyelash(ROOT, LINK, cyclesOUT, eeveeOUT,mname)
                        slot.material = mat
                        break
                    else:
                        SNBP.node_tree = bpy.data.node_groups[ngroup3(SKIN)]
                    if mban==7 or mban==0 or mname=='drb_EyeSocket':
                        LINK.new(SNBP.outputs['EEVEE'],cyclesOUT.inputs['Surface'])
                    else:
                        if Global.getIsPro():
                            LINK.new(SNBP.outputs['Cycles'], cyclesOUT.inputs['Surface'])
                        else:
                            LINK.new(SNBP.outputs['EEVEE'], cyclesOUT.inputs['Surface'])
                    if mban>0 and mban<7 and Global.getIsPro():
                        LINK.new(SNBP.outputs['Displacement'], cyclesOUT.inputs['Displacement'])
                    LINK.new(SNBP.outputs['EEVEE'], eeveeOUT.inputs['Surface'])
                    bc_key =slot.name.lower()+"_c"
                    bc_value = []
                    if bc_key in self.dct.keys():
                        bc_value = self.dct[bc_key]
                    if len(bc_value)==4 and mban!=8:
                        SNBP.inputs['Diffuse'].default_value = (bc_value[0],bc_value[1],bc_value[2],bc_value[3])
                    if mban == 8 :
                        Versions.eevee_alpha(mat,'HASHED',0)
                    if mban==0:
                        Versions.eevee_alpha(mat,'BLEND',0)
                        self.eyelashes(ROOT,LINK,SNBP.outputs['Cycles'],mname,cyclesOUT,eeveeOUT)
                    else:
                        for fidx,ft in enumerate(ftable):
                            if mname=='drb_Cornea':
                                break
                            key = str(mban)+ft[0]
                            if ft[1] not in SNBP.inputs:
                                continue
                            if key in self.dct.keys():
                                adr = self.dct[key]
                            else:
                                adr = ""
                            if os.path.exists(adr) == False:
                                continue
                            SNTIMG =  ROOT.new(type='ShaderNodeTexImage')
                            SNTIMG.name = Global.img_format(mname, ft[0])
                            img = bpy.data.images.load(filepath=adr)
                            SNTIMG.image = img
                            out_sntimg_color = SNTIMG.outputs['Color']
                            if fidx!=0:
                                Versions.to_color_space_non(SNTIMG)
                            LINK.new(out_sntimg_color,SNBP.inputs[ft[1]])#[ftable[1][fidx]])
                            if fidx== 1 and mban<7 and mban>0:
                                LINK.new(out_sntimg_color, SNBP.inputs['Displacement'])
                    slot.material = mat
                    if mban==8 or mban==7 or mban==0 or Global.getIsPro()==False:
                        slot.material.cycles.displacement_method = 'BUMP'
                    else:
                        slot.material.cycles.displacement_method = 'BOTH'
            NodeArrange.toNodeArrange(ROOT)

    def propTexture(self):
        skip = [Global.get_Body_name(),Global.get_Hair_name()+"OK",Global.get_Eyls_name()]
        for obj in Util.myacobjs():
            if Global.isRiggedObject(obj):
                if obj.name in skip:
                    continue
                for slot in obj.material_slots:
                    mat = bpy.data.materials[slot.name]
                    if mat is None:
                        return
                    count = 0
                    LINK = mat.node_tree.links
                    ROOT = mat.node_tree.nodes
                    PBSDF = None
                    NORM = None
                    bckey = slot.name.lower()+"_c"
                    bc_value=[]
                    if bckey in self.dct.keys():
                        bc_value = self.dct[bckey]
                    if len(bc_value)==4 and bc_value[3]<1.0:
                        Versions.eevee_alpha(mat, 'BLEND', 0)
                    name4= ['Material Output', 'Image Texture', 'Principled BSDF','Normal Map']
                    source_adr = ""
                    if len(mat.node_tree.nodes)==5 or len(mat.node_tree.nodes)==4:
                        for node in ROOT:
                            for nidx,nm in enumerate(name4):
                                if node.name == nm:
                                    count += 1
                                    if nidx==1:
                                        source_adr = node.image.filepath
                                    elif nidx==2:
                                        PBSDF = node
                                    elif nidx==3:
                                        NORM = node
                        if source_adr!="":
                            md = MatDct.MatDct()
                            cary = md.cloth_dct_0(source_adr)
                            pandb = insertBumpMap(ROOT,LINK)
                            BUMP = pandb[1]
                            ROOT = pandb[0]
                            PBSDF.inputs['Specular'].default_value = 0.3
                            if(len(PBSDF.inputs['Alpha'].links)>0):
                                Versions.eevee_alpha(mat, 'BLEND', 0)
                            for ca in cary:
                                for ft in ftable:
                                    if ft[0] == 'd':
                                        continue
                                    if ca[0].endswith(ft[0]):
                                        SNTIMG = ROOT.new(type='ShaderNodeTexImage')
                                        SNTIMG.name = Global.img_format(mat.name, ft[0])
                                        img = bpy.data.images.load(filepath=ca[1])
                                        SNTIMG.image = img
                                        Versions.to_color_space_non(SNTIMG)
                                        if ft[0]=='n':
                                            if NORM is not None:
                                                LINK.new(SNTIMG.outputs['Color'], NORM.inputs['Color'])
                                        elif ft[0]=='b':
                                            if BUMP is not None:
                                                LINK.new(SNTIMG.outputs['Color'], BUMP.inputs['Height'])
                                        else:
                                            LINK.new(SNTIMG.outputs['Color'], PBSDF.inputs[ft[1]])
                    NodeArrange.toNodeArrange(ROOT)

def getGroupNode(key):
    for slot in Global.getBody().material_slots:
        ROOT = bpy.data.materials[slot.name].node_tree.nodes
        for n in ROOT:
            if n.name.startswith("Group"):
                if n.node_tree.name.startswith(key):
                    return n

def getGroupNodeTree(key):
    rtn = getGroupNode(key)
    if rtn is not None:
        return rtn.node_tree

def adjust_material(kind,inc_value,isEye):
    skincombi = [
    ['Base Color.Hue', 11, 0],
    ['Base Color.Saturation', 11, 1],
    ['Base Color.Value', 11, 2],
    ['Base Color.Bright', 8, 1],
    ['Base Color.Contrast', 8, 2],
    ['Specular', 9, 1],
    ['Roughness', 10, 1],
    ['Roughness.Contrast', 9, 2],
    ['Specular.Contrast', 10, 2],
    ['Subsurface.Scale', 14, 1],
    ['Subsurface.Scale', 13, 1],
    ['Normal.Strength', 5, 0],
    ['Bump.Strength', 6, 0],
    ['Bump.Distance', 6, 1],
    ['Displacement.Height',4,2],#14
    ['Subsurface.Scale', 2, 2],
    ['Subsurface.Scale', 2, 1],
    ]
    eyecombi = [
        ['Base Color.Bright', 1, 1],
        ['Base Color.Contrast', 1, 2],
        ['Normal.Strength', 3, 0],
        ['Bump.Strength', 4, 0],
        ['Bump.Distance', 4, 1],
        ['Base Color.Hue', 6, 0],
        ['Base Color.Saturation', 6, 1],
        ['Base Color.Value', 6, 2],
    ]
    flg_skin = False
    if isEye:
        tree = getGroupNodeTree(ngroup3(EDRY))
        tbls = eyecombi
    else:
        tree = getGroupNodeTree(ngroup3(SKIN))
        tbls = skincombi
        flg_skin = True
    if tree is None:
        return
    nds = tree.nodes
    for tidx,tbl in enumerate(tbls):
        if tbl[0]==kind:
            t1 = getNidx(int(tbl[1]),nds)
            dv = nds[t1].inputs[tbl[2]].default_value
            cg = 1.0
            if flg_skin:
                if tidx > 8 and tidx<16:
                    cg = cg * Global.getSize() * 0.01
                if tidx == 9:
                    cg = cg * 3
                elif tidx == 10:
                    cg = cg * 0.5
                elif tidx==16:
                    cg = cg * 0.2
                # elif tidx==14:
                #     cg = cg * 12
                # elif tidx>=11 or tidx<=13:
                #     cg = cg * 8
            cg = cg * inc_value
            if tidx==15:
                dv[0] += cg * 10
                dv[1] += cg * 2
                dv[2] += cg
            else:
                dv += cg
            nds[t1].inputs[tbl[2]].default_value = dv

def getNidx(idx,nodes):
    for nidx,n in enumerate(nodes):
        if n.name.endswith("-" + str(idx)):
            return nidx
    return idx



def toGroupInputsDefault(flg_eye):
    k3 = [EDRY, EWET, SKIN]
    for kidx, k in enumerate(k3):
        dist_n = getGroupNode(ngroup3(k))
        for mat in bpy.data.materials:
            if mat.node_tree is None:
                continue
            n = None
            for sch_n in mat.node_tree.nodes:
                if sch_n.name.startswith('Group')==False:
                    continue
                if sch_n.node_tree is None:
                    continue
                if sch_n.node_tree.name==dist_n.node_tree.name:
                    n = sch_n
                    break
            if n is None:
                continue
            if flg_eye and ('eye' in sch_n.node_tree.name):
                if ('dry' in sch_n.node_tree.name):
                    for i, inp in enumerate(sch_n.inputs):
                        if len(inp.links) > 0:
                            continue
                        if i == 2:
                            inp.default_value = (0.5, 0.5, 1, 1)
                        else:
                            inp.default_value = (0.6, 0.6, 0.6, 1)
                elif ('wet' in sch_n.node_tree.name):
                    for i, inp in enumerate(sch_n.inputs):
                        if len(inp.links) > 0:
                            continue
                        inp.default_value = (1.0,1.0,1.0,1.0)
            elif ('skin' in sch_n.node_tree.name):
                for i, inp in enumerate(sch_n.inputs):
                    if len(inp.links) > 0:
                        continue
                    if i == 4:
                        inp.default_value = (0.5, 0.5, 1, 1)
                    elif i < 6:
                        inp.default_value = (0.6, 0.6, 0.6, 1)
                    elif i == 6:
                        inp.default_value = (0.287, 0.672, 0.565, 1)
                    elif i == 7:
                        #inp.default_value = (0.479, 0.012, 0.014, 1)
                        inp.default_value = (0.479, 0.053, 0.065, 1)
                    elif i == 8:
                        inp.default_value = 0.7
                    mname = mat.name.lower()
                    if ('mouth' in mname) or ('teeth' in mname) or ('nail' in mname):
                        if i==1:
                            inp.default_value = (0.9, 0.9, 0.9, 1)
                        elif i==2:
                            inp.default_value = (0.2, 0.2, 0.2, 1)
                        if ('teeth' in mname) or ('nail' in mname):
                            if i==6:
                                if ('teeth' in mname):
                                    inp.default_value = (0.45, 0.45, 0.45, 1)
                                else:
                                    inp.default_value = (0.22,0.36, 0.5,  1)
                            elif i==7:
                                if ('teeth' in mname):
                                    inp.default_value = (0.45, 0.45, 0.45, 1)
                                else:
                                    inp.default_value = (0.5, 0.36, 0.22, 1)
                            elif i==8:
                                inp.default_value = 0.0

def toEyeDryDefault(ntree):
    if ntree is None:
        return
    toGroupInputsDefault(True)
    nodes = ntree.nodes
    dvs = [
        [1, 1, 0.0],
        [1, 2, 0.0],
        [2,1,0.08],
        [2,2,[Global.getSize()*0.006,Global.getSize()*0.003,Global.getSize()*0.003]],
        [2, 5, 0.0],
        [2, 6, 0.3],
        [2,7,0.0],
        [2, 'IOR', 1.35],
        [2, 'Transmission', 0.0],
        [2,'Sheen',0.0],
        [6,0,0.5],
        [6, 1, 1.0],
        [6, 2, 1.0],
        [3, 0, Global.getSize() * 0.001],  # NormalMap Strength
        [4, 0, Global.getSize() * 0.001],  # Bump Strength
        [4, 1, Global.getSize() * 0.001],  # Bump Distance
    ]
    for dv in dvs:
        dv0 = getNidx(int(dv[0]),nodes)
        if isinstance(dv[2], float) or isinstance(dv[2], int):
            nodes[dv0].inputs[dv[1]].default_value = dv[2]
        else:
            for i in range(len(dv[2])):
                nodes[dv[0]].inputs[dv[1]].default_value[i] = dv[2][i]
    NodeArrange.toNodeArrange(ntree.nodes)
    
def toEyeWetDefault(ntree):
    if ntree is None:
        return
    toGroupInputsDefault(True)
    nodes = ntree.nodes
    dvs = [[4, 0, 1.45],
           [6, 0, [1.0, 1.0, 1.0,1.0]],
           [7, 1, 0.0],
           [2, 0, 0.1],
           [3, 0, 0.1],
           [3, 1, 0.1],
           [7, 0, [1.0, 1.0, 1.0, 1.0]],
           [7, 1,0.0],
           [7, 4, 1.0],
           [7, 5, 1.0],
           [7, 7, 0.0],
           [7, 'Transmission', 1.0],
           [7, 'Alpha', 0.5],
           ]
    for dv in dvs:
        dv0 = getNidx(int(dv[0]),nodes)
        if isinstance(dv[2], float) or isinstance(dv[2], int):
            nodes[dv0].inputs[dv[1]].default_value = dv[2]
        else:
            for i in range(len(dv[2])):
                nodes[dv0].inputs[dv[1]].default_value[i] = dv[2][i]
    NodeArrange.toNodeArrange(ntree.nodes)

def toSkinDefault(ntree):
    if ntree is None:
        return
    toGroupInputsDefault(False)
    nds = ntree.nodes
    nds[getNidx(4,nds)].space = 'OBJECT'
    nds[getNidx(13,nds)].falloff = 'RANDOM_WALK'
    nds[getNidx(14,nds)].falloff = 'RANDOM_WALK'
    dvs = [[5, 0, Global.getSize()*0.01],  # NormalMap Strength
           [6, 0, Global.getSize()*0.002],  # Bump Strength
           [6, 1, Global.getSize()*0.002],  # Bump Distance
           [7, 0, 1.330],  # Fresnel
           [13, 1, Global.getSize()*0.005],  # BlueSSS
           [14, 1, Global.getSize()*0.030],  # RedSSS
           [8, 1, 0.0],
           [9, 1, 0.1],
           [10, 1, 0],
           [8, 2, 0.0],
           [9, 2, 0.0],
           [10, 2, 0.0],
           [2, 1, 0.1],
           [2, 4, 0.0],
           [2, 'IOR', 1.33],
           [2, 'Transmission', 0.0],
           [2, 'Alpha', 1.0],
           [4, 2, Global.getSize()*0.0012],#Displacement Height
           [4, 1, Global.getSize()*0.005],#Displacement Middle
           [13, 4, 0.1],
           [14, 4, 0.1],
           [2, 14, 1.33],
           [2,2,[0.04*Global.getSize(),0.008*Global.getSize(),0.002*Global.getSize()]],
           [11,0,0.5],
           [11,1,1.0],
           [11,2,1.0],
           [7,0,1.33],
           ]
    for dv in dvs:
        dv0 = getNidx(int(dv[0]),nds)
        if isinstance(dv[2], float) or isinstance(dv[2], int):
            nds[dv0].inputs[dv[1]].default_value = dv[2]
        else:
            for i in range(len(dv[2])):
                nds[dv0].inputs[dv[1]].default_value[i] = dv[2][i]
    NodeArrange.toNodeArrange(ntree.nodes)

def clear_past_nodegroup():
    for ng in NGROUP3:
        for s in bpy.data.node_groups:
            if s.name==ng:
                bpy.data.node_groups.remove(s,do_unlink = True)
                break
                
class McyEyeDry:
    shaders = []
    mcy_eyedry = None
    
    def __init__(self):
        self.shaders = []
        self.mcy_eyedry = None
        self.makegroup()
        self.exeEyeDry()
        
    def makegroup(self):
        self.mcy_eyedry = bpy.data.node_groups.new(type="ShaderNodeTree", name=ngroup3(EDRY))
        nsc = 'NodeSocketColor'
        self.mcy_eyedry.inputs.new(nsc, 'Diffuse')
        self.mcy_eyedry.inputs.new(nsc, 'Bump')
        self.mcy_eyedry.inputs.new(nsc, 'Normal')
        self.mcy_eyedry.outputs.new('NodeSocketShader', 'Cycles')
        self.mcy_eyedry.outputs.new('NodeSocketVector', 'Displacement')
        self.mcy_eyedry.outputs.new('NodeSocketShader', 'EEVEE')
        
    def exeEyeDry(self):
        generatenames = [ 'NodeGroupInput', 'ShaderNodeBrightContrast','ShaderNodeBsdfPrincipled', 'ShaderNodeNormalMap',
                          'ShaderNodeBump','NodeGroupOutput','ShaderNodeHueSaturation']
        con_nums = [[[0, 0], [6, 4]],#Diffuse
                    [[6,0],[1,0]],
                    [[1, 0], [2, 0]],
                    [[1, 0], [2, 3]],

                    [[0,2],[3,1]],    #Normal
                    [[3, 0], [4, "Normal"]],
                    [[0, 1], [4, "Height"]],
                    [[4,0],[2,'Normal']],
                    [[2, 0], [5, 0]], #Out
                    [[2, 0], [5, 2]],
        ]
        ROOT = self.mcy_eyedry.nodes
        LINK = self.mcy_eyedry.links
        old_gname = ""
        for gidx, gname in enumerate(generatenames):
            if gname == '':
                gname = old_gname
            a = gname.find('.')
            sub = None
            if a > 0:
                sub = gname[a + 1:]
                gname = gname[:a]
            n = ROOT.new(type=gname)
            n.name = gname + "-" + str(gidx)
            if sub is not None:
                n.blend_type = sub
            self.shaders.append(n)
            old_gname = gname
        for cn in con_nums:
            outp = cn[0]
            inp = cn[1]
            LINK.new(
                self.shaders[outp[0]].outputs[outp[1]],
                self.shaders[inp[0]].inputs[inp[1]]
            )
            
class McyEyeWet:
    shaders = []
    mcy_eyewet = None
    
    def __init__(self):
        self.shaders = []
        self.mcy_eyewet = None
        self.makegroup()
        self.exeEyeWet()
        
    def makegroup(self):
        self.mcy_eyewet  = bpy.data.node_groups.new(type="ShaderNodeTree", name=ngroup3(EWET))
        nsc = 'NodeSocketColor'
        self.mcy_eyewet.inputs.new(nsc, 'Bump')
        self.mcy_eyewet.inputs.new(nsc,"Normal")
        self.mcy_eyewet.outputs.new('NodeSocketShader', 'Cycles')
        self.mcy_eyewet.outputs.new('NodeSocketShader', 'EEVEE')
        
    def exeEyeWet(self):
        generatenames = [ 'NodeGroupInput', 'ShaderNodeInvert', 'ShaderNodeNormalMap', 'ShaderNodeBump',
                          'ShaderNodeFresnel','ShaderNodeMixShader', 'ShaderNodeBsdfTransparent', 'ShaderNodeBsdfPrincipled',
                          'NodeGroupOutput']
        con_nums = [[[0, 0], [3, 'Height']],
                    [[0, 1], [2, 'Color']],
                    [[2, 'Normal'], [3, 'Normal']],
                    [[3, 'Normal'], [7, 'Normal']],
                    #shader
                    [[4, 0], [5, 0]],#fresnel->mix.fac
                    [[6, 0], [5, 1]],#trans->mix
                    [[7, 0], [5, 2]],#bsdfp->mix
                    [[5, 0], [8, 0]],
                    [[5, 0], [8, 1]],
        ]
        ROOT = self.mcy_eyewet.nodes
        LINK = self.mcy_eyewet.links
        old_gname = ""
        for gidx, gname in enumerate(generatenames):
            if gname == '':
                gname = old_gname

            a = gname.find('.')
            sub = None
            if a > 0:
                sub = gname[a + 1:]
                gname = gname[:a]
            n = ROOT.new(type=gname)
            n.name = gname + "-" + str(gidx)
            if sub is not None:
                n.blend_type = sub
            self.shaders.append(n)
            old_gname = gname
        for cn in con_nums:
            outp = cn[0]
            inp = cn[1]
            LINK.new(
                self.shaders[outp[0]].outputs[outp[1]],
                self.shaders[inp[0]].inputs[inp[1]]
            )

class McySkin:
    shaders = []
    mcy_skin = None
    def __init__(self):
        self.shaders = []
        self.mcy_skin = None
        self.makegroup()
        self.exeSkin()

    def makegroup(self):
        self.mcy_skin = bpy.data.node_groups.new(type="ShaderNodeTree", name=ngroup3(SKIN))
        nsc = 'NodeSocketColor'
        self.mcy_skin.inputs.new(nsc, 'Diffuse')
        self.mcy_skin.inputs.new(nsc, 'Specular')
        self.mcy_skin.inputs.new(nsc, 'Roughness')
        self.mcy_skin.inputs.new(nsc, 'Bump')
        self.mcy_skin.inputs.new(nsc, 'Normal')
        self.mcy_skin.inputs.new(nsc, 'Displacement')
        self.mcy_skin.inputs.new(nsc,"SSSBlue")
        self.mcy_skin.inputs.new(nsc,"SSSRed")
        self.mcy_skin.inputs.new('NodeSocketFloat', 'SSSMix')
        self.mcy_skin.outputs.new('NodeSocketShader', 'Cycles')
        self.mcy_skin.outputs.new('NodeSocketVector', 'Displacement')
        self.mcy_skin.outputs.new('NodeSocketShader', 'EEVEE')

    def exeSkin(self):
        generatenames = ['NodeGroupInput','NodeGroupOutput','ShaderNodeBsdfPrincipled','ShaderNodeMixRGB.MIX', #0
                         'ShaderNodeDisplacement','ShaderNodeNormalMap', 'ShaderNodeBump','ShaderNodeFresnel', #4
                         'ShaderNodeBrightContrast','','','ShaderNodeHueSaturation',                           #8
                         'ShaderNodeBsdfGlossy','ShaderNodeSubsurfaceScattering','','ShaderNodeInvert',        #12
                          'ShaderNodeMixShader', '','' ]           #16
        con_nums = [#Diffuse
                    [[0,0],[8,0]],
                    [[8, 0], [11, 4]],
                    [[11, 0], [2, 0]],
                    [[11, 0], [2, 3]],
                    [[11, 0], [13, 0]],
                    [[11, 0], [14, 0]],
                    #SSS
                    [[0, 6], [13, 2]],
                    [[0, 7], [14, 2]],
                    [[0,8],[18,0]],
                    #Normal
                    [[0 ,4], [5, 1]],
                    [[5, 0], [6, 'Normal']],
                    [[6,'Normal'],[2,'Normal']],
                    #Bump/displacement
                    [[0,3],[6,'Height']],
                    [[0,3],[3,1]],
                    [[0,5],[3,2]],
                    [[3,0],[4,'Height']],
                    [[4,0],[1,1]],
                    [[6,0],[7,1]],#Bump->Fresnel
                    [[7, 0], [16, 0]],  # Fresnel->Mix0
                    [[7, 0], [17, 0]],  # Fresnel->Mix1
                    [[16, 0], [18, 1]],  # Mix0->Mix2
                    [[17, 0], [18, 2]],  # Mix1->Mix2
                    #Specular/roughness
                    [[0,1],[9,0]],
                    [[9,0],[2,5]],
                    [[0,2],[15,1]],#rougness->invert
                    [[15,0],[10,0]],#invert->bright
                    [[10,0],[2,7]],#bright->bsdf
                    [[10,0],[12,1]],#bright_glossy
                    [[9,0],[12,0]],
                    [[12,0],[16,2]],
                    [[12, 0], [17, 2]],
                    [[13,0],[16,1]],#blue
                    [[14, 0], [17, 1]],#red
                    #out
                    [[18, 0], [1, 0]],
                    [[4, 0], [1, 1]],
                    [[2,0],[1,2]],
            ]
        ROOT = self.mcy_skin.nodes
        LINK = self.mcy_skin.links
        old_gname = ""
        for gidx,gname in enumerate(generatenames):
            if gname=='':
                gname = old_gname
            a = gname.find('.')
            sub = None
            if a>0:
                sub = gname[a+1:]
                gname = gname[:a]
            n = ROOT.new(type=gname)
            n.name = gname + "-" + str(gidx)
            if sub is not None:
                n.blend_type = sub
            self.shaders.append(n)
            old_gname = gname
        for cidx,cn in enumerate(con_nums):
            outp = cn[0]
            inp = cn[1]
            LINK.new(
                self.shaders[outp[0]].outputs[outp[1]],
                self.shaders[inp[0]].inputs[inp[1]]
            )
        NodeArrange.toNodeArrange(self.mcy_skin.nodes)

def forbitMinus():
    pbsdf = 'Principled BSDF'
    for dobj in Util.myccobjs():
        if dobj.type != 'MESH' or dobj==Global.getBody():
            continue
        for slot in dobj.material_slots:
            mat = bpy.data.materials.get(slot.name)
            if mat is None or mat.node_tree is None:
                continue
            ROOT = mat.node_tree.nodes
            for r in ROOT:
                if pbsdf in r.name:
                    for input in ROOT[pbsdf].inputs:
                        if len(input.links) == 0:
                            if type(input.default_value) is float:
                                if input.default_value < 0:
                                    input.default_value = 0.0
                                if input.name == 'Metallic' and input.default_value == 1.0:
                                    input.default_value = 0.0
                                if input.name == 'Specular' and input.default_value == 2.0:
                                    input.default_value = 0.2
                            elif type(input.default_value) is list:
                                for i in input.default_value:
                                    if type(i) is float:
                                        if input.default_value < 0:
                                            input.default_value = 0.0

def default_material():
    toEyeDryDefault(getGroupNodeTree(ngroup3(EDRY)))
    toEyeWetDefault(getGroupNodeTree(ngroup3(EWET)))
    toSkinDefault(getGroupNodeTree(ngroup3(SKIN)))

def skin_levl(flg_high):
    for slot in Global.getBody().material_slots:
        ROOT = bpy.data.materials[slot.name].node_tree.nodes
        LINK = bpy.data.materials[slot.name].node_tree.links
        SNBP = None
        for n in ROOT:
            if n.name.startswith('Group') == False:
                continue
            SNBP = n
            break
        if SNBP is None or SNBP.node_tree.name!=ngroup3(SKIN):
            continue
        if ('Cycles' in SNBP.outputs)==False or ('EEVEE' in SNBP.outputs)==False:
            continue
        for n in ROOT:
            if n.name.startswith('Material Output') and n.target=='CYCLES':
                if flg_high:
                    LINK.new(SNBP.outputs['Cycles'], n.inputs['Surface'])
                else:
                    LINK.new(SNBP.outputs['EEVEE'], n.inputs['Surface'])
    Global.setRenderSetting(flg_high)

def readImages(dct):
    for slot in Global.getBody().material_slots:
        ROOT = bpy.data.materials[slot.name].node_tree.nodes
        LINK = bpy.data.materials[slot.name].node_tree.links
        SNBP = None
        for n in ROOT:
            if n.name.startswith('Group') == False:
                continue
            SNBP = n
            break
        if SNBP is None:
            continue
        for midx in range(len(mtable)):
            mname = mtable[midx][0]
            mban = mtable[midx][1]
            if mban == 0 or mban == 8:
                continue
            if (mname.lower() in slot.name.lower()):
                for fidx,ft in enumerate(ftable):
                    key = str(mban) + ft[0]
                    if (ft[1] not in SNBP.inputs):
                        continue
                    if key in dct.keys():
                        adr = dct[key]
                    else:
                        adr = ""
                    if os.path.exists(adr) == False:
                        continue
                    inp = SNBP.inputs[ft[1]]
                    if inp.links is None or len(inp.links)==0:
                        SNTIMG = ROOT.new(type='ShaderNodeTexImage')
                        LINK.new(SNTIMG.outputs[0],inp)
                    for link in inp.links:
                        if link.from_node.name.startswith("Image Texture"):
                            SNTIMG = link.from_node
                            img = bpy.data.images.load(filepath=adr)
                            SNTIMG.image = img
                            if fidx != 0:
                                Versions.to_color_space_non(SNTIMG)

def insertBumpMap(ROOT,LINK):
    rtn = [None,None]
    PBSDF = None
    NML = None
    for n in ROOT:
        if n.name=='Principled BSDF':
            PBSDF = n
        elif n.name=='Normal Map':
            NML = n
    if PBSDF is None:
        return ROOT
    nlinks = PBSDF.inputs['Normal'].links
    for nl in nlinks:
        BUMP = ROOT.new(type='ShaderNodeBump')
        if NML is not None and nl.from_node==NML:
            LINK.new(BUMP.outputs['Normal'], PBSDF.inputs['Normal'])
            LINK.new(NML.outputs['Normal'], BUMP.inputs['Normal'])
            rtn[1] = BUMP
        elif nl.from_node.name=='Bump Map':
            rtn[1] = nl.from_node
    if rtn[1] is None:
        BUMP = ROOT.new(type='ShaderNodeBump')
        LINK.new(BUMP.outputs['Normal'], PBSDF.inputs['Normal'])
        rtn[1] = BUMP
    rtn[0] = ROOT
    return rtn


