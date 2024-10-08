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
                        print("DEBUG: forbitMinus(): node_input.name = " + node_input.name + ", node_input.default_value=" + str(node_input.default_value))
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
                                    print("DEBUG: forbitMinus(): node_input.name = " + node_input.name + ", node_input.default_value = " + str(node_input.default_value))
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

    # DB 2023-June-27: work-around for new materials (since obj is re-used)
    def reset_material_settings(self):
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
            # G9 material support
            "EyeMoisture Left",
            "EyeMoisture Right",
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
        if "Diffuse" in property_key or "Base Color" in property_key:
            self.is_Diffuse = True
        else:
            self.is_Diffuse = False

        # DB 2023-June-27: Alpha-Fix: Turn on alpha, and leave on for this material
        if "Opacity" in property_key and self.is_Alpha == False:
            self.is_Alpha = True
        # else:
        #     self.is_Alpha = False

        if "Refraction Weight" in property_key and property_key["Refraction Weight"]["Value"] > 0:
            self.is_Refract = True
            self.is_Alpha = True

    def check_refract(self):
        if "Refraction Weight" in self.mat_property_dict.keys():
            if self.mat_property_dict["Refraction Weight"]["Value"] > 0:
                self.is_Refract = True
                self.is_Alpha = True

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
                # G9 material support
                "EyeMoisture Left",
                "EyeMoisture Right",
                "Eye Left",
                "Eye Right",
            ]:
                Versions.eevee_alpha(mat, "HASHED", 0)

    def set_eevee_refract(self, mat):
        if self.is_Refract:
            mat.use_screen_refraction = True
            mat.refraction_depth = 0.8 * Global.get_size()
            Versions.eevee_alpha(mat, "HASHED", 0)

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

            self.reset_material_settings()
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

            # DB, 2024-09-25: Bugfix to account for combined diffuse+alpha image maps
            color_file = None
            alpha_file = None
            color_node = None
            alpha_node = None
            is_combined_diffuse_alpha = False
            # perform a pre-pass to popuate the color and alpha textures
            print("DEBUG: DazToBlender: setup_materials(): performing pre-pass to populate color and alpha textures, material: " + mat_name)
            for input_key in shader_node.inputs.keys():
                if "Texture" in input_key:
                    if input_key.split(": ")[0] in self.mat_property_dict.keys():
                        (
                            property_key,
                            property_type,
                            property_info,
                        ) = self.find_node_property(input_key, self.mat_property_dict)
                        if "Diffuse Color" in property_key:
                            print("DEBUG: DazToBlender: setup_materials(): property_key = Diffuse Color, property_info = " + str(property_info))
                            color_file = property_info
                        if "Opacity" in property_key:
                            print("DEBUG: DazToBlender: setup_materials(): property_key = Opacity, property_info = " + str(property_info))
                            alpha_file = property_info
            if (color_file is not None and color_file != ""
                and alpha_file is not None and alpha_file != ""
                and color_file == alpha_file):
                is_combined_diffuse_alpha = True
                print("DEBUG: DazToBlender: DtbMaterial.py: setup_materials(): is_combined_diffuse_alpha = True, material: " + mat_name)
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
                            # check if a usable node already exists
                            tex_image_node = None
                            if (is_combined_diffuse_alpha and "Diffuse Color" in property_key):
                                if alpha_node is not None:
                                    self.check_map_type(property_key)
                                    tex_image_node = alpha_node
                                    tex_node_output = tex_image_node.outputs["Color"]
                                    mat_links.new(
                                        tex_node_output, shader_node.inputs[input_key]
                                    )
                            elif (is_combined_diffuse_alpha and "Opacity" in property_key):
                                if color_node is not None:
                                    self.check_map_type(property_key)
                                    tex_image_node = color_node
                                    tex_node_output = tex_image_node.outputs["Alpha"]
                                    mat_links.new(
                                        tex_node_output, shader_node.inputs[input_key]
                                    )
                            if tex_image_node is None:
                                # create a texture node if one does not already exist
                                if os.path.exists(property_info):
                                    self.check_map_type(property_key)
                                    tex_image_node = mat_nodes.new(
                                        type="ShaderNodeTexImage"
                                    )
                                    self.create_texture_input(property_info, tex_image_node)
                                    if (is_combined_diffuse_alpha and "Diffuse Color" in property_key):
                                        color_node = tex_image_node
                                        tex_node_output = tex_image_node.outputs["Color"]
                                        mat_links.new(
                                            tex_node_output, shader_node.inputs[input_key]
                                        )
                                    elif (is_combined_diffuse_alpha and "Opacity" in property_key):
                                        alpha_node = tex_image_node
                                        tex_node_output = tex_image_node.outputs["Alpha"]
                                        mat_links.new(
                                            tex_node_output, shader_node.inputs[input_key]
                                        )
                                    else:
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
                # add principled BSDF node
                pbsdf = mat_nodes.new(type="ShaderNodeBsdfPrincipled")
                mat_links.new(shader_node.outputs["Base Color"], pbsdf.inputs["Base Color"])
                mat_links.new(shader_node.outputs["Roughness"], pbsdf.inputs["Roughness"])
                mat_links.new(shader_node.outputs["Normal"], pbsdf.inputs["Normal"])
                mat_links.new(shader_node.outputs["IOR"], pbsdf.inputs["IOR"])
                if bpy.app.version[0] >= 4:
                    mat_links.new(shader_node.outputs["Specular"], pbsdf.inputs["Specular IOR Level"])
                else:
                    mat_links.new(shader_node.outputs["Specular"], pbsdf.inputs["Specular"])
                # link pbsdf to outputs
                mat_links.new(pbsdf.outputs["BSDF"], out_node_cy.inputs["Surface"])
                mat_links.new(pbsdf.outputs["BSDF"], out_node_ev.inputs["Surface"])
            elif node_group == "IrayUber":
                # add principled BSDF node
                pbsdf = mat_nodes.new(type="ShaderNodeBsdfPrincipled")
                mat_links.new(shader_node.outputs["Base Color"], pbsdf.inputs["Base Color"])
                mat_links.new(shader_node.outputs["Metallic"], pbsdf.inputs["Metallic"])
                if bpy.app.version[0] >= 4:
                    mat_links.new(shader_node.outputs["Specular"], pbsdf.inputs["Specular IOR Level"])
                else:
                    mat_links.new(shader_node.outputs["Specular"], pbsdf.inputs["Specular"])
                mat_links.new(shader_node.outputs["Roughness"], pbsdf.inputs["Roughness"])
                mat_links.new(shader_node.outputs["Alpha"], pbsdf.inputs["Alpha"])
                mat_links.new(shader_node.outputs["Normal"], pbsdf.inputs["Normal"])
                # link pbsdf to outputs
                mat_links.new(pbsdf.outputs["BSDF"], out_node_cy.inputs["Surface"])
                mat_links.new(pbsdf.outputs["BSDF"], out_node_ev.inputs["Surface"])
                # DB 2024-10-02: handle refraction weight
                if self.is_Refract:
                    # set iray opacity to 0.05
                    if "Cutout Opacity: Value" in shader_node.inputs:
                        shader_node.inputs["Cutout Opacity: Value"].default_value = 0.05
            elif node_group == "EyeWet":
                pbsdf = mat_nodes.new(type="ShaderNodeBsdfPrincipled")
                pbsdf.inputs["Metallic"].default_value = 1.0
                pbsdf.inputs["Roughness"].default_value = 0.0
                pbsdf.inputs["IOR"].default_value = 1.450
                pbsdf.inputs["Alpha"].default_value = 0.5
                if bpy.app.version[0] >= 4:
                    pbsdf.inputs["Specular IOR Level"].default_value = 1.0
                    pbsdf.inputs["Transmission Weight"].default_value = 1.0
                else:
                    pbsdf.inputs["Specular"].default_value = 1.0
                    pbsdf.inputs["Transmission"].default_value = 1.0
                # add fresnel node
                fresnel = mat_nodes.new(type="ShaderNodeFresnel")
                fresnel.inputs["IOR"].default_value = 1.450
                # add transparent BSDF
                transparent = mat_nodes.new(type="ShaderNodeBsdfTransparent")
                # add mix shader
                mix = mat_nodes.new(type="ShaderNodeMixShader")
                # link nodes
                mat_links.new(fresnel.outputs["Fac"], mix.inputs["Fac"])
                mat_links.new(transparent.outputs["BSDF"], mix.inputs[1])
                mat_links.new(pbsdf.outputs["BSDF"], mix.inputs[2])
                mat_links.new(shader_node.outputs["Normal"], pbsdf.inputs["Normal"])
                mat_links.new(mix.outputs["Shader"], out_node_cy.inputs["Surface"])
                mat_links.new(mix.outputs["Shader"], out_node_ev.inputs["Surface"])
            elif node_group == "EyeDry":
                pbsdf = mat_nodes.new(type="ShaderNodeBsdfPrincipled")
                pbsdf.inputs["Roughness"].default_value = 0.0
                pbsdf.inputs["IOR"].default_value = 1.350
                if bpy.app.version[0] >= 4:
                    pbsdf.inputs["Specular IOR Level"].default_value = 0.0
                else:
                    pbsdf.inputs["Specular"].default_value = 0.0
                mat_links.new(shader_node.outputs["Base Color"], pbsdf.inputs["Base Color"])
                mat_links.new(shader_node.outputs["Normal"], pbsdf.inputs["Normal"])
                mat_links.new(pbsdf.outputs["BSDF"], out_node_cy.inputs["Surface"])
                mat_links.new(pbsdf.outputs["BSDF"], out_node_ev.inputs["Surface"])
            elif node_group == "Eyelashes":
                pbsdf = mat_nodes.new(type="ShaderNodeBsdfPrincipled")
                mat_links.new(shader_node.outputs["Base Color"], pbsdf.inputs["Base Color"])
                mat_links.new(shader_node.outputs["Normal"], pbsdf.inputs["Normal"])
                mat_links.new(shader_node.outputs["Alpha"], pbsdf.inputs["Alpha"])
                mat_links.new(pbsdf.outputs["BSDF"], out_node_cy.inputs["Surface"])
                mat_links.new(pbsdf.outputs["BSDF"], out_node_ev.inputs["Surface"])
            else:
                mat.cycles.displacement_method = "BUMP"

            if mat_nodes is not None:
                NodeArrange.toNodeArrange(mat_nodes)
