""" Game Readiness Tools for Blender
game_readiness_tools.py

This module contains functions for preparing 3D models for use in games and other real-time applications.  Intended for use with Daz Bridges and related tools.

Requirements:
    - Python 3.7+
    - Blender 3.6+

"""

from pathlib import Path
script_dir = str(Path( __file__ ).parent.absolute())

import os

try:
    import bpy
    import NodeArrange
except:
    print("DEBUG: blender python libraries not detected, continuing for pydoc mode.")
    

# do a mesh separation based on a vertex group, and keep the normals of the original mesh, but by "keep_normals", I mean to copy normal vectors to two arrays for the new object and the remaining object based on the vertex group or inverse of the vertex group, then for each vertex in the new mesh and remaining mesh, assign the normal vector from the corresponding array
# def separate_by_vertexgroup_keep_normals(obj, vertex_group_name):
def separate_by_vertexgroup(obj, vertex_group_name):
    # make list of all original objects
    original_objects = bpy.data.objects[:]

    # 1. check if obj is a mesh
    if obj.type == 'MESH':
        # 2. then check if the vertex group exists
        vertex_group = obj.vertex_groups.get(vertex_group_name)
        if vertex_group:
            # 3. then prepare two arrays for normal vectors, one for the new object, and one for the remaining object
            normals_new = []
            normals_remaining = []
            vertex_group_index = vertex_group.index
            # 4. copy normal vectors to the arrays based on the vertex group
            for vertex in obj.data.vertices:
                if any(group.group == vertex_group_index for group in vertex.groups):
                    normals_new.append(vertex.normal)
                else:
                    normals_remaining.append(vertex.normal)

            # 5. then perform the separation based on the vertex group by selecting the vertices in the vertex group and then separate by selection
            print("DEBUG: Separating mesh based on vertex group: ", vertex_group_name)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group=vertex_group_name)
            bpy.ops.object.vertex_group_select()
            try:
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                bpy.ops.object.mode_set(mode='OBJECT')
                print(f"ERROR: Separation failed. Make sure the vertex group ({vertex_group_name}) is not empty.")
                return

            # look for the new object by checking which object is not in the original objects
            new_obj = None
            for new_obj in bpy.data.objects:
                if new_obj not in original_objects:
                    break
            if new_obj is None:
                print("ERROR: New object not found after separation")
                return
            geo_name = vertex_group_name.replace("_GeoGroup", "_Geo")
            new_obj.name = geo_name

            # 6. then assign the normal vectors from the arrays to the new mesh and the remaining mesh
            # print("DEBUG: Applying custom normals for vertex group: ", vertex_group_name)
            # apply_custom_normals(new_obj, normals_new)
            # print("DEBUG: Applying custom normals for remaining vertices")
            # apply_custom_normals(obj, normals_remaining)

        else:
            print(f"ERROR: Vertex group '{vertex_group_name}' not found.")
            return
    else:
        print("ERROR: Active object is not a mesh.")
        return
    print(f"Separation based on vertex group '{vertex_group_name}' completed.")

def apply_custom_normals(obj, custom_normals):
    # Ensure the object is in object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.use_auto_smooth = True
    
    # Ensure that custom_normals is structured correctly:
    # It should be a list where each item is a tuple or list of three floats.
    structured_normals = [(n.x, n.y, n.z) for n in custom_normals]

    # sanity checks:
    # 1. check if number of elements in custom_normals matches number of normals in the mesh
    if len(structured_normals) != len(obj.data.vertices):
        print("ERROR: Number of custom normals does not match number of vertices in mesh")
        return
    # 2. check if the number of elements in each normal is 3
    if any(len(n) != 3 for n in structured_normals):
        print("ERROR: Each normal must be a tuple or list of three floats")
        return
    else:
        print("INFO: Number of custom normals and vertices match, len=3 for each normal")
    # 3. check if all elements in each normal are floats
    if any(not all(isinstance(v, float) for v in n) for n in structured_normals):
        print("ERROR: Each normal must be a tuple or list of three floats")
        return
    else:
        print("INFO: All elements in each normal are floats")
    # 4. check if custom normals are nearly equal to the original normals
    epsilon = 1e-6
    zero_vectors = 0
    for i, vertex in enumerate(obj.data.vertices):
        if all(abs(a - b) < epsilon for a, b in zip(vertex.normal, structured_normals[i])):
            print(f"INFO: Custom normal for vertex {i} is nearly equal to original normal")
            # set custom normal to zero vector
            structured_normals[i] = (0.0, 0.0, 0.0)
            zero_vectors += 1
    if zero_vectors > 0:
        print(f"INFO: {zero_vectors} custom normals set to zero vector")
    else:
        print("INFO: No custom normals set to zero vector")

    # Set custom normals
    obj.data.normals_split_custom_set_from_vertices(structured_normals)
    print("DEBUG: Custom normals applied to mesh: ", obj.name)

def get_vertexgroup_indices(group_name, obj=None):
    # object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Ensure your object is selected and active in Blender
    if obj is None:
        obj = bpy.context.active_object
    else:
        bpy.context.view_layer.objects.active = obj

    # List to hold the indices of vertices in the group
    vertex_indices = []

    # Ensure the object is a mesh
    if obj.type == 'MESH':       
        # Find the vertex group by name
        vertex_group = obj.vertex_groups.get(group_name)
        if vertex_group is not None:
            # Iterate through each vertex in the mesh
            for vertex in obj.data.vertices:
                for group in vertex.groups:
                    # Check if the vertex is in the vertex group
                    if group.group == vertex_group.index:
                        # Add the vertex index to the list
                        vertex_indices.append(vertex.index)
                        break  # Stop checking this vertex's groups
            
        else:
            print(f"Vertex group '{group_name}' not found.")
            return None
    else:
        print("Active object is not a mesh.")
        return None
    
    return vertex_indices


# set up vertex index files from a prepared model
def generate_vertex_index_files(obj, group_names):
    # print("DEBUG: generate_vertex_index_files():...")
    for group_name in group_names:
        vertex_indices = get_vertexgroup_indices(group_name, obj)
        # print(vertex_indices)
        filename = f"{script_dir}/vertex_indices/{group_name}_vertex_indices.txt"
        print("DEBUG: writing to file: " + filename)
        with open(filename, "w") as file:
            if vertex_indices is None:
                file.write("Vertex group not found.")
            else:
                for index in vertex_indices:
                    file.write(f"{index}\n")

# set up vertex index python data file from a prepared model
def generate_vertex_index_python_data(obj, group_names):
    # print("DEBUG: generate_vertex_index_python_data():...")
    filename = f"{script_dir}/python_vertex_indices.py"
    for group_name in group_names:
        vertex_indices = get_vertexgroup_indices(group_name, obj)
        # print(vertex_indices)
        print("DEBUG: writing to file: " + filename)
        with open(filename, "a") as file:
            if vertex_indices is None:
                file.write(f"# Vertex group '{group_name}' not found.\n\n")
            else:
                index_string_buffer = []
                for index in vertex_indices:
                    index_string_buffer += f"{index},"
                # file.write(f"{group_name} = [{index_string_buffer[:-1]}]\n\n")
                file.write(f"{group_name} = {vertex_indices}\n\n")

# create vertex groups from vertex index files
def create_vertex_groups_from_files(obj, group_names):
    # print("DEBUG: create_vertex_groups_from_files():...")
    for group_name in group_names:
        filename = f"{script_dir}/vertex_indices/{group_name}_vertex_indices.txt"
        print("DEBUG: filename: " + filename)
        if not os.path.exists(filename):
            print(f"File '{filename}' not found.")
            continue
        with open(filename, "r") as file:
            try:
                vertex_indices = [int(line) for line in file]
            except ValueError:
                print(f"Error reading file '{filename}'.")
                continue
            # Create a new vertex group
            new_group = obj.vertex_groups.new(name=group_name)
            # Assign the vertex indices to the group
            new_group.add(vertex_indices, 1.0, 'REPLACE')


def create_vertex_group(obj, group_name, vertex_indices):
    print("DEBUG: obj=" + obj.name + " creating vertex group: " + group_name + ", index count: " + str(len(vertex_indices)))
    # Create a new vertex group
    new_group = obj.vertex_groups.new(name=group_name)
    # Assign the vertex indices to the group
    new_group.add(vertex_indices, 1.0, 'REPLACE')

# remove all mesh objects other than the safe_mesh_names_list
def remove_extra_meshes(safe_mesh_names_list):
    # remove extra meshes
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            name = obj.name
            # if name.lower().contains("eyebrow") or name.lower().contains("eyelash") or name.lower().contains("tear") or name.lower().contains("moisture"):
            if name.lower() not in safe_mesh_names_list:
                print("DEBUG: Removing object " + name)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.ops.object.delete()

