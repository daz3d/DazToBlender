import os
import sys
import math
import json
import bpy

from . import Util
from . import Versions
from . import DataBase
from . import Global

sys.path.append(os.path.dirname(__file__))


class DtbShapeKeys:
    root = Global.getRootPath()
    flg_rigify = False

    var_name_index = 0
    var_name_range = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, flg_rigify, dtu):
        self.flg_rigify = flg_rigify
        self.bone_limits = dtu.get_bone_limits_dict()
        self.morph_links_dict = dtu.get_morph_links_dict()

    def make_drivers(self):
        body_obj = Global.getBody()
        print(body_obj)
        for dobj in Util.myccobjs():
            if Global.isRiggedObject(dobj):
                self.make_driver(dobj, body_obj)

    def get_transform_type(self, morph_link):
        bone_name = morph_link["Bone"]
        property_name = morph_link["Property"]

        bone_limits = self.bone_limits
        bone_order = bone_limits[bone_name][1]

        # Conversions for corresponding rotation properties betweem Daz Studio
        #   and Blender.
        if bone_order == "XYZ":
            if "XRotate" in property_name:
                return "ROT_Y"
            elif "YRotate" in property_name:
                return "ROT_Z"
            elif "ZRotate" in property_name:
                return "ROT_X"
        elif bone_order == "XZY":
            if "XRotate" in property_name:
                return "ROT_Y"
            elif "YRotate" in property_name:
                return "ROT_X"
            elif "ZRotate" in property_name:
                return "ROT_Z"
        elif bone_order == "YZX":
            if "XRotate" in property_name:
                return "ROT_X"
            elif "YRotate" in property_name:
                return "ROT_Y"
            elif "ZRotate" in property_name:
                return "ROT_Z"
        elif bone_order == "ZXY":
            if "XRotate" in property_name:
                return "ROT_Y"
            elif "YRotate" in property_name:
                return "ROT_Z"
            elif "ZRotate" in property_name:
                return "ROT_X"
        elif bone_order == "ZYX":
            if "XRotate" in property_name:
                return "ROT_X"
            elif "YRotate" in property_name:
                return "ROT_Z"
            elif "ZRotate" in property_name:
                return "ROT_Y"

        return "LOC_X"

    def get_var_correction(self, var_name, morph_link):
        # Correction factor for the cases where the property value is sign is
        #   reversed between Daz Studio and Blender
        correction_factor = 1

        bone_name = morph_link["Bone"]
        property_name = morph_link["Property"]

        # Return when controller is not a Bone
        if bone_name == "None":
            return var_name

        bone_limits = self.bone_limits
        bone_order = bone_limits[bone_name][1]

        prefix = bone_name[0:1]
        post_prefix = bone_name[1:2]
        is_right = False
        if prefix == "r" and post_prefix.isupper():
            is_right = True
        is_down = False
        if bone_name in [
            "hip",
            "pelvis",
            "lThighBend",
            "rThighBend",
            "lThighTwist",
            "rThighTwist",
            "lShin",
            "rShin",
        ]:
            is_down = True

        if bone_order == "XYZ":
            if "XRotate" in property_name:
                correction_factor = -1
            elif "YRotate" in property_name and is_right:
                correction_factor = -1
            elif "ZRotate" in property_name and is_right:
                correction_factor = 1
        elif bone_order == "XZY":
            if "XRotate" in property_name:
                correction_factor = -1
            elif "YRotate" in property_name and is_right:
                correction_factor = -1
            elif "ZRotate" in property_name and is_right:
                correction_factor = -1
        elif bone_order == "YZX":
            if "XRotate" in property_name:
                correction_factor = 1
            elif "YRotate" in property_name and is_down:
                correction_factor = -1
            elif "ZRotate" in property_name and is_down:
                correction_factor = -1
        elif bone_order == "ZXY":
            if "XRotate" in property_name:
                correction_factor = 1
            elif "YRotate" in property_name:
                correction_factor = 1
            elif "ZRotate" in property_name:
                correction_factor = 1
        elif bone_order == "ZYX":
            if "XRotate" in property_name:
                correction_factor = -1
            elif "YRotate" in property_name:
                correction_factor = 1
            elif "ZRotate" in property_name:
                correction_factor = 1

        # Include radians to degree convesion factor
        correction_factor = round(math.degrees(correction_factor), 2)

        var_name = "(" + var_name + "*" + str(correction_factor) + ")"
        return var_name

    def get_target_expression(self, var_name, morph_link, driver):
        """Currently does not support Raw Value/Current Value"""
        link_type = morph_link["Type"]
        scalar = str(round(morph_link["Scalar"], 2))
        addend = str(morph_link["Addend"])
        var_name = self.get_var_correction(var_name, morph_link)

        if link_type == 0:
            # ERCDeltaAdd
            delta_add = str(float(scalar) + float(addend))
            return "(" + var_name + "*" + delta_add + ")"
        elif link_type == 1:
            # ERCDivideInto
            driver.use_self = True
            return "(" + var_name + "/self.value+" + addend + ")"
        elif link_type == 2:
            # ERCDivideBy
            driver.use_self = True
            return "(" + "self.value/" + var_name + "+" + addend + ")"
        elif link_type == 3:
            # ERCMultiply
            return "(" + var_name + "+" + addend + ")"
        elif link_type == 4:
            # ERCSubtract
            driver.use_self = True
            return "(" + "self.value-" + var_name + "+" + addend + ")"
        elif link_type == 5:
            # ERCAdd
            driver.use_self = True
            return "(" + "self.value+" + var_name + "+" + addend + ")"
        elif link_type == 6:
            # ERCKeyed

            keyed = morph_link["Keys"]

            # Currently Skip the 3rd Key if Key 0 has two
            for i in range(len(keyed)):
                key = list(keyed)[i]
                if keyed[key]["Value"] == 0:
                    if len(keyed) > (i + 1):
                        next_key = list(keyed)[i + 1]
                        if (
                            (len(keyed) != 2)
                            and (keyed[next_key]["Value"] == 0)
                            and (keyed[next_key]["Rotate"] == 0)
                        ):
                            continue
                    key_0 = str(keyed[key]["Rotate"])
                if keyed[key]["Value"] == 1:
                    key_1 = str(keyed[key]["Rotate"])

            # Temporily Run lForearmBend as absolute as incorrect roll is applied.
            bone_name = morph_link["Bone"]
            if bone_name == "lForearmBend":
                key_0 = str(abs(float(key_0)))
                key_1 = str(abs(float(key_1)))

            dist = str((float(key_1) - float(key_0)))
            normalized_dist = str((1 - 0))

            return (
                "erc_keyed("
                + var_name
                + ","
                + key_0
                + ","
                + key_1
                + ","
                + normalized_dist
                + ","
                + dist
                + ")"
            )
        return var_name

    def get_morph_link_control_type(self, morph_link):
        if morph_link["Bone"] == "None":
            return "CONTROL_BY_MORPH"
        else:
            return "CONTROL_BY_BONE"

    def make_bone_var(self, morph_link, driver):
        # Add Variable
        link_var = driver.variables.new()
        link_var.name = self.get_next_var_name()
        link_var.type = "TRANSFORMS"

        # Set variable target
        target = link_var.targets[0]
        target.id = Global.getAmtr()
        target.bone_target = morph_link["Bone"]
        target.transform_space = "LOCAL_SPACE"
        target.transform_type = self.get_transform_type(morph_link)

        return link_var

    def make_morph_var(self, morph_link, driver, shape_key, mesh_name):
        # Add variable
        link_var = driver.variables.new()
        link_var.name = self.get_next_var_name()
        link_var.type = "SINGLE_PROP"

        # Set variable target
        target = link_var.targets[0]
        target.id_type = "KEY"
        target.id = shape_key
        block_id = mesh_name + "__" + morph_link["Property"]
        rna_data_path = 'key_blocks["' + block_id + '"].value'
        target.data_path = rna_data_path

        return link_var

    def property_in_shape_keys(self, morph_link, shape_key_blocks, mesh_name):
        property_name = morph_link["Property"]
        is_found = False
        for key_block in shape_key_blocks:
            if property_name == key_block.name[len(mesh_name + "__") :]:
                is_found = True
                break
        return is_found

    def load_morph_link_list(self):
        # Read all the morph links from the DTU
        return self.morph_links_dict

    def add_main_control(
        self, key_block, mesh_obj, morph_label, shape_key_min, shape_key_max, driver
    ):
        # Skip Basis shape key
        if key_block.name == "Basis":
            return

        # Create a custom property and set limits
        mesh_obj[morph_label] = 0.0
        rna_ui = mesh_obj.get("_RNA_UI")
        if rna_ui is None:
            mesh_obj["_RNA_UI"] = {}
            rna_ui = mesh_obj.get("_RNA_UI")
        rna_ui[morph_label] = {
            "min": shape_key_min,
            "max": shape_key_max,
            "soft_min": shape_key_min,
            "soft_max": shape_key_max,
        }

        # Add variable
        link_var = driver.variables.new()
        link_var.name = self.get_next_var_name()
        link_var.type = "SINGLE_PROP"

        # Set variable target
        target = link_var.targets[0]
        target.id_type = "OBJECT"
        target.id = mesh_obj
        rna_data_path = '["' + morph_label + '"]'
        target.data_path = rna_data_path

        # Set the Limits for Shapekey
        key_block.slider_min = shape_key_min
        key_block.slider_max = shape_key_max

        # Add to the Global list, so it can be used in the Daz To Blender Panel
        # Global.load_shape_key_custom_props(mesh_obj.name, morph_label)

        return "(" + link_var.name + "*1)"

    def add_custom_shape_key_prop(
        self, key_block, mesh_obj, morph_label, shape_key_min, shape_key_max
    ):
        # Skip Basis shape key
        if key_block.name == "Basis":
            return

        # Create a custom property and set limits
        mesh_obj[morph_label] = 0.0
        rna_ui = mesh_obj.get("_RNA_UI")
        if rna_ui is None:
            mesh_obj["_RNA_UI"] = {}
            rna_ui = mesh_obj.get("_RNA_UI")
        rna_ui[morph_label] = {
            "min": shape_key_min,
            "max": shape_key_max,
            "soft_min": shape_key_min,
            "soft_max": shape_key_max,
        }

        # Add driver
        driver = key_block.driver_add("value").driver
        driver.type = "SUM"

        # Add variable
        link_var = driver.variables.new()
        link_var.name = "var"
        link_var.type = "SINGLE_PROP"

        # Set variable target
        target = link_var.targets[0]
        target.id_type = "OBJECT"
        target.id = mesh_obj
        rna_data_path = '["' + morph_label + '"]'
        target.data_path = rna_data_path

        # Set the Limits for Shapekey
        key_block.slider_min = shape_key_min
        key_block.slider_max = shape_key_max

        # Add to the Global list, so it can be used in the Daz To Blender Panel
        # Global.load_shape_key_custom_props(mesh_obj.name, morph_label)

    def get_control_shape_key(self, key_name, body_mesh_name, body_key_blocks):
        # Get the body_block that matches the given key_name
        for body_block in body_key_blocks:
            body_key_name = body_block.name[len(body_mesh_name + "__") :]
            if key_name == body_key_name:
                return body_key_name
        return None

    def reset_var_names(self):
        self.var_name_index = 0

    def get_next_var_name(self):
        range_len = len(self.var_name_range)
        next_index = self.var_name_index % range_len
        suffix_index = (int)(self.var_name_index / range_len)
        var_name = self.var_name_range[next_index]
        if suffix_index > 0:
            var_name = var_name + str(suffix_index)
        self.var_name_index += 1
        return var_name

    # Add the next expression based on the type of ERC_Link it is
    def combine_target_expression(self, exp, morph_links, link_index):
        link_type = morph_links[link_index]["Type"]
        next_index = link_index + 1
        first_stage = [0, 4, 5, 6]
        second_stage = [1, 2, 3]

        if len(morph_links) - 1 >= next_index and link_type in first_stage:
            next_link_type = morph_links[next_index]["Type"]

            if link_index == 0:
                if next_link_type in first_stage:
                    return "(" + exp + "+"
                elif next_link_type in second_stage:
                    return exp
                else:
                    return exp + "+"

            elif link_index > 0:
                if next_link_type in first_stage:
                    return exp + "+"
                elif (next_link_type in second_stage) and (next_index != 1):
                    return exp + ")"

        elif (link_type in second_stage) and (link_index > 0):
            return "*" + exp
        elif (link_type in second_stage) and (link_index == 0):
            return "0 *" + exp
        elif (next_index == len(morph_links)) and (len(morph_links) > 1):
            return exp + ")"

        else:
            return exp + "+"

    def remove_missing_links(self, morph_links, body_mesh_obj):
        mesh_name = body_mesh_obj.data.name
        shape_key = body_mesh_obj.data.shape_keys
        if shape_key is None:
            return
        shape_key_blocks = shape_key.key_blocks
        updated_morph_links = []
        for link in morph_links:
            if shape_key_blocks.get(mesh_name + "__" + link["Property"]):
                updated_morph_links.append(link)
            elif link["Bone"] != "None":
                updated_morph_links.append(link)
        return updated_morph_links

    def make_body_mesh_drivers(self, body_mesh_obj):
        mesh_name = body_mesh_obj.data.name
        if len(mesh_name.split(".")) == 2:
            mesh_name = mesh_name.split(".")[0]

        shape_key = body_mesh_obj.data.shape_keys
        if shape_key is None:
            return

        # Create drivers for shape key blocks on the body mesh
        morph_links_list = self.load_morph_link_list()
        shape_key_blocks = shape_key.key_blocks
        for key_block in shape_key_blocks:
            key_name = key_block.name[len(mesh_name + "__") :]

            # Continue for Basis key block or not found in the morph links list
            if not key_name or key_name not in morph_links_list:
                continue

            morph_label = morph_links_list[key_name]["Label"]
            morph_links = morph_links_list[key_name]["Links"]
            morph_hidden = morph_links_list[key_name]["isHidden"]

            shape_key_min = float(morph_links_list[key_name]["Minimum"])
            shape_key_max = float(morph_links_list[key_name]["Maximum"])

            # If morph_links is empty add a custom property
            if not morph_links:
                # Create custom property for this shape key and drive it
                self.add_custom_shape_key_prop(
                    key_block, body_mesh_obj, morph_label, shape_key_min, shape_key_max
                )
                continue

            # Add driver
            driver = key_block.driver_add("value").driver
            driver.type = "SCRIPTED"

            expression = ""
            var_count = 0
            self.reset_var_names()
            updated_morph_links = self.remove_missing_links(morph_links, body_mesh_obj)
            for link_index, morph_link in enumerate(updated_morph_links):
                # Determine if the controller is a Bone or other shape key
                control_type = self.get_morph_link_control_type(morph_link)
                if control_type == "CONTROL_BY_NONE":
                    continue
                if control_type == "CONTROL_BY_MORPH":
                    is_found = self.property_in_shape_keys(
                        morph_link, shape_key_blocks, mesh_name
                    )
                    if not is_found:
                        # If the controller morph is not in listed shape keys
                        continue
                    var = self.make_morph_var(morph_link, driver, shape_key, mesh_name)
                    var_count += 1
                elif control_type == "CONTROL_BY_BONE":
                    var = self.make_bone_var(morph_link, driver)
                    var_count += 1

                exp = self.get_target_expression(var.name, morph_link, driver)
                if len(expression + exp + "+") >= 255:
                    # Driver script expression max lenght is 255
                    # break when the limit is reached to avoid errors
                    break

                expression += self.combine_target_expression(
                    exp, updated_morph_links, link_index
                )

            # Trim the extra chars
            if expression.endswith("+"):
                expression = expression[:-1]
            if expression.startswith("*"):
                expression = expression[1:]
            if expression.endswith("))") and var_count == 1:
                expression = expression[:-1]

            if not morph_hidden:
                expression = "(" + expression + ") +"
                expression += self.add_main_control(
                    key_block,
                    body_mesh_obj,
                    morph_label,
                    shape_key_min,
                    shape_key_max,
                    driver,
                )

            # Delete the driver and continue if there are no variables
            if var_count == 0:
                key_block.driver_remove("value")
                # Create custom property if no drivers and drive it
                self.add_custom_shape_key_prop(
                    key_block, body_mesh_obj, morph_label, shape_key_min, shape_key_max
                )
                continue

            driver.expression = expression

            # Set the Limits for Shapekey
            key_block.slider_min = shape_key_min
            key_block.slider_max = shape_key_max


    def make_other_mesh_drivers(self, other_mesh_obj, body_mesh_obj):
        other_mesh_name_shape = other_mesh_obj.name
        other_mesh_name = other_mesh_obj.data.name
        body_mesh_name = body_mesh_obj.data.name

        other_shape_key = other_mesh_obj.data.shape_keys
        body_shape_key = body_mesh_obj.data.shape_keys
        if other_shape_key is None or body_shape_key is None:
            return

        other_key_blocks = other_shape_key.key_blocks
        body_key_blocks = body_shape_key.key_blocks

        # Get morph_links_list for adding custom properties
        morph_links_list = self.load_morph_link_list()

        # Add drivers to the key blocks that have same name as in body mesh
        # Driver copies the value of the controller key block
        for other_block in other_key_blocks:
            other_key_name = other_block.name[len(other_mesh_name + "__") :]
            if not other_key_name:
                continue

            # Continue if other_key_name not found in morph_links_list
            if other_key_name not in morph_links_list:
                other_mesh_obj.shape_key_remove(other_block)
                continue

            morph_label = morph_links_list[other_key_name]["Label"]
            morph_links = morph_links_list[other_key_name]["Links"]
            shape_key_min = float(morph_links_list[other_key_name]["Minimum"])
            shape_key_max = float(morph_links_list[other_key_name]["Maximum"])
            controled_meshes = morph_links_list[other_key_name]["Controlled Meshes"]
            if bpy.context.window_manager.morph_optimize:
                if other_mesh_name_shape not in controled_meshes:
                    other_mesh_obj.shape_key_remove(other_block)
                    continue

            body_key_name = self.get_control_shape_key(
                other_key_name, body_mesh_name, body_key_blocks
            )
            if body_key_name:
                # Add driver targetting the body shape key that controls this
                driver = other_block.driver_add("value").driver
                driver.type = "SUM"

                # Add variable
                link_var = driver.variables.new()
                link_var.name = "var"
                link_var.type = "SINGLE_PROP"

                # Set variable target
                target = link_var.targets[0]
                target.id_type = "KEY"
                target.id = body_shape_key
                block_id = body_mesh_name + "__" + body_key_name
                rna_data_path = 'key_blocks["' + block_id + '"].value'
                target.data_path = rna_data_path
            else:
                # If morph_links is empty add a custom property
                if not morph_links:
                    # Create custom property for this shape key and drive it
                    self.add_custom_shape_key_prop(
                        other_block,
                        other_mesh_obj,
                        morph_label,
                        shape_key_min,
                        shape_key_max,
                    )
                    continue

    def make_driver(self, other_mesh_obj, body_mesh_obj):
        if other_mesh_obj == body_mesh_obj:
            # Create drivers on the body mesh shape keys
            self.make_body_mesh_drivers(body_mesh_obj)
        else:
            # Create drivers on the other (non body) mesh shape keys
            self.make_other_mesh_drivers(other_mesh_obj, body_mesh_obj)

    def delete001_sk(self):
        Global.setOpsMode("OBJECT")
        obj = Global.getBody()
        Versions.select(obj, True)
        Versions.active_object(obj)
        aobj = bpy.context.active_object
        sp = aobj.data.shape_keys
        if sp is not None:
            max = len(sp.key_blocks)
            i = 0
            for notouch in range(max):
                aobj.active_shape_key_index = i
                if aobj.active_shape_key.name.endswith(".001"):
                    bpy.ops.object.shape_key_remove(all=False)
                    max = max - 1
                else:
                    i = i + 1

    def get_rigify_bone_name(self, bname):
        rtn = ""
        db = DataBase.DB()
        for trf in db.toRigify:
            if trf[0] < 2:
                continue
            ops_trf = "r" + trf[1][1:]
            bool_ops = ops_trf == bname
            if trf[1] == bname or bool_ops:
                rtn = trf[2]
                if bool_ops:
                    rtn = rtn.replace(".L", ".R")
                break
        if rtn == "" and "Toe" in bname and len(bname) > 4:
            rtn = bname
        elif rtn.startswith("f_") or rtn.startswith("thumb."):
            pass
        elif ("DEF-" + rtn) in Global.getRgfyBones():
            rtn = "DEF-" + rtn
        swap = [["DEF-shoulder.", "shoulder."], ["DEF-pelvis.L", "tweak_spine"]]
        for sp in swap:
            if sp[0] in rtn:
                rtn = rtn.replace(sp[0], sp[1])
        return rtn

    def makeOneDriver(self, db):
        cur = db.tbl_mdrive
        aobj = Global.getBody()
        if Global.getIsG3():
            cur.extend(db.tbl_mdrive_g3)
        for row in cur:
            sk_name = aobj.active_shape_key.name
            if row[0] in sk_name and sk_name.endswith(".001") == False:
                dvr = aobj.data.shape_keys.key_blocks[sk_name].driver_add("value")
                dvr.driver.type = "SCRIPTED"
                var = dvr.driver.variables.new()
                Versions.set_debug_info(dvr)
                self.setDriverVariables(var, "val", Global.getAmtr(), row[1], row[2])
                exp = row[3]
                dvr.driver.expression = exp
                break

    def makeDrive(self, dobj, db):
        mesh_name = dobj.data.name
        Versions.active_object(dobj)
        aobj = bpy.context.active_object
        if bpy.data.meshes[mesh_name].shape_keys is None:
            return
        ridx = 0
        cur = db.tbl_mdrive
        if Global.getIsG3():
            cur.extend(db.tbl_mdrive_g3)
        while ridx < len(cur):
            max = len(bpy.data.meshes[mesh_name].shape_keys.key_blocks)
            row = cur[ridx]
            for i in range(max):
                if aobj is None:
                    continue
                aobj.active_shape_key_index = i
                if aobj.active_shape_key is None:
                    continue
                sk_name = aobj.active_shape_key.name
                if row[0] in sk_name and sk_name.endswith(".001") == False:
                    dvr = aobj.data.shape_keys.key_blocks[sk_name].driver_add("value")
                    dvr.driver.type = "SCRIPTED"
                    var = dvr.driver.variables.new()
                    Versions.set_debug_info(dvr)
                    if self.flg_rigify:
                        target_bone = self.get_rigify_bone_name(row[1])
                        xyz = self.toRgfyXyz(row[2], target_bone)
                        self.setDriverVariables(
                            var, "val", Global.getRgfy(), target_bone, xyz
                        )
                        exp = self.getRgfyExp(row[3], target_bone, row[0])
                        if ridx < len(cur) - 1 and cur[ridx + 1][0] in sk_name:
                            row2 = cur[ridx + 1]
                            target_bone2 = self.get_rigify_bone_name(row2[1])
                            var2 = dvr.driver.variables.new()
                            xyz2 = self.toRgfyXyz(row2[2], target_bone2)
                            self.setDriverVariables(
                                var2, "val2", Global.getRgfy(), target_bone2, xyz2
                            )
                            exp2 = self.getRgfyExp(row2[3], target_bone2, row2[0])
                            exp += "+" + exp2
                            ridx = ridx + 1
                        dvr.driver.expression = exp
                    break
            ridx = ridx + 1

    def toRgfyXyz(self, xyz, bname):
        zy_switch = ["chest", "hips"]
        for zy in zy_switch:
            if bname == zy:
                if xyz == 1:
                    return 2
                elif xyz == 2:
                    return 1
        return xyz

    def getRgfyExp(self, exp, target_bone, sk_name):
        exp = exp.replace(" ", "")
        exp_kind = [
            ["upper_arm", "", ""],
            ["forearm", "", ""],
            ["hand", "", ""],
            ["hip", "", ""],
            ["tweak_spine", "", ""],
            ["toe", "", ""],
            ["chest", "", "Side"],
            ["DEF-spine", "spine", "pJCMAbdomenFwd_35"],
        ]
        for ek in exp_kind:
            if (
                (ek[0] in target_bone)
                and target_bone.endswith(ek[1])
                and (ek[2] in sk_name)
            ):
                exp = self.invert_exp(exp)
                break
        return exp

    def setDriverVariables(self, var, varname, target_id, bone_target, xyz):
        var.name = varname
        var.type = "TRANSFORMS"
        target = var.targets[0]
        target.id = target_id
        target.bone_target = bone_target
        target.transform_space = "LOCAL_SPACE"
        if xyz == 0:
            target.transform_type = "ROT_X"
        elif xyz == 1:
            target.transform_type = "ROT_Y"
        elif xyz == 2:
            target.transform_type = "ROT_Z"

    def invert_exp(self, exp):
        flg_ToMs = ("val-" in exp) or ("*-" in exp) == False  # In case of Plus
        if flg_ToMs:
            if "val-" in exp:
                exp = exp.replace("val-", "val+")
            if ("*-" in exp) == False:
                exp = exp.replace("*", "*-")
        else:
            if "val+" in exp:
                exp = exp.replace("val+", "val-")
            if "*-" in exp:
                exp = exp.replace("*-", "*")
        return exp

    def toHeadMorphMs(self, db):
        dobj = Global.getBody()
        Versions.select(dobj, True)
        cur = db.tbl_facems
        Versions.active_object(dobj)
        for mesh in bpy.data.meshes:
            if mesh.name == dobj.data.name:
                if mesh.shape_keys is None:
                    continue
                for kb in mesh.shape_keys.key_blocks:
                    for row in cur:
                        if kb.name.lower() == row.lower():
                            kb.slider_min = -1

    def add_sk(self, dobj):
        Versions.select(dobj, True)
        Versions.active_object(dobj)
        for mesh in bpy.data.meshes:
            if mesh.name == dobj.data.name:
                bpy.ops.object.shape_key_add(from_mix=False)
                kblen = len(mesh.shape_keys.key_blocks)
                bpy.context.active_object.active_shape_key_index = kblen - 1

    def delete_old_vgroup(self, db):
        dobj = Global.getBody()
        for fv in db.fvgroup:
            for vg in dobj.vertex_groups:
                if vg.name == fv:
                    if vg.name in dobj.vertex_groups:
                        dobj.vertex_groups.remove(vg)
                        break

    def swap_fvgroup(self, db, objs):
        for obj in objs:
            dobj = bpy.data.objects[obj]
            for z in range(2):
                for _fs in db.fvgroup_swap:
                    fs = [_fs[0], _fs[1]]
                    if z == 1:
                        if fs[1].startswith("l") and fs[1].startswith("lower") == False:
                            fs[1] = "r" + fs[1][1:]
                            fs[0] = fs[0].replace(".L", ".R")
                        else:
                            continue
                    vgs = dobj.vertex_groups
                    for vg in vgs:
                        if vg.name == fs[1]:
                            vg.name = fs[0]

    def delete_oneobj_sk_from_command(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        aobj = Versions.get_active_object()
        if aobj is None:
            return
        self.delete_oneobj_sk(0, 100, 0, aobj, wm)
        wm.progress_end()

    def delete_oneobj_sk(self, min, onesa, oidx, obj, wm):
        v = min + onesa * oidx
        wm.progress_update(int(v))
        Versions.active_object(obj)
        if obj.data.shape_keys is None:
            return
        kbs = obj.data.shape_keys.key_blocks
        root_kb = [d.co[0] for didx, d in enumerate(kbs[0].data) if didx % 4 == 0]
        max = len(kbs)
        z0_same_idx_ary = []
        dels = []
        for z in range(2):
            if z == 0:
                decisa = onesa / (2.0 * max)
                old_dv = v
                for i in range(1, max):
                    dv = int(v + decisa * i)
                    if old_dv != dv:
                        wm.progress_update(dv)
                    kb = kbs[i]
                    if root_kb == [
                        d.co[0] for didx, d in enumerate(kb.data) if didx % 4 == 0
                    ]:
                        z0_same_idx_ary.append(i)
                    old_dv = dv
            else:
                if z0_same_idx_ary == []:
                    break
                decisa = onesa / (2.0 * len(z0_same_idx_ary))
                old_dv = v
                root_kb_yz = [
                    [d.co[1], d.co[2]]
                    for didx, d in enumerate(kbs[0].data)
                    if didx % 4 == 0
                ]
                for i in z0_same_idx_ary:
                    dv = int(v + onesa / 2.0 + decisa * i)
                    if old_dv != dv:
                        wm.progress_update(dv)
                    kb = kbs[i]
                    if root_kb_yz == [
                        [d.co[1], d.co[2]]
                        for didx, d in enumerate(kb.data)
                        if didx % 4 == 0
                    ]:
                        dels.append(i)
                    old_dv = dv
            dels.sort(reverse=True)
            for d in dels:
                Versions.get_active_object().active_shape_key_index = d
                bpy.ops.object.shape_key_remove(all=False)

    def delete_all_extra_sk(self, min, max, wm):
        objs = []
        for obj in Util.myccobjs():
            if obj.type == "MESH":
                objs.append(obj)
        allsa = max - min
        onesa = allsa / len(objs)
        for oidx, obj in enumerate(objs):
            self.delete_oneobj_sk(min, onesa, oidx, obj, wm)
