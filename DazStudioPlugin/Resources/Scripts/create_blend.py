"""Create Blend file from fbx/dtu

This script is used to create a blend file from fbx/dtu file which is exported from Daz Studio.

- Developed and tested with Blender 3.6 (Python 3.10) and Daz Studio 4.22

USAGE: blender.exe --background --python create_blend.py <fbx file>

EXAMPLE:

    blender.exe --background --python create_blend.py "C:/Users/username/Documents/DAZ 3D/DazToBlender/Export/Genesis8Female.fbx"

Version: 1.26
Date: 2024-09-02

"""

TEXTURE_ATLAS_SIZE_DEFAULT = 1024

g_logfile = ""

def _print_usage():
    print("\nUSAGE: blender.exe --background --python create_blend.py <fbx file>\n")

from pathlib import Path
script_dir = str(Path(__file__).parent.absolute())

import sys
import os
import json
import re
import shutil
import mathutils

try:
    import bpy
except:
    print("DEBUG: blender python libraries not detected, continuing for pydoc mode.")

try:
    import blender_tools
    import game_readiness_tools
except:
    sys.path.append(script_dir)
    import blender_tools
    import game_readiness_tools

try:
    import DTB
    from DTB import *
    G_DAZ_ADDON_LOADED = True
except:
    print("DEBUG: DazToBlender addon not detected, continuing in fallback mode.")
    G_DAZ_ADDON_LOADED = False


def _add_to_log(message):
    if (g_logfile == ""):
        logfile = script_dir + "/create_blend.log"
    else:
        logfile = g_logfile

    print(str(message))
    with open(logfile, "a") as file:
        file.write(str(message) + "\n")

