import os
import json
import pathlib
import bpy

from . import Global
from . import NodeArrange
from . import Versions
from . import MatDct
from . import Util


# region top-level methods
def srgb_to_linear_rgb(srgb):
    if srgb < 0:
        return 0
    elif srgb < 0.04045:
        return srgb / 12.92
    else:
        return ((srgb + 0.055) / 1.055) ** 2.4


def hex_to_col(hex, normalize=True, precision=6):
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
    pbsdf = "Principled BSDF"
    for dobj in Util.myccobjs():
        if dobj.type != "MESH" or dobj == Global.getBody():
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
                        if (
                            node_input.name == "Metallic"
                            and node_input.default_value == 1.0
                        ):
                            node_input.default_value = 0.0
                        if (
                            node_input.name == "Specular"
                            and node_input.default_value == 2.0
                        ):
                            node_input.default_value = 0.2
                    elif type(node_input.default_value) is list:
                        for i in node_input.default_value:
                            if type(i) is float:
                                if node_input.default_value < 0:
                                    node_input.default_value = 0.0


def adjust_material(kind, inc_value, isEye):
    skincombi = [
        ["Base Color.Hue", 11, 0],
        ["Base Color.Saturation", 11, 1],
        ["Base Color.Value", 11, 2],
        ["Base Color.Bright", 8, 1],
        ["Base Color.Contrast", 8, 2],
        ["Specular", 9, 1],
        ["Roughness", 10, 1],
        ["Roughness.Contrast", 9, 2],
        ["Specular.Contrast", 10, 2],
        ["Subsurface.Scale", 14, 1],
        ["Subsurface.Scale", 13, 1],
        ["Normal.Strength", 5, 0],
        ["Bump.Strength", 6, 0],
        ["Bump.Distance", 6, 1],
        ["Displacement.Height", 4, 2],  # 14
        ["Subsurface.Scale", 2, 2],
        ["Subsurface.Scale", 2, 1],
    ]
    eyecombi = [
        ["Base Color.Bright", 1, 1],
        ["Base Color.Contrast", 1, 2],
        ["Normal.Strength", 3, 0],
        ["Bump.Strength", 4, 0],
        ["Bump.Distance", 4, 1],
        ["Base Color.Hue", 6, 0],
        ["Base Color.Saturation", 6, 1],
        ["Base Color.Value", 6, 2],
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
    def __init__(self, dtu):
        self.material_list = dtu.get_materials_list()
        self.mat_data_dict = {}
        self.mat_property_dict = {}
        self.node_groups = []
        self.is_Diffuse = False
        self.is_Refract = False
        self.is_Alpha = False

    # TODO: Find a better way to create the dict
    def make_dct(self):
        mat_info_list = self.material_list
        for mat_info in mat_info_list:
            if mat_info["Asset Name"] == mat_info["Asset Label"]:
                if mat_info["Asset Name"] in self.mat_data_dict.keys():
                    self.mat_data_dict[mat_info["Asset Name"]][
                        mat_info["Material Name"]
                    ] = mat_info
                else:
                    self.mat_data_dict[mat_info["Asset Name"]] = {}
                    self.mat_data_dict[mat_info["Asset Name"]][
                        mat_info["Material Name"]
                    ] = mat_info
            elif mat_info["Asset Name"] != mat_info["Asset Label"]:
                if mat_info["Asset Name"] not in self.mat_data_dict.keys():
                    self.mat_data_dict[mat_info["Asset Name"]] = {}
                    self.mat_data_dict[mat_info["Asset Name"]][
                        mat_info["Material Name"]
                    ] = mat_info
                if mat_info["Asset Name"] in self.mat_data_dict.keys():
                    if (
                        mat_info["Material Name"]
                        not in self.mat_data_dict[mat_info["Asset Name"]]
                    ):
                        self.mat_data_dict[mat_info["Asset Name"]][
                            mat_info["Material Name"]
                        ] = mat_info
                if mat_info["Asset Label"] in self.mat_data_dict.keys():
                    self.mat_data_dict[mat_info["Asset Label"]][
                        mat_info["Material Name"]
                    ] = mat_info
                if mat_info["Asset Label"] not in self.mat_data_dict.keys():
                    self.mat_data_dict[mat_info["Asset Label"]] = {}
                    self.mat_data_dict[mat_info["Asset Label"]][
                        mat_info["Material Name"]
                    ] = mat_info

    def load_shader_nodes(self):
        file_path = os.path.join("dependencies", "link_library.blend")
        file_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(file_dir, file_path)

        # load node_groups from link_library.blend file
        with bpy.data.libraries.load(file_path) as (data_from, data_to):
            if len(bpy.data.node_groups) != len(data_from.node_groups):
                self.node_groups = data_from.node_groups
                data_to.node_groups = data_from.node_groups

    def get_mat_properties(self, mat_data):
        self.mat_property_dict = {}
        # To deal with material names sometimes being undescriptive.
        for mat_property in mat_data["Properties"]:
            self.mat_property_dict[mat_property["Name"]] = mat_property
            self.mat_property_dict[mat_property["Label"]] = mat_property
        return self.mat_property_dict

    def get_mat_type(self, material):
        material_name = material["Material Name"]
        material_type = material["Material Type"]
        object_type = material["Value"]
        if material_name in [
            "Cornea",
            "EyeMoisture",
            "EyeMoisture.00",
            "EylsMoisture",
            "Tear",
        ]:
            return "EyeWet"

        elif material_name in ["Pupils", "Trises", "Sclera"]:
            return "EyeDry"

        elif "Eyelashes" in object_type:
            return "Eyelashes"

        elif material_type == "Iray Uber":
            if object_type == "Actor/Character" or object_type == "Follower/Attachment/Lower-Body/Hip/Front":
                return "IrayUberSkin"
            else:
                return "IrayUber"

        elif material_type == "AoA_Subsurface":
            return "AoA_Subsurface"

        elif material_type == "omUberSurface":
            return "omUberSurface"

        elif material_type == "PBRSkin":
            return "IrayUberSkin"

        elif ("Hair" in material_type) or ("Hair" in object_type):
            return "IrayUber"

        elif material_type == "DAZ Studio Default":
            return "DAZ Studio Default"
        else:
            return "DefaultMaterial"

    def optimize_materials(self, mat_slot):
        mat = mat_slot.material
        if "Genesis" in mat["Asset Name"]:
            mat_name = mat["Asset Label"] + "_" + mat["Material Name"]
        else:
            mat_name = mat["Asset Name"] + "_" + mat["Material Name"]
        if mat_name not in bpy.data.materials:
            if mat["Asset Name"] != mat["Asset Label"]:
                mat.name = mat["Asset Name"] + "_" + mat["Material Name"]
                return
            else:
                return

        material = bpy.data.materials[mat_name]
        if mat_name != mat.name:
            if mat["Asset Name"] == material["Asset Name"]:
                mat_slot.material = material
                bpy.data.materials.remove(mat)
                return True

    # TODO: Check for all Color Maps
    def check_map_type(self, property_key):
        if "Diffuse" in property_key:
            self.is_Diffuse = True
        else:
            self.is_Diffuse = False
        if "Opacity" in property_key:
            self.is_Alpha = True
        else:
            self.is_Alpha = False

    def check_refract(self):
        if "Refraction Weight" in self.mat_property_dict.keys():
            if self.mat_property_dict["Refraction Weight"]["Value"] > 0:
                self.is_Refract = True

    def set_eevee_alpha(self, mat):
        if self.is_Alpha:
            Versions.eevee_alpha(mat, "HASHED", 0)
        else:
            mat_name = mat["Material Name"]
            if mat_name in [
                "Cornea",
                "EyeMoisture",
                "EylsMoisture",
                "Tear",
                "Eyelashes",
                "Glass",
            ]:
                Versions.eevee_alpha(mat, "HASHED", 0)

    def set_eevee_refract(self, mat):
        if self.is_Refract:
            mat.use_screen_refraction = True
            mat.refraction_depth = 0.8 * Global.get_size()

    def find_node_property(self, input_key, mat_property_dict):
        property_key, property_type = input_key.split(": ")
        property_info = mat_property_dict[property_key][property_type]
        return property_key, property_type, property_info

    def create_texture_input(self, tex_path, tex_image_node):
        tex_path = os.path.abspath(tex_path)
        tex_image = bpy.data.images.load(filepath=tex_path)
        tex_image_node.image = tex_image
        if not self.is_Diffuse:
            Versions.to_color_space_non(tex_image_node)

    def convert_color(self, color, shader_node):
        color_hex = color.lstrip("#")
        color_rgb = hex_to_col(color_hex)
        color_rgb.append(1)  # alpha
        return color_rgb

    def setup_materials(self, obj):
        for mat_slot in obj.material_slots:

            mat = mat_slot.material
            mat_name = mat.name

            obj_name = obj.name.replace(".Shape", "")
            obj_name = obj_name.split(".")[0]

            if mat is None:
                # Get or create a new material when slot is missing material
                mat = bpy.data.materials.get(mat_slot.name) or bpy.data.materials.new(
                    name=mat_slot.name
                )
                mat_slot.material = mat
            if obj_name not in self.mat_data_dict.keys():
                continue
            if mat_name not in self.mat_data_dict[obj_name].keys():
                mat_name = mat.name.split(".")[0]
                if mat_name not in self.mat_data_dict[obj_name].keys():
                    continue

            mat_data = self.mat_data_dict[obj_name][mat_name]
            self.mat_property_dict = self.get_mat_properties(mat_data)
            # Set Custom Properties
            for key in mat_data:
                if not key == "Properties":
                    mat[key] = mat_data[key]

            # Update Name
            new_name = mat["Asset Label"] + "_" + mat["Material Name"]

            if bpy.context.window_manager.combine_materials:
                # To Deal with a duplicate being converted first.
                if new_name in bpy.data.materials:
                    mat_slot.material = bpy.data.materials[new_name]
                    bpy.data.materials.remove(mat)
                    continue
                mat.name = new_name
                mat_name = mat.name
                # To Deal with duplications
                if self.optimize_materials(mat_slot):
                    continue

            mat.use_nodes = True
            mat_nodes = mat.node_tree.nodes
            mat_links = mat.node_tree.links

            # Remove all the nodes from the material
            for mat_node in mat_nodes:
                mat_nodes.remove(mat_node)

            # Create material output nodes and set corresponding targets
            out_node_cy = mat_nodes.new(type="ShaderNodeOutputMaterial")
            out_node_cy.target = "CYCLES"
            out_node_ev = mat_nodes.new(type="ShaderNodeOutputMaterial")
            out_node_ev.target = "EEVEE"

            # Create shader node and set links
            shader_node = mat_nodes.new(type="ShaderNodeGroup")
            node_group = self.get_mat_type(mat)
            shader_node.node_tree = bpy.data.node_groups[node_group]

            # Link corresponding nodes in the material
            render_output = None
            surface_input = out_node_cy.inputs["Surface"]
            render_output = shader_node.outputs["Cycles"]
            mat_links.new(render_output, surface_input)
            mat_links.new(shader_node.outputs["EEVEE"], out_node_ev.inputs["Surface"])
            # Find and Attach Node Input

            for input_key in shader_node.inputs.keys():

                if ("Texture" in input_key) or ("Value" in input_key):
                    # To deal with Gen 8.1 Not Share the Same info as Gen 8 "temp"
                    if input_key.split(": ")[0] in self.mat_property_dict.keys():
                        (
                            property_key,
                            property_type,
                            property_info,
                        ) = self.find_node_property(input_key, self.mat_property_dict)
                        if property_type == "Value":
                            # Check if Info is a Hex Color
                            if isinstance(property_info, str):
                                property_info = self.convert_color(
                                    property_info, shader_node
                                )
                            if input_key == "Normal Map: Value":
                                if isinstance(property_info, list):
                                    property_info = 1
                            shader_node.inputs[input_key].default_value = property_info

                        if property_type == "Texture":
                            if os.path.exists(property_info):
                                self.check_map_type(property_key)
                                tex_image_node = mat_nodes.new(
                                    type="ShaderNodeTexImage"
                                )
                                self.create_texture_input(property_info, tex_image_node)
                                tex_node_output = tex_image_node.outputs["Color"]
                                mat_links.new(
                                    tex_node_output, shader_node.inputs[input_key]
                                )

            # Set Alpha Modes
            self.check_refract()
            self.set_eevee_refract(mat)
            self.set_eevee_alpha(mat)

            # Set the cycles displacement method
            if node_group == "IrayUberSkin":
                mat_links.new(
                    shader_node.outputs["Displacement"],
                    out_node_cy.inputs["Displacement"],
                )
                mat.cycles.displacement_method = "BOTH"
            else:
                mat.cycles.displacement_method = "BUMP"

            if mat_nodes is not None:
                NodeArrange.toNodeArrange(mat_nodes)
