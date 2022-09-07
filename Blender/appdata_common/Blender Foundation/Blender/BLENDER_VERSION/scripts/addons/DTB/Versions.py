import bpy
import os
import math
from . import Global
from . import Util

# BV
def get_version():
    return bpy.app.version[0] + (bpy.app.version[1] / 100)


BV = get_version()
print(BV)
my_local_language = "en_US"


def getBV():
    return BV


def get_properties(dropdown):
    if BV >= 2.93:
        prop = dropdown.keywords
    else:
        prop = dropdown[1]

    return prop


def eevee_alpha(mat, mode, value):
    if BV < 2.80:
        pass
    else:
        mat.blend_method = mode
        if mode == "HASHED" or mode == "BLEND":
            if mode == "BLEND":
                mode = "CLIP"
            mat.shadow_method = mode
        if value > 0 and mode == "CLIP":
            mat.alpha_threshold = value


def rigify_finger():
    if BV >= 2.82:
        if Global.getRgfy() is not None:
            Global.finger(1)


def mix_mode(cr):
    if BV < 2.81:
        cr.use_offset = True
    else:
        cr.mix_mode = "ADD"


def pose_apply():
    if BV < 2.80:
        bpy.ops.pose.armature_apply()
    else:
        bpy.ops.pose.armature_apply(selected=True)


def select(object, flg_select):
    if object is None:
        return
    if BV < 2.80:
        object.select = flg_select
    else:
        if object.name in bpy.context.view_layer.objects:
            object.select_set(flg_select)


def subsurface_method(SNBP):
    if BV < 2.80:
        pass
    else:
        SNBP.subsurface_method = "RANDOM_WALK"


def make_sun():
    if Util.colobjs("DAZ_PUB").get("daz_sun") is not None:
        return
    if BV < 2.80:
        bpy.ops.object.lamp_add(
            type="SUN",
            radius=6.0,
            location=(140, 100, 150),
            rotation=(0.77, -0.401, -0.244),
        )
    else:
        bpy.ops.object.light_add(
            type="SUN",
            radius=6.0,
            location=(140, 100, 150),
            rotation=(0.77, -0.401, -0.244),
        )
    sun = bpy.context.object
    sun.name = "daz_sun"
    sun.data.use_nodes = True
    if sun.data.node_tree is not None:
        sun.data.node_tree.nodes["Emission"].inputs["Strength"].default_value = 5
    if BV < 2.80:
        sun.data.shadow_soft_size = 0.5
    else:
        sun.data.angle = math.radians(30)
    Util.to_other_collection([bpy.context.object], "DAZ_PUB", Util.cur_col_name())


def view_from_camera():
    if BV < 2.80:
        bpy.ops.view3d.viewnumpad(type="CAMERA")
    else:
        bpy.ops.view3d.view_camera()


def make_camera():
    if Util.colobjs("DAZ_PUB").get("daz_cam") is not None:
        return
    size = Global.getSize()
    if BV < 2.80:
        bpy.ops.object.camera_add(
            view_align=False,
            enter_editmode=False,
            location=(0.21 * size, -0.802 * size, 1.631 * size),
            rotation=(math.radians(91), 0, math.radians(15.2)),
        )
    else:
        bpy.ops.object.camera_add(
            align="WORLD",
            enter_editmode=False,
            location=(0.21 * size, -0.802 * size, 1.631 * size),
            rotation=(math.radians(91), 0, math.radians(15.2)),
        )
    Util.to_other_collection([bpy.context.object], "DAZ_PUB", Util.cur_col_name())
    bpy.context.object.name = "daz_cam"


