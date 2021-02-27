import os
import json
import pathlib
import bpy

from . import Global
from . import NodeArrange
from . import Versions
from . import MatDct
from . import Util

NGROUP3 = ['mcy_skin', 'mcy_eyewet', 'mcy_eyedry']
SKIN = 0
EWET = 1
EDRY = 2

mtable = [
    ["Torso", 2],
    ["Head", 2],
    ["Body", 3],
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
    ["anus", 9],
    ["labia", 9],
    ["clitoris", 9],
    ["vagina", 9],
    ["glans", 9],
    ["shaft", 9],
    ["testicles", 9],
    ["rectum", 9],
]

ftable = [
    ["d", "Diffuse"],
    ["b", "Bump"],
    ["s", "Specular"],
    ["r", "Roughness"],
    ["z", "Subsurface"],
    ["n", "Normal"]
]

# region top-level methods

def ngroup3(idx):
    return NGROUP3[idx] + Util.get_dzidx()


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


def adjust_material(kind, inc_value, isEye):
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
        ['Displacement.Height', 4, 2],  # 14
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
        tree = getGroupNodeTree(NGROUP3[EDRY])
        tbls = eyecombi
    else:
        tree = getGroupNodeTree(NGROUP3[SKIN])
        tbls = skincombi
        flg_skin = True
    if tree is None:
        return
    nds = tree.nodes
    for tidx, tbl in enumerate(tbls):
        if tbl[0] == kind:
            t1 = getNidx(int(tbl[1]), nds)
            dv = nds[t1].inputs[tbl[2]].default_value
            cg = 1.0
            if flg_skin:
                if tidx > 8 and tidx < 16:
                    cg = cg * Global.getSize() * 0.01
                if tidx == 9:
                    cg = cg * 3
                elif tidx == 10:
                    cg = cg * 0.5
                elif tidx == 16:
                    cg = cg * 0.2
                # elif tidx==14:
                #     cg = cg * 12
                # elif tidx>=11 or tidx<=13:
                #     cg = cg * 8
            cg = cg * inc_value
            if tidx == 15:
                dv[0] += cg * 10
                dv[1] += cg * 2
                dv[2] += cg
            else:
                dv += cg
            nds[t1].inputs[tbl[2]].default_value = dv


def getNidx(idx, nodes):
    for nidx, n in enumerate(nodes):
        if n.name.endswith("-" + str(idx)):
            return nidx
    return idx


def toGroupInputsDefault(flg_eye):
    k3 = [EDRY, EWET, SKIN]
    for kidx, k in enumerate(k3):
        dist_n = getGroupNode(NGROUP3[k])
        for mat in bpy.data.materials:
            if mat.node_tree is None:
                continue
            n = None
            for sch_n in mat.node_tree.nodes:
                if sch_n.name.startswith('Group') == False:
                    continue
                if sch_n.node_tree is None:
                    continue
                if sch_n.node_tree.name == dist_n.node_tree.name:
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
                        inp.default_value = (1.0, 1.0, 1.0, 1.0)
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
                        if i == 1:
                            inp.default_value = (0.9, 0.9, 0.9, 1)
                        elif i == 2:
                            inp.default_value = (0.2, 0.2, 0.2, 1)
                        if ('teeth' in mname) or ('nail' in mname):
                            if i == 6:
                                if ('teeth' in mname):
                                    inp.default_value = (0.45, 0.45, 0.45, 1)
                                else:
                                    inp.default_value = (0.22, 0.36, 0.5, 1)
                            elif i == 7:
                                if ('teeth' in mname):
                                    inp.default_value = (0.45, 0.45, 0.45, 1)
                                else:
                                    inp.default_value = (0.5, 0.36, 0.22, 1)
                            elif i == 8:
                                inp.default_value = 0.0


