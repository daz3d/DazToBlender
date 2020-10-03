
import os
import bpy
from . import DtbMaterial
from . import Global
from . import NodeArrange
from . import Versions
from . import MatDct
from . import Util
NGROUP3 = ['oct_skin','oct_eyewet','oct_eyedry']
SKIN = 0
EWET = 1
EDRY = 2
def ngroup3(idx):
    return NGROUP3[idx] + Util.get_dzidx()

class Octane:
    ftable = [["d", "Diffuse"],
              ["b", "Bump"],
              ["s", "Specular"],
              ["r", "Roughness"],
              ["z", "Medium"],
              ["n", "Normal"],
              ["t", "Opacity"]]
    mtable = DtbMaterial.mtable

    def config(self):
        bpy.context.scene.octane.ray_epsilon = 0.000010

    def __init__(self):
        if Global.if_octane()==False:
            return
        self.config()
        if Global.isDazOctane():
            OctSkin_daz()
        else:
            OctSkin()
        for obj in Util.myacobjs():
            self.execute(obj)
        Versions.make_camera()

    def eye_wet(self,ROOT,LINK):
        main = ROOT.new(type = 'ShaderNodeOctSpecularMat')
        main.inputs['Opacity'].default_value = 0.2
        main.inputs['Roughness'].default_value = 0.2
        main.inputs['Reflection'].default_value = (1.0, 1.0, 1.0, 1.0)
        main.inputs['Transmission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        out = ROOT.new(type = 'ShaderNodeOutputMaterial')
        out.target = 'octane'
        LINK.new(main.outputs[0],out.inputs[0])

    def execute(self,obj):
        for slot in obj.material_slots:
            ttable = [
                ["d", None],
                ["b",None],
                ["n", None],
                ["s", None],
                ["r", None],
                ["z", None],
                ["t", None], ]
            mat = bpy.data.materials.get(slot.name)
            if mat is None:
                continue
            mban = -1
            for mt in self.mtable:
                if mat.name.startswith("drb_" + mt[0]):
                    mban = mt[1]
                    break
            ROOT = mat.node_tree.nodes
            LINK = mat.node_tree.links
            flg_universe = False
            outmat = ROOT.new(type='ShaderNodeOutputMaterial')
            if mban==8:
                self.eye_wet(ROOT,LINK)
                continue
            if mban==7:
                mainNode = ROOT.new(type='ShaderNodeOctGlossyMat')
            elif mban<=0:
                mainNode = ROOT.new(type='ShaderNodeOctUniversalMat')
                flg_universe = True
            else:
                mainNode = ROOT.new(type='ShaderNodeGroup')
                mainNode.node_tree = bpy.data.node_groups[oct_ngroup3(SKIN)]
            LINK.new(mainNode.outputs['OutMat'], outmat.inputs['Surface'])
            outmat.target = 'octane'
            for nd in ROOT:
                if nd.type=='TEX_IMAGE':
                    for ft in self.ftable:
                        if ('-IMG.' + ft[0] + "-") in nd.name:
                            adr = nd.image.filepath
                            OCTIMG = ROOT.new(type = 'ShaderNodeOctImageTex')
                            OCTIMG.name = mat.name+"-OCT." + ft[0] + "-"
                            img = bpy.data.images.load(filepath=adr)
                            OCTIMG.image = img
                            inputname = ft[1]
                            if flg_universe and inputname=='Diffuse':
                                inputname = 'Albedo color'
                            LINK.new(mainNode.inputs[inputname],OCTIMG.outputs['OutTex'])
                            for tt in ttable:
                                if tt[0]==ft[0]:
                                    tt[1] = OCTIMG
                                    break
                elif nd.type=='BSDF_PRINCIPLED':
                    p_inp = ["Base Color", "", "Specular","Roughness", "", "", "Alpha"]
                    for pidx,pi in enumerate(p_inp):
                        if pi != "" and nd.inputs.get(pi) is not None:

                            if len(nd.inputs.get(pi).links)==0:
                                dv = nd.inputs.get(pi).default_value

                                pi = self.ftable[pidx][1]
                                if pidx==0:
                                    if flg_universe:
                                        pi = 'Albedo color'
                                    else:
                                        pi = 'Diffuse'
                                intype = mainNode.inputs[pi].type
                                if intype == 'VALUE' or intype=='RGBA':
                                    mainNode.inputs[pi].default_value = dv
            self.after_execute(ROOT,LINK,ttable,mainNode,mban>0)
            if mban>0:
                toGroupInputsDefault(mban==7)
            NodeArrange.toNodeArrange(ROOT)

    def after_execute(self,ROOT,LINK,ttable,universe,flg_human):
        afters = ['ShaderNodeOctIntValue',
                      'ShaderNodeOct2DTransform','ShaderNodeOctUVWProjection']
        for aidx,af in enumerate(afters):
            if flg_human==False and aidx<2:
                continue
            n = ROOT.new(type=af)
            if aidx==0:
                n.inputs[0].default_value = 1
                for i in range(3):#d,b,n
                    if ttable[i][1] is not None:
                        LINK.new(n.outputs[0],ttable[i][1].inputs['Gamma'])
            else:
                for tt in ttable:
                    if tt[1] is not None:
                        if aidx==1:
                            arg = 'Transform'
                        else:
                            arg = 'Projection'
                        LINK.new(n.outputs[0],tt[1].inputs[arg])
        for tidx,tt in enumerate(ttable):
            if (tidx==1 or tidx==2) and tt[1] is not None:
                tt[1].inputs['Power'].default_value = 0.4

NGROUP3 = ['oct_skin','oct_eyewet','oct_eyedry']
SKIN = 0
EWET = 1
EDRY = 2

def oct_ngroup3(idx):
    return NGROUP3[idx] + Util.get_dzidx()

class OctSkin_daz:
    shaders = []
    oct_skin = None

    def __init__(self):
        self.shaders = []
        self.oct_skin = None
        self.makegroup()
        self.exeSkin()
        self.adjust_default()

    def makegroup(self):
        self.oct_skin = bpy.data.node_groups.new(type="ShaderNodeTree", name=oct_ngroup3(SKIN))
        nsc = 'NodeSocketColor'
        self.oct_skin.inputs.new(nsc, 'Diffuse')
        self.oct_skin.inputs.new(nsc, 'Specular')
        self.oct_skin.inputs.new(nsc, 'Roughness')
        self.oct_skin.inputs.new(nsc, 'Bump')
        self.oct_skin.inputs.new(nsc, 'Normal')
        self.oct_skin.outputs.new('NodeSocketShader', 'OutMat')
        self.oct_skin.outputs.new('NodeSocketVector', 'Displacement')

    def adjust_default(self):
        scat = self.shaders[3]
        scat.inputs['Absorption Tex'].default_value = (0.1255,0.51,0.55,1)
        scat.inputs['Scattering Tex'].default_value = (0.51,0.7451,0.902,1)

    def exeSkin(self):
        generatenames = ['NodeGroupInput','ShaderNodeOctDiffuseMat','ShaderNodeOctGlossyMat','ShaderNodeOctScatteringMedium',
                         'ShaderNodeOctMixMat','ShaderNodeOctRoundEdges','ShaderNodeOctRGBSpectrumTex','NodeGroupOutput',]
        con_nums = [
            #Diffuse1
            [[0,0],[1,'Transmission']],
            # Diffuse2
            [[0,0],[1,0]],
            [[1,0],[4,1]],
            [[0,0],[2,0]],
            [[2,0],[4,2]],

            #Roughness
            [[0, 2], [1, 1]],
            [[0,2],[2,2]],

            #Specular
            [[0,1],[2,1]],

            #Normal
            [[0,4],[2,'Normal']],
            [[0, 4], [1, 'Normal']],

             #Scatter1
            [[3,0],[1,'Medium']],

            # #Alpha
            # [[0,5],[6,0]],
            # [[6, 0], [1, 'Opacity']],
            # [[6, 0], [2, 'Opacity']],

            #Bump
            [[0, 3], [2, 'Bump']],
            [[0, 3], [1, 'Bump']],

            #RoundEdge
            [[5, 0], [2, 'Edges rounding']],
            [[5, 0], [1, 'Edges rounding']],

              #out
            [[4, 0], [7, 0]],
        ]
        connect_group(con_nums, self.oct_skin, self.shaders, generatenames)

def getGroupNode(key):
    for slot in Global.getBody().material_slots:
        ROOT = bpy.data.materials[slot.name].node_tree.nodes
        for n in ROOT:
            if n.type=='GROUP':
                if n.node_tree.name.startswith(key):
                    return n

def toGroupInputsDefault(flg_eye):
    if Global.getBody() is None:
        return;
    dist_n = getGroupNode(ngroup3(SKIN))
    if dist_n is None:
        return
    for mat in bpy.data.materials:
        if mat.node_tree is None:
            continue
        n = None
        for sch_n in mat.node_tree.nodes:
            if sch_n.type!='GROUP':
                continue
            if sch_n.node_tree is None:
                continue
            if sch_n.node_tree.name==dist_n.node_tree.name:
                n = sch_n
                break
        if n is None:
            continue
        for i, inp in enumerate(sch_n.inputs):
            if len(inp.links) > 0:
                continue
            if i == 0:
                inp.default_value = (0.7, 0.6, 0.5, 1)
            elif i>0 and i<4:
                inp.default_value = (0.6, 0.6, 0.6, 1)
            elif i == 4:
                inp.default_value = (0.5, 0.5, 1, 1)
            mname = mat.name.lower()
            if ('mouth' in mname) or ('teeth' in mname) or ('nail' in mname):
                if i==1:
                    inp.default_value = (0.7, 0.7, 0.7, 1)
                elif i==2:
                    inp.default_value = (0.4, 0.4, 0.4, 1)

class OctSkin:
    shaders = []
    oct_skin = None
    def __init__(self):
        self.shaders = []
        self.oct_skin = None
        self.makegroup()
        self.exeSkin()

    def makegroup(self):
        self.oct_skin = bpy.data.node_groups.new(type="ShaderNodeTree", name=oct_ngroup3(SKIN))
        nsc = 'NodeSocketColor'
        self.oct_skin.inputs.new(nsc, 'Diffuse')
        self.oct_skin.inputs.new(nsc, 'Specular')
        self.oct_skin.inputs.new(nsc, 'Roughness')
        self.oct_skin.inputs.new(nsc, 'Bump')
        self.oct_skin.inputs.new(nsc, 'Normal')
        self.oct_skin.outputs.new('NodeSocketShader', 'OutMat')
        self.oct_skin.outputs.new('NodeSocketShader', 'Displacement')

    def make_default(self):
        pass

    def exeSkin(self):
        generatenames = ['NodeGroupInput','ShaderNodeOctColorCorrectTex','','ShaderNodeOctDiffuseMat',#0
                         'ShaderNodeOctMixMat','','','ShaderNodeOctRGBSpectrumTex',#4
                        'ShaderNodeOctScatteringMedium','','NodeGroupOutput','ShaderNodeOctGlossyMat',  #8
                         'ShaderNodeOctSpecularMat',''] #12
        con_nums = [
            #Diffuse
            [[0,0],[3,0]],
            [[3, 0], [4, 2]],
            [[4,0],[5,2]],
            [[5,0],[6,2]],

            [[0, 0], [12, 0]],
            [[0, 0], [13, 0]],

            # Scatter1
            [[8, 0], [12, 'Medium']],

            # Scatter2
            [[9, 0], [13, 'Medium']],

            #Specular1
            [[7,0],[2,0]],
            [[2,0],[12,1]],
            [[12,0],[4,1]],

            # Specular2
            [[7, 0], [1, 0]],
            [[1, 0], [13, 1]],
            [[13, 0], [5, 1]],

            #Glossy
            [[0,'Diffuse'],[11,'Diffuse']],
            [[0, "Specular"], [11, "Specular"]],
            [[0, "Roughness"], [11, "Roughness"]],
            [[11,0],[6,1]],

            #bump and Normal
            [[0, "Bump"], [12, "Bump"]],
            [[0, "Bump"], [13, "Bump"]],
            [[0, "Bump"], [3, "Bump"]],
            [[0, "Normal"], [12, "Normal"]],
            [[0, "Normal"], [13, "Normal"]],
            [[0, "Normal"], [3, "Normal"]],
            [[0, "Normal"], [11, "Normal"]],

            #out
            [[6, 0], [10, 0]],
        ]
        connect_group(con_nums, self.oct_skin, self.shaders, generatenames)
        self.shaders[7].inputs['Color'].default_value = (0.7, 0.095, 0.007, 1)
        self.shaders[9].inputs['Density'].default_value = 500
        self.shaders[9].inputs['Absorption Tex'].default_value = (0.477, 0.434, 0.086, 1)
        self.shaders[9].inputs['Scattering Tex'].default_value = (0.227, 0.248, 0.045, 1)
        self.shaders[8].inputs['Density'].default_value = 40
        self.shaders[8].inputs['Absorption Tex'].default_value = (0.251, 0.017, 0.0, 1)
        self.shaders[8].inputs['Scattering Tex'].default_value = (0.1, 0.003, 0.0, 1)
        for i in range(2):
            self.shaders[12+i].inputs['Roughness'].default_value = 0.2
            self.shaders[12+i].inputs[14].default_value = True
        self.shaders[1].inputs['Hue'].default_value = 0.2
        self.shaders[6].inputs[0].default_value = 0.2
        self.shaders[4].inputs[0].default_value = 0.6

def connect_group(con_nums,ngroup,shaders,generatenames):
    ROOT = ngroup.nodes
    LINK = ngroup.links
    old_gname = ""
    for gidx, gname in enumerate(generatenames):
        if gname == '':
            gname = old_gname
        n = ROOT.new(type=gname)
        n.name = gname + "-" + str(gidx)
        shaders.append(n)
        old_gname = gname
    for cidx, cn in enumerate(con_nums):
        outp = cn[0]
        inp = cn[1]
        LINK.new(
            shaders[outp[0]].outputs[outp[1]],
            shaders[inp[0]].inputs[inp[1]]
        )
    NodeArrange.toNodeArrange(ngroup.nodes)