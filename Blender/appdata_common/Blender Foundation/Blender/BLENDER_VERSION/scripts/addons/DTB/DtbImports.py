import bpy

def fbx_catched_error(filepath):
    # if Blender 3.6 or greater, enable use_prepost_rot
    local_use_prepost_rot = False
    if bpy.app.version[0] >= 3 and bpy.app.version[1] >= 6:
        local_use_prepost_rot = True
    try:
        bpy.ops.import_scene.fbx(
                            filepath = filepath,
                            use_manual_orientation = False,
                            global_scale = 1,
                            bake_space_transform = False,
                            use_custom_normals = True,
                            use_image_search = True, # check if needed
                            use_anim = True,
                            anim_offset = 1,
                            ignore_leaf_bones = False,
                            force_connect_children = False,
                            automatic_bone_orientation = False,
                            primary_bone_axis = 'Y',
                            secondary_bone_axis = 'X',
                            use_prepost_rot = local_use_prepost_rot,
                            )
    except Exception as e:
        print(e)