def toEyeDryDefault(ntree):
    if ntree is None:
        return
    toGroupInputsDefault(True)
    nodes = ntree.nodes
    dvs = [
        [1, 1, 0.0],
        [1, 2, 0.0],
        [2, 1, 0.08],
        [2, 2, [Global.getSize()*0.006, Global.getSize()*0.003, Global.getSize()*0.003]],
        [2, 5, 0.0],
        [2, 6, 0.3],
        [2, 7, 0.0],
        [2, 'IOR', 1.35],
        [2, 'Transmission', 0.0],
        [2, 'Sheen', 0.0],
        [6, 0, 0.5],
        [6, 1, 1.0],
        [6, 2, 1.0],
        [3, 0, Global.getSize() * 0.001],  # NormalMap Strength
        [4, 0, Global.getSize() * 0.001],  # Bump Strength
        [4, 1, Global.getSize() * 0.001],  # Bump Distance
    ]
    for dv in dvs:
        dv0 = getNidx(int(dv[0]), nodes)
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
    dvs = [
        [4, 0, 1.45],
        [6, 0, [1.0, 1.0, 1.0, 1.0]],
        [7, 1, 0.0],
        [2, 0, 0.1],
        [3, 0, 0.1],
        [3, 1, 0.1],
        [7, 0, [1.0, 1.0, 1.0, 1.0]],
        [7, 1, 0.0],
        [7, 4, 1.0],
        [7, 5, 1.0],
        [7, 7, 0.0],
        [7, 'Transmission', 1.0],
        [7, 'Alpha', 0.5],
    ]
    for dv in dvs:
        dv0 = getNidx(int(dv[0]),  nodes)
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
    nds[getNidx(4, nds)].space = 'OBJECT'
    nds[getNidx(13, nds)].falloff = 'RANDOM_WALK'
    nds[getNidx(14, nds)].falloff = 'RANDOM_WALK'
    dvs = [
        [5, 0, Global.getSize()*0.01],  # NormalMap Strength
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
        [4, 2, Global.getSize() * 0.0012],  # Displacement Height
        [4, 1, Global.getSize() * 0.005],  # Displacement Middle
        [13, 4, 0.1],
        [14, 4, 0.1],
        [2, 14, 1.33],
        [2, 2, [
            0.04 * Global.getSize(),
            0.008 * Global.getSize(),
            0.002 * Global.getSize()
        ]],
        [11, 0, 0.5],
        [11, 1, 1.0],
        [11, 2, 1.0],
        [7, 0, 1.33],
    ]
    for dv in dvs:
        dv0 = getNidx(int(dv[0]), nds)
        if isinstance(dv[2], float) or isinstance(dv[2], int):
            nds[dv0].inputs[dv[1]].default_value = dv[2]
        else:
            for i in range(len(dv[2])):
                nds[dv0].inputs[dv[1]].default_value[i] = dv[2][i]
    NodeArrange.toNodeArrange(ntree.nodes)


def clear_past_nodegroup():
    for ng in NGROUP3:
        for s in bpy.data.node_groups:
            if s.name == ng:
                bpy.data.node_groups.remove(s, do_unlink=True)
                break


def forbitMinus():
    pbsdf = 'Principled BSDF'
    for dobj in Util.myccobjs():
        if dobj.type != 'MESH' or dobj == Global.getBody():
            continue
        for slot in dobj.material_slots:
            mat = bpy.data.materials.get(slot.name)
            if mat is None or mat.node_tree is None:
                continue
            mat_nodes = mat.node_tree.nodes
            for mat_node in mat_nodes:
                if pbsdf not in mat_node.name:
                    continue
                for node_input in mat_nodes[pbsdf].inputs:
                    if len(node_input.links) != 0:
                        continue
                    if type(node_input.default_value) is float:
                        if node_input.default_value < 0:
                            node_input.default_value = 0.0
                        if node_input.name == 'Metallic' and node_input.default_value == 1.0:
                            node_input.default_value = 0.0
                        if node_input.name == 'Specular' and node_input.default_value == 2.0:
                            node_input.default_value = 0.2
                    elif type(node_input.default_value) is list:
                        for i in node_input.default_value:
                            if type(i) is float:
                                if node_input.default_value < 0:
                                    node_input.default_value = 0.0


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
        if SNBP is None or SNBP.node_tree.name != ngroup3(SKIN):
            continue
        if ('Cycles' in SNBP.outputs) == False or ('EEVEE' in SNBP.outputs) == False:
            continue
        for n in ROOT:
            if n.name.startswith('Material Output') and n.target == 'CYCLES':
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
                for fidx, ft in enumerate(ftable):
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
                    if inp.links is None or len(inp.links) == 0:
                        SNTIMG = ROOT.new(type='ShaderNodeTexImage')
                        LINK.new(SNTIMG.outputs[0], inp)
                    for link in inp.links:
                        if link.from_node.name.startswith("Image Texture"):
                            SNTIMG = link.from_node
                            img = bpy.data.images.load(filepath=adr)
                            SNTIMG.image = img
                            if fidx != 0:
                                Versions.to_color_space_non(SNTIMG)