# remove all materials with "moisture" in the name
def remove_moisture_materials(obj):
    mat_indices_to_remove = []
    # edit mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    # clear selection
    bpy.ops.mesh.select_all(action='DESELECT')
    # object mode
    bpy.ops.object.mode_set(mode="OBJECT")
    for idx, mat_slot in enumerate(obj.material_slots):
        if  mat_slot.material and "moisture" in mat_slot.material.name.lower():
            print("DEBUG: Removing vertices with material " + mat_slot.material.name)
            mat_indices_to_remove.append(idx)
    if len(mat_indices_to_remove) > 0:
        for poly in obj.data.polygons:
            if poly.material_index in mat_indices_to_remove:
                # print("DEBUG: Removing poly with material index " + str(poly.material_index) + ", poly.index=" + str(poly.index))
                poly.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode="OBJECT")

# remove all materials other than the safe_material_names_list
def remove_extra_materials(safe_material_names_list, safe_mesh_names_list=[]):
    if bpy.context.view_layer.objects.active is None:
        bpy.context.view_layer.objects.active = bpy.data.objects[0]
    # object mode
    bpy.ops.object.mode_set(mode="OBJECT")
    materials_to_remove = []
    for obj in bpy.data.objects:
        # query for material names of each obj
        if obj.type == 'MESH':
            if obj.name.lower() in safe_mesh_names_list:
                continue
            obj_materials = obj.data.materials
            for mat in obj_materials:
                mat_name = mat.name
                if mat_name.lower() in safe_material_names_list:
                    continue
                print("DEBUG: Removing material " + mat_name + " from object " + obj.name)
                materials_to_remove.append([obj, mat])
    for obj, mat in materials_to_remove:
        # remove material
        print("DEBUG: Removing material " + mat.name + " from object " + obj.name)
        bpy.context.view_layer.objects.active = obj
        bpy.context.object.active_material_index = obj.material_slots.find(mat.name)
        bpy.ops.object.material_slot_remove()

def add_decimate_modifier_per_vertex_group(obj, vertex_group_name, decimation_ratio):
    if vertex_group_name not in obj.vertex_groups:
        print("ERROR: add_decimate_modifier_per_vertex_group(): vertex_group_name not found: " + vertex_group_name + " for object: " + obj.name)
        return
    # object mode
    bpy.ops.object.mode_set(mode="OBJECT")
    # deselect all
    bpy.ops.object.select_all(action='DESELECT')
    # select object
    obj.select_set(True)
    # add decimation modifier
    bpy.context.view_layer.objects.active = obj
    print("DEBUG: adding decimation modifier for group: " + vertex_group_name + " to object: " + obj.name)
    new_modifier = obj.modifiers.new(name=vertex_group_name, type='DECIMATE')
    new_modifier.name = vertex_group_name
    new_modifier.decimate_type = 'COLLAPSE'
    new_modifier.ratio = decimation_ratio
    new_modifier.use_collapse_triangulate = True
    new_modifier.use_symmetry = True
    new_modifier.vertex_group = vertex_group_name

def setup_world_lighting(color, strength=5.0):
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    background = nodes.new(type='ShaderNodeBackground')
    background.inputs['Color'].default_value = color
    background.inputs['Strength'].default_value = strength
    world_output = nodes.new(type='ShaderNodeOutputWorld')
    links = world.node_tree.links
    links.new(background.outputs['Background'], world_output.inputs['Surface'])
    bpy.context.scene.world = world   
    return background

def add_basic_lighting(strength=5.0):
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.data.energy = strength  # Adjust as needed
    sun.data.use_shadow = False
    # sun.data.angle = 0.523599
    return sun

def setup_bake_nodes(material, atlas):
    nodes = material.node_tree.nodes
    for node in nodes:
        node.select = False
    # Create Image Texture node for baking target
    bake_node = nodes.new(type='ShaderNodeTexImage')
    bake_node.image = atlas
    bake_node.select = True
    nodes.active = bake_node   
    return bake_node

def cleanup_bake_nodes(obj, bake_nodes, unlink_emission=False):
    for mat_slot in obj.material_slots:
        if mat_slot.material and mat_slot.material.use_nodes:
            material = mat_slot.material
            for bake_node in bake_nodes:
                if bake_node in material.node_tree.nodes.values():
                    material.node_tree.nodes.remove(bake_node)
            if unlink_emission:
                nodes = material.node_tree.nodes
                if bpy.app.version >= (4, 0, 0):
                    material.node_tree.links.remove(nodes['Principled BSDF'].inputs['Emission Color'].links[0])
                else:
                    material.node_tree.links.remove(nodes['Principled BSDF'].inputs['Emission'].links[0])
    return

def find_roughness_node(material):
    nodes = material.node_tree.nodes
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            if "Roughness" in node.inputs and node.inputs["Roughness"].is_linked:
                return node.inputs["Roughness"].links[0].from_node
    # create placeholder roughness node
    nodes = material.node_tree.nodes
    roughness_node = nodes.new(type='ShaderNodeRGB')
    if nodes.get('Principled BSDF') is not None:
        roughness_value = nodes['Principled BSDF'].inputs['Roughness'].default_value
        roughness_node.outputs['Color'].default_value = (roughness_value, roughness_value, roughness_value, 1.0)
        print(f"DEBUG: find_roughness_node(): Place holder Roughness value: {roughness_value} used for material: {material.name}")
    else:
        print(f"DEBUG: find_roughness_node(): Principled BSDF node not found for material: {material.name}")
        roughness_node.outputs['Color'].default_value = (0.5, 0.5, 0.5, 1.0)
    return roughness_node

def find_metallic_node(material):
    nodes = material.node_tree.nodes
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            if "Metallic" in node.inputs and node.inputs["Metallic"].is_linked:
                return node.inputs["Metallic"].links[0].from_node
    # create placeholder metallic node
    nodes = material.node_tree.nodes
    metallic_node = nodes.new(type='ShaderNodeRGB')
    if nodes.get('Principled BSDF') is not None:
        metallic_value = nodes['Principled BSDF'].inputs['Metallic'].default_value
        metallic_node.outputs['Color'].default_value = (metallic_value, metallic_value, metallic_value, 1.0)
        print(f"DEBUG: find_metallic_node(): Place holder Metallic value: {metallic_value} used for material: {material.name}")
    else:
        print(f"DEBUG: find_metallic_node(): Principled BSDF node not found for material: {material.name}")
        metallic_node.outputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    return metallic_node

def find_alpha_node(material, no_placeholder=False):
    nodes = material.node_tree.nodes
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            if "Alpha" in node.inputs and node.inputs["Alpha"].is_linked:
                return node.inputs["Alpha"].links[0].from_node
    # create placeholder alpha node
    nodes = material.node_tree.nodes
    alpha_node = nodes.new(type='ShaderNodeRGB')
    if nodes.get('Principled BSDF') is not None:
        alpha_value = nodes['Principled BSDF'].inputs['Alpha'].default_value
        alpha_node.outputs['Color'].default_value = (alpha_value, alpha_value, alpha_value, alpha_value)
        print(f"DEBUG: find_alpha_node(): Place holder Alpha value: {alpha_value} used for material: {material.name}")
    else:
        print(f"DEBUG: find_alpha_node(): Principled BSDF node not found for material: {material.name}")
        alpha_node.outputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    return alpha_node

def find_diffuse_node(material, no_placeholder=False):
    nodes = material.node_tree.nodes
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            if "Base Color" in node.inputs and node.inputs["Base Color"].is_linked:
                return node.inputs["Base Color"].links[0].from_node
    if no_placeholder:
        return None
    # create placeholder diffuse node
    nodes = material.node_tree.nodes
    diffuse_node = nodes.new(type='ShaderNodeRGB')
    if nodes.get('Principled BSDF') is not None:
        diffuse_node.outputs['Color'].default_value = nodes['Principled BSDF'].inputs['Base Color'].default_value
    else:
        diffuse_node.outputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    return diffuse_node

def bake_roughness_to_atlas(obj, atlas, bake_quality=4, clear_texture=False):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = bake_quality
    bpy.context.scene.cycles.time_limit = 1
    bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
    bpy.context.scene.render.bake.margin = 8

    # Setup bake nodes for each material
    bake_nodes = []
    for mat_slot in obj.material_slots:
        if mat_slot.material and mat_slot.material.use_nodes:
            print(f"Setting up bake node for material: {mat_slot.material.name}")
            bake_node = setup_bake_nodes(mat_slot.material, atlas)
            bake_nodes.append(bake_node)
        else:
            print(f"Warning: Material slot has no material or doesn't use nodes: {mat_slot.name}")    
    if not bake_nodes:
        print("Error: No bake nodes were created. Check if the object has materials with nodes.")
        return

    # Bake
    print("Starting bake operation...")
    bpy.ops.object.bake(type='ROUGHNESS', use_clear=clear_texture, margin=8)
    print("Bake operation completed.")

    # Clean up bake nodes
    cleanup_bake_nodes(obj, bake_nodes)

    return