def pivot_active_element_and_center_and_trnormal():
    if BV < 2.80:
        for space in bpy.context.area.spaces:
            if space.type == "VIEW_3D":
                space.pivot_point = "ACTIVE_ELEMENT"
                space.cursor_location = (0.0, 0.0, 0.0)
        bpy.context.space_data.transform_orientation = "NORMAL"
        bpy.context.space_data.transform_manipulators = {"TRANSLATE", "ROTATE"}
    else:
        bpy.context.scene.tool_settings.transform_pivot_point = "ACTIVE_ELEMENT"
        bpy.ops.view3d.snap_cursor_to_center()
        for s in bpy.context.scene.transform_orientation_slots:
            s.type = "NORMAL"


def orientation_to_global():
    if BV < 2.80:
        bpy.context.space_data.transform_orientation = "GLOBAL"
    else:
        for s in bpy.context.scene.transform_orientation_slots:
            s.type = "GLOBAL"


def rotate(kakudo, xyz):
    key4 = ["x", "y", "z"]
    index = -1
    for i, key in enumerate(key4):
        if xyz.lower() == key:
            index = i
            break
    if index < 0:
        return
    if BV < 2.80:
        t = [0, 0, 0]
        t[index] = 1
        bpy.ops.transform.rotate(value=math.radians(kakudo), axis=(t[0], t[1], t[2]))
    else:
        xyz = xyz.upper()
        t = [False, False, False]
        t[index] = True
        bpy.ops.transform.rotate(
            value=math.radians(kakudo),
            orient_axis=xyz,
            constraint_axis=(t[0], t[1], t[2]),
        )


def bone_display_type(amtr):
    if BV < 2.80:
        amtr.data.draw_type = "BBONE"
    else:
        amtr.data.display_type = "BBONE"


def foot_ikbone_rotate(i):
    if BV < 2.80:
        bpy.ops.transform.rotate(
            value=math.radians(17 + (i * -34)),
            axis=(0, 1, 0),
        )
        bpy.ops.transform.rotate(
            value=math.radians(-27),
            axis=(1, 0, 0),
        )
    elif BV < 2.83:
        bpy.ops.transform.rotate(
            value=math.radians(-17 + (i * 34)),
            orient_axis="Y",
            constraint_axis=(False, True, False),
        )

        bpy.ops.transform.rotate(
            value=math.radians(27),
            orient_axis="X",
            constraint_axis=(True, False, False),
        )
    else:
        ps = 17
        ms = -34
        if not Global.getIsMan():
            if Global.getIsG3():
                pass
            else:
                ps = ps + 8 * 2
                ms = ms - 16 * 2
        else:
            if Global.getIsG3() and BV > 2.83:
                ps = 0 - ps
                ms = 0 - ms
        bpy.ops.transform.rotate(
            value=math.radians(ps + (i * ms)),
            orient_axis="Y",
            constraint_axis=(False, True, False),
        )
        bpy.ops.transform.rotate(
            value=math.radians(-27),
            orient_axis="X",
            constraint_axis=(True, False, False),
        )


def show_wire(object):
    if object is None:
        return
    if BV < 2.80:
        bpy.context.object.draw_type = "WIRE"
    else:
        bpy.context.object.display_type = "WIRE"


def make_vgroup_new(object, vgname):
    if object is None:
        return
    if BV < 2.80:
        object.vertex_groups.new(vgname)
    else:
        object.vertex_groups.new(name=vgname)


def active_object_none():
    bpy.context.view_layer.objects.active = None


def active_object(object):
    if object is None:
        return
    if BV < 2.80:
        if object.name in bpy.context.scene.objects:
            if bpy.context.active_object != object:
                bpy.context.scene.objects.active = object
    else:
        if object.name in bpy.context.view_layer.objects:
            if bpy.context.view_layer.objects.active != object:
                bpy.context.view_layer.objects.active = object


def to_color_space_non(node):
    if BV < 2.80:
        node.color_space = "NONE"
    else:
        if node.image is not None and node.image.name in bpy.data.images:
            bpy.data.images[node.image.name].colorspace_settings.name = "Non-Color"


def get_active_object():
    if BV < 2.80:
        return bpy.context.active_object
    else:
        return bpy.context.view_layer.objects.active