def _main(argv):
    try:
        line = str(argv[-1])
    except:
        _print_usage()
        return

    try:
        start, stop = re.search("#([0-9]*)\.", line).span(0)
        token_id = int(line[start+1:stop-1])
        print(f"DEBUG: token_id={token_id}")
    except:
        print(f"ERROR: unable to parse token_id from '{line}'")
        token_id = 0

    blender_tools.delete_all_items()
    blender_tools.switch_to_layout_mode()

    fbxPath = line.replace("\\","/").strip()
    if (not os.path.exists(fbxPath)):
        _add_to_log("ERROR: main(): fbx file not found: " + str(fbxPath))
        exit(1)
        return

    # prepare intermediate folder paths
    blenderFilePath = fbxPath.replace(".fbx", ".blend")
    intermediate_folder_path = os.path.dirname(fbxPath)

    if ("B_FIG" in fbxPath):
        jsonPath = fbxPath.replace("B_FIG.fbx", "FIG.dtu")
    elif ("B_ENV" in fbxPath):
        jsonPath = fbxPath.replace("B_ENV.fbx", "ENV.dtu")
    else:
        jsonPath = fbxPath.replace(".fbx", ".dtu")

    use_blender_tools = True
    use_legacy_addon = False
    output_blend_filepath = ""
    texture_atlas_mode = ""
    texture_atlas_size = 0
    export_rig_mode = ""
    enable_gpu_baking = False
    enable_embed_textures = False
    generate_final_fbx = False
    generate_final_glb = False
    generate_final_usd = False
    use_material_x = False
    try:
        with open(jsonPath, "r") as file:
            json_obj = json.load(file)
        # use_blender_tools = json_obj["Use Blender Tools"]
        if "Asset Type" in json_obj:
            asset_type = json_obj["Asset Type"]
        if "Output Blend Filepath" in json_obj:
            output_blend_filepath = json_obj["Output Blend Filepath"]
        if "Embed Textures" in json_obj:
            enable_embed_textures = json_obj["Embed Textures"]
        if "Generate Final Fbx" in json_obj:
            generate_final_fbx = json_obj["Generate Final Fbx"]
        if "Generate Final Glb" in json_obj:
            generate_final_glb = json_obj["Generate Final Glb"]
        if "Generate Final Usd" in json_obj:
            generate_final_usd = json_obj["Generate Final Usd"]
        if "Use MaterialX" in json_obj:
            use_material_x = json_obj["Use MaterialX"]
        if "Use Legacy Addon" in json_obj:
            use_legacy_addon = json_obj["Use Legacy Addon"]
        if "Texture Atlas Mode" in json_obj:
            texture_atlas_mode = json_obj["Texture Atlas Mode"]
        if "Texture Atlas Size" in json_obj:
            texture_atlas_size = json_obj["Texture Atlas Size"]
        if "Export Rig Mode" in json_obj:
            export_rig_mode = json_obj["Export Rig Mode"]
        if "Enable Gpu Baking" in json_obj:
            enable_gpu_baking = json_obj["Enable Gpu Baking"]
    except:
        print("ERROR: error occured while reading json file: " + str(jsonPath))

    force_connect_bones = False

    if texture_atlas_size == 0:
        texture_atlas_size = TEXTURE_ATLAS_SIZE_DEFAULT

    if output_blend_filepath != "":
        blenderFilePath = output_blend_filepath

    if use_legacy_addon and G_DAZ_ADDON_LOADED:
        if "DTB" not in bpy.context.preferences.addons:
            G_DAZ_ADDON_ENABLED = False
            # load DazToBlender addon
            _add_to_log("INFO: Legacy Addon Chosen by User, but Addon not enabled! Attempting to enable DazToBlender Addon...")
            try:
                bpy.ops.preferences.addon_enable(module="DTB")
                _add_to_log("DazToBlender Addon enabled.")
                G_DAZ_ADDON_ENABLED = True
            except Exception as e:
                _add_to_log("ERROR: Unable to enable DazToBlender Addon, reverting to modern pathway.")
                _add_to_log("EXCEPTION: " + str(e))
                # raise e
        else:
            G_DAZ_ADDON_ENABLED = True

    if use_legacy_addon and G_DAZ_ADDON_LOADED and G_DAZ_ADDON_ENABLED:
        _add_to_log("DEBUG: main(): using legacy pathway...")
        DTB.Global.bNonInteractiveMode = 1
        DTB.Global.nSceneScaleOverride = 0.01

        sDtuFolderPath = os.path.dirname(jsonPath)
        oDtu = DTB.DataBase.DtuLoader()
        with open(jsonPath, "r") as data:
            oDtu.dtu_dict = json.load(data)

        DTB.Global.clear_variables()
        DTB.Global.setHomeTown(sDtuFolderPath)
        DTB.Global.load_asset_name()

        asset_type = oDtu.get_asset_type()
        if asset_type == "Environment" or asset_type == "StaticMesh":
            bpy.ops.import_dtu.env()
        else:
            bpy.ops.import_dtu.fig()

        DTB.Global.bNonInteractiveMode = 0

    else:
        _add_to_log("DEBUG: main(): using modern pathway...")

        # load FBX
        _add_to_log("DEBUG: main(): loading fbx file: " + str(fbxPath))
        blender_tools.import_fbx(fbxPath, force_connect_bones)

        blender_tools.center_all_viewports()
        _add_to_log("DEBUG: main(): loading json file: " + str(jsonPath))
        dtu_dict = blender_tools.process_dtu(jsonPath)

    debug_blend_file = False
    if debug_blend_file:
        debug_blend_file = fbxPath.replace(".fbx", "_debug.blend")
        bpy.ops.wm.save_as_mainfile(filepath=debug_blend_file)

    make_uv = True
    if texture_atlas_mode == "per_mesh":
        _add_to_log("DEBUG: main(): converting to per mesh atlas...")
        bake_quality = 1
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.visible_get():
                atlas, atlas_material, _ = game_readiness_tools.convert_to_atlas(obj, intermediate_folder_path, texture_atlas_size, bake_quality, make_uv, enable_gpu_baking)
    elif texture_atlas_mode == "single_atlas":
        _add_to_log("DEBUG: main(): converting to single atlas...")
        texture_size = 2048
        bake_quality = 1
        # collect all meshes
        obj_list = []
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.visible_get():
                obj_list.append(obj)
        atlas, atlas_material, _ = game_readiness_tools.convert_to_atlas(obj_list, intermediate_folder_path, texture_atlas_size, bake_quality, make_uv, enable_gpu_baking)

    # remove missing or unused images
    print("DEBUG: deleting missing or unused images...")
    for image in bpy.data.images:
        is_missing = False
        if image.filepath:
            imagePath = bpy.path.abspath(image.filepath)
            if (not os.path.exists(imagePath)):
                is_missing = True

        is_unused = False
        if image.users == 0:
            is_unused = True

        if is_missing or is_unused:
            bpy.data.images.remove(image)

    # cleanup all unused and unlinked data blocks
    print("DEBUG: main(): cleaning up unused data blocks...")
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    # pack images
    if enable_embed_textures:
        print("DEBUG: packing images...")
        bpy.ops.file.pack_all()

    if export_rig_mode == "unreal" or export_rig_mode == "metahuman":
        # apply all transformations on armature
        for obj in bpy.data.objects:
            bpy.ops.object.select_all(action='DESELECT')
            if obj.type == 'ARMATURE':
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        blender_tools.fix_unreal_rig()

    if export_rig_mode == "mixamo":
        # modify blend file to be mixamo compatible for more convenient export to fbx
        blender_tools.force_mixamo_compatible_materials()

    bpy.ops.wm.save_mainfile(filepath=blenderFilePath)
    _add_to_log("DEBUG: main(): blend file saved: " + str(blenderFilePath))

    if generate_final_glb:
        glb_output_file_path = blenderFilePath.replace(".blend", ".glb")
        try:
            bpy.ops.export_scene.gltf(filepath=glb_output_file_path, export_format="GLB", 
                                      use_visible=True,
                                    #   use_renderable=True,
                                      use_selection=False, 
                                      export_animations=True,
                                      export_bake_animation=True,
                                    #   export_normals=False,
                                      export_morph=True
                                    )
            _add_to_log("DEBUG: save completed.")
        except Exception as e:
            _add_to_log("ERROR: unable to save Final GLB file: " + glb_output_file_path)
            _add_to_log("EXCEPTION: " + str(e))
            raise e

    if generate_final_fbx:
        add_leaf_bones = False
        smooth_type = "OFF"
        if export_rig_mode == "mixamo":
            add_leaf_bones = True
            # blender_tools.force_mixamo_compatible_materials()
        if export_rig_mode == "unreal" or export_rig_mode == "metahuman":
            smooth_type = "FACE"
        fbx_output_file_path = blenderFilePath.replace(".blend", ".fbx")
        try:
            bpy.ops.export_scene.fbx(filepath=fbx_output_file_path, 
                                    add_leaf_bones = add_leaf_bones,
                                    path_mode = "COPY",
                                    embed_textures = enable_embed_textures,
                                    use_visible = True,
                                    mesh_smooth_type = smooth_type
                                    )
            _add_to_log("DEBUG: save completed.")
        except Exception as e:
            _add_to_log("ERROR: unable to save Final FBX file: " + fbx_output_file_path)
            _add_to_log("EXCEPTION: " + str(e))
            raise e

    if generate_final_usd:
        usd_output_file_path = blenderFilePath.replace(".blend", ".usdz")
        # if blender < 4, don't use extra options
        if bpy.app.version < (4, 2, 0):
            try:
                _add_to_log("DEBUG: Using older version of USD Exporter for Blender: " + str(bpy.app.version))
                bpy.ops.wm.usd_export(filepath=usd_output_file_path,
                                        export_textures = True,
                                        export_animation = True,
                                        export_armatures = True,
                                        convert_orientation = True,
                                        )
                _add_to_log("DEBUG: save completed.")
            except Exception as e:
                _add_to_log("ERROR: unable to save Final USD file: " + usd_output_file_path)
                _add_to_log("EXCEPTION: " + str(e))
                raise e
        else:
            try:
                _add_to_log("DEBUG: Using USD Exporter for Blender >= 4.2.0")
                bpy.ops.wm.usd_export(filepath=usd_output_file_path, 
                                        export_textures = True,
                                        export_animation = True,
                                        export_armatures = True,
                                        export_shapekeys = True,
                                        generate_materialx_network = use_material_x,
                                        export_custom_properties = True,
                                        export_cameras = True,
                                        export_lights = True,
                                        convert_orientation = True,
                                        )
                _add_to_log("DEBUG: save completed.")
            except Exception as e:
                _add_to_log("ERROR: unable to save Final USD file: " + usd_output_file_path)
                _add_to_log("EXCEPTION: " + str(e))
                raise e

    return

# Execute main()
if __name__=='__main__':
    print("Starting script...")
    _add_to_log("Starting script... DEBUG: sys.argv=" + str(sys.argv))
    _main(sys.argv[4:])
    print("script completed.")
    exit(0)