def bake_normal_to_atlas(obj, atlas, bake_quality=4, clear_texture=False):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = bake_quality
    bpy.context.scene.cycles.time_limit = 1
    bpy.context.scene.cycles.bake_type = 'NORMAL'
    bpy.context.scene.render.bake.margin = 8

    # Setup bake nodes for each material
    bake_nodes = []
    for mat_slot in obj.material_slots:
        if mat_slot.material and mat_slot.material.use_nodes:
            print(f"Setting up bake node for material: {mat_slot.material.name}")
            bake_node = setup_bake_nodes(mat_slot.material, atlas)
            bake_nodes.append(bake_node)
        else:
            print(f"Warning: Material slot has no material or doesn't use nodes: {mat_slot.name}")    
    if not bake_nodes:
        print("Error: No bake nodes were created. Check if the object has materials with nodes.")
        return

    # Bake
    print("Starting bake operation...")
    bpy.ops.object.bake(type='NORMAL', use_clear=clear_texture, margin=8)
    print("Bake operation completed.")

    # Clean up bake nodes
    cleanup_bake_nodes(obj, bake_nodes)

    return

def bake_metallic_to_atlas(obj, atlas, bake_quality=4, clear_texture=False):
    # # check metallic is linked to principled bsdf
    # metallic_found = False
    # for mat_slot in obj.material_slots:
    #     if mat_slot.material and mat_slot.material.use_nodes:
    #         for node in mat_slot.material.node_tree.nodes:
    #             if node.type == 'BSDF_PRINCIPLED':
    #                 if "Metallic" in node.inputs and node.inputs["Metallic"].is_linked:
    #                     metallic_found = True
    #                     break
    #         break    
    # if not metallic_found:
    #     print("Warning: No metallic map found. Skipping metallic bake.")
    #     return
    
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = bake_quality
    bpy.context.scene.cycles.time_limit = 1
    bpy.context.scene.cycles.bake_type = 'EMIT'
    bpy.context.scene.render.bake.use_pass_emit = True
    bpy.context.scene.render.bake.margin = 8

    # Setup bake nodes for each material
    bake_nodes = []
    for mat_slot in obj.material_slots:
        if mat_slot.material and mat_slot.material.use_nodes:
            print(f"Setting up bake node for material: {mat_slot.material.name}")
            bake_node = setup_bake_nodes(mat_slot.material, atlas)
            bake_nodes.append(bake_node)
            material = mat_slot.material
            nodes = material.node_tree.nodes
            metallic_node = find_metallic_node(material)
            output_type = ""
            # loop through and find linked output
            for output in metallic_node.outputs:
                if output.is_linked:
                    output_type = output.name
                    break
            if output_type == "" and type(metallic_node) == bpy.types.ShaderNodeRGB:
                output_type = 'Color'
            # link image texture color to emission color of Principled BSDF node    
            if bpy.app.version >= (4, 0, 0):
                material.node_tree.links.new(metallic_node.outputs[output_type], nodes['Principled BSDF'].inputs['Emission Color'])
                nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.0
            else:
                material.node_tree.links.new(metallic_node.outputs[output_type], nodes['Principled BSDF'].inputs['Emission'])   
        else:
            print(f"Warning: Material slot has no material or doesn't use nodes: {mat_slot.name}")    
    if not bake_nodes:
        print("Error: No bake nodes were created. Check if the object has materials with nodes.")
        return

    # Bake
    print("Starting bake operation...")
    bpy.ops.object.bake(type='EMIT', use_clear=clear_texture, margin=8)
    print("Bake operation completed.")

    # Clean up bake nodes
    cleanup_bake_nodes(obj, bake_nodes, True)

    return

def bake_alpha_to_atlas(obj, atlas, bake_quality=4, clear_texture=False):
    print(f"Starting bake process for object: {obj.name}")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = bake_quality
    bpy.context.scene.cycles.time_limit = 1
    bpy.context.scene.cycles.bake_type = 'EMIT'
    bpy.context.scene.render.bake.use_pass_emit = True
    bpy.context.scene.render.bake.margin = 8

    # Setup bake nodes for each material
    bake_nodes = []
    for mat_slot in obj.material_slots:
        if mat_slot.material and mat_slot.material.use_nodes:
            print(f"Setting up bake node for material: {mat_slot.material.name}")
            bake_node = setup_bake_nodes(mat_slot.material, atlas)
            bake_nodes.append(bake_node)
            material = mat_slot.material
            nodes = material.node_tree.nodes
            alpha_node = find_alpha_node(material)
            output_type = ""
            # loop through and find linked output
            for output in alpha_node.outputs:
                if output.is_linked:
                    output_type = output.name
                    break
            if output_type == "" and type(alpha_node) == bpy.types.ShaderNodeRGB:
                output_type = 'Color'
            # link image texture color to emission color of Principled BSDF node    
            if bpy.app.version >= (4, 0, 0):
                material.node_tree.links.new(alpha_node.outputs[output_type], nodes['Principled BSDF'].inputs['Emission Color'])
                nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.0
            else:
                material.node_tree.links.new(alpha_node.outputs[output_type], nodes['Principled BSDF'].inputs['Emission'])
        else:
            print(f"Warning: Material slot has no material or doesn't use nodes: {mat_slot.name}")    
    if not bake_nodes:
        print("Error: No bake nodes were created. Check if the object has materials with nodes.")
        return

    # Bake
    print("Starting bake operation...")
    bpy.ops.object.bake(type='EMIT', pass_filter={'EMIT'}, use_clear=clear_texture, margin=8)
    print("Bake operation completed.")
    
    # Clean up bake nodes
    cleanup_bake_nodes(obj, bake_nodes, True)

    return


def bake_diffuse_to_atlas(obj, atlas, bake_quality=4, clear_texture=False):
    print(f"Starting bake process for object: {obj.name}")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = bake_quality
    bpy.context.scene.cycles.time_limit = 1
    bpy.context.scene.cycles.bake_type = 'COMBINED'
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = False
    bpy.context.scene.render.bake.use_pass_glossy = False
    bpy.context.scene.render.bake.use_pass_diffuse = False
    bpy.context.scene.render.bake.use_pass_transmission = False
    bpy.context.scene.render.bake.use_pass_emit = True
    bpy.context.scene.render.bake.margin = 8

    # Setup bake nodes for each material
    bake_nodes = []
    for mat_slot in obj.material_slots:
        if mat_slot.material and mat_slot.material.use_nodes:
            print(f"Setting up bake node for material: {mat_slot.material.name}")
            bake_node = setup_bake_nodes(mat_slot.material, atlas)
            bake_nodes.append(bake_node)
            material = mat_slot.material
            nodes = material.node_tree.nodes
            diffuse_node = find_diffuse_node(material)
            output_type = ""
            # loop through and find linked output
            for output in diffuse_node.outputs:
                if output.is_linked:
                    # check what it is linked to
                    for link in output.links:
                        if link.to_node.type == 'BSDF_PRINCIPLED' and link.to_socket.name == 'Base Color':
                            output_type = output.name
                            break
            if output_type == "" and type(diffuse_node) == bpy.types.ShaderNodeRGB:
                output_type = 'Color'
            # link image texture color to emission color of Principled BSDF node    
            if bpy.app.version >= (4, 0, 0):
                material.node_tree.links.new(diffuse_node.outputs[output_type], nodes['Principled BSDF'].inputs['Emission Color'])
                nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.0
            else:
                material.node_tree.links.new(diffuse_node.outputs[output_type], nodes['Principled BSDF'].inputs['Emission'])
        else:
            print(f"Warning: Material slot has no material or doesn't use nodes: {mat_slot.name}")    
    if not bake_nodes:
        print("Error: No bake nodes were created. Check if the object has materials with nodes.")
        return

    # Bake
    print("Starting bake operation...")
    bpy.ops.object.bake(type='EMIT', pass_filter={'EMIT'}, use_clear=clear_texture, margin=8)
    print("Bake operation completed.")
    
    # Clean up bake nodes
    cleanup_bake_nodes(obj, bake_nodes, True)

    return