def show_x_ray(object):
    if object is None:
        return
    if BV < 2.80:
        object.show_x_ray = True
    else:
        object.show_in_front = True


def isHide(object):
    if object is None:
        return True
    if BV < 2.80:
        return object.hide
    else:
        return object.hide_viewport


def hide_view(object, flg_hide):
    if object is None:
        return
    if BV < 2.80:
        object.hide = flg_hide
    else:
        object.hide_viewport = flg_hide


def is_hide_view(object):
    if object is None:
        return
    if BV < 2.80:
        return object.hide
    else:
        return object.hide_viewport


def set_csmooth(object, factor, repeat, vgroup):
    if object is None:
        return
    for mod in object.modifiers:
        if mod.name.startswith("CorrectiveSmooth"):
            if BV < 2.70:
                pass
            else:
                mod.factor = factor
                mod.iterations = repeat
                if vgroup is not None:
                    mod.vertex_group = vgroup
                    mod.name = vgroup
                mod.show_in_editmode = True
                mod.show_on_cage = True


def set_subdiv(object):
    if object is None:
        return
    for mod in object.modifiers:
        if BV < 2.80:
            if mod.name == "Subsurf":
                if os.name == "nt":
                    mod.use_opensubdiv = True
                mod.render_levels = 3 - Global.getSubdivLevel()
                mod.levels = 0
                if os.name == "nt":
                    bpy.context.user_preferences.system.opensubdiv_compute_type = "NONE"
        else:
            if mod.name == "Subdivision":
                mod.render_levels = 3 - Global.getSubdivLevel()
                mod.levels = 0


def set_link(object, flg_link, colname):
    if object is None:
        return
    if BV < 2.80:
        if flg_link:
            bpy.context.scene.objects.link(object)
        else:
            bpy.context.scene.objects.unlink(object)
    else:
        if flg_link:
            Util.colobjs(colname).link(object)
            if object.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(object)
        else:
            if object.name in Util.colobjs(colname):
                Util.colobjs(colname).unlink(object)


def set_debug_info(dvr):
    if dvr is None:
        return
    if BV < 2.80:
        dvr.driver.show_debug_info = True
    else:
        pass


def to_other_layer(obj_names, col_name):
    if object is None:
        return
    if BV < 2.80:
        for on in obj_names:
            ob = bpy.data.objects[on]
            if ob is None:
                continue
            ob.layers[19] = True
            for i in range(20):
                ob.layers[i] = i == 19
    else:
        col = None
        if col_name in bpy.data.collections:
            col = bpy.data.collections[col_name]
            if (col_name in bpy.context.scene.collection.children.keys()) == False:
                bpy.context.scene.collection.children.link(col)
        else:
            col = bpy.data.collections.new(col_name)
            bpy.context.scene.collection.children.link(col)
            col.hide_viewport = True
            col.hide_render = True
        for on in obj_names:
            ob = Util.colobjs(col_name).get(on)
            if ob is None:
                continue
            if (on in col.objects) == False:
                col.objects.link(ob)
            if on in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(ob)


def do_chest_upper(blist, neck_lower_head):
    if BV < 2.82:
        return blist
    else:
        for b in blist:
            if b[0] == "chestUpper":
                for i in range(len(neck_lower_head)):
                    b[4 + i] = neck_lower_head[i]
        return blist


def undo_chest_upper(rig, chest_upper_tail):
    if BV < 2.82:
        pass
    else:
        bs = ["spine_fk.003", "DEF-spine.003", "MCH-WGT-chest", "ORG-spine.003"]
        for b in bs:
            for i in range(len(chest_upper_tail)):
                rig.data.edit_bones.get(b).tail[i] = chest_upper_tail[i]


def adjust_spine23(ebones, bnames):
    if BV < 2.82:
        pass
    else:
        for b in bnames:
            if ebones.get(b) is not None:
                ebones.get(b).head[2] -= 0.01 * Global.getSize()


