import json
import os

import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
)

from bpy.types import (
    PropertyGroup,
)

from . import Global
from . import DtbIKBones
from . import DtbCommands


class ImportFilesCollection(PropertyGroup):
    name: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype="FILE_PATH",
    )


class CustomPathProperties(PropertyGroup):
    # test
    path: StringProperty(
        name="",
        description="Choose Path for Auto-Import",
        default="",
        maxlen=1024,
        subtype="DIR_PATH",
    )


def init_props():
    w_mgr = bpy.types.WindowManager
    scn = bpy.types.Scene
    w_mgr.skin_prop = EnumProperty(
        name="skin",
        description="Skin Adjust",
        items=[
            ("1", "Base Color.Hue", "1"),
            ("2", "Base Color.Saturation", "2"),
            ("3", "Base Color.Value", "3"),
            ("4", "Base Color.Bright", "4"),
            ("5", "Base Color.Contrast", "5"),
            ("6", "Specular", "6"),
            ("7", "Roughness", "7"),
            ("8", "Roughness.Contrast", "8"),
            ("9", "Specular.Contrast", "9"),
            ("10", "Subsurface.Scale", "10"),
            ("11", "Normal.Strength", "11"),
            ("12", "Bump.Strength", "12"),
            ("13", "Bump.Distance", "13"),
            ("14", "Displacement.Height", "14"),
        ],
        default="1",
    )
    w_mgr.eye_prop = EnumProperty(
        name="skin",
        description="Eyes Adjust",
        items=[
            ("1", "Base Color.Hue", "1"),
            ("2", "Base Color.Saturation", "2"),
            ("3", "Base Color.Value", "3"),
            ("4", "Base Color.Bright", "4"),
            ("5", "Base Color.Contrast", "5"),
            ("6", "Normal.Strength", "6"),
            ("7", "Bump.Strength", "7"),
            ("8", "Bump.Distance", "8"),
        ],
        default="1",
    )
    w_mgr.search_prop = StringProperty(
        name="",
        default="",
        description="Search_shape_keys",
        update=DtbCommands.search_morph_,
    )
    w_mgr.is_eye = BoolProperty(name="eyes")
    w_mgr.ftime_prop = BoolProperty(name="ftime")
    w_mgr.br_onoff_prop = BoolProperty(
        name="br_onoff", default=True, update=DtbIKBones.bonerange_onoff
    )
    w_mgr.ifk0 = BoolProperty(name="ifk0", default=False, update=DtbIKBones.ifk_update0)
    w_mgr.ifk1 = BoolProperty(name="ifk1", default=False, update=DtbIKBones.ifk_update1)
    w_mgr.ifk2 = BoolProperty(name="ifk2", default=False, update=DtbIKBones.ifk_update2)
    w_mgr.ifk3 = BoolProperty(name="fik3", default=False, update=DtbIKBones.ifk_update3)
    w_mgr.new_morph = BoolProperty(name="_new_morph", default=False)
    w_mgr.skip_isk = BoolProperty(name="_skip_isk", default=False)

    figure_items = [
        ("null", "Choose Character", "Select which figure you wish to import")
    ]
    w_mgr.choose_daz_figure = EnumProperty(
        name="Highlight for Collection",
        description="Choose any figure in your scene to which you wish to add a pose.",
        items=figure_items,
        default="null",
    )


def config_props():
    w_mgr = bpy.types.WindowManager
    scn = bpy.types.Scene
    w_mgr.update_scn_settings = BoolProperty(
        name="update_scn_settings",
        description="Updates the Render Engine, Shading Type, and Using Depth Under Mouse",
        default=True,
    )
    w_mgr.update_viewport = BoolProperty(
        name="update_viewport",
        description="Updates the Viewport, and Camera for your Scale",
        default=True,
    )
    w_mgr.use_custom_path = BoolProperty(
        name="Use Custom Import Path",
        default=False,
    )
    w_mgr.morph_prefix = BoolProperty(
        name="morph_prefix",
        default=True,
    )
    w_mgr.morph_optimize = BoolProperty(
        name="morph_optimize",
        default=True,
    )
    w_mgr.combine_materials = BoolProperty(
        name="combine_materials",
        default=True,
    )
    w_mgr.add_pose_lib = BoolProperty(
        name="add_pose_lib",
        default=True,
    )
    w_mgr.scene_scale = EnumProperty(
        name="Scene Scale",
        description="Used to change scale of imported object and scale settings",
        items=[
            ("0.01", "Real Scale (Centimeters)", "Daz Scale"),
            ("0.1", "x10", "10 x Daz Scale"),
            ("1", "x100 (Meters)", "100 x Daz Scale"),
        ],
        default="0.01",
    )
    w_mgr.search_morph_list = StringProperty(
        name="",
        default="Type Keyword Here",
        description="Search_shape_keys",
    )


def load_config():
    data = {}
    config = Global.get_config_path()
    config_file_path = os.path.join(config, "daz_paths.json")
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, "r") as f:
                data = json.load(f)
        except:
            print("ERROR: Unable to read DazToBlender config file: \"" + config_file_path + "\".")
    return data


def key_exists(key, data):
    if key in data.keys():
        return data[key]
    else:
        return "undefined"


def update_config():
    config = load_config()
    w_mgr = bpy.types.WindowManager
    scn = bpy.types.Scene
    if config:
        custom_path = key_exists("Custom Path", config)
        use_custom = key_exists("Use Custom Path", config)
        scene_scale = key_exists("Scene Scale", config)
        add_pose_lib = key_exists("Add to Pose Library", config)
        combine_materials = key_exists("Combine Dupe Materials", config)
        morph_prefix = key_exists("Remove Morph Prefix", config)
        morph_optimize = key_exists("Optimize Morphs", config)

        if (use_custom != "undefined") and (custom_path != "undefined"):
            print(use_custom)
            w_mgr.use_custom_path = BoolProperty(
                name="Use Custom Import Path",
                default=use_custom,
            )
            cp = CustomPathProperties
            cp.path = StringProperty(
                name="",
                description="Choose Path for Auto-Import",
                default=custom_path,
                maxlen=1024,
                subtype="DIR_PATH",
            )
            scn.dtb_custom_path = PointerProperty(type=cp)