def create_texture_atlas(obj_name, atlas_size=4096):
    atlas = bpy.data.images.new(name=f"{obj_name}_Atlas", width=atlas_size, height=atlas_size, alpha=True)
    atlas_material = bpy.data.materials.new(name=f"{obj_name}_Atlas_Material")
    atlas_material.use_nodes = True
    nodes = atlas_material.node_tree.nodes
    tex_node = nodes.new(type='ShaderNodeTexImage')
    tex_node.image = atlas
    atlas_material.node_tree.links.new(tex_node.outputs['Color'], nodes["Principled BSDF"].inputs['Base Color'])
    # connect alpha channel to alpha output
    atlas_material.node_tree.links.new(tex_node.outputs['Alpha'], nodes["Principled BSDF"].inputs['Alpha'])
    return atlas, atlas_material

def create_new_uv_layer(obj_or_list, name="AtlasUV"):
    if isinstance(obj_or_list, list):
        for obj in obj_or_list:
            new_uv = create_new_uv_layer(obj, name)
        return new_uv
    obj = obj_or_list
    mesh = obj.data
    new_uv = mesh.uv_layers.new(name=name)
    mesh.uv_layers.active = new_uv
    return new_uv

def repack_uv(obj_or_list):
    bpy.ops.object.select_all(action='DESELECT')
    if not isinstance(obj_or_list, list):
        obj_or_list = [obj_or_list]
    for obj in obj_or_list:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    # bpy.ops.uv.pack_islands(margin=0.001)
    bpy.ops.uv.pack_islands(udim_source='ACTIVE_UDIM', rotate=True, rotate_method='ANY', scale=True, 
                            merge_overlap=False, margin_method='FRACTION', margin=0.005,
                            pin=False, pin_method='LOCKED', shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')

def unwrap_object(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=0.001),
    bpy.ops.object.mode_set(mode='OBJECT')

def assign_atlas_to_object(obj_or_list, atlas_material):
    if isinstance(obj_or_list, list):
        for obj in obj_or_list:
            assign_atlas_to_object(obj, atlas_material)
        return
    obj = obj_or_list
    original_materials = [slot.material for slot in obj.material_slots]
    obj.data.materials.clear()
    obj.data.materials.append(atlas_material)
    return original_materials

def switch_uv(obj_or_list, new_uv_name):
    if isinstance(obj_or_list, list):
        for obj in obj_or_list:
            switch_uv(obj, new_uv_name)
        return
    obj = obj_or_list
    try:
        obj.data.uv_layers[new_uv_name].active_render = True
    except:
        print("ERROR: retrying to set uv layer: " + new_uv_name)
        try:
            obj.data.uv_layers[new_uv_name].active_render = True
        except:
            print("ERROR: Unable to set active_render for uv layer: " + new_uv_name)

def remove_other_uvs(obj_or_list, new_uv_name):
    if isinstance(obj_or_list, list):
        for obj in obj_or_list:
            remove_other_uvs(obj, new_uv_name)
        return
    obj = obj_or_list
    uv_layer_names_to_remove = []
    # remove other UVs
    uv_layer_names_to_remove = []
    for uv_layer in obj.data.uv_layers:
        current_uv_name = str(uv_layer.name)
        if current_uv_name != new_uv_name:
            uv_layer_names_to_remove.append(current_uv_name)
    
    for uv_layer_name in uv_layer_names_to_remove:
        uv_layer = obj.data.uv_layers.get(uv_layer_name)
        if uv_layer is not None:
            print("DEBUG: removing uv_layer: " + uv_layer_name)
            obj.data.uv_layers.remove(uv_layer)

def obj_uses_alpha(obj_list):
    if type(obj_list) != list:
        obj_list = [obj_list]
    for obj in obj_list:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        if "Alpha" in node.inputs and node.inputs["Alpha"].is_linked:
                            return True
                        elif "Alpha" in node.inputs and node.inputs["Alpha"].default_value != 1.0:
                            print(f"DEBUG: obj_uses_alpha({obj.name}\':\'{mat_slot.name}): Alpha default value: " + str(node.inputs["Alpha"].default_value))
                            return True
    return False

def obj_uses_diffuse(obj_list):
    if type(obj_list) != list:
        obj_list = [obj_list]
    for obj in obj_list:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        if "Base Color" in node.inputs and node.inputs["Base Color"].is_linked:
                            return True
                        elif "Base Color" in node.inputs and node.inputs["Base Color"].default_value != (0.0, 0.0, 0.0, 1.0):
                            print(f"DEBUG: obj_uses_diffuse({obj.name}\':\'{mat_slot.name}): Base Color default value: " + str(node.inputs["Base Color"].default_value))
                            return True
    return False

def obj_uses_metallic(obj_list):
    if type(obj_list) != list:
        obj_list = [obj_list]
    for obj in obj_list:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        if "Metallic" in node.inputs and node.inputs["Metallic"].is_linked:
                            return True
                        elif "Metallic" in node.inputs and node.inputs["Metallic"].default_value != 0.0:
                            print(f"DEBUG: obj_uses_metallic({obj.name}\':\'{mat_slot.name}): Metallic default value: " + str(node.inputs["Metallic"].default_value))
                            return True
    return False

def obj_uses_roughness(obj_list):
    if type(obj_list) != list:
        obj_list = [obj_list]
    for obj in obj_list:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        if "Roughness" in node.inputs and node.inputs["Roughness"].is_linked:
                            return True
                        elif "Roughness" in node.inputs and node.inputs["Roughness"].default_value != 0.5:
                            print(f"DEBUG: obj_uses_roughness({obj.name}\':\'{mat_slot.name}): Roughness default value: " + str(node.inputs["Roughness"].default_value))
                            return True
    return False

def obj_uses_normal(obj_list):
    if type(obj_list) != list:
        obj_list = [obj_list]
    for obj in obj_list:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        if "Normal" in node.inputs and node.inputs["Normal"].is_linked:
                            return True
    return False

def convert_to_atlas(obj_list, image_output_path, atlas_size=4096, bake_quality=4, make_uv=True, enable_gpu=False):
    if type(obj_list) != list:
        obj_list = [obj_list]

    # compatibility checks
    # make sure Principled BSDF is materials
    for obj in obj_list:
        if obj.visible_get() == False:
            print(f"ERROR: Object {obj.name} is not visible")
            return None, None, None
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        break
                else:
                    print(f"ERROR: No Principled BSDF node found in material: {mat_slot.material.name}")
                    return None, None, None

    obj_name = obj_list[0].name

    print(f"Starting atlas conversion for object list, using object name for atlas: {obj_name}")

    uses_alpha = obj_uses_alpha(obj_list)
    uses_diffuse = obj_uses_diffuse(obj_list)
    uses_metallic = obj_uses_metallic(obj_list)
    uses_roughness = obj_uses_roughness(obj_list)
    uses_normal = obj_uses_normal(obj_list)

    diffuse_atlas, atlas_material = create_texture_atlas(obj_name, atlas_size)
    if uses_alpha:
        alpha_atlas = bpy.data.images.new(name=f"{obj_name}_Atlas_A", width=atlas_size, height=atlas_size)
    if uses_normal:
        normal_atlas = bpy.data.images.new(name=f"{obj_name}_Atlas_N", width=atlas_size, height=atlas_size)
    if uses_metallic:
        metallic_atlas = bpy.data.images.new(name=f"{obj_name}_Atlas_M", width=atlas_size, height=atlas_size)
    if uses_roughness:
        roughness_atlas = bpy.data.images.new(name=f"{obj_name}_Atlas_R", width=atlas_size, height=atlas_size)

    if make_uv:
        new_uv_name = "AtlasUV"
        new_uv = create_new_uv_layer(obj_list, new_uv_name)
        # unwrap_object(obj)
        repack_uv(obj_list)

    if enable_gpu:
        enable_gpu_acceleration()

    for obj in obj_list:
        if uses_alpha:
            bake_alpha_to_atlas(obj, alpha_atlas, bake_quality, False)
        if uses_diffuse:
            bake_diffuse_to_atlas(obj, diffuse_atlas, bake_quality, False)
        if uses_normal:
            bake_normal_to_atlas(obj, normal_atlas, bake_quality, False)
        if uses_metallic:
            bake_metallic_to_atlas(obj, metallic_atlas, bake_quality, False)
        if uses_roughness:
            bake_roughness_to_atlas(obj, roughness_atlas, bake_quality, False)

    if uses_alpha:
        alpha_atlas_path = image_output_path + "/" + f"{obj_name}_Atlas_A.png"
        print("DEBUG: saving: " + alpha_atlas_path)
        # save atlas image to disk
        alpha_atlas.filepath_raw = alpha_atlas_path
        alpha_atlas.file_format = 'PNG'
        alpha_atlas.save()
        copy_intensity_to_alpha(alpha_atlas, diffuse_atlas)

    if uses_diffuse or uses_alpha:
        diffuse_atlas_path = image_output_path + "/" + f"{obj_name}_Atlas_D.png"
        print("DEBUG: saving: " + diffuse_atlas_path)
        # save atlas image to disk
        diffuse_atlas.filepath_raw = diffuse_atlas_path
        diffuse_atlas.file_format = 'PNG'
        diffuse_atlas.save()

    if uses_normal:
        normal_atlas_path = image_output_path + "/" + f"{obj_name}_Atlas_N.jpg"
        print("DEBUG: saving: " + normal_atlas_path)
        normal_atlas.filepath_raw = normal_atlas_path
        normal_atlas.file_format = 'JPEG'
        normal_atlas.save()

    if uses_metallic:
        metallic_atlas_path = image_output_path + "/" + f"{obj_name}_Atlas_M.jpg"
        print("DEBUG: saving: " + metallic_atlas_path)
        metallic_atlas.filepath_raw = metallic_atlas_path
        metallic_atlas.file_format = 'JPEG'
        metallic_atlas.save()

    if uses_roughness:
        roughness_atlas_path = image_output_path + "/" + f"{obj_name}_Atlas_R.jpg"
        print("DEBUG: saving: " + roughness_atlas_path)
        roughness_atlas.filepath_raw = roughness_atlas_path
        roughness_atlas.file_format = 'JPEG'
        roughness_atlas.save()

    nodes = atlas_material.node_tree.nodes
    if uses_normal:
        # link normal atlas to atlas material
        normal_tex_node = nodes.new(type='ShaderNodeTexImage')
        normal_tex_node.image = normal_atlas
        normal_tex_node.image.colorspace_settings.name = 'Non-Color'
        normal_node = nodes.new(type='ShaderNodeNormalMap')
        atlas_material.node_tree.links.new(normal_tex_node.outputs['Color'], normal_node.inputs['Color'])
        atlas_material.node_tree.links.new(normal_node.outputs['Normal'], nodes["Principled BSDF"].inputs['Normal'])
    if uses_roughness:
        # link roughness atlas to atlas material
        roughness_node = nodes.new(type='ShaderNodeTexImage')
        roughness_node.image = roughness_atlas
    #    roughness_node.image.colorspace_settings.name = 'Non-Color'
        atlas_material.node_tree.links.new(roughness_node.outputs['Color'], nodes["Principled BSDF"].inputs['Roughness'])
    if uses_metallic:
        # link metallic atlas to atlas material
        metallic_node = nodes.new(type='ShaderNodeTexImage')
        metallic_node.image = metallic_atlas
    #    metallic_node.image.colorspace_settings.name = 'Non-Color'
        atlas_material.node_tree.links.new(metallic_node.outputs['Color'], nodes["Principled BSDF"].inputs['Metallic'])
    NodeArrange.toNodeArrange(nodes)

    original_materials = assign_atlas_to_object(obj_list, atlas_material)

    if make_uv:
        switch_uv(obj_list, new_uv_name)
        remove_other_uvs(obj_list, new_uv_name)

    # # remove world lighting
    # if background:
    #     background.inputs['Strength'].default_value = 0.0
    # # bpy.context.scene.world.use_nodes = False

    print("Atlas conversion completed.")

    return diffuse_atlas, atlas_material, original_materials


import bpy
import numpy as np

def srgb_to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(x):
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * (x ** (1/2.4)) - 0.055)

