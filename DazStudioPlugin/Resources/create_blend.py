"""Create Blend file from fbx/dtu

This script is used to create a blend file from fbx/dtu file which is exported from Daz Studio.

- Developed and tested with Blender 3.6 (Python 3.10) and Daz Studio 4.22

USAGE: blender.exe --background --python create_blend.py <fbx file>

EXAMPLE:

    blender.exe --background --python create_blend.py "C:/Users/username/Documents/DAZ 3D/DazToBlender/Export/Genesis8Female.fbx"

"""

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
except:
    sys.path.append(script_dir)
    import blender_tools

try:
    import DTB
    from DTB import *
    g_daz_addon_loaded = True
except:
    print("DEBUG: DazToBlender addon not detected, continuing in fallback mode.")
    g_daz_addon_loaded = False


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
    else:
        jsonPath = fbxPath.replace(".fbx", ".dtu")

    if g_daz_addon_loaded:

        # load DazToBlender addon
        _add_to_log("DEBUG: main(): loading DazToBlender addon")
        DTB.Global.bNonInteractiveMode = 1;
        DTB.Global.nSceneScaleOverride = float(bpy.context.window_manager.scene_scale);
    #    DTB.Global.nSceneScaleOverride = 1;
        sDtuFolderPath = os.path.dirname(jsonPath)
        oDtu = DTB.DataBase.DtuLoader();
        with open(jsonPath, "r") as data:
            oDtu.dtu_dict = json.load(data)
        DTB.Global.clear_variables()
        DTB.Global.setHomeTown(sDtuFolderPath)
        DTB.Global.load_asset_name()
    #    DTB.Util.decideCurrentCollection('ENV')
    #    DTB.Environment.ReadFbx(jsonPath, 0, 0, oDtu)
        oImportHelper = DTB.DtbOperators.ImportHelper()
        oImportHelper.import_one(fbxPath)

        DTB.Global.bNonInteractiveMode = 0;

    else:
        # load FBX
        _add_to_log("DEBUG: main(): loading fbx file: " + str(fbxPath))
        blender_tools.import_fbx(fbxPath)

        blender_tools.center_all_viewports()
        _add_to_log("DEBUG: main(): loading json file: " + str(jsonPath))
        dtu_dict = blender_tools.process_dtu(jsonPath)

    # pack images
    bpy.ops.file.pack_all()

    bpy.ops.wm.save_as_mainfile(filepath=blenderFilePath)

    return

# Execute main()
if __name__=='__main__':
    print("Starting script...")
    _add_to_log("Starting script... DEBUG: sys.argv=" + str(sys.argv))
    _main(sys.argv[4:])
    print("script completed.")
    exit(0)
