import os
import re
import bpy

from . import Global


class MatDct:
    dct = {}

    mat_types__bpart = [
        ["face", "1"],
        ["head", "2"],
        ["ears", "1"],
        ["eyesocket", "1"],
        ["lips", "1"],
        ["torso", "2"],
        ["body", "3"],
        ["legs", "3"],
        ["toenails", "3"],
        ["arms", "4"],
        ["fingernails", "4"],
        ["mouth", "5"],
        ["teeth", "5"],
        ["eyelashes", "0"],
        ["irises", "6"],  # I
        ["sclera", "6"],  # II
        ["pupils", "6"],  # III
        ["irises", "7"],  # I
        ["sclera", "7"],  # II
        ["pupils", "7"],  # III
        ["cornea", "8"],
        ["eyemoisture", "8"],
        ["genitaria", "9"],
        ["anus", "9"],
        ["rectum", "9"],
        ["labia", "9"],
        ["clitoris", "9"],
        ["vagina", "9"],
        ["glans", "9"],
        ["shaft", "9"],
        ["testicles", "9"],
    ]
    mat_props__imgs = [
        ["diff", "diff", "d"],
        ["diff", "MapD", "d"],
        ["Albedo", "mapd", "d"],
        ["Base", "TX", "d"],
        ["base_color", "basecolor", "d"],
        ["Base Color", "BaseColor", "d"],
        ["bump", "bump", "b"],
        ["bump", "MapB", "b"],
        ["bump", "mapb", "b"],
        ["bump", "mapb01", "b"],
        ["bump", "Height", "b"],
        ["bump", "bmp.", "b"],
        ["bump", "disp.", "b"],
        ["bump", "MapB01", "b"],
        ["specu", "specc.", "s"],
        ["specu", "spec.", "s"],
        ["specu", "MapS", "s"],
        ["specu", "Maps", "s"],
        ["sss", "sss", "z"],
        ["normal", "nm", "n"],
        ["rough", "rough", "r"],
        ["trans", "tr", "t"],
        ["eyelashes", "eyelashes", "t"],
        ["diff", "D", "d"],
        ["bump", "B", "b"],
        ["specu", "S", "s"],
        ["sss", "sss", "z"],
        ["normal", "NM", "n"],
        ["normal", "nml.", "n"],
        ["normal", "Nm", "n"],
        ["rough", "R", "r"],
        ["trans", "TR", "t"],
        ["trans", "Tr", "t"],
        ["Alpha", "alpha", "t"]
    ]

    def get_dct(self):
        return self.dct

    # For all the material slots with 'Principled BSDF' and Base Color as
    # a Texture that match with the hardcoded list 'bpart'
    # Example: (key, value) = (3d, <texture path>)
    def make_dct_from_body(self):
        tex_dir_path = ""
        for mat_slot in Global.getBody().material_slots:
            mat = bpy.data.materials.get(mat_slot.name)
            if mat is not None:
                for mat_node in mat.node_tree.nodes:
                    if mat_node.name == "Principled BSDF":
                        base_color = mat_node.inputs.get("Base Color")
                        if base_color is not None:
                            # link_limit of base_color is 1
                            base_color_links = base_color.links
                            if len(base_color_links) == 0:
                                break
                            source_node = base_color_links[0].from_node
                            if source_node.name.startswith("Image Texture"):
                                tex_path = source_node.image.filepath
                                mat_slot_name = mat_slot.name

                                # clean material name from suffexes
                                suffix_index = mat_slot_name.rfind(".00")
                                if suffix_index > 2:
                                    mat_slot_name = mat_slot_name[
                                        0: suffix_index
                                    ]

                                for mat_name_num in self.mat_types__bpart:
                                    if mat_name_num[0].lower() in mat_slot_name.lower():
                                        mat_num = mat_name_num[1]
                                        if mat_num == '6':
                                            mat_num = '7'

                                        key = mat_num + 'd'
                                        self.add_to_dct(key, tex_path)

                                        if int(mat_num) < 5 and tex_dir_path == "":
                                            tex_dir_path = os.path.dirname(
                                                tex_path
                                            )
        if tex_dir_path != "":
            self.search_directory(tex_dir_path)

    def make_dct_from_directory(self, path):
        self.dct = {}
        self.search_directory(path)

    # Read mtl file from the ObjExporter and create a dictionary
    def make_dct_from_mtl(self):
        self.dct = {}
        self.make_dct_from_body()

        tex_dir_path = ""
        inter_dir_path = Global.getHomeTown()
        if os.path.exists(inter_dir_path) == False:
            mtl_path = Global.getRootPath() + "DTB.mtl"
        else:
            mtl_path = inter_dir_path + "/FIG.mtl"

        # return if the calculated path to the mtl file doesn't exist
        if os.path.exists(mtl_path) == False:
            return

        mtl_lines = []
        with open(mtl_path, errors='ignore', encoding='utf-8') as mtl_file:
            lines = mtl_file.readlines()
        for line in lines:
            line = line.strip()
            line = line.replace('"', '')
            if len(line) > 2:
                mtl_lines.append(line.lower())
        directory_memo = ""
        for i in range(len(mtl_lines)):
            mtl_line = mtl_lines[i]
            if mtl_line.startswith("newmtl"):
                key = ""
                tr_key = ""
                name_key = ""
                prefix_index = len("newmtl ")
                newmtl_name = mtl_line[prefix_index:]
                for mat_name_num in self.mat_types__bpart:
                    mat_name = mat_name_num[0].lower()
                    pref_ind = len("newmtl ")
                    case1 = mat_name in newmtl_name
                    case2 = (mat_name + "_") in newmtl_name
                    case3 = ("_" + mat_name) in newmtl_name
                    if case1 or case2 or case3:
                        if name_key == '':
                            name_key = newmtl_name
                        mat_num = mat_name_num[1]
                        if mat_num == '6':
                            mat_num = '7'
                        if key == '':
                            key = mat_num + "d"
                        if tr_key == '':
                            tr_key = mat_num + "t"
                        break
                if key == "":
                    key = newmtl_name + "_d"
                    tr_key = newmtl_name + "_t"

                base_color_key = newmtl_name + "_c"
                j = i + 1
                path = ""
                tr_path = ""
                base_color_value = []
                alpha_value = 1.0

                # iterate through lines until next "newmtl"
                while j < len(mtl_lines):
                    mtl_line = mtl_lines[j]
                    if mtl_line.startswith("newmtl"):
                        break
                    if mtl_line.startswith("map"):
                        space_index = mtl_line.find(" ")
                        if space_index > -1:
                            if mtl_line.startswith("map_kd"):
                                path = mtl_line[space_index + 1:]
                                if not os.path.exists(path):
                                    dir_path = os.path.dirname(path)
                                    case1 = os.path.exists(dir_path)
                                    case2 = os.path.isdir(dir_path)
                                    case3 = directory_memo == ""
                                    if case1 and case2 and case3:
                                        directory_memo = dir_path
                                    path = ""
                            elif mtl_line.startswith("map_d"):
                                tr_path = mtl_line[space_index + 1:]
                                if not os.path.exists(tr_path):
                                    tr_path = ""
                    elif mtl_line.startswith("kd ") and len(mtl_line) >= 8:
                        values = mtl_line[3:].split()
                        for value in values:
                            base_color_value.append(float(value))
                        base_color_value.append(1.0)
                    elif mtl_line.startswith("d ") and len(mtl_line) >= 3:
                        alpha_value = float(mtl_line[2:])
                    j += 1

                if path != "":
                    if tex_dir_path == "" and '_' not in key:
                        tex_dir_path = os.path.dirname(path)
                    self.add_to_dct(key, path)
                self.add_to_dct(tr_key, tr_path)
                if len(base_color_value) == 4:
                    if alpha_value != 1.0:
                        base_color_value[3] = alpha_value
                    self.add_to_dct(base_color_key, base_color_value)

        if tex_dir_path == "":
            tex_dir_path = directory_memo
        if tex_dir_path != "":
            self.search_directory(tex_dir_path)

    # Check and add (key, value) to dct
    def add_to_dct(self, key, value):
        if value == "":
            return

        if key not in self.dct:
            self.dct[key] = value
        elif ('_' in key) and len(key) > 2:
            for i in range(1, 10):
                suffix_index = key.rfind("_")
                key2 = key[:suffix_index] + ".00" + str(i) + key[suffix_index:]
                if key2 not in self.dct:
                    self.dct[key2] = value
                    break

    def check_match(self, mat_prop, tex_name, index, is_cloth):
        if index == 0:
            if (mat_prop in tex_name) or (mat_prop.lower() in tex_name.lower()) or (mat_prop.upper() in tex_name.upper()):
                return True
        else:
            if len(mat_prop) == 1:
                if is_cloth:
                    return False
                else:
                    mat_prop = mat_prop.upper()
            delimiters = ['-', '.', '_']
            for delimiter in delimiters:
                case1 = (mat_prop + delimiter) in tex_name
                case2 = (delimiter + mat_prop) in tex_name
                if case1 or case2:
                    return True
            if (len(mat_prop) > 2 and mat_prop[:1].isupper() and mat_prop[1:].islower() and (mat_prop in tex_name)):
                return True
        return False

    # Find matches with all the textures in the directory and add to self.dct
    def search_directory(self, dir_path):
        daz_tex_path_win = {
            "female": "C:\\Users\\Public\\Documents\\My DAZ 3D Library\\Runtime\\Textures\\DAZ\\Characters\\Genesis8\\FemaleBase",
            "male": "C:\\Users\\Public\\Documents\\My DAZ 3D Library\\Runtime\\Textures\\DAZ\\Characters\\Genesis8\\MaleBase"
        }
        daz_tex_path_mac = {
            "female": "/Users/Share/My DAZ 3D Library/Runtime/Textures/DAZ/Characters/Genesis8/FemaleBase",
            "male": "/Users/Share/My DAZ 3D Library/Runtime/Textures/DAZ/Characters/Genesis8/MaleBase"
        }
        fig_tex_paths = [dir_path, ""]

        # Check gender and os. Set the corresponding address.
        if Global.getIsMan():
            if os.name == 'nt':
                fig_tex_paths[1] = daz_tex_path_win["male"]
            else:
                fig_tex_paths[1] = daz_tex_path_mac["male"]
        else:
            if os.name == 'nt':
                fig_tex_paths[1] = daz_tex_path_win["female"]
            else:
                fig_tex_paths[1] = daz_tex_path_mac["female"]

        # TODO: Verify if we need to search in default path
        # Skip if both represent same directories
        # if os.path.samefile(fig_tex_paths[0], fig_tex_paths[1]):
        #     fig_tex_paths[1] = "skip"

        for index in range(len(fig_tex_paths)):
            if index > 0:
                self.mat_props__imgs.append(["diff", "Eyes01", "d"])

            fig_tex_path = fig_tex_paths[index]
            if os.path.exists(fig_tex_path) and os.path.isdir(fig_tex_path):
                tex_names = os.listdir(fig_tex_path)
                # Check for matches with each texture from the directory
                for tex_name in tex_names:
                    tex_name_lower = tex_name.lower()
                    mat_type_prop = ["", ""]
                    for i in range(2):
                        # Find a mat_type match for the texture
                        for mat_name_num in self.mat_types__bpart:
                            mat_v = mat_name_num[i]
                            case1 = (i == 0) and mat_v in tex_name_lower
                            case2 = (i == 1) and (
                                "00" + mat_v) in tex_name_lower
                            if case1 or case2:
                                if mat_type_prop[0] == "":
                                    mat_type_prop[0] = mat_name_num[1]
                                    break

                        # Find a mat_prop match for the texture
                        for mat_prop in self.mat_props__imgs:
                            prop = mat_prop[i]
                            case1 = self.check_match(
                                prop,
                                tex_name,
                                i,
                                is_cloth=False
                            )
                            case2 = self.check_match(
                                prop,
                                tex_name_lower,
                                i,
                                is_cloth=False
                            )
                            if case1 or case2:
                                if mat_type_prop[1] == "":
                                    mat_type_prop[1] = mat_prop[2]
                                    break

                            if len(prop) == 1 and i > 0:
                                pattern = "[a-z]" + prop.upper() + "\d"
                                match = re.search(pattern, tex_name)
                                if match:
                                    if mat_type_prop[1] == "":
                                        mat_type_prop[1] = mat_prop[2]
                                        break

                    # Add to the dict if both type and property values exist
                    if mat_type_prop[0] != "" and mat_type_prop[1] != "":
                        if mat_type_prop[0] == '6':
                            mat_type_prop[0] = '7'
                        key = mat_type_prop[0] + mat_type_prop[1]
                        value = os.path.join(fig_tex_path, tex_name)
                        self.add_to_dct(key, value)

    def cloth_dct_0(self, adr):
        c_dir = os.path.dirname(adr)
        c_name = os.path.splitext(os.path.basename(adr))[0]
        if not os.path.exists(c_dir):
            return None
        if c_name != "":
            for i in range(3):
                if i == 0:
                    rtn = self.cloth_dct(c_name, c_dir, adr)
                    if rtn != []:
                        return rtn
                elif i == 1:
                    for img in self.mat_props__imgs:
                        if img[2] == 'd':
                            for j in range(2):
                                if c_name.endswith(img[j]):
                                    myc_name = c_name[0:len(
                                        c_name) - len(img[j])]
                                    rtn = self.cloth_dct(myc_name, c_dir, adr)

                                    if rtn != []:
                                        return rtn
                else:
                    if len(c_name) >= 12:
                        c_name = c_name[:(len(c_name) // 2) - 2]
                    elif len(c_name) >= 8:
                        c_name = c_name[:3]
                    else:
                        c_name = c_name[:1]
                    return self.cloth_dct(c_name, c_dir, adr)
        return None

    def cloth_dct(self, cname, aadr, skip_adr):
        skip_adr = os.path.realpath(os.path.abspath(skip_adr))
        cloth_dct = []
        if os.path.exists(aadr) and os.path.isdir(aadr):
            list = os.listdir(path=aadr)
            for l in list:
                L = l
                l = l.lower()
                if L.startswith(cname) == False:
                    continue
                twd = [cname, ""]
                for z in range(2):
                    for img in self.mat_props__imgs:
                        ig = img[z]
                        if self.check_match(ig, L, z, True) or self.check_match(ig, l, z, True):
                            if twd[1] == "":
                                twd[1] = img[2]
                                break
                if twd[0] != "" and twd[1] != "":
                    wd = twd[0] + "-" + twd[1]
                    for cd in cloth_dct:
                        if cd[0] == wd:
                            wd = ""
                            break
                    if wd != "":
                        ans = os.path.join(aadr, L)
                        ans = os.path.realpath(os.path.abspath(ans))
                        if skip_adr != ans:
                            cloth_dct.append([wd, ans])
        return cloth_dct