def copy_intensity_to_alpha(source_image, target_image):
    # Ensure the dimensions match
    if (source_image.size[0] != target_image.size[0] and 
        source_image.size[1] != target_image.size[1]):
        raise ValueError(f"Source and target images must have the same dimensions: \
                         source=({source_image.size[0]}, {source_image.size[1]}), \
                        target=({target_image.size[0]}, {target_image.size[1]})")
    
    # Get image data as numpy arrays
    source_pixels = np.array(source_image.pixels[:]).reshape((-1, 4))
    target_pixels = np.array(target_image.pixels[:]).reshape((-1, 4))
    
    # Convert source RGB to linear space
    # source_linear = srgb_to_linear(source_pixels[:, :3])
    
    # Calculate intensity in linear space using correct coefficients
    # intensity = np.dot(source_linear, [0.2126, 0.7152, 0.0722])
    # intensity = np.dot(source_pixels[:, :3], [0.299, 0.587, 0.114])
    intensity = np.mean(source_pixels[:, :3], axis=1)

    # Copy intensity to alpha channel of target image
    target_pixels[:, 3] = intensity
    
    # Convert RGB of target back to sRGB space (alpha remains linear)
    # target_pixels[:, :3] = linear_to_srgb(target_pixels[:, :3])
    
    # Update the target image
    target_image.pixels = target_pixels.flatten()
    
    # Refresh the image in Blender
    target_image.update()



def transfer_weights(source_mesh_name, target_mesh_name):
    # Ensure objects exist
    if source_mesh_name not in bpy.data.objects or target_mesh_name not in bpy.data.objects:
        raise ValueError(f"One or both of the specified meshes do not exist in the scene: {source_mesh_name}, {target_mesh_name}")

    # Get source and target objects
    source_obj = bpy.data.objects[source_mesh_name]
    target_obj = bpy.data.objects[target_mesh_name]

    # Switch to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select and activate the target mesh
    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj

    # Delete existing vertex groups on the target mesh
    if target_obj.vertex_groups:
        bpy.ops.object.vertex_group_remove(all=True)

    # Create corresponding vertex groups in the target mesh
    for src_vg in source_obj.vertex_groups:
        target_obj.vertex_groups.new(name=src_vg.name)

    # Ensure both objects are selected and source is active
    source_obj.select_set(True)
    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = source_obj

    # Use data_transfer operator to transfer vertex group weights
    bpy.ops.object.data_transfer(
        data_type='VGROUP_WEIGHTS',
        use_create=True,
        vert_mapping='POLYINTERP_NEAREST',
        layers_select_src='ALL',
        layers_select_dst='NAME',
        mix_mode='REPLACE',
        mix_factor=1.0
    )

    # Switch back to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # get armature from source_obj and parent target_obj to same armature
    armature_name = None
    for mod in source_obj.modifiers:
        if mod.type == "ARMATURE":
            armature_name = mod.object.name
            break
    if armature_name is not None:
        # deselect all
        bpy.ops.object.select_all(action='DESELECT')
        # select target_obj
        target_obj.select_set(True)
        bpy.data.objects[armature_name].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[armature_name]
        bpy.ops.object.parent_set(type='ARMATURE')
        for mod in target_obj.modifiers:
            if mod.type == "ARMATURE":
                mod.name = armature_name

    print(f"Weights transferred successfully from {source_mesh_name} to {target_mesh_name}!")

import bmesh
from mathutils import Vector

def get_significant_vertex_group_names(obj, vertex_index, weight_threshold):
    vertex = obj.data.vertices[vertex_index]
    return [obj.vertex_groups[g.group].name for g in vertex.groups if g.weight >= weight_threshold]

def have_common_vertex_groups_per_vertex(source_obj, source_vert_index, target_obj, target_face_index, weight_threshold=0.55):
    source_groups = set(get_significant_vertex_group_names(source_obj, source_vert_index, weight_threshold))
    target_face = target_obj.data.polygons[target_face_index]
    target_groups = set()
    for vert in target_face.vertices:
        target_groups.update(get_significant_vertex_group_names(target_obj, vert, weight_threshold))
    return bool(source_groups.intersection(target_groups))

def have_common_vertex_groups_per_face(source_obj, source_face, target_obj, target_face_index, weight_threshold=0.55):
    source_groups = set()
    for vert in source_face.verts:
        source_groups.update(get_significant_vertex_group_names(source_obj, vert.index, weight_threshold))

    target_face = target_obj.data.polygons[target_face_index]
    target_groups = set()
    for vert in target_face.vertices:
        target_groups.update(get_significant_vertex_group_names(target_obj, vert, weight_threshold))

    return bool(source_groups.intersection(target_groups))

def are_normals_opposite(normal1, normal2, threshold=0.01):
    return normal1.normalized().dot(normal2.normalized()) < -1 + threshold

def are_normals_same(normal1, normal2, threshold=0.01):
    return normal1.normalized().dot(normal2.normalized()) > 1 - threshold