def msg(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        if BV < 2.8:
            self.layout.label(message)
        else:
            self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def set_international_fonts(is_internal):
    if BV < 2.80:
        bpy.context.user_preferences.system.use_international_fonts = is_internal
    else:
        bpy.context.preferences.view.use_international_fonts = is_internal


def get_defspine002_heatail():
    if BV < 2.81:
        return 0.3
    else:
        return 0.0


def set_english():
    global my_local_language
    my_local_language = get_language()
    set_language("en_US")


def reverse_language():
    set_language(my_local_language)


def set_language(lang):
    if BV < 2.80:
        bpy.context.user_preferences.system.use_international_fonts = lang != "en_US"
    elif BV < 2.83:
        bpy.context.preferences.view.use_international_fonts = lang != "en_US"
    else:
        bpy.context.preferences.view.language = lang


def get_language():
    if BV < 2.80:
        if bpy.context.user_preferences.system.use_international_fonts:
            return "ho_GE"
        else:
            return "en_US"
    elif BV < 2.83:
        if bpy.context.preferences.view.use_international_fonts:
            return "ho_GE"
        else:
            return "en_US"
    else:
        return bpy.context.preferences.view.language


def to_main_layer_active():
    if BV < 2.8:
        for i in range(20):
            for s in bpy.data.scenes:
                if "Scene" in s.name:
                    s.layers[i] = i == 0
    else:
        bpy.context.view_layer.active_layer_collection = (
            bpy.context.view_layer.layer_collection
        )


def import_obj(path):

    Global.store_ary(False)
    if BV < 2.80:
        bpy.ops.import_scene.obj(
            filepath=path,
            axis_forward="-Z",
            axis_up="Y",
            filter_glob="*.obj;*.mtl",
            use_smooth_groups=True,
            use_split_objects=True,
            use_split_groups=True,
            use_groups_as_vgroups=False,
            use_image_search=True,
            split_mode="OFF",
            global_clamp_size=0.0,
        )
    elif BV < 3.00:
        bpy.ops.import_scene.obj(
            filepath=path,
            axis_forward="-Z",
            axis_up="Y",
            filter_glob="*.obj;*.mtl",
            use_smooth_groups=True,
            use_split_objects=True,
            use_split_groups=True,
            use_groups_as_vgroups=False,
            use_image_search=True,
            split_mode="OFF",
            global_clamp_size=0.0,
        )
    else:
        bpy.ops.import_scene.obj(
            filepath=path,
            axis_forward="-Z",
            axis_up="Y",
            filter_glob="*.obj;*.mtl",
            use_smooth_groups=True,
            use_split_objects=True,
            use_split_groups=True,
            use_groups_as_vgroups=False,
            use_image_search=True,
            split_mode="OFF",
            global_clamp_size=0.0,
        )
    Global.store_ary(True)
    wnew = Global.what_new()
    if wnew in Util.myccobjs():
        return Util.myccobjs()[wnew]
    else:
        return None

# blender 3.0 break change:
# Replaced PoseBone.custom_shape_scale scalar with a PoseBone.custom_shape_scale_xyz vector
def handle_custom_shape_scale(obj, value):
    if BV < 3.00:
        obj.custom_shape_scale = value
    else:
        obj.custom_shape_scale_xyz.x = value
        obj.custom_shape_scale_xyz.y = value
        obj.custom_shape_scale_xyz.z = value

# blender 3.0 break change:
# Replaced PoseBone.custom_shape_scale scalar with a PoseBone.custom_shape_scale_xyz vector
def check_custom_shape_scale_equal(obj, value):
    if BV < 3.00:
        if obj.custom_shape_scale == value:
            return True
        else:
            return False
    else:
        if obj.custom_shape_scale_xyz.x == value and obj.custom_shape_scale_xyz.y == value and obj.custom_shape_scale_xyz.z == value:
            return True
        else:
            return False
