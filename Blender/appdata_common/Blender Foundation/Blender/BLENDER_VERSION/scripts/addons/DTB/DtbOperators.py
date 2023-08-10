from . import DazRigBlend
from . import DtbShapeKeys
from . import DataBase
from . import ToRigify
from . import Global
from . import Versions
from . import DtbDazMorph
from . import DtbMaterial
from . import CustomBones
from . import Poses
from . import Animations
from . import Util
from . import DtbCommands
from . import DtbIKBones
from . import DtbProperties
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import EnumProperty
from bpy.props import BoolProperty
from bpy.props import StringProperty
from bpy.props import PointerProperty
import os
import json
from copy import deepcopy

region = "UI"
BV = Versions.getBV()


# Start of Utlity Classes
def reload_dropdowns(version):
    if version == "choose_daz_figure":
        w_mgr = bpy.types.WindowManager
        prop = Versions.get_properties(w_mgr.choose_daz_figure)
        for arm in Util.all_armature():
            check = [x for x in prop["items"] if x[0] == arm.name]
            if len(check) == 0:
                if "Asset Name" in arm.keys():
                    prop["items"].append(
                        (arm.name, arm["Asset Name"], arm["Collection"])
                    )
        w_mgr.choose_daz_figure = EnumProperty(
            name=prop["name"],
            description=prop["description"],
            items=prop["items"],
            default=Global.get_Amtr_name(),
        )


class OP_SAVE_CONFIG(bpy.types.Operator):
    bl_idname = "save.daz_settings"
    bl_label = "Save Config"
    bl_description = "Saves the Configuration to be used by Daz and Blender"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = context.scene
        w_mgr = context.window_manager
        data = {}
        config = Global.get_config_path()
        config_file_path = os.path.join(config, "daz_paths.json")
        if os.path.exists(config_file_path):
            with open(config_file_path, "r") as f:
                data = json.load(f)
        data["Custom Path"] = scn.dtb_custom_path.path.replace("\\", "/")
        data["Use Custom Path"] = w_mgr.use_custom_path
        with open(os.path.join(config, "daz_paths.json"), "w") as f:
            json.dump(data, f, indent=2)
        self.report({"INFO"}, "Config Saved!")
        return {"FINISHED"}