def autofit_mesh(source, target, fit_ratio=1.0, distance_cutoff=10.0, pass1_iterations=200, pass2_iterations=5, lock_tagged_verts=True):

    weight_threshold = 0.55
    normal_threshold = 0.01

    weight_threshold_end = 0.20
    normal_threshold_end = 0.99
    weight_threshold_step = (weight_threshold_end - weight_threshold) / pass1_iterations
    normal_threshold_step = (normal_threshold_end - normal_threshold) / pass1_iterations

    ray_cast_direction = 1
    offset_multiplier = fit_ratio
    if fit_ratio < 1:
        ray_cast_direction = -1
        offset_multiplier = 2 - fit_ratio

    num_zeros = 0

    previous_source_mesh = bmesh.new()
    previous_source_mesh.from_mesh(source.data)

    previous_source_mesh.faces.ensure_lookup_table()
    original_normals = [f.normal.copy() for f in previous_source_mesh.faces]
    tagged_verts = []
    def add_tagged_verts(v):
        if v not in tagged_verts:
            tagged_verts.append(v)

    bm_source = bmesh.new()
    bm_source.from_mesh(source.data)

    for iteration in range(pass1_iterations):
        bm_source.faces.ensure_lookup_table()
        previous_source_mesh.from_mesh(source.data)

        moved_vertices = []
        num_verts = 0
        skipped = 0
        ignored = 0
        hits = 0
        
        for i, v in enumerate(bm_source.verts):
            if v in tagged_verts and lock_tagged_verts:
                continue

            normal = Vector((0, 0, 0))
            for f in v.link_faces:
                normal += f.normal.normalized()
            normal.normalize()

            hit, loc, face_normal, face_index = target.ray_cast(v.co, normal * ray_cast_direction, distance=distance_cutoff)
            if hit:
                hits += 1
                if have_common_vertex_groups_per_vertex(source, i, target, face_index, weight_threshold) == False:
                    # ignored += 1
                    continue
                if are_normals_opposite(face_normal, normal, 0.9) == True:
                    ignored += 1
                    continue
                if are_normals_same(face_normal, normal, normal_threshold) == False:
                # if are_normals_same(face_normal, normal, 0.9) == False:
                    skipped += 1
                    continue

                offset = (loc) - (v.co)
                if v in moved_vertices:
                    continue
                v.co += offset * offset_multiplier
                moved_vertices.append(v)
                num_verts += 1
        
        # print(f"DEBUG: [{iteration}] PASS1: CHECKING FOR SELF-POKETHROUGH....")
        # bm_source.verts.ensure_lookup_table()
        # bm_source.faces.ensure_lookup_table()
        # bm_source.normal_update()
        # result2a, vertex_indexes_a = calculate_if_self_pokethrough(source, bm_source)
        # if result2a:
        #     ##############################################
        #     print(f"DEBUG:::: EXIT DUMP")
        #     print("DEBUG: vertices: " + str(vertex_indexes_a))
        #     bm_source.to_mesh(source.data)
        #     source.data.update()
        #     bm_source.free()
        #     previous_source_mesh.free()
        #     return

        #     ##############################################
        #     ## revert to position in previous mesh
        #     print(f"DEBUG: (PASS1) Self poke through detected, undoing offset for {len(vertex_indexes_a)} vertices")
        #     print("DEBUG: vertices: " + str(vertex_indexes_a))
        #     previous_source_mesh.verts.ensure_lookup_table()
        #     for vertex_index in vertex_indexes_a:
        #         current_vert = bm_source.verts[vertex_index]
        #         previous_vert = previous_source_mesh.verts[vertex_index]
        #         if current_vert.co == previous_vert.co:
        #             # this vert was not moved, undo the neighboring verts
        #             print(f"DEBUG: UNDO WARNING: vert was not moved: vertex_index={vertex_index}, current_vert={current_vert.co}, previous_vert={previous_vert.co}")
        #         else:
        #             print(f"DEBUG: UNDO: vertex_index={vertex_index}, current_vert={current_vert.co}, previous_vert={previous_vert.co}")
        #             current_vert.co = previous_vert.co
        #             add_tagged_verts(current_vert)
        #             if current_vert in moved_vertices:
        #                 moved_vertices.remove(current_vert)
        # else:
        #     print("DEBUG: (PASS1) No self poke through detected.")
        # # double check
        # result2b, vertex_indexes_b = calculate_if_self_pokethrough(source, bm_source)
        # if result2b:
        #     # find overlap between vertex_indexes and vertex_indexesb
        #     overlap = [value for value in vertex_indexes_b if value in vertex_indexes_a]
        #     not_overlap = [value for value in vertex_indexes_b if value not in vertex_indexes_a]
        #     if len(overlap) > 0:
        #         print(f"DEBUG: autofit_mesh(): PASS1: [{source.name}] Self poke through still detected for {len(overlap)} vertices. Aborting.")
        #         print("DEBUG: vertices: overlap=" + str(overlap) + ", not_overlap=" + str(not_overlap))
        #         bm_source.to_mesh(source.data)
        #         source.data.update()
        #         bm_source.free()
        #         previous_source_mesh.free()
        #         return
        #     else:
        #         print(f"**ERROR**: Secondary pokethrough created by UNDO: {len(vertex_indexes_b)} vertices")
        #         print("DEBUG: secondary vertices: " + str(vertex_indexes_b))
        #         previous_source_mesh.verts.ensure_lookup_table()
        #         for vertex_index in vertex_indexes_b:
        #             current_vert = bm_source.verts[vertex_index]
        #             if current_vert in moved_vertices:
        #                 previous_vert = previous_source_mesh.verts[vertex_index]
        #                 current_vert.co = previous_vert.co
        #                 add_tagged_verts(bm_source.verts[vertex_index])
        #                 moved_vertices.remove(current_vert)
        #             else:
        #                 print(f"****ERROR****: unfixable secondary pokethrough, aborting: {vertex_index}")
        #                 bm_source.to_mesh(source.data)
        #                 source.data.update()
        #                 bm_source.free()
        #                 previous_source_mesh.free()
        #                 return

        # print(f"DEBUG: [{iteration}] PASS1: CHECKING FOR FLIPPED FACE NORMALS....")
        bm_source.verts.ensure_lookup_table()
        bm_source.faces.ensure_lookup_table()
        bm_source.normal_update()
        result, face_indexes = calculate_if_normals_were_flipped(bm_source, original_normals)
        if result:
            print(f"DEBUG: (PASS1) Flip detected, undoing offset for {len(face_indexes)} faces")
            previous_source_mesh.faces.ensure_lookup_table()
            for face_index in face_indexes:
                current_face = bm_source.faces[face_index]
                previous_face = previous_source_mesh.faces[face_index]
                for i, current_vert in enumerate(current_face.verts):
                    current_vert.co = previous_face.verts[i].co
                    add_tagged_verts(current_vert)
                    if current_vert in moved_vertices:
                        moved_vertices.remove(current_vert)
        # double check
        result, _ = calculate_if_normals_were_flipped(bm_source, original_normals)
        if result:
            print("DEBUG: autofit_mesh(): PASS1: Flipped normals detected. Aborting.")
            bm_source.free()
            previous_source_mesh.free()
            return


        print(f"DEBUG: autofit_mesh(): PASS1: [{iteration}] hits={hits}, moved={num_verts}, skipped={skipped}, ignored={ignored}, (offset_multiplier={offset_multiplier:.2f}, fit_ratio={fit_ratio:.2f}), normal={normal_threshold:.3f}, weight={weight_threshold:.3f})")

        bm_source.to_mesh(source.data)
        source.data.update()

        weight_threshold += weight_threshold_step
        normal_threshold += normal_threshold_step

        if len(moved_vertices) == 0:
            num_zeros += 1
            # if weight_threshold >= 0.24:
            #     weight_threshold -= 0.05
            # # if normal_threshold <= 0.1:
            # if normal_threshold <= 1:
            #     normal_threshold += 0.01
            if num_zeros > 18:
                break
        else:
            num_zeros = 0

    bm_target = bmesh.new()
    bm_target.from_mesh(target.data)
    bm_target.faces.ensure_lookup_table()

    for iteration in range(pass2_iterations):
    # for iteration in range(0):
        bm_source.faces.ensure_lookup_table()
        previous_source_mesh.from_mesh(source.data)

        third_pass_faces_moved = []
        num_third_pass_faces = 0
        skipped_faces = 0
        not_skipped = 0
        total_skip_no_skip = 0
        opposite = 0
        same = 0
        not_same = 0
        vertex_moved = []
        for i, v in enumerate(bm_target.verts):
            normal = Vector((0, 0, 0))
            for f in v.link_faces:
                normal += f.normal
            normal.normalize()
            
            hit, loc, face_normal, face_index = source.ray_cast(v.co, -normal * ray_cast_direction, distance=distance_cutoff)
            if hit:
                total_skip_no_skip += 1
                if have_common_vertex_groups_per_vertex(target, i, source, face_index) == False:
                    skipped_faces += 1
                    continue
                if are_normals_opposite(face_normal, normal, 1.0) == True:
                    # skipped_faces += 1
                    opposite += 1
                    continue
                if are_normals_same(face_normal, normal, 0.01) == False:
                    # skipped_faces += 1
                    # opposite += 1
                    not_same += 1
                    continue
                same += 1

                offset = v.co - loc

                bm_source.faces.ensure_lookup_table()
                source_face = bm_source.faces[face_index]
                if source_face in third_pass_faces_moved:
                    continue

                for s_v in source_face.verts:
                    if s_v in tagged_verts:
                        continue
                    if s_v in vertex_moved:
                        continue
                    s_v.co += offset * offset_multiplier
                    vertex_moved.append(s_v)
                    pass
                third_pass_faces_moved.append(source_face)
                num_third_pass_faces += 1

        bm_source.verts.ensure_lookup_table()
        bm_source.faces.ensure_lookup_table()
        bm_source.normal_update()
        result, face_indexes = calculate_if_normals_were_flipped(bm_source, original_normals)
        if result:
            print(f"DEBUG: (PASS2) Flip detected, undoing offset for {len(face_indexes)} faces")
            previous_source_mesh.faces.ensure_lookup_table()
            for face_index in face_indexes:
                current_face = bm_source.faces[face_index]
                previous_face = previous_source_mesh.faces[face_index]
                for i, current_vert in enumerate(current_face.verts):
                    current_vert.co = previous_face.verts[i].co
                    add_tagged_verts(current_vert)
        result, _ = calculate_if_normals_were_flipped(bm_source, original_normals)
        if result:
            print("DEBUG: autofit_mesh(): PASS2: Flipped normals detected. Aborting.")
            bm_source.free()
            previous_source_mesh.free()
            bm_target.free()
            return

        # bm_source.verts.ensure_lookup_table()
        # bm_source.faces.ensure_lookup_table()
        # bm_source.normal_update()
        # result2, vertex_indexes = calculate_if_self_pokethrough(source, bm_source)
        # if result2:
        #     ## revert to position in previous mesh
        #     # print(f"DEBUG: (PASS2) Self poke through detected, undoing offset for {len(vertex_indexes)} vertices")
        #     # print("DEBUG: vertices: " + str(vertex_indexes))
        #     previous_source_mesh.verts.ensure_lookup_table()
        #     for vertex_index in vertex_indexes:
        #         current_vert = bm_source.verts[vertex_index]
        #         previous_vert = previous_source_mesh.verts[vertex_index]
        #         current_vert.co = previous_vert.co
        #         add_tagged_verts(current_vert)
        # # double check
        # result2, vertex_indexes = calculate_if_self_pokethrough(source, bm_source)
        # if result2:
        #     print(f"DEBUG: autofit_mesh(): PASS2: Self poke through still detected for {len(vertex_indexes)} vertices. Aborting.")
        #     print("DEBUG: vertices: " + str(vertex_indexes))
        #     bm_source.to_mesh(source.data)
        #     source.data.update()
        #     bm_source.free()
        #     previous_source_mesh.free()
        #     return

        print(f"DEBUG: autofit_mesh(): PASS2: [{iteration}] total_skip_no_skip={total_skip_no_skip}, moved={num_third_pass_faces}, skipped={skipped_faces}, opposite={opposite}, same={same}, not_same={not_same}")
        bm_source.to_mesh(source.data)
        source.data.update()

    tagged_vert_indexes = [v.index for v in tagged_verts]
    if lock_tagged_verts:
        lock_string = "locked verts"
    else:
        lock_string = "tagged verts"
    print(f"DEBUG: {lock_string} [{len(tagged_vert_indexes)}] = " + str(tagged_vert_indexes))

    bm_source.free()
    bm_target.free()
    previous_source_mesh.free()

    print(f"autofit_mesh(): obj={source.name} DONE")


