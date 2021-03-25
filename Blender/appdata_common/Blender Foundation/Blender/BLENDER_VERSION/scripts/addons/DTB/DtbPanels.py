import bpy
import mathutils
from copy import deepcopy
from . import DazRigBlend
from . import DtbShapeKeys
from . import DataBase
from . import ToRigify
from . import Global
from . import Versions
from . import DtbDazMorph
from . import DtbOperators
from . import DtbMaterial
from . import CustomBones
from . import Poses
from . import Animations
from . import Util
from . import DtbCommands
from . import DtbIKBones
from bpy.props import EnumProperty
from bpy.props import BoolProperty
from bpy.props import StringProperty
import threading
import time


region = 'UI'
BV = Versions.getBV()


class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = region
    if BV <2.80:
        bl_category = "Tools"
    else:
        bl_category = "Daz To Blender"


class DTB_PT_MAIN(View3DPanel, bpy.types.Panel):
    bl_label = "Daz To Blender"
    bl_idname = "VIEW3D_PT_main_daz"
    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        box.operator('import.fbx', icon='POSE_HLT')
        box.operator('import.env', icon='WORLD')
        if context.object and context.active_object:
            cobj = context.active_object
            if Global.get_Body_name() == "" and Global.get_Rgfy_name() == "" and Global.get_Amtr_name() == "":
                Global.clear_variables()
                Global.decide_HERO()
            if context.object.type == 'ARMATURE' and Global.getRgfy() is None and Global.getAmtr() is None:
                Global.clear_variables()
                Global.find_AMTR(cobj)
                Global.find_RGFY(cobj)
            if context.object.type == 'MESH' and Global.getBody() is None:
                Global.clear_variables()
                Global.find_BODY(cobj)
            if cobj.mode == 'POSE':
                if Global.get_Amtr_name() != cobj.name and len(cobj.data.bones) > 90 and len(cobj.data.bones) < 200:
                    Global.clear_variables()
                    Global.find_Both(cobj)
                if Global.get_Rgfy_name() != cobj.name and len(cobj.data.bones) > 600:
                    Global.clear_variables()
                    Global.find_Both(cobj)
            elif context.object.type == 'MESH':
                if Global.get_Body_name() != "" and Global.get_Body_name() != cobj.name and len(
                        cobj.vertex_groups) > 163 \
                        and len(cobj.data.vertices) >= 16384 \
                        and len(cobj.vertex_groups) < 500 and len(cobj.data.vertices) < 321309:
                    Global.clear_variables()
                    Global.find_Both(cobj)
            if DtbIKBones.ik_access_ban == False and context.active_object.mode == 'POSE':
                l.separator()
                if Global.amIAmtr(context.object):
                    col = l.column(align=True)
                    r = col.row(align=True)
                    for i in range(len(DtbIKBones.ik_name)):
                        if i == 2:
                            r = col.row(align=True)
                        influence_data_path = DtbIKBones.get_influece_data_path(DtbIKBones.bone_name[i])
                        if influence_data_path is not None:
                            r.prop(w_mgr, 'ifk' + str(i), text=DtbIKBones.ik_name[i], toggle=True)
                    col.operator('limb.redraw',icon='LINE_DATA')
                    l.separator()
                elif Global.amIRigfy(context.object):
                    if BV<2.81:
                        row = l.row(align=True)
                        row.alignment = 'EXPAND'
                        row.operator('my.iktofk', icon="MESH_CIRCLE")
                        row.operator('my.fktoik', icon="MESH_CUBE")
                if Global.amIAmtr(context.object):
                    l.operator('to.rigify', icon='ARMATURE_DATA')
                if Global.amIRigfy(context.object):
                    if BV<2.81:
                        row = l.row(align=True)
                        row.alignment = 'EXPAND'
                        row.operator('match.ikfk')
                        row.prop(w_mgr, "br_onoff_prop", text="Joint Range", toggle=True)
                    else:
                        l.prop(w_mgr, "br_onoff_prop", text="Joint Range", toggle=True)
                
            if Global.amIBody(context.object):
                col = l.column(align=True)
                box = col.box()
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(w_mgr, "is_eye", text="Eye")
                row.prop(w_mgr, "ftime_prop", text="x 4")
                if w_mgr.is_eye:
                    box.prop(w_mgr, "eye_prop", text="")
                else:
                    box.prop(w_mgr, "skin_prop", text="")
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.operator('material.up', icon="TRIA_UP")
                row.operator('material.down', icon="TRIA_DOWN")
                box.operator('df.material')
            if context.object.type == 'MESH':
                if Global.isRiggedObject(context.object):
                    if Versions.get_active_object().mode == 'OBJECT':
                        l.prop(w_mgr, 'new_morph', text="Make New Morph")
                    row = l.row(align=True)
                    row.operator('exsport.morph', icon="TRIA_LEFT")
                    row.operator('to.sculpt', icon="MONKEY")
                    if DtbIKBones.obj_exsported != "":
                        l.label(text=DtbIKBones.obj_exsported)
                    
                l.separator()
       
        # l.operator('df.optimize', icon="MATERIAL")

class DTB_PT_POSE(View3DPanel, bpy.types.Panel):        
    bl_idname = "VIEW3D_PT_pose_daz"
    bl_label = "Pose Tools"
    
    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        l.operator('my.clear')
        l.separator()
        box.prop(w_mgr, "choose_daz_figure", text = "")
        box.operator('import.pose', icon='POSE_HLT')
        row = box.row(align=True)
        row.prop(w_mgr, "add_pose_lib", text="Add to Pose Library", toggle=False)

class DTB_PT_MATERIAL(View3DPanel, bpy.types.Panel):        
    bl_idname = "VIEW3D_PT_material_daz"
    bl_label = "Material Settings"

    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        box.label(text = "Import Settings")
        row = box.row(align=True)
        row.prop(w_mgr, "combine_materials", text="Combine Dupe Materials", toggle=False)
        
        
class DTB_PT_GENERAL(View3DPanel, bpy.types.Panel):        
    bl_idname = "VIEW3D_PT_general_daz"
    bl_label = "General Settings"

    def draw(self, context):
        l = self.layout
        box = l.box()
        w_mgr = context.window_manager
        row = box.row(align=True)
        row.prop(w_mgr, "quick_heavy", text="Quick But Heavy", toggle=False)
        l.prop(w_mgr, "scene_scale", text = "")
        l.operator('refresh.alldaz', icon='BOIDS')
        l.operator('remove.alldaz', icon='BOIDS')
        

class DTB_PT_COMMANDS(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_commands_daz"
    bl_label = "Commands List"

    def draw(self, context):
        l = self.layout
        w_mgr = context.window_manager
        l.label(text = "What does it do?:  Command")
        l.label(text = "Imports Pose:   #getpose")
        row = l.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(w_mgr, "search_prop")
        if context.object and context.active_object:
            if context.object.type == 'MESH':
                row.operator('command.search', icon='VIEWZOOM')
        else:
            row.operator('command.search', icon='HAND')