class REFRESH_DAZ_FIGURES(bpy.types.Operator):
    bl_idname = "refresh.alldaz"
    bl_label = "Refresh All Daz Figures"
    bl_description = (
        "Refreshes List of Figures\nOnly needed if figure is not in dropdown"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w_mgr = bpy.types.WindowManager
        prop = Versions.get_properties(w_mgr.choose_daz_figure)
        check = ["null"]
        for arm in Util.all_armature():
            check = [x for x in prop["items"] if x[0] == arm.name]
            if len(check) == 0:
                if "Asset Name" in arm.keys():
                    prop["items"].append(
                        (arm.name, arm["Asset Name"], arm["Collection"])
                    )
        if "null" in check:
            prop["items"] = [("null", "Choose Character", "Default Value")]
        w_mgr.choose_daz_figure = EnumProperty(
            name=prop["name"],
            description=prop["description"],
            items=prop["items"],
            default=prop["default"],
        )
        return {"FINISHED"}


class REMOVE_DAZ_OT_button(bpy.types.Operator):
    bl_idname = "remove.alldaz"
    bl_label = "Remove All Daz"
    bl_description = "Clears out all imported assets\nCurrently deletes all Materials"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        col = bpy.data.collections.get("DAZ_ROOT")
        if col is not None:
            for c in col.children:
                for obj in c.objects:
                    bpy.data.objects.remove(obj)
                bpy.data.collections.remove(c)
            for material in bpy.data.materials:
                material.user_clear()
                bpy.data.materials.remove(material)
        return {"FINISHED"}


class RENAME_MORPHS(bpy.types.Operator):
    bl_idname = "rename.morphs"
    bl_label = "Remove Morph Prefix"

    def execute(self, context):
        Global.setOpsMode("OBJECT")
        selected_objects = []
        fig_object_name = bpy.context.window_manager.choose_daz_figure
        if fig_object_name == "null":
            selected_objects.append(bpy.context.object)
        else:
            selected_objects = Global.get_children(bpy.data.objects[fig_object_name])
        for selected_object in selected_objects:

            if selected_object is None or selected_object.type != "MESH":
                self.report({"WARNING"}, "Select Object or Choose From Dropdown")
                continue
            if selected_object.data.shape_keys is None:
                self.report(
                    {"INFO"}, "No Morphs found on {0}".format(selected_object.name)
                )
                continue
            # get its shapekeys
            shape_keys = selected_object.data.shape_keys.key_blocks
            string_to_replace = selected_object.data.name + "__"
            # loop through shapekeys and replace the names
            for key in shape_keys:
                key.name = key.name.replace(string_to_replace, "")
        self.report({"INFO"}, "Morphs renamed!")

        return {"FINISHED"}


# End of Utlity Classes
# Start of Import Classes
class IMP_OT_FBX(bpy.types.Operator):
    """Supports Genesis 3, 8, 8.1 and 9"""

    bl_idname = "import.fbx"
    bl_label = "Import New Genesis Figure"
    bl_options = {"REGISTER", "UNDO"}
    root = Global.getRootPath()

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def finish_obj(self):
        Versions.reverse_language()
        Versions.pivot_active_element_and_center_and_trnormal()
        Global.setRenderSetting(True)

    def layGround(self):
        Util.deleteEmptyDazCollection()
        if bpy.context.window_manager.update_scn_settings:
            bpy.context.preferences.inputs.use_mouse_depth_navigate = True
            # bpy.context.scene.render.engine = "CYCLES"
            bpy.context.space_data.shading.type = "SOLID"
            bpy.context.space_data.shading.color_type = "OBJECT"
            bpy.context.space_data.shading.show_shadows = False
        Versions.set_english()
        bco = bpy.context.object
        if bco != None and bco.mode != "OBJECT":
            Global.setOpsMode("OBJECT")
        bpy.ops.view3d.snap_cursor_to_center()

    def pbar(self, v, wm):
        wm.progress_update(v)

    def import_one(self, fbx_adr):
        Versions.active_object_none()
        Util.decideCurrentCollection("FIG")
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        Global.clear_variables()
        DtbIKBones.ik_access_ban = True

        # Instant of classes
        dtu = DataBase.DtuLoader()
        drb = DazRigBlend.DazRigBlend(dtu)
        dtb_shaders = DtbMaterial.DtbShaders(dtu)
        anim = Animations.Animations(dtu)
        pose = Poses.Posing(dtu)
        dsk = DtbShapeKeys.DtbShapeKeys(False, dtu)
        db = DataBase.DB()
        self.pbar(5, wm)

        anim.reset_total_key_count()
        drb.convert_file(filepath=fbx_adr)
        self.pbar(10, wm)
        Global.load_dtu(dtu)
        Global.store_variables()
        self.pbar(15, wm)

        if Global.getAmtr() is not None and Global.getBody() is not None:

            ###############################
            # materials
            dtb_shaders.make_dct()
            dtb_shaders.load_shader_nodes()
            body = Global.getBody()
            dtb_shaders.setup_materials(body)
            self.pbar(35, wm)
            
            fig_objs_names = [Global.get_Body_name()]
            for obj in Util.myacobjs():
                # Skip for any of the following cases
                case1 = not Global.isRiggedObject(obj)
                case2 = obj.name in fig_objs_names
                if case1 or case2:
                    continue
                dtb_shaders.setup_materials(obj)
            self.pbar(40, wm)

            # # materials
            # DtbMaterial.forbitMinus()
            # self.pbar(95, wm)
            # Global.deselect()

            # Set Custom Properties
            Global.getAmtr()["Asset Name"] = dtu.get_asset_name()
            Global.getAmtr()["Collection"] = Util.cur_col_name()
            reload_dropdowns("choose_daz_figure")
            pose.add_skeleton_data()

            # Translate any global Bone Name(s)
            DtbIKBones.ik_name = DataBase.translate_bonenames(DtbIKBones.ik_name)
            DtbIKBones.bone_name = DataBase.translate_bonenames(DtbIKBones.bone_name)
            db.translate_member_bonenames()

            #############################
            # Re-orient rest pose
            Global.deselect()  # deselect all the objects
            pose.clear_pose()  # Select Armature and clear transform
            drb.mub_ary_A()  # Find and read FIG.dat file
            drb.preprocess_empty_objects()  # On "EMPTY" type objects
            self.pbar(18, wm)
            drb.preprocess_bones()  # clear transform, clear and reapply parent, CMs -> METERS
            Global.deselect()
            self.pbar(20, wm)
            drb.set_bone_head_tail()  # Sets head and tail positions for all the bones

            # Re-orient active pose and animations
            Global.deselect()
            self.pbar(25, wm)
            drb.bone_limit_modify()
            if anim.has_keyframe(Global.getAmtr()):
                anim.clean_animations()
            Global.deselect()
            self.pbar(30, wm)
            drb.unwrapuv()
            Global.deselect()

            if Global.getIsGen():
                drb.fixGeniWeight(db)
            Global.deselect()
            self.pbar(45, wm)
            Global.setOpsMode("OBJECT")
            Global.deselect()

            # DB: 2022-Sept-7, Get_Genital()
            DtbCommands.Get_Genital(dtu)
            dsk.make_body_mesh_drivers(Global.getBody())

            # Shape keys
            dsk.make_drivers()
            Global.deselect()
            self.pbar(60, wm)

            # Make IK controls
            drb.makeRoot()
            drb.makePole()
            drb.makeIK()
            drb.pbone_limit()
            drb.mub_ary_Z()
            self.pbar(70, wm)
            Global.setOpsMode("OBJECT")

            # Assign IK constraints
            Global.setOpsMode("OBJECT")
            Global.deselect()
            self.pbar(90, wm)
            amt = Global.getAmtr()
            for bname in DtbIKBones.bone_name:
                if bname in amt.pose.bones.keys():
                    bone = amt.pose.bones[bname]
                    for bc in bone.constraints:
                        if bc.name == bname + "_IK":
                            pbik = amt.pose.bones.get(bname + "_IK")
                            amt.pose.bones[bname].constraints[
                                bname + "_IK"
                            ].influence = 0
            drb.makeBRotationCut(
                db
            )  # lock movements around axes with zeroed limits for each bone
            Global.deselect()

            # Do custom bone shapes
            try:
                CustomBones.CBones()
            except:
                print("Custom bones currently not supported for this character")
            self.pbar(80, wm)

            # Hide and disable IK controls
            DtbIKBones.hide_ik(-1, True)
            DtbIKBones.set_scene_settings(anim.total_key_count)
            self.pbar(100, wm)
            DtbIKBones.ik_access_ban = False


            Versions.active_object(Global.getAmtr())
            Global.setOpsMode("POSE")
            drb.mub_ary_Z()
            Global.setOpsMode("OBJECT")
            drb.finishjob()

            Global.setOpsMode("OBJECT")
            if not anim.has_keyframe(Global.getAmtr()):
                pose.update_scale()
                pose.restore_pose()  # Run when no animation exists.


            if bpy.context.window_manager.morph_prefix:
                bpy.ops.rename.morphs('EXEC_DEFAULT')

            self.report({"INFO"}, "Success")
        else:
            # if dtu asset type is Animation, then skip error message
            if dtu.get_asset_type() == "Animation":
                print("DEBUG: IMP_OT_FBX.import_one(): ERROR: Global.getAmtr()=" + str(Global.getAmtr()) + ", Global.getBody()=" + str(Global.getBody()))
            else:
                self.show_error()

        wm.progress_end()
        DtbIKBones.ik_access_ban = False


    def execute(self, context):
        if bpy.context.window_manager.use_custom_path:
            self.root = Global.get_custom_path()
            print(self.root)
        if self.root == "":
            self.report({"ERROR"}, "Configuration Error: unable to determine intermediate folder path!")
            return {"FINISHED"}
        if os.path.exists(self.root) == False:
            self.report({"ERROR"}, "No exports found in intermediate folder: \"" + self.root + "\".")
            return {"FINISHED"}
        self.layGround()
        current_dir = os.getcwd()

        os.chdir(self.root)

        for i in range(10):
            fbx_adr = os.path.join(self.root, "FIG", "FIG" + str(i), "B_FIG.fbx")
            if os.path.exists(fbx_adr) == False:
                break
            Global.setHomeTown(os.path.join(self.root, "FIG/FIG" + str(i)))
            Global.load_asset_name()
            self.import_one(fbx_adr)
        self.finish_obj()
        os.chdir(current_dir)
        return {"FINISHED"}

    def show_error(self):
        Global.setOpsMode("OBJECT")
        for b in Util.myacobjs():
            bpy.data.objects.remove(b)
        filepath = os.path.join(os.path.dirname(__file__), "img", "Error.fbx")
        if os.path.exists(filepath):
            bpy.ops.import_scene.fbx(filepath=filepath)
            bpy.context.space_data.shading.type = "SOLID"
            bpy.context.space_data.shading.color_type = "TEXTURE"
        for b in Util.myacobjs():
            for i in range(3):
                b.scale[i] = 0.01


class IMP_OT_ENV(bpy.types.Operator):
    bl_idname = "import.env"
    bl_label = "Import New Env/Prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        from . import Environment

        Environment.EnvProp()
        return {"FINISHED"}


# Start of Pose Classes
class IMP_OT_POSE(bpy.types.Operator, ImportHelper):
    """Imports Daz Poses (.DUF)"""

    bl_idname = "import.pose"
    bl_label = "Import Pose"
    bl_options = {"REGISTER", "UNDO"}
    filename_ext: StringProperty(
        default=".duf",
        options={"HIDDEN"},
    )
    filter_glob: StringProperty(
        default="*.duf",
        options={"HIDDEN"},
    )
    files: bpy.props.CollectionProperty(type=DtbProperties.ImportFilesCollection)

    def execute(self, context):
        # Instance Classes
        pose = Poses.Posing("POSE")
        dirname = os.path.dirname(self.filepath)
        for i, f in enumerate(self.files, 1):
            durPath = os.path.join(dirname, f.name)
            pose.pose_copy(durPath)
        return {"FINISHED"}


class CLEAR_OT_Pose(bpy.types.Operator):

    bl_idname = "my.clear"
    bl_label = "Clear All Poses"

    def clear_all_poses(self):
        if bpy.context.object is None:
            return
        # if context is not pose mode, switch to pose mode
        if bpy.context.mode != "POSE":
            bpy.ops.object.mode_set(mode="POSE")
        # disable IK handles
        ik_undo_table = [False, False, False, False]
        try:
            for idx in range(4):
                ik_value = DtbIKBones.get_ik_influence(
                    DtbIKBones.get_influece_data_path(DtbIKBones.bone_name[idx])
                )
                if ik_value >= 0.5:
                    ik_undo_table[idx] = True
                DtbIKBones.hide_ik(idx, True)
                DtbIKBones.iktofk(idx)
                DtbIKBones.reset_pole(idx)
        except:
            pass
        if (
            Global.getAmtr() is not None
            and Versions.get_active_object() == Global.getAmtr()
        ):
            for pb in Global.getAmtr().pose.bones:
                pb.bone.select = True
        if (
            Global.getRgfy() is not None
            and Versions.get_active_object() == Global.getRgfy()
        ):
            for pb in Global.getRgfy().pose.bones:
                pb.bone.select = True
        bpy.ops.pose.transforms_clear()
        bpy.ops.pose.select_all(action="DESELECT")
        # restore IK handles
        try:
            for idx in range(4):
                if ik_undo_table[idx]:
                    # print("2023-July-02, DEBUG: clear_all_poses(): trying to restore ik_handle idx=" + str(idx))
                    DtbIKBones.hide_ik(idx, False)
                    DtbIKBones.fktoik(idx)
        except:
            pass
        bpy.ops.pose.select_all(action="DESELECT")

    def execute(self, context):
        self.clear_all_poses()
        # print("2023-July-02, DEBUG: clear_all_poses() has finished.")
        return {"FINISHED"}


# End of Pose Classes

# Start of Material Classes


class OPTIMIZE_OT_material(bpy.types.Operator):
    bl_idname = "df.optimize"
    bl_label = "Optimize Materials(WIP)"

    def execute(self, context):
        DtbMaterial.optimize_materials()
        return {"FINISHED"}


# End of Material Classes


# Start of Rigify Classes


def clear_pose_for_rigify():
    if bpy.context.object is None:
        return
    if (
        Global.getAmtr() is not None
        and Versions.get_active_object() == Global.getAmtr()
    ):
        for pb in Global.getAmtr().pose.bones:
            pb.bone.select = True
    if (
        Global.getRgfy() is not None
        and Versions.get_active_object() == Global.getRgfy()
    ):
        for pb in Global.getRgfy().pose.bones:
            pb.bone.select = True
    bpy.ops.pose.transforms_clear()
    bpy.ops.pose.select_all(action="DESELECT")


class TRANS_OT_Rigify(bpy.types.Operator):
    bl_idname = "to.rigify"
    bl_label = "To Rigify"

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        ## TODO: add G9 support
        if Global.getIsG9():
            self.report({"ERROR"}, "Genesis 9 is not supported yet in the auto Rigify tool.")
            return {"FINISHED"}
        clear_pose_for_rigify()
        Util.active_object_to_current_collection()
        dtu = DataBase.DtuLoader()
        trf = ToRigify.ToRigify(dtu)
        db = DataBase.DB()
        DtbIKBones.adjust_shin_y(2, False)
        DtbIKBones.adjust_shin_y(3, False)
        trf.toRigify(db, self)
        return {"FINISHED"}


# End of Rigify Classes