# scale object by face normals
def scale_by_face_normals(obj, scale_factor=1.0):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    previous_mesh = bmesh.new()
    previous_mesh.from_mesh(obj.data)

    # flip normal depending on scale_factor
    normal_direction = 1
    if scale_factor < 1:
        normal_direction = -1

    bm.faces.ensure_lookup_table()
    # Store the original face normals
    original_normals = [face.normal.copy() for face in bm.faces]

    bm.verts.ensure_lookup_table()
    # calculate average distance between vertices
    total_average_distances = 0
    num_average_distances = 0
    for vert in bm.verts:
        # find linked verts
        total_distances = 0
        num_distances = 0
        for neighbor in vert.link_edges:
            # calculate distance
            distance = (neighbor.verts[0].co - neighbor.verts[1].co).length
            total_distances += distance
            num_distances += 1
        average_distances = total_distances / num_distances
        total_average_distances += average_distances
        num_average_distances += 1
    average_distance = total_average_distances / num_average_distances

    # calculate offset
    offset = average_distance * abs(1 - scale_factor)
    print(f"DEBUG: scale_by_face_normals(): offset={offset}, average_distance={average_distance}, scale_factor={scale_factor}")

    flipped_normals = False
    locked_verts = []
    def add_locked_verts(v):
        if v not in locked_verts:
            locked_verts.append(v)

    num_iterations = 200
    for iteration in range(num_iterations):
        previous_mesh.from_mesh(obj.data)
        previous_mesh.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # iterate by vertex
        for vert in bm.verts:
            if vert in locked_verts:
                continue
            normal = Vector((0, 0, 0))
            for f in vert.link_faces:
                normal += f.normal
            normal = normal.normalized() * normal_direction
            vert.co += normal * (offset/num_iterations)
        
        # calculate if normals were flipped by the operation
        result, face_indexes = calculate_if_normals_were_flipped(bm, original_normals)
        if result:
            for face_index in face_indexes:
                current_face = bm.faces[face_index]
                previous_face = previous_mesh.faces[face_index]
                for i, current_vert in enumerate(current_face.verts):
                    print(f"DEBUG: Flip detected, undoing offset for vertex {current_vert.index}")
                    current_vert.co = previous_face.verts[i].co
                    add_locked_verts(vert)
        
        # recheck for flipped normals
        result, _ = calculate_if_normals_were_flipped(bm, original_normals)
        if result:
            flipped_normals = True
            break

        if flipped_normals == False:
            bm.to_mesh(obj.data)
        else:
            break
    print(f"DEBUG: scale_by_face_normals(): iteration={iteration}, flipped_normals={flipped_normals}")
    obj.data.update()
    bm.free()
    previous_mesh.free()

    print("DEBUG: scale_by_face_normals(): DONE")


def calculate_if_normals_were_flipped(bm, original_normals):
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    face_index_array = []
    normals_flipped = False
    for i, face in enumerate(bm.faces):
        new_normal = face.normal
        original_normal = original_normals[i]
        new_normal = new_normal.normalized()
        original_normal = original_normal.normalized()
        if new_normal.dot(original_normal) < 0:  # Normal has flipped
            normals_flipped = True
            face_index_array.append(i)

    return normals_flipped, face_index_array

import mathutils