def insert_bump_map(nodes, links):
    rtn = [None, None]
    PBSDF = None
    NML = None
    for n in nodes:
        if n.name == 'Principled BSDF':
            PBSDF = n
        elif n.name == 'Normal Map':
            NML = n
    if PBSDF is None:
        return nodes
    nlinks = PBSDF.inputs['Normal'].links
    for nl in nlinks:
        BUMP = nodes.new(type='ShaderNodeBump')
        if NML is not None and nl.from_node == NML:
            links.new(BUMP.outputs['Normal'], PBSDF.inputs['Normal'])
            links.new(NML.outputs['Normal'], BUMP.inputs['Normal'])
            rtn[1] = BUMP
        elif nl.from_node.name == 'Bump Map':
            rtn[1] = nl.from_node
    if rtn[1] is None:
        BUMP = nodes.new(type='ShaderNodeBump')
        links.new(BUMP.outputs['Normal'], PBSDF.inputs['Normal'])
        rtn[1] = BUMP
    rtn[0] = nodes
    return rtn

# endregion top-level methods

class DtbShaders:
    dct = {}
    mat_data_dict = {}

    def __init__(self):
        pass

    def make_dct(self):
        self.dct = []
        mat_dct = MatDct.MatDct()
        mat_dct.make_dct_from_mtl()
        self.dct = mat_dct.get_dct()

        input_file = open(Global.getHomeTown() + Global.getFileSp() + "FIG.dtu")
        dtu_content = input_file.read()
        mat_info_list = json.loads(dtu_content)["Materials"]
        for mat_info in mat_info_list:
            self.mat_data_dict[mat_info["Material Name"]] = mat_info

    def load_shader_nodes(self):
        file_path = "./dependencies/link_library.blend"
        file_path = os.path.join(pathlib.Path().absolute(), file_path)
        
        # load node_groups from link_library.blend file
        with bpy.data.libraries.load(file_path) as (data_from, data_to):
            data_to.node_groups = data_from.node_groups

    def set_eyelash_mat(self, mat_nodes, mat_links, out_node_cy, out_node_ev):
        # Create and set BSDF Transparent node
        bsdf_trans_node = mat_nodes.new(type='ShaderNodeBsdfTransparent')
        tex_path = ""
        if "0t" in self.dct.keys():
            tex_path = self.dct["0t"]
        # If texture is not found, set bsdf_trans node outputs and return
        if not os.path.exists(tex_path):
            mat_links.new(bsdf_trans_node.outputs['BSDF'], out_node_cy.inputs[0])
            mat_links.new(bsdf_trans_node.outputs['BSDF'], out_node_ev.inputs[0])
            return

        # Create and set other nodes
        tex_image_node = mat_nodes.new(type='ShaderNodeTexImage')
        tex_image_node.image = bpy.data.images.load(filepath=tex_path)

        mix_shader_node = mat_nodes.new(type='ShaderNodeMixShader')
        invert_node = mat_nodes.new(type='ShaderNodeInvert')

        bsdf_diff_node = mat_nodes.new(type='ShaderNodeBsdfDiffuse')
        bsdf_diff_node.inputs['Color'].default_value = (0.1, 0.1, 0.1, 1)
        bsdf_diff_node.inputs['Roughness'].default_value = 0.2

        # Create node liking maps and set the links
        node_maps = [
            [invert_node.inputs['Color'], tex_image_node.outputs['Color']],
            [mix_shader_node.inputs[0], invert_node.outputs['Color']],
            [mix_shader_node.inputs[2], bsdf_trans_node.outputs['BSDF']],
            [mix_shader_node.inputs[1], bsdf_diff_node.outputs['BSDF']],
            [mix_shader_node.outputs[0], out_node_cy.inputs[0]],
            [mix_shader_node.outputs[0], out_node_ev.inputs[0]]
        ]
        for node_map in node_maps:
            mat_links.new(node_map[0], node_map[1])

    # TODO: Remove all the hardcoding
    def body_texture(self):
        for mat_slot in Global.getBody().material_slots:
            mat = mat_slot.material
            if mat is None:
                # Get or create a new material when slot is missing material
                mat = bpy.data.materials.get(mat_slot.name) \
                    or bpy.data.materials.new(name=mat_slot.name)
                mat_slot.material = mat

            # Get material data
            mat_name = mat.name
            if mat_name not in self.mat_data_dict.keys():
                continue
            mat_data = self.mat_data_dict[mat_name]
                    
            mat.use_nodes = True
            mat_nodes = mat.node_tree.nodes
            mat_links = mat.node_tree.links

            # Remove all the nodes from the material
            for mat_node in mat_nodes:
                mat_nodes.remove(mat_node)

            # Crete material output nodes and set corresponding targets
            out_node_cy = mat_nodes.new(type="ShaderNodeOutputMaterial")
            out_node_cy.target = 'CYCLES'
            out_node_ev = mat_nodes.new(type="ShaderNodeOutputMaterial")
            out_node_ev.target = 'EEVEE'

            # If Eyelashes, setup nodes and break
            if mat_name == "Eyelashes":
                Versions.eevee_alpha(mat, 'BLEND', 0)
                self.set_eyelash_mat(mat_nodes, mat_links, out_node_cy, out_node_ev)
                break

            # Create shader node and set links
            shader_node = mat_nodes.new(type='ShaderNodeGroup')
            if mat_name in [
                                "Cornea",
                                "EyeMoisture",
                                "EyeMoisture.00",
                                "EylsMoisture"
                            ]:
                shader_node.node_tree = bpy.data.node_groups["EyeWet"]
            elif mat_name in ["Pupils", "Trises", "Sclera"]:
                shader_node.node_tree = bpy.data.node_groups["EyeDry"]
            else:
                shader_node.node_tree = bpy.data.node_groups["IrayUberSkin"]

            # Link corresponding nodes in the material
            render_output = None
            surface_input = out_node_cy.inputs['Surface']
            if mat_name in [
                            "Pupils", "Trises", "Sclera", 
                            "Eyelashes", "EyeSocket"
                        ]:
                render_output = shader_node.outputs['EEVEE']
            else:
                render_output = shader_node.outputs['Cycles']
            mat_links.new(render_output, surface_input)

            if mat_name in [
                            "Face", "Lips", "Ears", "EyeSocket",
                            "Torso", "Head", "Genitalia",
                            "Body", "Legs", "Toenails",
                            "Arms", "Fingernails",
                            "Teeth", "Mouth",                            
                        ]:
                mat_links.new(
                            shader_node.outputs['Displacement'],
                            out_node_cy.inputs['Displacement']
                        )
            mat_links.new(
                        shader_node.outputs['EEVEE'], 
                        out_node_ev.inputs['Surface']
                    )
            
            mat_property_dict = {}
            for mat_property in mat_data["Properties"]:
                mat_property_dict[mat_property["Name"]] = mat_property

            if "Diffuse" in shader_node.inputs.keys():
                color_hex = mat_property_dict["Diffuse Color"]["Value"]
                color_hex = color_hex.lstrip('#')
                color_rgb = [int(color_hex[i:i+2], 16) for i in (0, 2, 4)]
                color_rgb.append(255) # alpha
                shader_node.inputs['Diffuse'].default_value = color_rgb

            if mat_name in [
                    "Cornea",
                    "EyeMoisture",
                    "EyeMoisture.00",
                    "EylsMoisture"
                ]:
                Versions.eevee_alpha(mat, 'HASHED', 0)

            # Find and set texture links to the shader node
            for input_key in shader_node.inputs.keys():
                property_key = ""
                is_diffuse = False

                if input_key == "Diffuse":
                    property_key = "Diffuse Color"
                    is_Diffuse = True
                elif input_key == "Roughness":
                    property_key = "Specular Lobe 1 Roughness"
                elif input_key == "Normal":
                    property_key = "Normal Map"
                
                if property_key != "":
                    tex_path = mat_property_dict[property_key]["Texture"]
                    if not os.path.exists(tex_path):
                        continue

                    tex_image_node = mat_nodes.new(
                                        type='ShaderNodeTexImage'
                                    )
                    tex_image = bpy.data.images.load(filepath=tex_path)
                    tex_image_node.image = tex_image
                    tex_node_output = tex_image_node.outputs['Color']

                    if not is_Diffuse:
                        Versions.to_color_space_non(tex_image_node)

                    mat_links.new(
                        tex_node_output,
                        shader_node.inputs[input_key]
                    )
            
                # Set the cycles displacement method
                if mat_name in [
                    "Cornea", "EyeMoisture", "EyeMoisture.00", "EylsMoisture", "Pupils", "Trises", "Sclera",
                    "Eyelashes"
                ]:
                    mat.cycles.displacement_method = 'BUMP'
                else:
                    mat.cycles.displacement_method = 'BOTH'

            if mat_nodes is not None:
                NodeArrange.toNodeArrange(mat_nodes)

    def prop_texture(self):
        fig_objs_names = [
                Global.get_Body_name(),
                Global.get_Hair_name() + "OK",
                Global.get_Eyls_name()
            ]
        for obj in Util.myacobjs():
            # Skip for any of the following cases
            case1 = not Global.isRiggedObject(obj)
            case2 = obj.name in fig_objs_names
            if case1 or case2:
                continue

            for mat_slot in obj.material_slots:
                mat = bpy.data.materials[mat_slot.name]
                if mat is None:
                    continue
                
                base_color_key = mat_slot.name.lower() + "_c"
                base_color_value = []
                if base_color_key not in self.dct.keys():
                    continue
                base_color_value = self.dct[base_color_key]
                if len(base_color_value) == 4 and base_color_value[3] < 1.0:
                    Versions.eevee_alpha(mat, 'BLEND', 0)

                mat_nodes = mat.node_tree.nodes
                mat_links = mat.node_tree.links
                image_path = ""
                prin_bsdf_node = None
                norm_map_node = None
                if len(mat_nodes) == 5 or len(mat_nodes) == 4:
                    for node in mat_nodes:
                        if node.name == "Image Texture":
                            image_path = node.image.filepath
                        elif node.name == "Principled BSDF":
                            prin_bsdf_node = node
                        elif node.name == "Normal Map":
                            norm_map_node = node

                    if image_path != "":
                        md = MatDct.MatDct()
                        cary = md.cloth_dct_0(image_path)
                        pandb = insert_bump_map(mat_nodes, mat_links)
                        BUMP = pandb[1]
                        mat_nodes = pandb[0]
                        prin_bsdf_node.inputs['Specular'].default_value = 0.3
                        if(len(prin_bsdf_node.inputs['Alpha'].links) > 0):
                            Versions.eevee_alpha(mat, 'BLEND', 0)
                        for ca in cary:
                            for ft in ftable:
                                if ft[0] == 'd':
                                    continue
                                if ca[0].endswith(ft[0]):
                                    SNTIMG = mat_nodes.new(
                                        type='ShaderNodeTexImage')
                                    img = bpy.data.images.load(
                                        filepath=ca[1])
                                    SNTIMG.image = img
                                    Versions.to_color_space_non(SNTIMG)
                                    if ft[0] == 'n':
                                        if norm_map_node is not None:
                                            mat_links.new(
                                                SNTIMG.outputs['Color'], norm_map_node.inputs['Color'])
                                    elif ft[0] == 'b':
                                        if BUMP is not None:
                                            mat_links.new(
                                                SNTIMG.outputs['Color'], BUMP.inputs['Height'])
                                    else:
                                        mat_links.new(
                                            SNTIMG.outputs['Color'], prin_bsdf_node.inputs[ft[1]])

                NodeArrange.toNodeArrange(mat_nodes)


