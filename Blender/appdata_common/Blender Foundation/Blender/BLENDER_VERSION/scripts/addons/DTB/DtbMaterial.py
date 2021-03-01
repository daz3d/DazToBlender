import os
import json
import pathlib
import bpy

from . import Global
from . import NodeArrange
from . import Versions
from . import MatDct
from . import Util

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

def srgb_to_linear_rgb(srgb):
    if   srgb < 0:       return 0
    elif srgb < 0.04045: return srgb/12.92
    else:             return ((srgb+0.055)/1.055)**2.4


def hex_to_col(hex,normalize=True,precision=6):
    col = []
    it = iter(hex)
    for char in it:
        col.append(int(char + it.__next__(), 16))
    if normalize:
        col = map(lambda x: x / 255, col)
        col = map(lambda x: round(x, precision), col)
    return list(srgb_to_linear_rgb(c) for c in col)


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

def default_material():
    getGroupNodeTree("EyeDry")
    getGroupNodeTree("EyeWet")
    getGroupNodeTree("IrayUberSkin")

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
        tree = getGroupNodeTree("EyeDry")
        tbls = eyecombi
    else:
        tree = getGroupNodeTree("IrayUberSkin")
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



# endregion top-level methods

class DtbShaders:
    dct = {}
    mat_data_dict = {}
    node_groups = []
    is_Diffuse = False
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
        file_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(file_dir, file_path)
        
        # load node_groups from link_library.blend file
        with bpy.data.libraries.load(file_path) as (data_from, data_to):
            if len(bpy.data.node_groups) != len(data_from.node_groups):
                self.node_groups = data_from.node_groups
                data_to.node_groups = data_from.node_groups
    
    def get_mat_properties(self,mat_data):
        mat_property_dict = {}
        for mat_property in mat_data["Properties"]:
            mat_property_dict[mat_property["Name"]] = mat_property
        return mat_property_dict
    

    def set_eevee_alpha(self,mat):
        if mat.name == "Eyelashes":
                Versions.eevee_alpha(mat, 'BLEND', 0)
        if mat.name in [
                    "Cornea",
                    "EyeMoisture",
                    "EyeMoisture.00",
                    "EylsMoisture"
                ]:
                Versions.eevee_alpha(mat, 'HASHED', 0)

   
    def find_node_property(self,input_key,mat_property_dict):
        property_key, property_type = input_key.split(": ")
        property_info = mat_property_dict[property_key][property_type]
        return property_key,property_type,property_info
        
    #TODO: Check for all Color Maps            
    def check_map_type(self,property_key):
        if "Diffuse" in property_key:
            self.is_Diffuse = True

   
    def create_texture_input(self,tex_path,tex_image_node):
        
        tex_image = bpy.data.images.load(filepath=tex_path)
        tex_image_node.image = tex_image
        if not self.is_Diffuse:
            Versions.to_color_space_non(tex_image_node)
   

    def convert_color(self,color,shader_node):
        color_hex = color.lstrip('#')
        color_rgb = hex_to_col(color_hex)
        color_rgb.append(1) # alpha
        return color_rgb
   
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
            # To Deal With Multiple Characters
            mat_name = mat.name.split(".0")[0]
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
            elif mat_name in ["Eyelashes"]:
                shader_node.node_tree = bpy.data.node_groups["Eyelashes"]
            else:
                shader_node.node_tree = bpy.data.node_groups["IrayUberSkin"]

            # Link corresponding nodes in the material
            render_output = None
            surface_input = out_node_cy.inputs['Surface']
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
            
            mat_property_dict = self.get_mat_properties(mat_data)
            self.set_eevee_alpha(mat)
            # Find and Attach Node Input
            for input_key in shader_node.inputs.keys():
    
                if ("Texture" in input_key) or ("Value" in input_key):
                    # To deal with Gen 8.1 Not Share the Same info as Gen 8 "temp"
                    if input_key.split(": ")[0] in mat_property_dict.keys():
                        property_key,property_type,property_info = self.find_node_property(input_key,mat_property_dict)
                        if property_type == "Value":
                            # Check if Info is a Hex Color
                            if isinstance(property_info,str):
                                property_info = self.convert_color(property_info,shader_node)
                            shader_node.inputs[input_key].default_value = property_info

                        if property_type == "Texture":
                            if os.path.exists(property_info): 
                                self.check_map_type(property_key)
                                tex_image_node = mat_nodes.new(
                                                type='ShaderNodeTexImage'
                                            )
                                self.create_texture_input(property_info,tex_image_node)
                                tex_node_output = tex_image_node.outputs['Color']
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
                        #pandb = insert_bump_map(mat_nodes, mat_links)
                        #BUMP = pandb[1]
                        #mat_nodes = pandb[0]
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