def calculate_if_self_pokethrough(obj, bm):
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    self_pokethrough = False
    vertex_index_list = []
    for i, vert in enumerate(bm.verts):
        ###### DB 2024/8/11, average of linked face normals may not be equivalent to vertex normal ==> USE VERTEX NORMAL
        # normal = Vector((0, 0, 0))
        # for f in vert.link_faces:
        #     normal += f.normal
        # normal = normal.normalized()
        #######
        normal = vert.normal
        normal = normal.normalized()

        # ray cast against self, get face and face normal
        hit, loc, face_normal, face_index = obj.ray_cast(vert.co, normal)
        if hit:
            # if loc == vert.co:
            #     # print(f"DEBUG: premature self-pokethrough detection trigger, skipping: hit loc={loc}, vert.co={vert.co}")
            #     continue
            linked_face_indexes = [f.index for f in vert.link_faces]
            if face_index in linked_face_indexes:
                # print(f"DEBUG: Invalid hit: face_index={face_index}, vert.link_faces={str(linked_face_indexes)}")
                continue
            face_normal = face_normal.normalized()
            # print(f"****** v[{vert.index}] = {vert.co}")
            if face_normal.dot(normal) < 0:
                # check if edges intersect with face
                for edge in vert.link_edges:
                    if vert.co == edge.verts[0].co:
                        point_a = edge.verts[0].co
                        point_b = edge.verts[1].co
                        vert_b = edge.verts[1]
                    else:
                        point_a = edge.verts[1].co
                        point_b = edge.verts[0].co
                        vert_b = edge.verts[0]
                    edge_vector = point_b - point_a
                    edge_vector.normalize()
                    # hit_loc = mathutils.geometry.intersect_line_plane(point_a, point_b, loc, face_normal)
                    hit2, hit_loc, _, _ = obj.ray_cast(point_a, edge_vector)
                    if hit2 and hit_loc is not None:
                        if hit_loc == point_a or (hit_loc - point_a).length < 0.0001:
                            # print(f"DEBUG: Invalid result (condition1): [{i}] hit_loc={hit_loc}, vert.co={vert.co}, skipping")
                            continue
                        if hit_loc == point_b or (hit_loc - point_b).length < 0.0001:
                            # print(f"DEBUG: Invalid result (condition2): [{i}] hit_loc={hit_loc}, neighbor={point_b}, skipping")
                            continue
                        # check if hit_loc is on the edge
                        v1 = hit_loc - point_a
                        v2 = hit_loc - point_b
                        v1.normalize()
                        v2.normalize()
                        # must be near -1
                        epsilon = 0.1
                        dot = v1.dot(v2)
                        # if abs((-1) - dot) < epsilon:
                        if dot <= 0:
                            face_verts = bm.faces[face_index].verts
                            result = mathutils.geometry.intersect_point_tri(hit_loc, face_verts[0].co, face_verts[1].co, face_verts[2].co)
                            if result is not None:
                                print(f"DEBUG: Self poke through detected for vertex {i}: vert_index={vert.index} {vert.co}, hit_loc={hit_loc}, edge=({edge.verts[0].co}, {edge.verts[1].co})")
                                # print(f"DEBUG2: dot={v1.dot(v2):5f}, v1={v1}, v2={v2}, hit_loc={hit_loc}, loc={loc}")

                                print(f"****** v[{vert.index}] = {vert.co}")
                                self_pokethrough = True
                                if i not in vertex_index_list:                                
                                    vertex_index_list.append(i)
                                # hit_loc_vert = create_vertex_at_loc(bm, hit_loc)
                                # vertex_index_list.append(hit_loc_vert.index)
                                break
                            # else:
                            #     print(f"DEBUG: Invalid result (condition4): [{i}] dot={dot:.5f}, hit_loc={hit_loc}, edge.verts[0]={edge.verts[0].co}, edge.verts[1]={edge.verts[1].co}, skipping")
                            #     self_pokethrough = True
                            #     if i not in vertex_index_list:
                            #         vertex_index_list.append(i)
                            #     if vert_b.index not in vertex_index_list:
                            #         vertex_index_list.append(vert_b.index)
                            #     hit_vert = create_vertex_at_loc(bm, hit_loc)
                            #     bm.verts.index_update()
                            #     bm.verts.ensure_lookup_table()
                            #     vertex_index_list.append(hit_vert.index)
                            #     break
                        # else:
                        #     print(f"DEBUG: Invalid result (condition3): [{i}] dot={dot:.5f}, hit_loc={hit_loc}, edge.verts[0]={edge.verts[0].co}, edge.verts[1]={edge.verts[1].co}, skipping")
                        #     self_pokethrough = True
                        #     if i not in vertex_index_list:
                        #         vertex_index_list.append(i)
                        #         break

    return self_pokethrough, vertex_index_list


def create_vertex_at_loc(bm, location):
        
    # Create a new vertex at the hit location
    new_vert = bm.verts.new(location)
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
        
    return new_vert


def remove_obscured_faces(obj, offset=0.001, threshold_list=[0.5, 1.0, 1.5]):
    if "StudioPresentationType" in obj:
        asset_type = obj["StudioPresentationType"]
        if "Hair" in asset_type:
            # hair_thresholds = [0.25]
            # if threshold_list[0] > hair_thresholds[0]:
            #     threshold_list = hair_thresholds
            # else:
            #     threshold_list = [threshold_list[0]]
            # print(f"DEBUG: Hair asset deteted: Using reduced settings for : {obj.name}, thresholds={[str(threshold_list)]}")
            print(f"DEBUG: Hair asset deteted: skipping hidden surface removal : {obj.name}")

    print(f"DEBUG: remove_obscured_faces(): obj={obj.name}, offset={offset}, threshold_list={threshold_list}")
    # Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create a bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Get the scene for ray_cast
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    faces_to_remove = []

    # for threshold in [offset*500, offset*1000, offset*2000, offset*3000, offset*4000]:
    # for threshold in [0.005, 0.010, 0.015]:
    for threshold in threshold_list:
        bm.faces.ensure_lookup_table()
        print(f"DEBUG: threshold = {threshold:.4f}")

        for face in bm.faces:
            obscured_verts = []
            if face in faces_to_remove:
                continue
            for v in face.verts:
                obscured_face_normal = []
                for f in v.link_faces:
                    vert_normal = f.normal
                    ray_origin = v.co + vert_normal * offset
                    ray_direction = vert_normal                

                    # result, location, normal, index, hit_obj, _ = scene.ray_cast(depsgraph, ray_origin, ray_direction)
                    result, location, normal, index, = obj.ray_cast(ray_origin, ray_direction)
                    # If ray hit something and it's not the current face, mark for removal
                    # if result and (hit_obj != obj or (hit_obj == obj and index != face.index)):
                    if result and index != face.index:
                        # if location is far away, it's not an occluder
                        # print(f"DEBUG: ray_cast:[{v.index}] length = {(location - ray_origin).length:.2f} vs threshold={threshold:.2f}")
                        if (location - ray_origin).length > threshold:
                            continue
                        obscured_face_normal.append(f)
                    else:
                        # print(f"DEBUG: ray_cast:[{v.index}] no hit, offset={offset}, threshold={threshold:.2f}")
                        pass
                # If all linked face normal directions are obscured, mark vertex for removal
                # print(f"DEBUG: [{v.index}] obscured_face_normal = {len(obscured_face_normal)} vs link_normals={len(v.link_faces)}")
                if len(obscured_face_normal) == len(v.link_faces):
                    obscured_verts.append(v)
            # If all verts are obscured, mark face for removal
            # print(f"DEBUG: obscured_verts = {len(obscured_verts)} vs face.verts={len(face.verts)}")
            if len(obscured_verts) == len(face.verts):
                faces_to_remove.append(face)               
    
    # Remove marked faces
    bmesh.ops.delete(bm, geom=faces_to_remove, context='FACES')
    
    # Update mesh
    bm.to_mesh(obj.data)
    obj.data.update()
    
    # Free bmesh
    bm.free()
    
    print(f"Removed {len(faces_to_remove)} obscured faces")

def get_triangle_count(obj):
    # Create a derived mesh to evaluate the modifier without applying it
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()

    # Count the number of triangles in the evaluated mesh
    triangles_count = sum(len(poly.vertices) - 2 for poly in mesh_eval.polygons)

    # Clean up the evaluated mesh data to free up memory
    obj_eval.to_mesh_clear()
    
    return triangles_count

def adjust_decimation_to_target(obj, target_triangles, tolerance=0.01):
    print(f"DEBUG: adjust_decimation_to_target(): obj={obj.name}, target_triangles={target_triangles}, tolerance={tolerance}")
    # Ensure the object has a Decimate modifier
    decimate_mod = next((mod for mod in obj.modifiers if mod.type == 'DECIMATE'), None)
    if not decimate_mod:
        decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
    
    decimate_mod.decimate_type = 'COLLAPSE'
    
    # Initial bounds for binary search
    low_ratio, high_ratio = 0.0, 1.0
    
    max_iterations = 50
    for iterations in range(max_iterations):
        # Set the current ratio
        current_ratio = (low_ratio + high_ratio) / 2
        decimate_mod.ratio = current_ratio

        # Update the mesh
        bpy.context.view_layer.update()
        
        # Get the current triangle count
        current_triangles = get_triangle_count(obj)

        print(f"DEBUG: Iteration {iterations}, Ratio: {current_ratio:.8f}, Triangles: {current_triangles}, Target: {target_triangles}")

        # Check if we're within tolerance
        if abs(current_triangles - target_triangles) <= tolerance * target_triangles:
            break
        
        # Adjust the bounds
        if current_triangles > target_triangles:
            high_ratio = current_ratio
        else:
            low_ratio = current_ratio

    print(f"Final decimation ratio: {current_ratio:.4f}, Triangles: {current_triangles}")

def enable_gpu_acceleration():
    # Enable GPU acceleration if available
    cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
    cuda_devices = cycles_prefs.get_devices_for_type('CUDA')
    optix_devices = cycles_prefs.get_devices_for_type('OPTIX')
    hip_devices = cycles_prefs.get_devices_for_type('HIP')
    
    if cuda_devices or optix_devices or hip_devices:
        print("GPU acceleration available. Enabling GPU rendering.")
        cycles_prefs.compute_device_type = 'CUDA' if cuda_devices else 'OPTIX' if optix_devices else 'HIP'
        bpy.context.scene.cycles.device = 'GPU'
        
        # Enable all available devices
        for device in cuda_devices + optix_devices + hip_devices:
            device.use = True
    else:
        print("No GPU acceleration available. Using CPU.")
        bpy.context.scene.cycles.device = 'CPU'
