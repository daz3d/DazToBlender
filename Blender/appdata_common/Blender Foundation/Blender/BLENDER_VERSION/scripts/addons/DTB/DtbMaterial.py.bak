import os
import json
import pathlib
import bpy
import pprint

from . import Global
from . import NodeArrange
from . import Versions
from . import MatDct
from . import Util
from . import BumpToNormal


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
            if ("Name" not in mat_property or "Label" not in mat_property):
                continue
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
            if object_type == "Actor/Character":
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

    def optimize_materials(self, mat_slot, sObjectName=""):
        print("ENTER: DEBUG: DtbMaterial.py, optimize_materials()")
        mat = mat_slot.material
        if "Genesis" in mat["Asset Name"]:
            mat_name = mat["Asset Label"] + "_" + mat["Material Name"]
        else:
            mat_name = mat["Asset Name"] + "_" + mat["Material Name"]
        # check if mat_name is already in materials
        mat_name += sObjectName;
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


    # remove shader_node from convert_color()
    def daz_color_to_rgb(self, color):
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



            # handle Tile
            Horizontal_Tiles = self.mat_property_dict.get("Horizontal Tiles")
            Vertical_Tiles = self.mat_property_dict.get("Vertical Tiles")
            if Horizontal_Tiles["Value"] > 1 or Vertical_Tiles["Value"] > 1:
                # create Mapping node and Coord node
                mapping_node = mat_nodes.new("ShaderNodeMapping")
                coord_node = mat_nodes.new("ShaderNodeTexCoord")
                # set value
                # x
                mapping_node.inputs["Scale"].default_value[0] = Horizontal_Tiles["Value"]
                # y
                mapping_node.inputs["Scale"].default_value[1] = Vertical_Tiles["Value"]
                # link them
                mat_links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
                # link mapping_node to all texture node
                for node in mat_nodes:
                    if node.bl_idname == "ShaderNodeTexImage":
                        mat_links.new(mapping_node.outputs["Vector"], node.inputs["Vector"])

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


    #set a texture node
    def set_tex_node(self, tex_path, property_name, mat_nodes, mat_links, shader_node, input_key):
        if os.path.exists(tex_path):
            # this will set is_Diffuse or is_Alpha, which will be used in create_texture_input
            self.check_map_type(property_name)
            tex_image_node = mat_nodes.new("ShaderNodeTexImage")

            self.create_texture_input(tex_path, tex_image_node)
            tex_node_output = tex_image_node.outputs["Color"]
            mat_links.new(
                tex_node_output, shader_node.inputs[input_key]
            )

    #set value or add texture node
    def set_value_or_tex(self, property_name, mat_nodes, mat_links, shader_node, input_key):
        property = self.mat_property_dict.get(property_name)
        if property is None:
            print("can not find: " + property_name)
            return

        if len(property["Texture"])>0:
            tex_path = property["Texture"]
            self.set_tex_node(tex_path, property_name, mat_nodes, mat_links, shader_node, input_key)
        elif property["Data Type"] == "Double":
            shader_node.inputs[input_key].default_value = property["Value"]

    #set color or add texture node
    def set_color_or_tex(self, property_name, mat_nodes, mat_links, shader_node, input_key):
        property = self.mat_property_dict.get(property_name)
        if property is None:
            print("can not find: " + property_name)
            return

        if property["Data Type"] == "Color":
            color = self.daz_color_to_rgb(property["Value"])
            shader_node.inputs[input_key].default_value = (color[0], color[1], color[2], color[3])

        elif len(property["Texture"])>0:
            tex_path = property["Texture"]
            self.set_tex_node(tex_path, "Diffuse", mat_nodes, mat_links, shader_node, input_key)





    # use Principled BSDF shader
    def setup_principled_materials(self, obj):
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

            # change viewport display
            mat.metallic = 0
            # set viewport display color
            # set eyeball to black
            if "Irises" in mat_name:
                mat.diffuse_color = (0,0,0,1)
            elif "Pupils" in mat_name:
                mat.diffuse_color = (0,0,0,1)
            elif "Cornea" in mat_name:
                mat.diffuse_color = (0,0,0,0)
            elif "_Lips" in mat_name:
                mat.diffuse_color = (1, 0.8, 0.8, 1)
            elif "Eyelashes" in mat_name:
                mat.diffuse_color = (0,0,0,0.5)

            # map iray shader to Principled BSDF shader from here

            # find Principled BSDF shader node
            shader_node = mat_nodes.get("Principled BSDF")

            # find Principled BSDF by bl_idname
            if shader_node is None:
                for node in mat_nodes:
                    if node.bl_idname == "ShaderNodeBsdfPrincipled":
                        shader_node = node

            # if still no shader node, then create one
            if shader_node is None:
                shader_node = mat_nodes.new("ShaderNodeBsdfPrincipled")

            if shader_node is None:
                print("can not find Principled BSDF node for mat: " + mat.name)
                # do not create a new Principled BSDF, so we can see what may be wrong from shader editor
                # make it easier to fix bugs
                continue

            # change subsurface_method to fixed. The new automatically one is not good and has bugs
            shader_node.subsurface_method = 'RANDOM_WALK_FIXED_RADIUS'

            # show info for debug
            # pprint.pprint(self.mat_property_dict)
            # print(" ")

            # find "Normal Map" node
            normal_node = mat_nodes.get("Normal Map")
            if normal_node is not None:
                # change label "Normal/Map" to "Normal Map"
                # there is no such name as "Normal/Map" in blender
                normal_node.label = "Normal Map"

            # find normal node by bl_idname
            if normal_node is None:
                for node in mat_nodes:
                    if node.bl_idname == "ShaderNodeNormalMap":
                        normal_node = node

            # if still no normal node, then create one
            if normal_node is None:
                normal_node = mat_nodes.new("ShaderNodeNormalMap")

            # map iray material to blender
            # iray mat's Properties looks like this:
            # {
            #     "Name": "Diffuse Weight",
            #     "Label": "Diffuse Weight",
            #     "Value": 1,
            #     "Data Type": "Double",
            #     "Texture": ""
            # },
            # {
            #     "Name": "Diffuse Color",
            #     "Label": "Base Color",
            #     "Value": "#ffffff",
            #     "Data Type": "Color",
            #     "Texture": "texture_path.jpg"
            # },
            # {
            #     "Name": "Diffuse Overlay Color",
            #     "Label": "Diffuse Overlay Color",
            #     "Value": "#c0c0c0",
            #     "Data Type": "Color",
            #     "Texture": ""
            # },
            for input_key in shader_node.inputs.keys():
                # reset
                property = None
                tex_path = ""

                if input_key == "Base Color":
                    # an Image Texture node should already be linked to shader_node
                    property = self.mat_property_dict.get("Diffuse Color")
                    if property["Texture"] == "":
                        # set color value
                        color = self.daz_color_to_rgb(property["Value"])
                        shader_node.inputs[input_key].default_value = (color[0], color[1], color[2], color[3])

                elif input_key == "Subsurface":
                    property = self.mat_property_dict.get("Translucency Weight")
                    if property is None:
                        print("can not find: " + "Translucency Weight")
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    if property["Data Type"] == "Double":
                        shader_node.inputs[input_key].default_value = property["Value"] * Global.sss_rate

                    elif len(property["Texture"])>0:
                        tex_path = property["Texture"]
                        self.set_tex_node(tex_path, "Translucency Weight", mat_nodes, mat_links, shader_node, input_key)

                elif input_key == "Subsurface Radius":
                    # always use this value
                    shader_node.inputs[input_key].default_value[0] = 0.2
                    shader_node.inputs[input_key].default_value[1] = 0.2
                    shader_node.inputs[input_key].default_value[2] = 0.2

                elif input_key == "Subsurface Color":
                    Translucency_Color = self.mat_property_dict.get("Translucency Color")
                    Base_Color_Effect = self.mat_property_dict.get("Base Color Effect")

                    if Translucency_Color is None:
                        continue

                    # do not use Translucency Color's texture, always use the color value
                    color = self.daz_color_to_rgb(Translucency_Color["Value"])

                    # Base_Color_Effect values: Scatter Only(0), Scatter & Transmit(1)，Scatter & Transmit Intensity(2)
                    if Base_Color_Effect is not None:
                        if Base_Color_Effect["Value"] != 0:
                            SSS_Reflectance_Tint = self.mat_property_dict.get("SSS Reflectance Tint")
                            tint_color = self.daz_color_to_rgb(SSS_Reflectance_Tint["Value"])
                            #r
                            color[0] = color[0] * tint_color[0]
                            #g
                            color[1] = color[1] * tint_color[1]
                            #b
                            color[2] = color[2] * tint_color[2]
                            #alpha is always 1, so no need to handle

                    # set blender's color
                    shader_node.inputs[input_key].default_value = (color[0], color[1], color[2], color[3])

                elif input_key == "Subsurface IOR":
                    # useless
                    pass

                elif input_key == "Subsurface Anisotropy":
                    # useless
                    pass

                elif input_key == "Metallic":
                    self.set_value_or_tex("Metallic Weight", mat_nodes, mat_links, shader_node, input_key)

                elif input_key == "Specular":
                    #need to merge Glossy and Dual Lobe Specular
                    Dual_Lobe_Specular_Weight = self.mat_property_dict.get("Dual Lobe Specular Weight")
                    Dual_Lobe_Specular_Reflectivity = self.mat_property_dict.get("Dual Lobe Specular Reflectivity")
                    Specular_Lobe_1_Roughness = self.mat_property_dict.get("Specular Lobe 1 Roughness")
                    Specular_Lobe_2_Roughness = self.mat_property_dict.get("Specular Lobe 2 Roughness")
                    Dual_Lobe_Specular_Ratio = self.mat_property_dict.get("Dual Lobe Specular Ratio")
                    Glossy_Layered_Weight = self.mat_property_dict.get("Glossy Layered Weight")
                    Glossy_Weight = self.mat_property_dict.get("Glossy Weight")
                    Glossy_Reflectivity = self.mat_property_dict.get("Glossy Reflectivity")
                    Glossy_Roughness = self.mat_property_dict.get("Glossy Roughness")

                    if (Dual_Lobe_Specular_Weight is None or
                        Dual_Lobe_Specular_Reflectivity is None or
                        Specular_Lobe_1_Roughness is None or
                        Specular_Lobe_2_Roughness is None or
                        Dual_Lobe_Specular_Ratio is None or
                        Glossy_Layered_Weight is None or
                        Glossy_Weight is None or
                        Glossy_Reflectivity is None or
                        Glossy_Roughness is None):
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    if Glossy_Weight["Value"] > 0:
                        Glossy_Layered_Weight = Glossy_Weight

                    # calculate dual lobe specular's final roughness
                    r1 = Specular_Lobe_1_Roughness["Value"]
                    r2 = Specular_Lobe_2_Roughness["Value"]
                    ratio = Dual_Lobe_Specular_Ratio["Value"]
                    # (1- rated_r) = ((1-r2) * (1-ratio) + (1-r1) * ratio)
                    rated_r = 1 - (((1-r2) * (1-ratio)) + ((1-r1) * ratio))
                    if rated_r > 1:
                        rated_r = 1
                    elif rated_r < 0:
                        rated_r = 0

                    if Dual_Lobe_Specular_Weight["Value"] > 0 and len(Dual_Lobe_Specular_Weight["Texture"])>0:
                        #use Dual_Lobe_Specular_Weight texture
                        self.set_tex_node(Dual_Lobe_Specular_Weight["Texture"], "Dual Lobe Specular Weight", mat_nodes, mat_links, shader_node, input_key)

                    elif Dual_Lobe_Specular_Weight["Value"] > 0 and len(Dual_Lobe_Specular_Reflectivity["Texture"])>0:
                        #use Dual_Lobe_Specular_Reflectivity texture
                        self.set_tex_node(Dual_Lobe_Specular_Reflectivity["Texture"], "Dual Lobe Specular Reflectivity", mat_nodes, mat_links, shader_node, input_key)

                    elif Glossy_Layered_Weight["Value"] > 0 and len(Glossy_Layered_Weight["Texture"])>0:
                        #use Glossy_Layered_Weight texture
                        self.set_tex_node(Glossy_Layered_Weight["Texture"], "Glossy Layered Weight", mat_nodes, mat_links, shader_node, input_key)

                    elif Glossy_Layered_Weight["Value"] > 0 and len(Glossy_Reflectivity["Texture"])>0:
                        #use Glossy_Reflectivity texture
                        self.set_tex_node(Glossy_Reflectivity["Texture"], "Glossy Reflectivity", mat_nodes, mat_links, shader_node, input_key)

                    elif Dual_Lobe_Specular_Weight["Value"] > 0 and Glossy_Layered_Weight["Value"] == 0:
                        #use Dual_Lobe_Specular value
                        shader_node.inputs[input_key].default_value = Dual_Lobe_Specular_Reflectivity["Value"] * Dual_Lobe_Specular_Weight["Value"]

                    elif Dual_Lobe_Specular_Weight["Value"] == 0 and Glossy_Layered_Weight["Value"] > 0:
                        #use Glossy value
                        shader_node.inputs[input_key].default_value = Glossy_Reflectivity["Value"] * Glossy_Layered_Weight["Value"]

                    elif Dual_Lobe_Specular_Weight["Value"] > 0 and Glossy_Layered_Weight["Value"] > 0:
                        # merge value
                        spec_value = Dual_Lobe_Specular_Reflectivity["Value"] * Dual_Lobe_Specular_Weight["Value"] * (1-rated_r)
                        glossy_value = Glossy_Reflectivity["Value"] * Glossy_Layered_Weight["Value"] * (1-Glossy_Roughness["Value"])

                        # use the higher one
                        value = Glossy_Reflectivity["Value"] * Glossy_Layered_Weight["Value"]
                        if spec_value > glossy_value:
                            value = Dual_Lobe_Specular_Reflectivity["Value"] * Dual_Lobe_Specular_Weight["Value"]

                        # merge value
                        # value = (Dual_Lobe_Specular_Reflectivity["Value"] * Dual_Lobe_Specular_Weight["Value"] + Glossy_Reflectivity["Value"] * Glossy_Layered_Weight["Value"]) * 0.5

                        shader_node.inputs[input_key].default_value = value
                    else:
                        shader_node.inputs[input_key].default_value = 0

                elif input_key == "Roughness":
                    #need to merge Glossy and Dual Lobe Specular
                    Dual_Lobe_Specular_Weight = self.mat_property_dict.get("Dual Lobe Specular Weight")
                    Dual_Lobe_Specular_Reflectivity = self.mat_property_dict.get("Dual Lobe Specular Reflectivity")
                    Specular_Lobe_1_Roughness = self.mat_property_dict.get("Specular Lobe 1 Roughness")
                    Specular_Lobe_2_Roughness = self.mat_property_dict.get("Specular Lobe 2 Roughness")
                    Dual_Lobe_Specular_Ratio = self.mat_property_dict.get("Dual Lobe Specular Ratio")

                    Glossy_Layered_Weight = self.mat_property_dict.get("Glossy Layered Weight")
                    Glossy_Weight = self.mat_property_dict.get("Glossy Weight")

                    Glossy_Reflectivity = self.mat_property_dict.get("Glossy Reflectivity")
                    Glossy_Roughness = self.mat_property_dict.get("Glossy Roughness")

                    if (Glossy_Roughness is None):
                        shader_node.inputs[input_key].default_value = 0.5
                        continue

                    glossy_r = Glossy_Roughness["Value"]
                    if len(Glossy_Roughness["Texture"]) > 0:
                        self.set_tex_node(Glossy_Roughness["Texture"], "Glossy Roughness", mat_nodes, mat_links, shader_node, input_key)

                    if (Dual_Lobe_Specular_Weight is None or
                        Dual_Lobe_Specular_Reflectivity is None or
                        Specular_Lobe_1_Roughness is None or
                        Specular_Lobe_2_Roughness is None or
                        Dual_Lobe_Specular_Ratio is None or
                        Glossy_Layered_Weight is None or
                        Glossy_Weight is None or
                        Glossy_Reflectivity is None or
                        Glossy_Roughness is None):
                        continue

                    if Glossy_Weight["Value"] > 0:
                        Glossy_Layered_Weight = Glossy_Weight

                    # calculate dual lobe specular's final roughness
                    r1 = Specular_Lobe_1_Roughness["Value"]
                    r2 = Specular_Lobe_2_Roughness["Value"]
                    ratio = Dual_Lobe_Specular_Ratio["Value"]
                    # (1- rated_r) = ((1-r2) * (1-ratio) + (1-r1) * ratio)
                    rated_r = 1 - (((1-r2) * (1-ratio)) + ((1-r1) * ratio))
                    if rated_r > 1:
                        rated_r = 1
                    elif rated_r < 0:
                        rated_r = 0

                    # if there is a texture for weight or Reflectivity,
                    # since we can not add node between texture node and Princile shader node
                    # we merge it's value to roughness
                    if len(Glossy_Layered_Weight["Texture"]) > 0 :
                        # (1-new_value) = (1-value)*Glossy_Layered_Weight["Value"]
                        glossy_r = 1-((1-glossy_r)*Glossy_Layered_Weight["Value"])
                        if glossy_r > 1:
                            glossy_r = 1
                        elif glossy_r < 0:
                            glossy_r = 0

                    if len(Glossy_Reflectivity["Texture"]) > 0 :
                        # (1-new_value) = (1-value)*Glossy_Reflectivity["Value"]
                        glossy_r = 1-((1-glossy_r)*Glossy_Reflectivity["Value"])
                        if glossy_r > 1:
                            glossy_r = 1
                        elif glossy_r < 0:
                            glossy_r = 0


                    spec_r = rated_r
                    # if there is a texture for weight or Reflectivity,
                    # since we can not add node between texture node and Princile shader node
                    # we merge it's value to roughness
                    if len(Dual_Lobe_Specular_Weight["Texture"]) > 0 :
                        # (1-new_value) = (1-value)*Dual_Lobe_Specular_Weight["Value"]
                        spec_r = 1-((1-spec_r)*Dual_Lobe_Specular_Weight["Value"])
                        if spec_r > 1:
                            spec_r = 1
                        elif spec_r < 0:
                            spec_r = 0

                    if len(Dual_Lobe_Specular_Reflectivity["Texture"]) > 0 :
                        # (1-new_value) = (1-value)*Dual_Lobe_Specular_Reflectivity["Value"]
                        spec_r = 1-((1-spec_r)*Dual_Lobe_Specular_Reflectivity["Value"])
                        if spec_r > 1:
                            spec_r = 1
                        elif spec_r < 0:
                            spec_r = 0

                    if Dual_Lobe_Specular_Weight["Value"] > 0 and len(Specular_Lobe_1_Roughness["Texture"])>0:
                        #use Specular_Lobe_1_Roughness texture
                        self.set_tex_node(Specular_Lobe_1_Roughness["Texture"], "Specular Lobe 1 Roughness", mat_nodes, mat_links, shader_node, input_key)

                    elif Glossy_Layered_Weight["Value"] > 0 and len(Glossy_Roughness["Texture"])>0:
                        #use Glossy_Roughness texture
                        self.set_tex_node(Glossy_Roughness["Texture"], "Glossy Roughness", mat_nodes, mat_links, shader_node, input_key)

                    elif Dual_Lobe_Specular_Weight["Value"] > 0 and Glossy_Layered_Weight["Value"] == 0:
                        #use Dual_Lobe_Specular value
                        shader_node.inputs[input_key].default_value = spec_r

                    elif Dual_Lobe_Specular_Weight["Value"] == 0 and Glossy_Layered_Weight["Value"] > 0:
                        #use Glossy value
                        shader_node.inputs[input_key].default_value = glossy_r

                    elif Dual_Lobe_Specular_Weight["Value"] > 0 and Glossy_Layered_Weight["Value"] > 0:
                        # merge value
                        spec_value = Dual_Lobe_Specular_Reflectivity["Value"] * Dual_Lobe_Specular_Weight["Value"] * (1-rated_r)
                        glossy_value = Glossy_Reflectivity["Value"] * Glossy_Layered_Weight["Value"] * (1-Glossy_Roughness["Value"])

                        # use the higher one
                        value = glossy_r
                        if spec_value > glossy_value:
                            value = spec_r

                        # merge value
                        # value = (spec_r + glossy_r) * 0.5

                        shader_node.inputs[input_key].default_value = value
                    else:
                        shader_node.inputs[input_key].default_value = 0

                elif input_key == "Anisotropic":
                    value = 0
                    Glossy_Layered_Weight = self.mat_property_dict.get("Glossy Layered Weight")
                    Top_Coat_Weight = self.mat_property_dict.get("Top Coat Weight")

                    if (Glossy_Layered_Weight is None or Top_Coat_Weight is None):
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    if Glossy_Layered_Weight["Value"] > 0:
                        Glossy_Anisotropy = self.mat_property_dict.get("Glossy Anisotropy")
                        value = Glossy_Anisotropy["Value"]

                    elif Top_Coat_Weight["Value"] > 0 or len(Top_Coat_Weight["Texture"])>0:
                        Top_Coat_Anisotropy = self.mat_property_dict.get("Top Coat Anisotropy")
                        value = Top_Coat_Anisotropy["Value"]

                    shader_node.inputs[input_key].default_value = value


                elif input_key == "Anisotropic Rotation":
                    value = 0
                    Glossy_Layered_Weight = self.mat_property_dict.get("Glossy Layered Weight")
                    Top_Coat_Weight = self.mat_property_dict.get("Top Coat Weight")

                    if (Glossy_Layered_Weight is None or Top_Coat_Weight is None):
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    if Glossy_Layered_Weight["Value"] > 0:
                        Glossy_Anisotropy_Rotations = self.mat_property_dict.get("Glossy Anisotropy Rotations")
                        value = Glossy_Anisotropy_Rotations["Value"]

                    elif Top_Coat_Weight["Value"] > 0 or len(Top_Coat_Weight["Texture"])>0:
                        Top_Coat_Rotations = self.mat_property_dict.get("Top Coat Rotations")
                        value = Top_Coat_Rotations["Value"]

                    shader_node.inputs[input_key].default_value = value

                elif input_key == "Sheen":
                    # seems no such thing in daz mat
                    pass

                elif input_key == "Clearcoat":
                    Top_Coat_Weight = self.mat_property_dict.get("Top Coat Weight")
                    Reflectivity = self.mat_property_dict.get("Reflectivity")

                    if (Reflectivity is None or Top_Coat_Weight is None):
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    if len(Top_Coat_Weight["Texture"])>0:
                        #use Top_Coat_Weight texture
                        self.set_tex_node(Top_Coat_Weight["Texture"], "Top Coat Weight", mat_nodes, mat_links, shader_node, input_key)
                    elif Top_Coat_Weight["Value"] > 0 and len(Reflectivity["Texture"])>0:
                        #use Reflectivity texture
                        self.set_tex_node(Reflectivity["Texture"], "Reflectivity", mat_nodes, mat_links, shader_node, input_key)
                    else:
                        #set value
                        weight_value = Top_Coat_Weight["Value"]
                        reflect_value = Reflectivity["Value"]
                        shader_node.inputs[input_key].default_value = reflect_value * weight_value

                elif input_key == "Clearcoat Roughness":
                    self.set_value_or_tex("Top Coat Roughness", mat_nodes, mat_links, shader_node, input_key)

                elif input_key == "Clearcoat Normal":
                    # map to daz's Top Coat Bump, but nobody use it, so let's pass it
                    pass

                elif input_key == "IOR":
                    self.set_value_or_tex("Refraction Index", mat_nodes, mat_links, shader_node, input_key)

                elif input_key == "Transmission":
                    self.set_value_or_tex("Refraction Weight", mat_nodes, mat_links, shader_node, input_key)

                    # need to set alpha too
                    Refraction_Weight = self.mat_property_dict.get("Refraction Weight")

                    if (Refraction_Weight is None):
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    if Refraction_Weight["Value"] > 0:
                        if shader_node.inputs["Alpha"].default_value > 0.3:
                            shader_node.inputs["Alpha"].default_value = 0.3
                            mat.blend_method = 'HASHED'


                elif input_key == "Transmission Roughness":
                    self.set_value_or_tex("Refraction Roughness", mat_nodes, mat_links, shader_node, input_key)

                elif input_key == "Emission":
                    property = self.mat_property_dict.get("Emission Color")
                    if property is None:
                        continue

                    # do not handle color "#000000"
                    if property["Texture"] == "" and property["Value"] == "#000000":
                        pass
                    else:
                        self.set_color_or_tex("Emission Color", mat_nodes, mat_links, shader_node, input_key)

                elif input_key == "Emission Strength":
                    # map to Luminance, Luminance Units
                    Luminance = self.mat_property_dict.get("Luminance")
                    # Luminance Units: cd/m^2(0) kcd/m^2(1), cd/ft^2(2), cd/cm^2(3)
                    Luminance_Units = self.mat_property_dict.get("Luminance Units")

                    if (Luminance is None or Luminance_Units is None):
                        shader_node.inputs[input_key].default_value = 0
                        continue

                    luminance_value = Luminance["Value"]
                    if Luminance_Units == 1:
                        luminance_value = luminance_value * 1000
                    elif Luminance_Units == 2:
                        luminance_value = luminance_value * (1/0.3048) * (1/0.3048)
                    elif Luminance_Units == 3:
                        luminance_value = luminance_value * 100 * 100

                    shader_node.inputs[input_key].default_value = luminance_value/50000

                elif input_key == "Alpha":
                    # alpha texture should already be done, but sometime it put diffuse map to this one
                    # remove all links and old nodes
                    for link in shader_node.inputs[input_key].links:
                        from_node = link.from_node
                        mat_links.remove(link)
                        mat_nodes.remove(from_node)

                    # re-create alpha map, the one come already there could be wrong
                    self.set_value_or_tex("Cutout Opacity", mat_nodes, mat_links, shader_node, input_key)

                    # re-set value for transmission
                    Cutout_Opacity = self.mat_property_dict.get("Cutout Opacity")
                    Refraction_Weight = self.mat_property_dict.get("Refraction Weight")

                    if (Cutout_Opacity is None or Refraction_Weight is None):
                        shader_node.inputs[input_key].default_value = 1
                        continue

                    if Refraction_Weight["Value"] > 0 and Cutout_Opacity["Texture"] == "":
                        if shader_node.inputs[input_key].default_value > 0.3:
                            shader_node.inputs[input_key].default_value = 0.3
                            mat.blend_method = 'HASHED'

                    # need to set texture type to non-color
                    # for link in shader_node.inputs[input_key].links:
                    #     alpha_texture = link.from_node
                    #     if alpha_texture.bl_idname == "ShaderNodeTexImage":
                    #         Versions.to_color_space_non(alpha_texture)

                elif input_key == "Normal":
                    # check both normal and bump texture
                    Normal_Map = self.mat_property_dict.get("Normal Map")
                    Bump_Strength = self.mat_property_dict.get("Bump Strength")

                    if (Normal_Map is None or Bump_Strength is None):
                        continue

                    if len(Normal_Map["Texture"])>0:
                        #get Normal Map node:
                        self.set_tex_node(Normal_Map["Texture"], "Normal Map", mat_nodes, mat_links, normal_node, "Color")
                        normal_node.inputs["Strength"].default_value = Normal_Map["Value"]*0.5

                    if len(Bump_Strength["Texture"])>0:
                        if Global.bConvertBumpToNormal and Normal_Map["Texture"] == "":
                            # check if normal file is already exist
                            normal_path, normal_name, _ = BumpToNormal.getNormalPath(Bump_Strength["Texture"])

                            need_convert = True
                            # reuse normal map file
                            if Global.bReuseNormal:
                                if os.path.isfile(normal_path):
                                    need_convert = False

                            # only convert bump to normal if normal map is not existed in blender's image list
                            normalImage = bpy.data.images.get(normal_name)
                            if os.path.isfile(normal_path) and normalImage is not None:
                                need_convert = False
                            # convert bump map into normal map
                            # put it into the same folder of bump map
                            # use name as: bumFileName_normal
                            # use the same file type as bump map
                            # and get the normal file's path
                            # also make max image size to 2048
                            if need_convert:
                                print("convert bump to normal for mat: " + mat_name)
                                normal_path = BumpToNormal.bumpToNormalAuto(Bump_Strength["Texture"], 2048, False)

                            if normal_path != "":
                                # create node for this normal map
                                # get Normal Map node:
                                self.set_tex_node(normal_path, "Normal Map", mat_nodes, mat_links, normal_node, "Color")
                                normal_node.inputs["Strength"].default_value = Bump_Strength["Value"]*0.5
                            else:
                                print("convert bump to normal failed")

                        else:
                            # add Bump node
                            bump_node = mat_nodes.new("ShaderNodeBump")
                            self.set_tex_node(Bump_Strength["Texture"], "Bump", mat_nodes, mat_links, bump_node, "Height")
                            bump_node.inputs["Strength"].default_value = Bump_Strength["Value"]*0.1
                            bump_node.inputs["Distance"].default_value = 0.01

                            # remove link between normal map node and shader
                            for link in shader_node.inputs[input_key].links:
                                mat_links.remove(link)

                            # link bump node to shader
                            mat_links.new(bump_node.outputs[input_key], shader_node.inputs[input_key])
                            # link normal node to bump node
                            mat_links.new(normal_node.outputs[input_key], bump_node.inputs[input_key])


            # handle Tile
            Horizontal_Tiles = self.mat_property_dict.get("Horizontal Tiles")
            Vertical_Tiles = self.mat_property_dict.get("Vertical Tiles")

            if (Horizontal_Tiles is not None and Vertical_Tiles is not None):
                if Horizontal_Tiles["Value"] > 1 or Vertical_Tiles["Value"] > 1:
                    # create Mapping node and Coord node
                    mapping_node = mat_nodes.new("ShaderNodeMapping")
                    coord_node = mat_nodes.new("ShaderNodeTexCoord")
                    # set value
                    # x
                    mapping_node.inputs["Scale"].default_value[0] = Horizontal_Tiles["Value"]
                    # y
                    mapping_node.inputs["Scale"].default_value[1] = Vertical_Tiles["Value"]
                    # link them
                    mat_links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
                    # link mapping_node to all texture node
                    for node in mat_nodes:
                        if node.bl_idname == "ShaderNodeTexImage":
                            mat_links.new(mapping_node.outputs["Vector"], node.inputs["Vector"])


            # Set Alpha Modes
            Cutout_Opacity = self.mat_property_dict.get("Cutout Opacity")

            if (Cutout_Opacity is not None):
                if shader_node.inputs["Alpha"].default_value < 1 or len(Cutout_Opacity["Texture"])>0:
                    mat.blend_method = 'HASHED'

            if mat_nodes is not None:
                NodeArrange.toNodeArrange(mat_nodes)