class McyEyeDry:
    shaders = []
    mcy_eyedry = None

    def __init__(self):
        self.shaders = []
        self.mcy_eyedry = None
        self.make_group()
        self.exe_eye_dry()

    def make_group(self):
        self.mcy_eyedry = bpy.data.node_groups.new(
            type="ShaderNodeTree", name=ngroup3(EDRY))
        nsc = 'NodeSocketColor'
        self.mcy_eyedry.inputs.new(nsc, 'Diffuse')
        self.mcy_eyedry.inputs.new(nsc, 'Bump')
        self.mcy_eyedry.inputs.new(nsc, 'Normal')
        self.mcy_eyedry.outputs.new('NodeSocketShader', 'Cycles')
        self.mcy_eyedry.outputs.new('NodeSocketVector', 'Displacement')
        self.mcy_eyedry.outputs.new('NodeSocketShader', 'EEVEE')

    def exe_eye_dry(self):
        generate_names = ['NodeGroupInput', 'ShaderNodeBrightContrast', 'ShaderNodeBsdfPrincipled', 'ShaderNodeNormalMap',
                         'ShaderNodeBump', 'NodeGroupOutput', 'ShaderNodeHueSaturation']
        con_nums = [[[0, 0], [6, 4]],  # Diffuse
                    [[6, 0], [1, 0]],
                    [[1, 0], [2, 0]],
                    [[1, 0], [2, 3]],

                    [[0, 2], [3, 1]],  # Normal
                    [[3, 0], [4, "Normal"]],
                    [[0, 1], [4, "Height"]],
                    [[4, 0], [2, 'Normal']],
                    [[2, 0], [5, 0]],  # Out
                    [[2, 0], [5, 2]],
                    ]
        ROOT = self.mcy_eyedry.nodes
        LINK = self.mcy_eyedry.links
        old_gname = ""
        for g_index, g_name in enumerate(generate_names):
            if g_name == '':
                g_name = old_gname
            a = g_name.find('.')
            sub = None
            if a > 0:
                sub = g_name[a + 1:]
                g_name = g_name[:a]
            n = ROOT.new(type=g_name)
            n.name = g_name + "-" + str(g_index)
            if sub is not None:
                n.blend_type = sub
            self.shaders.append(n)
            old_gname = g_name
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
        self.make_group()
        self.exe_eye_wet()

    def make_group(self):
        self.mcy_eyewet = bpy.data.node_groups.new(
            type="ShaderNodeTree", name=ngroup3(EWET))
        nsc = 'NodeSocketColor'
        self.mcy_eyewet.inputs.new(nsc, 'Bump')
        self.mcy_eyewet.inputs.new(nsc, "Normal")
        self.mcy_eyewet.outputs.new('NodeSocketShader', 'Cycles')
        self.mcy_eyewet.outputs.new('NodeSocketShader', 'EEVEE')

    def exe_eye_wet(self):
        generate_names = ['NodeGroupInput', 'ShaderNodeInvert', 'ShaderNodeNormalMap', 'ShaderNodeBump',
                         'ShaderNodeFresnel', 'ShaderNodeMixShader', 'ShaderNodeBsdfTransparent', 'ShaderNodeBsdfPrincipled',
                         'NodeGroupOutput']
        con_nums = [[[0, 0], [3, 'Height']],
                    [[0, 1], [2, 'Color']],
                    [[2, 'Normal'], [3, 'Normal']],
                    [[3, 'Normal'], [7, 'Normal']],
                    # shader
                    [[4, 0], [5, 0]],  # fresnel->mix.fac
                    [[6, 0], [5, 1]],  # trans->mix
                    [[7, 0], [5, 2]],  # bsdfp->mix
                    [[5, 0], [8, 0]],
                    [[5, 0], [8, 1]],
                    ]
        ROOT = self.mcy_eyewet.nodes
        LINK = self.mcy_eyewet.links
        old_gname = ""
        for g_index, g_name in enumerate(generate_names):
            if g_name == '':
                g_name = old_gname

            a = g_name.find('.')
            sub = None
            if a > 0:
                sub = g_name[a + 1:]
                g_name = g_name[:a]
            n = ROOT.new(type=g_name)
            n.name = g_name + "-" + str(g_index)
            if sub is not None:
                n.blend_type = sub
            self.shaders.append(n)
            old_gname = g_name
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
        self.make_group()
        self.exe_skin()

    def make_group(self):
        self.mcy_skin = bpy.data.node_groups.new(
            type="ShaderNodeTree", name=ngroup3(SKIN))
        nsc = 'NodeSocketColor'
        self.mcy_skin.inputs.new(nsc, 'Diffuse')
        self.mcy_skin.inputs.new(nsc, 'Specular')
        self.mcy_skin.inputs.new(nsc, 'Roughness')
        self.mcy_skin.inputs.new(nsc, 'Bump')
        self.mcy_skin.inputs.new(nsc, 'Normal')
        self.mcy_skin.inputs.new(nsc, 'Displacement')
        self.mcy_skin.inputs.new(nsc, "SSSBlue")
        self.mcy_skin.inputs.new(nsc, "SSSRed")
        self.mcy_skin.inputs.new('NodeSocketFloat', 'SSSMix')
        self.mcy_skin.outputs.new('NodeSocketShader', 'Cycles')
        self.mcy_skin.outputs.new('NodeSocketVector', 'Displacement')
        self.mcy_skin.outputs.new('NodeSocketShader', 'EEVEE')

    def exe_skin(self):
        generate_names = ['NodeGroupInput', 'NodeGroupOutput', 'ShaderNodeBsdfPrincipled', 'ShaderNodeMixRGB.MIX',  # 0
                         'ShaderNodeDisplacement', 'ShaderNodeNormalMap', 'ShaderNodeBump', 'ShaderNodeFresnel',  # 4
                         'ShaderNodeBrightContrast', '', '', 'ShaderNodeHueSaturation',  # 8
                         'ShaderNodeBsdfGlossy', 'ShaderNodeSubsurfaceScattering', '', 'ShaderNodeInvert',  # 12
                         'ShaderNodeMixShader', '', '']  # 16
        con_nums = [  # Diffuse
            [[0, 0], [8, 0]],
            [[8, 0], [11, 4]],
            [[11, 0], [2, 0]],
            [[11, 0], [2, 3]],
            [[11, 0], [13, 0]],
            [[11, 0], [14, 0]],
            # SSS
            [[0, 6], [13, 2]],
            [[0, 7], [14, 2]],
            [[0, 8], [18, 0]],
            # Normal
            [[0, 4], [5, 1]],
            [[5, 0], [6, 'Normal']],
            [[6, 'Normal'], [2, 'Normal']],
            # Bump/displacement
            [[0, 3], [6, 'Height']],
            [[0, 3], [3, 1]],
            [[0, 5], [3, 2]],
            [[3, 0], [4, 'Height']],
            [[4, 0], [1, 1]],
            [[6, 0], [7, 1]],  # Bump->Fresnel
            [[7, 0], [16, 0]],  # Fresnel->Mix0
            [[7, 0], [17, 0]],  # Fresnel->Mix1
            [[16, 0], [18, 1]],  # Mix0->Mix2
            [[17, 0], [18, 2]],  # Mix1->Mix2
            # Specular/roughness
            [[0, 1], [9, 0]],
            [[9, 0], [2, 5]],
            [[0, 2], [15, 1]],  # rougness->invert
            [[15, 0], [10, 0]],  # invert->bright
            [[10, 0], [2, 7]],  # bright->bsdf
            [[10, 0], [12, 1]],  # bright_glossy
            [[9, 0], [12, 0]],
            [[12, 0], [16, 2]],
            [[12, 0], [17, 2]],
            [[13, 0], [16, 1]],  # blue
            [[14, 0], [17, 1]],  # red
            # out
            [[18, 0], [1, 0]],
            [[4, 0], [1, 1]],
            [[2, 0], [1, 2]],
        ]
        ROOT = self.mcy_skin.nodes
        LINK = self.mcy_skin.links
        old_gname = ""

        for g_index, g_name in enumerate(generate_names):
            if g_name == '':
                g_name = old_gname
            a = g_name.find('.')
            sub = None
            if a > 0:
                sub = g_name[a+1:]
                g_name = g_name[:a]
            n = ROOT.new(type=g_name)
            n.name = g_name + "-" + str(g_index)
            if sub is not None:
                n.blend_type = sub
            self.shaders.append(n)
            old_gname = g_name
            
        for cidx, cn in enumerate(con_nums):
            outp = cn[0]
            inp = cn[1]
            LINK.new(
                self.shaders[outp[0]].outputs[outp[1]],
                self.shaders[inp[0]].inputs[inp[1]]
            )
        NodeArrange.toNodeArrange(self.mcy_skin.nodes)
