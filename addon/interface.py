import bpy
import bl_ui
import rna_keymap_ui

from bpy.types import Curve, SurfaceCurve, TextCurve
from cycles.ui import find_node, find_node_input, use_branched_path, use_sample_all_lights, use_cpu

from .utilities import update, namestack, batchname, datablock, icon, preferences
from .config import remote


class namestack:


    def __init__(self, stack, context):
        self.layout = stack.layout

        if preferences(context).update_display_stack and preferences(context).update_ready:
            row = self.layout.row()
            row.alignment = 'CENTER'
            row.scale_y = 2
            row.operator('namestack.update_info', text='Update Available!', icon='ERROR', emboss=False)


        self.option = namestack.options(context)
        self.find_and_replace(context)
        self.layout.separator()
        self.stack(context)


    def find_and_replace(self, context):
        column = self.layout.column(align=True)
        row = column.row(align=True)
        row.prop(self.option, 'find', text='', icon='VIEWZOOM')

        if self.option.find:
            row.operator('namestack.clear_find', text='', icon='X')

        row.operator('namestack.options', text='', icon='FILTER')
        row.menu('namestack.specials', text='', icon='COLLAPSEMENU')

        if self.option.find:
            row = column.row(align=True)
            row.prop(self.option, 'replace', text='', icon='FILE_REFRESH')

            if self.option.replace:
                row.operator('namestack.clear_replace', text='', icon='X')

            sub = row.row(align=True)
            sub.scale_x = 0.2

            sub.operator('namestack.options', text='OK')


    def stack(self, context):
        self.stack = namestack.stack(context)

        # TODO: add display limit
        if self.stack:
            for object in self.stack['datablocks']:
                self.stack_object(self, context, object)
        else:
            self.no_stack()


    def no_stack(self):
        option = self.option.filter_options['options']

        row = self.layout.row()
        row.alignment = 'CENTER'

        # TODO: hide names that do not match search in name stack
        # if self.option.find:
        #
        #     row.label(text='No matches found')

        if option.display_mode == 'ACTIVE':
            row.label(text='No active object')
        elif option.display_mode == 'SELECTED':
            row.label(text='No selected objects')
        else:
            row.label(text='No visible objects')

        self.layout.separator()


    def specials(stack, context):
        option = namestack.options(context)
        layout = stack.layout

        layout.label(text='Find & Replace')

        layout.separator()

        layout.prop(option, 'case_sensitive')
        layout.prop(option, 'regex')

        layout.separator()

        layout.label(text='Batch Naming')

        layout.separator()

        #layout.operator('namestack.batchname', text='Transfer Names')
        #layout.operator('namestack.batchname', text='Count Names')

        #layout.separator()

        layout.operator('namestack.batchname', icon='SORTALPHA')


    class stack_object:


        def __init__(self, stack, context, object):
            self.option = namestack.options(context).filter_options['options']
            self.context = context
            self.object = object

            column = stack.layout.column(align=True)

            self.row(stack.stack['objects'], column, self.object, icon.object(self.object), emboss=True if self.object.select or self.object == self.context.active_object else False, active=not (self.object == self.context.scene.objects.active and not self.object.select))

            for type in stack.stack['objects'][object.name]['types']:
                getattr(self, type)(stack.stack['objects'][object.name][type], column)
            for _ in range(preferences(self.context).separators):
                stack.layout.separator()


        def row(self, location, column, datablock, icon, name_type='name', emboss=False, active=True):

            if datablock:
                row = column.row(align=True)
                row.active = location[getattr(datablock, name_type)]['active']

                sub = row.row(align=True if emboss else False)
                sub.scale_x = 1.5 if not emboss else 1.6
                sub.active = active

                operator = sub.operator('namestack.datablock', text='', icon=icon, emboss=emboss)
                operator.click_through = preferences(self.context).click_through
                operator.context_override = ''
                operator.object_name = self.object.name
                operator.target_name = getattr(datablock, name_type)
                operator.identifier = identifier(datablock)

                row.prop(datablock, name_type, text='')


        def groups(self, location, column):
            for group in location['datablocks']:
                self.row(location, column, group, icon('groups'))


        def grease_pencils(self, location, column):

            self.row(location, column, location['datablocks'][0], icon('grease_pencils'))

            for layer in location[location['datablocks'][0].name]['grease_pencil_layers']['datablocks']:
                self.row(location[location['datablocks'][0].name]['grease_pencil_layers'], column, layer, icon('grease_pencil_layers'), name_type='info')


        def actions(self, location, column):
            self.row(location, column, location['datablocks'][0], icon('actions'))


        def constraints(self, location, column):
            for constraint in location['datablocks']:
                self.row(location, column, constraint, icon('constraints'))


        def modifiers(self, location, column):

            for modifier in location['datablocks']:
                self.row(location, column, modifier, icon.modifier(modifier))

                if 'particle_system' in location[modifier.name]:
                    self.row(location[modifier.name]['particle_system'], column, location[modifier.name]['particle_system'][modifier.particle_system.name]['datablock'], icon.subtype('particle_system'))
                    self.row(location[modifier.name]['particle_system'][modifier.particle_system.name]['particle_settings'], column, location[modifier.name]['particle_system'][modifier.particle_system.name]['particle_settings'][modifier.particle_system.settings.name]['datablock'], 'DOT')

                    if 'textures' in location[modifier.name]['particle_system'][modifier.particle_system.name]['particle_settings'][modifier.particle_system.settings.name]:
                        for texture in location[modifier.name]['particle_system'][modifier.particle_system.name]['particle_settings'][modifier.particle_system.settings.name]['textures']['datablocks']:
                            self.row(location[modifier.name]['particle_system'][modifier.particle_system.name]['particle_settings'][modifier.particle_system.settings.name]['textures'], column,  location[modifier.name]['particle_system'][modifier.particle_system.name]['particle_settings'][modifier.particle_system.settings.name]['textures'][texture.name]['datablock'], icon('textures'))


        def object_data(self, location, column):
            self.row(location, column, location['datablocks'][0], icon.object_data(self.object), emboss=True if self.object.select or self.object == self.context.active_object else False, active=not (self.object == self.context.scene.objects.active and not self.object.select))


        def bone_groups(self, location, column):
            for group in location['datablocks']:
                self.row(location, column, group, icon('bone_groups'))


        def bones(self, location, column): # TODO: implement bones for all armatures in namestack

            if location['datablocks']:
                column.separator()

            for bone in location['datablocks']:
                active_bone = self.context.active_bone if self.context.mode == 'EDIT_ARMATURE' else self.context.active_pose_bone
                bone_selected = bone.select if self.context.mode == 'EDIT_ARMATURE' else bone.bone.select

                self.row(location, column, bone, icon('bones'), emboss=True if bone_selected or bone == active_bone else False, active=not (bone == active_bone and not bone_selected))

                if 'bone_constraints' in location[bone.name]:
                    self.constraints(location[bone.name]['bone_constraints'], column)


        def shapekeys(self, location, column):
            for shapekey in location['datablocks']:
                self.row(location, column, shapekey, icon('shapekeys'))


        def vertex_groups(self, location, column):
            for vertex_group in location['datablocks']:
                self.row(location, column, vertex_group, icon('vertex_groups'))


        def uv_maps(self, location, column):
            for uv_map in location['datablocks']:
                self.row(location, column, uv_map, icon('uv_maps'))


        def vertex_colors(self, location, column):
            for vertex_color in location['datablocks']:
                self.row(location, column, vertex_color, icon('vertex_colors'))


        def materials(self, location, column):

            for material in location['datablocks']:
                self.row(location, column, material, icon('materials'))

                if material:
                    if 'textures' in location[material.name]:
                        for texture in location[material.name]['textures']['datablocks']:
                            self.row(location[material.name]['textures'], column, texture, icon('textures'))


    class options:


        def __init__(self, operator, context):

            self.option = namestack.options(context).filter_options['options']

            split = operator.layout.column().split(percentage=0.15)
            column = split.column()
            column.prop(self.option, 'mode', expand=True)

            # self.set_height(column, 4)

            self.split = split.column(align=True)

            if self.option.mode == 'FILTERS':
                self.filters(context)
                self.display_mode(context)

            else:
                self.extra_options(context)

        @staticmethod
        def set_height(column, separators):

            for _ in range(0, separators):
                column.separator()


        def display_mode(self, context):

            row = self.split.row()

            row.prop(self.option, 'display_mode', expand=True)


        def filters(self, context):

            column = self.split.column(align=True)

            row = column.row(align=True)
            split = row.split(percentage=0.1, align=True)
            column = split.column(align=True)
            column.scale_y = 2
            column.prop(self.option, 'toggle_all', text='', icon='RADIOBUT_OFF' if not self.option.toggle_all else 'RADIOBUT_ON')

            column = split.column(align=True)
            row = column.row(align=True)
            row.scale_x = 2
            row.prop(self.option, 'groups', text='', icon=icon('groups'))
            row.prop(self.option, 'grease_pencils', text='', icon=icon('grease_pencils'))
            row.prop(self.option, 'actions', text='', icon=icon('actions'))
            row.prop(self.option, 'constraints', text='', icon=icon('constraints'))
            row.prop(self.option, 'modifiers', text='', icon=icon('modifiers'))
            row.prop(self.option, 'bones', text='', icon=icon('bones'))
            row.prop(self.option, 'bone_groups', text='', icon=icon('bone_groups'))
            row.prop(self.option, 'bone_constraints', text='', icon=icon('bone_constraints'))

            row = column.row(align=True)
            row.scale_x = 2
            row.prop(self.option, 'shapekeys', text='', icon=icon('shapekeys'))
            row.prop(self.option, 'vertex_groups', text='', icon=icon('vertex_groups'))
            row.prop(self.option, 'uv_maps', text='', icon=icon('uv_maps'))
            row.prop(self.option, 'vertex_colors', text='', icon=icon('vertex_colors'))
            row.prop(self.option, 'particle_systems', text='', icon=icon('particle_systems'))
            row.prop(self.option, 'materials', text='', icon=icon('materials'))
            row.prop(self.option, 'textures', text='', icon=icon('textures'))
            row.prop(self.option, 'images', text='', icon=icon('images'))


        def extra_options(self, context):

            row = self.split.row(align=True)
            row.prop(preferences(context), 'pin_active', toggle=True)
            row.prop(preferences(context), 'click_through', toggle=True)

            row = self.split.row(align=True)
            row.prop(preferences(context), 'location', expand=True)

            row = self.split.row()
            row.prop(preferences(context), 'filter_popup_width', text='Pop-up Width')


class datablock:

    # TODO: hide extra settings for these datablock types if there is a target and context override in datablock operator
    # target object
    # target mesh
    # target curve
    # target metaball
    # target armature
    # target lattice
    # target empty
    # target speaker
    # target camera
    # target lamp
    # target material
    # target texture
    # target particles
    # target group
    # target grease pencil
    # target grease pencil layer
    # target action
    # target constraint
    # target modifier
    # target image
    # target bone group
    # target pose bone
    # target edit bone
    # target vertex group
    # target shapekey
    # target uv map (MeshTexturePolyLayer)
    # target vertex color (MeshLoopColorLayer)
    # target material
    # target texture
    # target particle system
    # target particle settings

    # TODO: pin id, name stack needs to override but not replace pin state if it is called from name stack
        # this should work with the individual states too such as modifier, if a modifier is pinned after being called from name stack, unless the operator is called again from the stack only show the last pin state, otherwise show the new datablock target and maintain the old pin state
        #XXX: add pin history navigation


    def __init__(self, operator, context):
        self.draw_overrides = [
            'RENDERLAYER_PT_freestyle_lineset',
            'WORLD_PT_game_context_world',
            'WORLD_PT_game_world',
            'WORLD_PT_game_environment_lighting',
            'WORLD_PT_game_mist',
            'WORLD_PT_context_world',
            'WORLD_PT_preview',
            'WORLD_PT_world',
            'WORLD_PT_ambient_occlusion',
            'WORLD_PT_environment_lighting',
            'WORLD_PT_indirect_lighting',
            'WORLD_PT_gather',
            'WORLD_PT_mist',
            'CYCLES_WORLD_PT_preview',
            'CYCLES_WORLD_PT_surface',
            'CYCLES_WORLD_PT_volume',
            'CYCLES_WORLD_PT_ambient_occlusion',
            'CYCLES_WORLD_PT_mist',
            'CYCLES_WORLD_PT_ray_visibility',
            'CYCLES_WORLD_PT_settings',
            'OBJECT_PT_context_object',
            'OBJECT_PT_motion_paths',
            'OBJECT_PT_constraints',
            'DATA_PT_modifiers',
            'DATA_PT_context_curve',
            'DATA_PT_shape_curve',
            'DATA_PT_curve_texture_space',
            'DATA_PT_geometry_curve',
            'DATA_PT_pathanim',
            'DATA_PT_active_spline',
            'DATA_PT_font',
            'DATA_PT_paragraph',
            'DATA_PT_text_boxes',
            'DATA_PT_context_metaball',
            'DATA_PT_metaball',
            'DATA_PT_mball_texture_space',
            'DATA_PT_metaball_element',
            'DATA_PT_context_mesh',
            'DATA_PT_normals',
            'DATA_PT_texture_space',
            'DATA_PT_uv_texture',
            'DATA_PT_vertex_colors',
            'DATA_PT_customdata',
        ]

        self.header_overrides = [
            'WORLD_PT_game_environment_lighting',
            'WORLD_PT_game_mist',
            'WORLD_PT_ambient_occlusion',
            'WORLD_PT_environment_lighting',
            'WORLD_PT_environment_lighting',
            'WORLD_PT_indirect_lighting',
            'WORLD_PT_mist',
            'CYCLES_WORLD_PT_ambient_occlusion',
            'DATA_PT_pathanim',
        ]

        self.poll_overrides = [
            'WORLD_PT_game_context_world',
            'WORLD_PT_context_world',
            'WORLD_PT_preview',
            'WORLD_PT_world',
            'WORLD_PT_ambient_occlusion',
            'WORLD_PT_environment_lighting',
            'WORLD_PT_indirect_lighting',
            'WORLD_PT_gather',
            'WORLD_PT_mist',
            'WORLD_PT_game_context_world',
            'WORLD_PT_game_environment_lighting',
            'WORLD_PT_game_mist',
            'CYCLES_WORLD_PT_preview',
            'CYCLES_WORLD_PT_surface',
            'CYCLES_WORLD_PT_volume',
            'CYCLES_WORLD_PT_ambient_occlusion',
            'CYCLES_WORLD_PT_mist',
            'CYCLES_WORLD_PT_ray_visibility',
            'CYCLES_WORLD_PT_settings',
            'DATA_PT_context_curve',
            'DATA_PT_shape_curve',
            'DATA_PT_curve_texture_space',
            'DATA_PT_geometry_curve',
            'DATA_PT_pathanim',
            'DATA_PT_active_spline',
            'DATA_PT_font',
            'DATA_PT_paragraph',
            'DATA_PT_text_boxes',
            'DATA_PT_context_metaball',
            'DATA_PT_metaball',
            'DATA_PT_mball_texture_space',
            'DATA_PT_metaball_element',
            'DATA_PT_context_mesh',
            'DATA_PT_normals',
            'DATA_PT_texture_space',
            'DATA_PT_uv_texture',
            'DATA_PT_vertex_colors',
            'DATA_PT_customdata',
        ]

        self.operator = operator

        layout = operator.layout

        self.option = datablock.options(context)

        row = layout.row(align=True)
        row.prop(self.option, 'context', text='', expand=True)
        # row.menu('namestack.datablock_specials', text='', icon='COLLAPSEMENU') # TODO: make datablock pop-up specials menu

        box_column = layout.column()

        panels = getattr(self.option, self.option.context.lower())

        getattr(self, self.option.context.lower())(context)

        self.draw_panels(context, panels, box_column)


    def render(self, context):
        self._frame_rate_args_prev = None
        self._preset_class = None
        RENDER_PT_dimensions = bpy.types.RENDER_PT_dimensions
        self._draw_framerate_label = bpy.types.RENDER_PT_dimensions._draw_framerate_label
        self.draw_framerate = bpy.types.RENDER_PT_dimensions.draw_framerate


    def render_layer(self, context):
        self.draw_pass_type_buttons = bpy.types.RENDERLAYER_PT_layer_passes.draw_pass_type_buttons
        self.draw_edge_type_buttons = bpy.types.RENDERLAYER_PT_freestyle_lineset.draw_edge_type_buttons
        self.draw_modifier_box_header = bpy.types.RENDERLAYER_PT_freestyle_linestyle.draw_modifier_box_header
        self.draw_modifier_common = bpy.types.RENDERLAYER_PT_freestyle_linestyle.draw_modifier_common
        self.draw_modifier_box_error = bpy.types.RENDERLAYER_PT_freestyle_linestyle.draw_modifier_box_error
        self.draw_modifier_color_ramp_common = bpy.types.RENDERLAYER_PT_freestyle_linestyle.draw_modifier_color_ramp_common
        self.draw_modifier_curve_common = bpy.types.RENDERLAYER_PT_freestyle_linestyle.draw_modifier_curve_common


    def scene(self, context):
        pass


    def world(self, context):
        pass


    def object(self, context):
        pass


    def constraint(self, context):
        self.space_template = bpy.types.OBJECT_PT_constraints.space_template
        self.target_template = bpy.types.OBJECT_PT_constraints.target_template
        self.ik_template = bpy.types.OBJECT_PT_constraints.ik_template
        self._getConstraintClip = bpy.types.OBJECT_PT_constraints._getConstraintClip

        self.CAMERA_SOLVER = bpy.types.OBJECT_PT_constraints.CAMERA_SOLVER
        self.FOLLOW_TRACK = bpy.types.OBJECT_PT_constraints.FOLLOW_TRACK
        self.OBJECT_SOLVER = bpy.types.OBJECT_PT_constraints.OBJECT_SOLVER
        self.COPY_LOCATION = bpy.types.OBJECT_PT_constraints.COPY_LOCATION
        self.COPY_ROTATION = bpy.types.OBJECT_PT_constraints.COPY_ROTATION
        self.COPY_SCALE = bpy.types.OBJECT_PT_constraints.COPY_SCALE
        self.COPY_TRANSFORMS = bpy.types.OBJECT_PT_constraints.COPY_TRANSFORMS
        self.LIMIT_DISTANCE = bpy.types.OBJECT_PT_constraints.LIMIT_DISTANCE
        self.LIMIT_LOCATION = bpy.types.OBJECT_PT_constraints.LIMIT_LOCATION
        self.LIMIT_ROTATION = bpy.types.OBJECT_PT_constraints.LIMIT_ROTATION
        self.LIMIT_SCALE = bpy.types.OBJECT_PT_constraints.LIMIT_SCALE
        self.MAINTAIN_VOLUME = bpy.types.OBJECT_PT_constraints.MAINTAIN_VOLUME
        self.TRANSFORM = bpy.types.OBJECT_PT_constraints.TRANSFORM
        self.TRANSFORM_CACHE = bpy.types.OBJECT_PT_constraints.TRANSFORM_CACHE
        self.CLAMP_TO = bpy.types.OBJECT_PT_constraints.CLAMP_TO
        self.DAMPED_TRACK = bpy.types.OBJECT_PT_constraints.DAMPED_TRACK
        self.LOCKED_TRACK = bpy.types.OBJECT_PT_constraints.LOCKED_TRACK
        self.STRETCH_TO = bpy.types.OBJECT_PT_constraints.STRETCH_TO
        self.TRACK_TO = bpy.types.OBJECT_PT_constraints.TRACK_TO
        self.ACTION = bpy.types.OBJECT_PT_constraints.ACTION
        self.CHILD_OF = bpy.types.OBJECT_PT_constraints.CHILD_OF
        self.FLOOR = bpy.types.OBJECT_PT_constraints.FLOOR
        self.FOLLOW_PATH = bpy.types.OBJECT_PT_constraints.FOLLOW_PATH
        self.PIVOT = bpy.types.OBJECT_PT_constraints.PIVOT
        self.RIGID_BODY_JOINT = bpy.types.OBJECT_PT_constraints.RIGID_BODY_JOINT
        self.SHRINKWRAP = bpy.types.OBJECT_PT_constraints.SHRINKWRAP


    def modifier(self, context):
        self.ARMATURE = bpy.types.DATA_PT_modifiers.ARMATURE
        self.ARRAY = bpy.types.DATA_PT_modifiers.ARRAY
        self.BEVEL = bpy.types.DATA_PT_modifiers.BEVEL
        self.BOOLEAN = bpy.types.DATA_PT_modifiers.BOOLEAN
        self.BUILD = bpy.types.DATA_PT_modifiers.BUILD
        self.MESH_CACHE = bpy.types.DATA_PT_modifiers.MESH_CACHE
        self.MESH_SEQUENCE_CACHE = bpy.types.DATA_PT_modifiers.MESH_SEQUENCE_CACHE
        self.CAST = bpy.types.DATA_PT_modifiers.CAST
        self.CLOTH = bpy.types.DATA_PT_modifiers.CLOTH
        self.COLLISION = bpy.types.DATA_PT_modifiers.COLLISION
        self.CURVE = bpy.types.DATA_PT_modifiers.CURVE
        self.DECIMATE = bpy.types.DATA_PT_modifiers.DECIMATE
        self.DISPLACE = bpy.types.DATA_PT_modifiers.DISPLACE
        self.DYNAMIC_PAINT = bpy.types.DATA_PT_modifiers.DYNAMIC_PAINT
        self.EDGE_SPLIT = bpy.types.DATA_PT_modifiers.EDGE_SPLIT
        self.EXPLODE = bpy.types.DATA_PT_modifiers.EXPLODE
        self.FLUID_SIMULATION = bpy.types.DATA_PT_modifiers.FLUID_SIMULATION
        self.HOOK = bpy.types.DATA_PT_modifiers.HOOK
        self.LAPLACIANDEFORM = bpy.types.DATA_PT_modifiers.LAPLACIANDEFORM
        self.LAPLACIANSMOOTH = bpy.types.DATA_PT_modifiers.LAPLACIANSMOOTH
        self.LATTICE = bpy.types.DATA_PT_modifiers.LATTICE
        self.MASK = bpy.types.DATA_PT_modifiers.MASK
        self.MESH_DEFORM = bpy.types.DATA_PT_modifiers.MESH_DEFORM
        self.MIRROR = bpy.types.DATA_PT_modifiers.MIRROR
        self.MULTIRES = bpy.types.DATA_PT_modifiers.MULTIRES
        self.OCEAN = bpy.types.DATA_PT_modifiers.OCEAN
        self.PARTICLE_INSTANCE = bpy.types.DATA_PT_modifiers.PARTICLE_INSTANCE
        self.PARTICLE_SYSTEM = bpy.types.DATA_PT_modifiers.PARTICLE_SYSTEM
        self.SCREW = bpy.types.DATA_PT_modifiers.SCREW
        self.SHRINKWRAP = bpy.types.DATA_PT_modifiers.SHRINKWRAP
        self.SIMPLE_DEFORM = bpy.types.DATA_PT_modifiers.SIMPLE_DEFORM
        self.SMOKE = bpy.types.DATA_PT_modifiers.SMOKE
        self.SMOOTH = bpy.types.DATA_PT_modifiers.SMOOTH
        self.SOFT_BODY = bpy.types.DATA_PT_modifiers.SOFT_BODY
        self.SOLIDIFY = bpy.types.DATA_PT_modifiers.SOLIDIFY
        self.SUBSURF = bpy.types.DATA_PT_modifiers.SUBSURF
        self.SURFACE = bpy.types.DATA_PT_modifiers.SURFACE
        self.SURFACE_DEFORM = bpy.types.DATA_PT_modifiers.SURFACE_DEFORM
        self.UV_PROJECT = bpy.types.DATA_PT_modifiers.UV_PROJECT
        self.WARP = bpy.types.DATA_PT_modifiers.WARP
        self.WAVE = bpy.types.DATA_PT_modifiers.WAVE
        self.REMESH = bpy.types.DATA_PT_modifiers.REMESH
        self.vertex_weight_mask = bpy.types.DATA_PT_modifiers.vertex_weight_mask
        self.VERTEX_WEIGHT_EDIT = bpy.types.DATA_PT_modifiers.VERTEX_WEIGHT_EDIT
        self.VERTEX_WEIGHT_MIX = bpy.types.DATA_PT_modifiers.VERTEX_WEIGHT_MIX
        self.VERTEX_WEIGHT_PROXIMITY = bpy.types.DATA_PT_modifiers.VERTEX_WEIGHT_PROXIMITY
        self.SKIN = bpy.types.DATA_PT_modifiers.SKIN
        self.TRIANGULATE = bpy.types.DATA_PT_modifiers.TRIANGULATE
        self.UV_WARP = bpy.types.DATA_PT_modifiers.UV_WARP
        self.WIREFRAME = bpy.types.DATA_PT_modifiers.WIREFRAME
        self.DATA_TRANSFER = bpy.types.DATA_PT_modifiers.DATA_TRANSFER
        self.NORMAL_EDIT = bpy.types.DATA_PT_modifiers.NORMAL_EDIT
        self.CORRECTIVE_SMOOTH = bpy.types.DATA_PT_modifiers.CORRECTIVE_SMOOTH


    def data(self, context):
        pass

    def bone(self, context):
        pass


    def bone_constraint(self, context):
        self.space_template = bpy.types.BONE_PT_constraints.space_template
        self.target_template = bpy.types.BONE_PT_constraints.target_template
        self.ik_template = bpy.types.BONE_PT_constraints.ik_template
        self._getConstraintClip = bpy.types.BONE_PT_constraints._getConstraintClip

        self.CAMERA_SOLVER = bpy.types.BONE_PT_constraints.CAMERA_SOLVER
        self.FOLLOW_TRACK = bpy.types.BONE_PT_constraints.FOLLOW_TRACK
        self.OBJECT_SOLVER = bpy.types.BONE_PT_constraints.OBJECT_SOLVER
        self.COPY_LOCATION = bpy.types.BONE_PT_constraints.COPY_LOCATION
        self.COPY_ROTATION = bpy.types.BONE_PT_constraints.COPY_ROTATION
        self.COPY_SCALE = bpy.types.BONE_PT_constraints.COPY_SCALE
        self.COPY_TRANSFORMS = bpy.types.BONE_PT_constraints.COPY_TRANSFORMS
        self.LIMIT_DISTANCE = bpy.types.BONE_PT_constraints.LIMIT_DISTANCE
        self.LIMIT_LOCATION = bpy.types.BONE_PT_constraints.LIMIT_LOCATION
        self.LIMIT_ROTATION = bpy.types.BONE_PT_constraints.LIMIT_ROTATION
        self.LIMIT_SCALE = bpy.types.BONE_PT_constraints.LIMIT_SCALE
        self.MAINTAIN_VOLUME = bpy.types.BONE_PT_constraints.MAINTAIN_VOLUME
        self.TRANSFORM = bpy.types.BONE_PT_constraints.TRANSFORM
        self.TRANSFORM_CACHE = bpy.types.BONE_PT_constraints.TRANSFORM_CACHE
        self.CLAMP_TO = bpy.types.BONE_PT_constraints.CLAMP_TO
        self.DAMPED_TRACK = bpy.types.BONE_PT_constraints.DAMPED_TRACK
        self.IK = bpy.types.BONE_PT_constraints.IK
        self.LOCKED_TRACK = bpy.types.BONE_PT_constraints.LOCKED_TRACK
        self.SPLINE_IK = bpy.types.BONE_PT_constraints.SPLINE_IK
        self.STRETCH_TO = bpy.types.BONE_PT_constraints.STRETCH_TO
        self.TRACK_TO = bpy.types.BONE_PT_constraints.TRACK_TO
        self.ACTION = bpy.types.BONE_PT_constraints.ACTION
        self.CHILD_OF = bpy.types.BONE_PT_constraints.CHILD_OF
        self.FLOOR = bpy.types.BONE_PT_constraints.FLOOR
        self.FOLLOW_PATH = bpy.types.BONE_PT_constraints.FOLLOW_PATH
        self.PIVOT = bpy.types.BONE_PT_constraints.PIVOT
        self.SHRINKWRAP = bpy.types.BONE_PT_constraints.SHRINKWRAP


    def material(self, context):
        pass


    def texture(self, context):
        pass


    def particles(self, context):
        pass


    def physics(self, context):
        pass


    def draw_panels(self, context, panels, column):
        for panel in panels:
            type = getattr(bpy.types, panel.id)
            if hasattr(type, 'COMPAT_ENGINES'):
                if context.scene.render.engine in type.COMPAT_ENGINES:
                    if self.poll_check(context, panel, type):
                        self.draw_panel(context, column, panel, type)
            elif self.poll_check(context, panel, type):
                self.draw_panel(context, column, panel, type)


    def poll_check(self, context, panel, type):
        if panel.id_org in self.poll_overrides:
            name = 'CYCLES' + panel.id[7:] if panel.id[:7] == 'CYCLES_' else panel.id
            split = name.split('_')
            name = '_'.join(split[2:])
            if getattr(self, '{}_poll_{}'.format(split[0].lower(), name))(context):
                return True
        else:
            if hasattr(type, 'poll'):
                if type.poll(context):
                    return True
            else:
                return True
        return False


    def draw_panel(self, context, column, panel, type):
        name = 'CYCLES' + panel.id[7:] if panel.id[:7] == 'CYCLES_' else panel.id
        split = name.split('_')
        name = '_'.join(split[2:])

        draw_header = getattr(self, '{}_draw_header_{}'.format(split[0].lower(), name)) if panel.id in self.header_overrides else None
        draw = getattr(self, '{}_draw_{}'.format(split[0].lower(), name)) if panel.id in self.draw_overrides else None

        self.draw_box(context, column, panel, type, draw_header=draw_header, draw=draw)


    def draw_box(self, context, column, panel, type, draw_header=None, draw=None):
        box_column = column.column(align=self.option.context not in {'CONSTRAINT', 'MODIFIER'})

        if not panel.hide_header:
            box = box_column.box()
            row = box.row(align=True)
            row.alignment = 'LEFT'

            sub = row.row(align=True)
            sub.scale_x = 0.5
            sub.prop(panel, 'collapsed', text='', icon='TRIA_DOWN' if not panel.collapsed else 'TRIA_RIGHT', emboss=False)

            if hasattr(type, 'draw_header'):
                sub = row.row(align=True)
                sub.scale_x = 0.8
                self.layout = sub
                if draw_header:
                    draw_header(context)
                else:
                    type.draw_header(self, context)

            row.prop(panel, 'collapsed', text=panel.label, toggle=True, emboss=False) # TODO: Run this as a collapse operator, catch event and emulate panel behavior

            sub = row.row(align=True)
            sub.prop(panel, 'collapsed', text=' ', toggle=True, emboss=False)

            if not panel.collapsed:
                box = box_column.box()
                column = box.column()

                self.layout = column
                if draw is not None:
                    draw(context)
                else:
                    type.draw(self, context)

        else:
            column = box_column

            self.layout = column
            if draw is not None:
                draw(context)
            else:
                type.draw(self, context)


    #####################
    ## BEGIN OVERRIDES ##
    #####################

    ## helpers ##
    @staticmethod
    def _draw_keyframing_setting(context, layout, ks, ksp, label, toggle_prop, prop, userpref_fallback=None):
        if ksp:
            item = ksp

            if getattr(ks, toggle_prop):
                owner = ks
                propname = prop
            else:
                owner = context.user_preferences.edit
                if userpref_fallback:
                    propname = userpref_fallback
                else:
                    propname = prop
        else:
            item = ks

            owner = context.user_preferences.edit
            if userpref_fallback:
                propname = userpref_fallback
            else:
                propname = prop

        row = layout.row(align=True)
        row.prop(item, toggle_prop, text='', icon='STYLUS_PRESSURE', toggle=True)  # XXX: needs dedicated icon

        subrow = row.row()
        subrow.active = getattr(item, toggle_prop)
        if subrow.active:
            subrow.prop(item, prop, text=label)
        else:
            subrow.prop(owner, propname, text=label)

    @staticmethod
    def panel_node_draw(layout, id_data, output_type, input_name):
        if not id_data.use_nodes:
            layout.operator('namestack.use_shading_nodes', icon='NODETREE')
            return False

        ntree = id_data.node_tree

        node = find_node(id_data, output_type)
        if not node:
            layout.label(text='No output node')
        else:
            input = find_node_input(node, input_name)
            layout.template_node_view(ntree, node, input)

        return True


    ## draw headers ##
    def world_draw_header_game_environment_lighting(self, context):
        light = context.scene.world.light_settings
        self.layout.prop(light, 'use_environment_light', text='')


    def world_draw_header_game_mist(self, context):
        world = context.scene.world
        self.layout.prop(world.mist_settings, 'use_mist', text='')


    def world_draw_header_ambient_occlusion(self, context):
        light = context.scene.world.light_settings
        self.layout.prop(light, 'use_ambient_occlusion', text='')


    def world_draw_header_environment_lighting(self, context):
        light = context.scene.world.light_settings
        self.layout.prop(light, 'use_environment_light', text='')


    def world_draw_header_indirect_lighting(self, context):
        light = context.scene.world.light_settings
        self.layout.prop(light, 'use_indirect_light', text='')


    def world_draw_header_mist(self, context):
        world = context.scene.world
        self.layout.prop(world.mist_settings, 'use_mist', text='')


    def cyclesworld_draw_header_ambient_occlusion(self, context):
        light = context.scene.world.light_settings
        self.layout.prop(light, 'use_ambient_occlusion', text='')


    def data_draw_header_pathanim(self, context):
        curve = context.object.data

        self.layout.prop(curve, 'use_path', text='')


    ## draw ##
    # render layer
    def renderlayer_draw_freestyle_lineset(self, context):
        layout = self.layout

        render = context.scene.render
        render_layer = render.layers.active
        freestyle = render_layer.freestyle_settings
        lineset = freestyle.linesets.active

        layout.active = render_layer.use_freestyle

        row = layout.row()
        rows = 4 if lineset else 2
        row.template_list('RENDERLAYER_UL_linesets', '', freestyle, 'linesets', freestyle.linesets, 'active_index', rows=rows)

        sub = row.column(align=True)
        sub.operator('scene.freestyle_lineset_add', icon='ZOOMIN', text='')
        sub.operator('scene.freestyle_lineset_remove', icon='ZOOMOUT', text='')
        sub.menu('RENDER_MT_lineset_specials', icon='DOWNARROW_HLT', text='')
        if lineset:
            sub.separator()
            sub.separator()
            sub.operator('scene.freestyle_lineset_move', icon='TRIA_UP', text='').direction = 'UP'
            sub.operator('scene.freestyle_lineset_move', icon='TRIA_DOWN', text='').direction = 'DOWN'

            column = layout.column()
            column.label(text='Selection By:')
            row = column.row(align=True)
            row.prop(lineset, 'select_by_visibility', text='Visibility', toggle=True)
            row.prop(lineset, 'select_by_edge_types', text='Edge Types', toggle=True)
            row.prop(lineset, 'select_by_face_marks', text='Face Marks', toggle=True)
            row.prop(lineset, 'select_by_group', text='Group', toggle=True)
            row.prop(lineset, 'select_by_image_border', text='Image Border', toggle=True)

            if lineset.select_by_visibility:
                column.label(text='Visibility:')
                row = column.row(align=True)
                row.prop(lineset, 'visibility', expand=True)
                if lineset.visibility == 'RANGE':
                    row = column.row(align=True)
                    row.prop(lineset, 'qi_start')
                    row.prop(lineset, 'qi_end')

            if lineset.select_by_edge_types:
                column.label(text='Edge Types:')
                row = column.row()
                row.prop(lineset, 'edge_type_negation', expand=True)
                row.prop(lineset, 'edge_type_combination', expand=True)

                split = column.split()

                sub = split.column()
                self.draw_edge_type_buttons(self, sub, lineset, 'silhouette')
                self.draw_edge_type_buttons(self, sub, lineset, 'border')
                self.draw_edge_type_buttons(self, sub, lineset, 'contour')
                self.draw_edge_type_buttons(self, sub, lineset, 'suggestive_contour')
                self.draw_edge_type_buttons(self, sub, lineset, 'ridge_valley')

                sub = split.column()
                self.draw_edge_type_buttons(self, sub, lineset, 'crease')
                self.draw_edge_type_buttons(self, sub, lineset, 'edge_mark')
                self.draw_edge_type_buttons(self, sub, lineset, 'external_contour')
                self.draw_edge_type_buttons(self, sub, lineset, 'material_boundary')

            if lineset.select_by_face_marks:
                column.label(text='Face Marks:')
                row = column.row()
                row.prop(lineset, 'face_mark_negation', expand=True)
                row.prop(lineset, 'face_mark_condition', expand=True)

            if lineset.select_by_group:
                column.label(text='Group:')
                row = column.row()
                row.prop(lineset, 'group', text='')
                row.prop(lineset, 'group_negation', expand=True)


    def draw_color_modifier(self, context, modifier):
        layout = self.layout

        column = layout.column(align=True)
        self.draw_modifier_box_header(self, column.box(), modifier)
        if modifier.expanded:
            box = column.box()
            self.draw_modifier_common(self, box, modifier)

            if modifier.type == 'ALONG_STROKE':
                self.draw_modifier_color_ramp_common(self, box, modifier, False)

            elif modifier.type == 'DISTANCE_FROM_OBJECT':
                box.prop(modifier, 'target')
                self.draw_modifier_color_ramp_common(self, box, modifier, True)
                prop = box.operator('scene.freestyle_fill_range_by_selection')
                prop.type = 'COLOR'
                prop.name = modifier.name

            elif modifier.type == 'DISTANCE_FROM_CAMERA':
                self.draw_modifier_color_ramp_common(self, box, modifier, True)
                prop = box.operator('scene.freestyle_fill_range_by_selection')
                prop.type = 'COLOR'
                prop.name = modifier.name

            elif modifier.type == 'MATERIAL':
                row = box.row()
                row.prop(modifier, 'material_attribute', text='')
                sub = row.column()
                sub.prop(modifier, 'use_ramp')
                if modifier.material_attribute in {'LINE', 'DIFF', 'SPEC'}:
                    sub.active = True
                    show_ramp = modifier.use_ramp
                else:
                    sub.active = False
                    show_ramp = True
                if show_ramp:
                    self.draw_modifier_color_ramp_common(self, box, modifier, False)

            elif modifier.type == 'TANGENT':
                self.draw_modifier_color_ramp_common(self, box, modifier, False)

            elif modifier.type == 'NOISE':
                self.draw_modifier_color_ramp_common(self, box, modifier, False)
                row = box.row(align=False)
                row.prop(modifier, 'amplitude')
                row.prop(modifier, 'period')
                row.prop(modifier, 'seed')

            elif modifier.type == 'CREASE_ANGLE':
                self.draw_modifier_color_ramp_common(self, box, modifier, False)
                row = box.row(align=True)
                row.prop(modifier, 'angle_min')
                row.prop(modifier, 'angle_max')

            elif modifier.type == 'CURVATURE_3D':
                self.draw_modifier_color_ramp_common(self, box, modifier, False)
                row = box.row(align=True)
                row.prop(modifier, 'curvature_min')
                row.prop(modifier, 'curvature_max')
                freestyle = context.scene.render.layers.active.freestyle_settings
                if not freestyle.use_smoothness:
                    message = 'Enable Face Smoothness to use this modifier'
                    self.draw_modifier_box_error(self, column.box(), modifier, message)


    def draw_alpha_modifier(self, context, modifier):
        layout = self.layout

        column = layout.column(align=True)
        self.draw_modifier_box_header(self, column.box(), modifier)
        if modifier.expanded:
            box = column.box()
            self.draw_modifier_common(self, box, modifier)

            if modifier.type == 'ALONG_STROKE':
                self.draw_modifier_curve_common(self, box, modifier, False, False)

            elif modifier.type == 'DISTANCE_FROM_OBJECT':
                box.prop(modifier, 'target')
                self.draw_modifier_curve_common(self, box, modifier, True, False)
                prop = box.operator('scene.freestyle_fill_range_by_selection')
                prop.type = 'ALPHA'
                prop.name = modifier.name

            elif modifier.type == 'DISTANCE_FROM_CAMERA':
                self.draw_modifier_curve_common(self, box, modifier, True, False)
                prop = box.operator('scene.freestyle_fill_range_by_selection')
                prop.type = 'ALPHA'
                prop.name = modifier.name

            elif modifier.type == 'MATERIAL':
                box.prop(modifier, 'material_attribute', text='')
                self.draw_modifier_curve_common(self, box, modifier, False, False)

            elif modifier.type == 'TANGENT':
                self.draw_modifier_curve_common(self, box, modifier, False, False)

            elif modifier.type == 'NOISE':
                self.draw_modifier_curve_common(self, box, modifier, False, False)
                row = box.row(align=False)
                row.prop(modifier, 'amplitude')
                row.prop(modifier, 'period')
                row.prop(modifier, 'seed')

            elif modifier.type == 'CREASE_ANGLE':
                self.draw_modifier_curve_common(self, box, modifier, False, False)
                row = box.row(align=True)
                row.prop(modifier, 'angle_min')
                row.prop(modifier, 'angle_max')

            elif modifier.type == 'CURVATURE_3D':
                self.draw_modifier_curve_common(self, box, modifier, False, False)
                row = box.row(align=True)
                row.prop(modifier, 'curvature_min')
                row.prop(modifier, 'curvature_max')
                freestyle = context.scene.render.layers.active.freestyle_settings
                if not freestyle.use_smoothness:
                    message = 'Enable Face Smoothness to use this modifier'
                    self.draw_modifier_box_error(self, column.box(), modifier, message)


    def draw_thickness_modifier(self, context, modifier):
        layout = self.layout

        column = layout.column(align=True)
        self.draw_modifier_box_header(self, column.box(), modifier)
        if modifier.expanded:
            box = column.box()
            self.draw_modifier_common(self, box, modifier)

            if modifier.type == 'ALONG_STROKE':
                self.draw_modifier_curve_common(self, box, modifier, False, True)

            elif modifier.type == 'DISTANCE_FROM_OBJECT':
                box.prop(modifier, 'target')
                self.draw_modifier_curve_common(self, box, modifier, True, True)
                prop = box.operator('scene.freestyle_fill_range_by_selection')
                prop.type = 'THICKNESS'
                prop.name = modifier.name

            elif modifier.type == 'DISTANCE_FROM_CAMERA':
                self.draw_modifier_curve_common(self, box, modifier, True, True)
                prop = box.operator('scene.freestyle_fill_range_by_selection')
                prop.type = 'THICKNESS'
                prop.name = modifier.name

            elif modifier.type == 'MATERIAL':
                box.prop(modifier, 'material_attribute', text='')
                self.draw_modifier_curve_common(self, box, modifier, False, True)

            elif modifier.type == 'CALLIGRAPHY':
                box.prop(modifier, 'orientation')
                row = box.row(align=True)
                row.prop(modifier, 'thickness_min')
                row.prop(modifier, 'thickness_max')

            elif modifier.type == 'TANGENT':
                self.draw_modifier_curve_common(self, box, modifier, False, False)
                self.mapping = 'CURVE'
                row = box.row(align=True)
                row.prop(modifier, 'thickness_min')
                row.prop(modifier, 'thickness_max')

            elif modifier.type == 'NOISE':
                row = box.row(align=False)
                row.prop(modifier, 'amplitude')
                row.prop(modifier, 'period')
                row = box.row(align=False)
                row.prop(modifier, 'seed')
                row.prop(modifier, 'use_asymmetric')

            elif modifier.type == 'CREASE_ANGLE':
                self.draw_modifier_curve_common(self, box, modifier, False, False)
                row = box.row(align=True)
                row.prop(modifier, 'thickness_min')
                row.prop(modifier, 'thickness_max')
                row = box.row(align=True)
                row.prop(modifier, 'angle_min')
                row.prop(modifier, 'angle_max')

            elif modifier.type == 'CURVATURE_3D':
                self.draw_modifier_curve_common(self, box, modifier, False, False)
                row = box.row(align=True)
                row.prop(modifier, 'thickness_min')
                row.prop(modifier, 'thickness_max')
                row = box.row(align=True)
                row.prop(modifier, 'curvature_min')
                row.prop(modifier, 'curvature_max')
                freestyle = context.scene.render.layers.active.freestyle_settings
                if not freestyle.use_smoothness:
                    message = 'Enable Face Smoothness to use this modifier'
                    self.draw_modifier_box_error(self, column.box(), modifier, message)


    def draw_geometry_modifier(self, context, modifier):
        layout = self.layout

        column = layout.column(align=True)
        self.draw_modifier_box_header(self, column.box(), modifier)
        if modifier.expanded:
            box = column.box()

            if modifier.type == 'SAMPLING':
                box.prop(modifier, 'sampling')

            elif modifier.type == 'BEZIER_CURVE':
                box.prop(modifier, 'error')

            elif modifier.type == 'SINUS_DISPLACEMENT':
                split = box.split()
                column = split.column()
                column.prop(modifier, 'wavelength')
                column.prop(modifier, 'amplitude')
                column = split.column()
                column.prop(modifier, 'phase')

            elif modifier.type == 'SPATIAL_NOISE':
                split = box.split()
                column = split.column()
                column.prop(modifier, 'amplitude')
                column.prop(modifier, 'scale')
                column.prop(modifier, 'octaves')
                column = split.column()
                column.prop(modifier, 'smooth')
                column.prop(modifier, 'use_pure_random')

            elif modifier.type == 'PERLIN_NOISE_1D':
                split = box.split()
                column = split.column()
                column.prop(modifier, 'frequency')
                column.prop(modifier, 'amplitude')
                column.prop(modifier, 'seed')
                column = split.column()
                column.prop(modifier, 'octaves')
                column.prop(modifier, 'angle')

            elif modifier.type == 'PERLIN_NOISE_2D':
                split = box.split()
                column = split.column()
                column.prop(modifier, 'frequency')
                column.prop(modifier, 'amplitude')
                column.prop(modifier, 'seed')
                column = split.column()
                column.prop(modifier, 'octaves')
                column.prop(modifier, 'angle')

            elif modifier.type == 'BACKBONE_STRETCHER':
                box.prop(modifier, 'backbone_length')

            elif modifier.type == 'TIP_REMOVER':
                box.prop(modifier, 'tip_length')

            elif modifier.type == 'POLYGONIZATION':
                box.prop(modifier, 'error')

            elif modifier.type == 'GUIDING_LINES':
                box.prop(modifier, 'offset')

            elif modifier.type == 'BLUEPRINT':
                row = box.row()
                row.prop(modifier, 'shape', expand=True)
                box.prop(modifier, 'rounds')
                row = box.row()
                if modifier.shape in {'CIRCLES', 'ELLIPSES'}:
                    row.prop(modifier, 'random_radius')
                    row.prop(modifier, 'random_center')
                elif modifier.shape == 'SQUARES':
                    row.prop(modifier, 'backbone_length')
                    row.prop(modifier, 'random_backbone')

            elif modifier.type == '2D_OFFSET':
                row = box.row(align=True)
                row.prop(modifier, 'start')
                row.prop(modifier, 'end')
                row = box.row(align=True)
                row.prop(modifier, 'x')
                row.prop(modifier, 'y')

            elif modifier.type == '2D_TRANSFORM':
                box.prop(modifier, 'pivot')
                if modifier.pivot == 'PARAM':
                    box.prop(modifier, 'pivot_u')
                elif modifier.pivot == 'ABSOLUTE':
                    row = box.row(align=True)
                    row.prop(modifier, 'pivot_x')
                    row.prop(modifier, 'pivot_y')
                row = box.row(align=True)
                row.prop(modifier, 'scale_x')
                row.prop(modifier, 'scale_y')
                box.prop(modifier, 'angle')

            elif modifier.type == 'SIMPLIFICATION':
                box.prop(modifier, 'tolerance')

    # scene
    @staticmethod
    def draw_keyframing_settings(context, layout, ks, ksp):
        datablock._draw_keyframing_setting(
                context, layout, ks, ksp, 'Needed',
                'use_insertkey_override_needed', 'use_insertkey_needed',
                userpref_fallback='use_keyframe_insert_needed')

        datablock._draw_keyframing_setting(
                context, layout, ks, ksp, 'Visual',
                'use_insertkey_override_visual', 'use_insertkey_visual',
                userpref_fallback='use_visual_keying')

        datablock._draw_keyframing_setting(
                context, layout, ks, ksp, 'XYZ to RGB',
                'use_insertkey_override_xyz_to_rgb', 'use_insertkey_xyz_to_rgb')


    # world
    def world_draw_game_context_world(self, context):
        layout = self.layout

        scene = context.scene
        world = scene.world
        space = context.space_data

        split = layout.split(percentage=0.85)
        split.template_ID(scene, 'world', new='world.new')


    def world_draw_game_world(self, context):
        layout = self.layout

        world = context.scene.world

        row = layout.row()
        row.column().prop(world, 'horizon_color')
        row.column().prop(world, 'zenith_color')
        row.column().prop(world, 'ambient_color')


    def world_draw_game_environment_lighting(self, context):
        layout = self.layout

        light = context.scene.world.light_settings

        layout.active = light.use_environment_light

        split = layout.split()
        split.prop(light, 'environment_energy', text='Energy')
        split.prop(light, 'environment_color', text='')


    def world_draw_game_mist(self, context):
        layout = self.layout

        world = context.scene.world

        layout.active = world.mist_settings.use_mist

        layout.prop(world.mist_settings, 'falloff')

        row = layout.row(align=True)
        row.prop(world.mist_settings, 'start')
        row.prop(world.mist_settings, 'depth')

        layout.prop(world.mist_settings, 'intensity', text='Minimum Intensity')


    def world_draw_context_world(self, context):
        layout = self.layout

        scene = context.scene
        world = scene.world
        texture_count = world and len(world.texture_slots.keys())
        split = layout.split(percentage=0.85)
        if scene:
            split.template_ID(scene, 'world', new='world.new')
        if texture_count:
            split.label(text=str(texture_count), icon='TEXTURE')


    def world_draw_preview(self, context):
        self.layout.template_preview(context.scene.world)


    def world_draw_world(self, context):
        layout = self.layout

        world = context.scene.world

        row = layout.row()
        row.prop(world, 'use_sky_paper')
        row.prop(world, 'use_sky_blend')
        row.prop(world, 'use_sky_real')

        row = layout.row()
        row.column().prop(world, 'horizon_color')
        column = row.column()
        column.prop(world, 'zenith_color')
        column.active = world.use_sky_blend
        row.column().prop(world, 'ambient_color')

        row = layout.row()
        row.prop(world, 'exposure')
        row.prop(world, 'color_range')


    def world_draw_ambient_occlusion(self, context):
        layout = self.layout

        light = context.scene.world.light_settings

        layout.active = light.use_ambient_occlusion

        split = layout.split()
        split.prop(light, 'ao_factor', text='Factor')
        split.prop(light, 'ao_blend_type', text='')


    def world_draw_environment_lighting(self, context):
        layout = self.layout

        light = context.scene.world.light_settings

        layout.active = light.use_environment_light

        split = layout.split()
        split.prop(light, 'environment_energy', text='Energy')
        split.prop(light, 'environment_color', text='')


    def world_draw_indirect_lighting(self, context):
        layout = self.layout

        light = context.scene.world.light_settings

        layout.active = light.use_indirect_light and light.gather_method == 'APPROXIMATE'

        split = layout.split()
        split.prop(light, 'indirect_factor', text='Factor')
        split.prop(light, 'indirect_bounces', text='Bounces')

        if light.gather_method == 'RAYTRACE':
            layout.label(text='Only works with Approximate gather method')


    def world_draw_gather(self, context):
        layout = self.layout

        light = context.scene.world.light_settings

        layout.active = light.use_ambient_occlusion or light.use_environment_light or light.use_indirect_light

        layout.row().prop(light, 'gather_method', expand=True)

        split = layout.split()

        col = split.column()
        col.label(text='Attenuation:')
        if light.gather_method == 'RAYTRACE':
            col.prop(light, 'distance')
        col.prop(light, 'use_falloff')
        sub = col.row()
        sub.active = light.use_falloff
        sub.prop(light, 'falloff_strength', text='Strength')

        if light.gather_method == 'RAYTRACE':
            col = split.column()

            col.label(text='Sampling:')
            col.prop(light, 'sample_method', text='')

            sub = col.column()
            sub.prop(light, 'samples')

            if light.sample_method == 'ADAPTIVE_QMC':
                sub.prop(light, 'threshold')
                sub.prop(light, 'adapt_to_speed', slider=True)
            elif light.sample_method == 'CONSTANT_JITTERED':
                sub.prop(light, 'bias')

        if light.gather_method == 'APPROXIMATE':
            col = split.column()

            col.label(text='Sampling:')
            col.prop(light, 'passes')
            col.prop(light, 'error_threshold', text='Error')
            col.prop(light, 'use_cache')
            col.prop(light, 'correction')


    def world_draw_mist(self, context):
        layout = self.layout

        world = context.scene.world

        layout.active = world.mist_settings.use_mist

        split = layout.split()

        col = split.column()
        col.prop(world.mist_settings, 'intensity')
        col.prop(world.mist_settings, 'start')

        col = split.column()
        col.prop(world.mist_settings, 'depth')
        col.prop(world.mist_settings, 'height')

        layout.prop(world.mist_settings, 'falloff')


    def cyclesworld_draw_preview(self, context):
        self.layout.template_preview(context.scene.world)


    def cyclesworld_draw_surface(self, context):
        layout = self.layout

        world = context.scene.world

        if not self.panel_node_draw(layout, world, 'OUTPUT_WORLD', 'Surface'):
            row = layout.row()
            row.prop(world, 'horizon_color', text='Color')


    def cyclesworld_draw_volume(self, context):
        layout = self.layout

        world = context.scene.world
        self.panel_node_draw(layout, world, 'OUTPUT_WORLD', 'Volume')


    def cyclesworld_draw_ambient_occlusion(self, context):
        layout = self.layout

        light = context.scene.world.light_settings
        scene = context.scene

        row = layout.row()
        sub = row.row()
        sub.active = light.use_ambient_occlusion or scene.render.use_simplify
        sub.prop(light, 'ao_factor', text='Factor')
        row.prop(light, 'distance', text='Distance')


    def cyclesworld_draw_mist(self, context):
        layout = self.layout

        world = context.scene.world

        split = layout.split(align=True)
        split.prop(world.mist_settings, 'start')
        split.prop(world.mist_settings, 'depth')

        layout.prop(world.mist_settings, 'falloff')


    def cyclesworld_draw_ray_visibility(self, context):
        layout = self.layout

        world = context.scene.world
        visibility = world.cycles_visibility

        flow = layout.column_flow()

        flow.prop(visibility, 'camera')
        flow.prop(visibility, 'diffuse')
        flow.prop(visibility, 'glossy')
        flow.prop(visibility, 'transmission')
        flow.prop(visibility, 'scatter')


    def cyclesworld_draw_settings(self, context):
        layout = self.layout

        world = context.scene.world
        cworld = world.cycles
        # cscene = context.scene.cycles

        split = layout.split()

        col = split.column()

        col.label(text='Surface:')
        col.prop(cworld, 'sample_as_light', text='Multiple Importance')

        sub = col.column(align=True)
        sub.active = cworld.sample_as_light
        sub.prop(cworld, 'sample_map_resolution')
        if use_branched_path(context):
            subsub = sub.row(align=True)
            subsub.active = use_sample_all_lights(context)
            subsub.prop(cworld, 'samples')
        sub.prop(cworld, 'max_bounces')

        col = split.column()
        col.label(text='Volume:')
        sub = col.column()
        sub.active = use_cpu(context)
        sub.prop(cworld, 'volume_sampling', text='')
        col.prop(cworld, 'volume_interpolation', text='')
        col.prop(cworld, 'homogeneous_volume', text='Homogeneous')


    # object
    def object_draw_context_object(self, context):
        layout = self.layout
        row = layout.row()
        row.template_ID(context.scene.objects, 'active')


    def object_draw_motion_paths(self, context):
        ob = context.object
        avs = ob.animation_visualization
        mpath = ob.motion_path

        bl_ui.properties_animviz.MotionPathButtonsPanel.draw_settings(self, context, avs, mpath)


    def object_draw_constraints(self, context):
        layout = self.layout

        object = context.active_object

        layout.operator_menu_enum('object.constraint_add', 'type')

        for constraint in object.constraints:
            box = layout.template_constraint(constraint)
            if box:
                getattr(self, constraint.type)(self, context, box, constraint)

                if constraint.type not in {'RIGID_BODY_JOIN', 'NULL'}:
                    box.prop(constraint, 'influence')


    # data
    def data_draw_modifiers(self, context):
        layout = self.layout

        object = context.active_object

        layout.operator_menu_enum('object.modifier_add', 'type')

        for modifier in object.modifiers:
            box = layout.template_modifier(modifier)
            if box:
                getattr(self, modifier.type)(self, box, object, modifier)


    def data_draw_context_curve(self, context):
        layout = self.layout

        obj = context.object
        layout.template_ID(obj, 'data')


    def data_draw_shape_curve(self, context):
        layout = self.layout

        curve = context.object.data
        is_surf = type(curve) is SurfaceCurve
        is_curve = type(curve) is Curve
        is_text = type(curve) is TextCurve

        if is_curve:
            row = layout.row()
            row.prop(curve, 'dimensions', expand=True)

        split = layout.split()

        col = split.column()
        col.label(text='Resolution:')
        sub = col.column(align=True)
        sub.prop(curve, 'resolution_u', text='Preview U')
        sub.prop(curve, 'render_resolution_u', text='Render U')
        if is_curve:
            col.label(text='Twisting:')
            col.prop(curve, 'twist_mode', text='')
            col.prop(curve, 'twist_smooth', text='Smooth')
        elif is_text:
            col.label(text='Display:')
            col.prop(curve, 'use_fast_edit', text='Fast Editing')

        col = split.column()

        if is_surf:
            sub = col.column()
            sub.label(text='')
            sub = col.column(align=True)
            sub.prop(curve, 'resolution_v', text='Preview V')
            sub.prop(curve, 'render_resolution_v', text='Render V')

        if is_curve or is_text:
            col.label(text='Fill:')
            sub = col.column()
            sub.active = (curve.dimensions == '2D' or (curve.bevel_object is None and curve.dimensions == '3D'))
            sub.prop(curve, 'fill_mode', text='')
            col.prop(curve, 'use_fill_deform')

        if is_curve:
            col.label(text='Path/Curve-Deform:')
            sub = col.column()
            subsub = sub.row()
            subsub.prop(curve, 'use_radius')
            subsub.prop(curve, 'use_stretch')
            sub.prop(curve, 'use_deform_bounds')


    def data_draw_curve_texture_space(self, context):
        layout = self.layout

        curve = context.object.data

        row = layout.row()
        row.prop(curve, 'use_auto_texspace')
        row.prop(curve, 'use_uv_as_generated')

        row = layout.row()
        row.column().prop(curve, 'texspace_location', text='Location')
        row.column().prop(curve, 'texspace_size', text='Size')

        layout.operator('curve.match_texture_space')


    def data_draw_geometry_curve(self, context):
        layout = self.layout

        curve = context.object.data

        split = layout.split()

        col = split.column()
        col.label(text='Modification:')
        col.prop(curve, 'offset')
        col.prop(curve, 'extrude')
        col.label(text='Taper Object:')
        col.prop(curve, 'taper_object', text='')

        col = split.column()
        col.label(text='Bevel:')
        col.prop(curve, 'bevel_depth', text='Depth')
        col.prop(curve, 'bevel_resolution', text='Resolution')
        col.label(text='Bevel Object:')
        col.prop(curve, 'bevel_object', text='')

        if type(curve) is not TextCurve:
            col = layout.column(align=True)
            row = col.row()
            row.label(text='Bevel Factor:')

            col = layout.column()
            col.active = (
                    (curve.bevel_depth > 0.0) or
                    (curve.extrude > 0.0) or
                    (curve.bevel_object is not None))
            row = col.row(align=True)
            row.prop(curve, 'bevel_factor_mapping_start', text='')
            row.prop(curve, 'bevel_factor_start', text='Start')
            row = col.row(align=True)
            row.prop(curve, 'bevel_factor_mapping_end', text='')
            row.prop(curve, 'bevel_factor_end', text='End')

            row = layout.row()
            sub = row.row()
            sub.active = curve.taper_object is not None
            sub.prop(curve, 'use_map_taper')
            sub = row.row()
            sub.active = curve.bevel_object is not None
            sub.prop(curve, 'use_fill_caps')


    def data_draw_pathanim(self, context):
        layout = self.layout

        curve = context.object.data

        layout.active = curve.use_path

        col = layout.column()
        col.prop(curve, 'path_duration', text='Frames')
        col.prop(curve, 'eval_time')

        # these are for paths only
        row = layout.row()
        row.prop(curve, 'use_path_follow')


    def data_draw_active_spline(self, context):
        layout = self.layout

        curve = context.object.data
        act_spline = curve.splines.active
        is_surf = type(curve) is SurfaceCurve
        is_poly = (act_spline.type == 'POLY')

        split = layout.split()

        if is_poly:
            # These settings are below but its easier to have
            # polys set aside since they use so few settings
            row = layout.row()
            row.label(text='Cyclic:')
            row.prop(act_spline, 'use_cyclic_u', text='U')

            layout.prop(act_spline, 'use_smooth')
        else:
            col = split.column()
            col.label(text='Cyclic:')
            if act_spline.type == 'NURBS':
                col.label(text='Bezier:')
                col.label(text='Endpoint:')
                col.label(text='Order:')

            col.label(text='Resolution:')

            col = split.column()
            col.prop(act_spline, 'use_cyclic_u', text='U')

            if act_spline.type == 'NURBS':
                sub = col.column()
                # sub.active = (not act_spline.use_cyclic_u)
                sub.prop(act_spline, 'use_bezier_u', text='U')
                sub.prop(act_spline, 'use_endpoint_u', text='U')

                sub = col.column()
                sub.prop(act_spline, 'order_u', text='U')
            col.prop(act_spline, 'resolution_u', text='U')

            if is_surf:
                col = split.column()
                col.prop(act_spline, 'use_cyclic_v', text='V')

                # its a surface, assume its a nurbs
                sub = col.column()
                sub.active = (not act_spline.use_cyclic_v)
                sub.prop(act_spline, 'use_bezier_v', text='V')
                sub.prop(act_spline, 'use_endpoint_v', text='V')
                sub = col.column()
                sub.prop(act_spline, 'order_v', text='V')
                sub.prop(act_spline, 'resolution_v', text='V')

            if act_spline.type == 'BEZIER':
                col = layout.column()
                col.label(text='Interpolation:')

                sub = col.column()
                sub.active = (curve.dimensions == '3D')
                sub.prop(act_spline, 'tilt_interpolation', text='Tilt')

                col.prop(act_spline, 'radius_interpolation', text='Radius')

            layout.prop(act_spline, 'use_smooth')


    def data_draw_font(self, context):
        layout = self.layout

        text = context.object.data
        char = context.object.data.edit_format

        row = layout.split(percentage=0.25)
        row.label(text='Regular')
        row.template_ID(text, 'font', open='font.open', unlink='font.unlink')
        row = layout.split(percentage=0.25)
        row.label(text='Bold')
        row.template_ID(text, 'font_bold', open='font.open', unlink='font.unlink')
        row = layout.split(percentage=0.25)
        row.label(text='Italic')
        row.template_ID(text, 'font_italic', open='font.open', unlink='font.unlink')
        row = layout.split(percentage=0.25)
        row.label(text='Bold & Italic')
        row.template_ID(text, 'font_bold_italic', open='font.open', unlink='font.unlink')

        # layout.prop(text, 'font')

        split = layout.split()

        col = split.column()
        col.prop(text, 'size', text='Size')
        col = split.column()
        col.prop(text, 'shear')

        split = layout.split()

        col = split.column()
        col.label(text='Object Font:')
        col.prop(text, 'family', text='')

        col = split.column()
        col.label(text='Text on Curve:')
        col.prop(text, 'follow_curve', text='')

        split = layout.split()

        col = split.column()
        sub = col.column(align=True)
        sub.label(text='Underline:')
        sub.prop(text, 'underline_position', text='Position')
        sub.prop(text, 'underline_height', text='Thickness')

        col = split.column()
        col.label(text='Character:')
        col.prop(char, 'use_bold')
        col.prop(char, 'use_italic')
        col.prop(char, 'use_underline')

        row = layout.row()
        row.prop(text, 'small_caps_scale', text='Small Caps')
        row.prop(char, 'use_small_caps')


    def data_draw_paragraph(self, context):
        layout = self.layout

        text = context.object.data

        layout.label(text='Horizontal Alignment:')
        layout.row().prop(text, 'align_x', expand=True)

        layout.label(text='Vertical Alignment:')
        layout.row().prop(text, 'align_y', expand=True)

        split = layout.split()

        col = split.column(align=True)
        col.label(text='Spacing:')
        col.prop(text, 'space_character', text='Letter')
        col.prop(text, 'space_word', text='Word')
        col.prop(text, 'space_line', text='Line')

        col = split.column(align=True)
        col.label(text='Offset:')
        col.prop(text, 'offset_x', text='X')
        col.prop(text, 'offset_y', text='Y')


    def data_draw_text_boxes(self, context):
        layout = self.layout

        text = context.object.data

        split = layout.split()
        col = split.column()
        col.operator('font.textbox_add', icon='ZOOMIN')
        col = split.column()

        for i, box in enumerate(text.text_boxes):

            boxy = layout.box()

            row = boxy.row()

            split = row.split()

            col = split.column(align=True)

            col.label(text='Dimensions:')
            col.prop(box, 'width', text='Width')
            col.prop(box, 'height', text='Height')

            col = split.column(align=True)

            col.label(text='Offset:')
            col.prop(box, 'x', text='X')
            col.prop(box, 'y', text='Y')

            row.operator('font.textbox_remove', text='', icon='X', emboss=False).index = i


    def data_draw_context_metaball(self, context):
        layout = self.layout

        ob = context.object
        layout.template_ID(ob, 'data')


    def data_draw_metaball(self, context):
        layout = self.layout

        mball = context.object.data

        split = layout.split()

        col = split.column()
        col.label(text='Resolution:')
        sub = col.column(align=True)
        sub.prop(mball, 'resolution', text='View')
        sub.prop(mball, 'render_resolution', text='Render')

        col = split.column()
        col.label(text='Settings:')
        col.prop(mball, 'threshold', text='Threshold')

        layout.label(text='Update:')
        layout.row().prop(mball, 'update_method', expand=True)


    def data_draw_mball_texture_space(self, context):
        layout = self.layout

        mball = context.object.data

        layout.prop(mball, 'use_auto_texspace')

        row = layout.row()
        row.column().prop(mball, 'texspace_location', text='Location')
        row.column().prop(mball, 'texspace_size', text='Size')


    def data_draw_metaball_element(self, context):
        layout = self.layout

        metaelem = context.object.data.elements.active

        layout.prop(metaelem, 'type')

        split = layout.split()

        col = split.column(align=True)
        col.label(text='Settings:')
        col.prop(metaelem, 'stiffness', text='Stiffness')
        col.prop(metaelem, 'use_negative', text='Negative')
        col.prop(metaelem, 'hide', text='Hide')

        col = split.column(align=True)

        if metaelem.type in {'CUBE', 'ELLIPSOID'}:
            col.label(text='Size:')
            col.prop(metaelem, 'size_x', text='X')
            col.prop(metaelem, 'size_y', text='Y')
            col.prop(metaelem, 'size_z', text='Z')

        elif metaelem.type == 'TUBE':
            col.label(text='Size:')
            col.prop(metaelem, 'size_x', text='X')

        elif metaelem.type == 'PLANE':
            col.label(text='Size:')
            col.prop(metaelem, 'size_x', text='X')
            col.prop(metaelem, 'size_y', text='Y')


    def data_draw_context_mesh(self, context):
        layout = self.layout

        ob = context.object
        layout.template_ID(ob, 'data')


    def data_draw_normals(self, context):
        layout = self.layout

        mesh = context.object.data

        split = layout.split()

        col = split.column()
        col.prop(mesh, 'use_auto_smooth')
        sub = col.column()
        sub.active = mesh.use_auto_smooth and not mesh.has_custom_normals
        sub.prop(mesh, 'auto_smooth_angle', text='Angle')

        split.prop(mesh, 'show_double_sided')


    def data_draw_texture_space(self, context):
        layout = self.layout

        mesh = context.object.data

        layout.prop(mesh, 'texture_mesh')

        layout.separator()

        layout.prop(mesh, 'use_auto_texspace')
        row = layout.row()
        row.column().prop(mesh, 'texspace_location', text='Location')
        row.column().prop(mesh, 'texspace_size', text='Size')


    def data_draw_uv_texture(self, context):
        layout = self.layout

        me = context.object.data

        row = layout.row()
        col = row.column()

        col.template_list('MESH_UL_uvmaps_vcols', 'uvmaps', me, 'uv_textures', me.uv_textures, 'active_index', rows=1)

        col = row.column(align=True)
        col.operator('mesh.uv_texture_add', icon='ZOOMIN', text='')
        col.operator('mesh.uv_texture_remove', icon='ZOOMOUT', text='')


    def data_draw_vertex_colors(self, context):
        layout = self.layout

        me = context.object.data

        row = layout.row()
        col = row.column()

        col.template_list('MESH_UL_uvmaps_vcols', 'vcols', me, 'vertex_colors', me.vertex_colors, 'active_index', rows=1)

        col = row.column(align=True)
        col.operator('mesh.vertex_color_add', icon='ZOOMIN', text='')
        col.operator('mesh.vertex_color_remove', icon='ZOOMOUT', text='')


    def data_draw_customdata(self, context):
        layout = self.layout

        obj = context.object
        me = obj.data
        col = layout.column()

        col.operator('mesh.customdata_mask_clear', icon='X')
        col.operator('mesh.customdata_skin_clear', icon='X')

        if me.has_custom_normals:
            col.operator('mesh.customdata_custom_splitnormals_clear', icon='X')
        else:
            col.operator('mesh.customdata_custom_splitnormals_add', icon='ZOOMIN')

        col = layout.column()

        col.enabled = (obj.mode != 'EDIT')
        col.prop(me, 'use_customdata_vertex_bevel')
        col.prop(me, 'use_customdata_edge_bevel')
        col.prop(me, 'use_customdata_edge_crease')


    ## poll ##
    # world
    @staticmethod
    def world_poll_game_context_world(self, context):
        return True

    @staticmethod
    def world_poll_context_world(context):
        return True

    @staticmethod
    def world_poll_preview(context):
        return context.scene.world

    @staticmethod
    def world_poll_world(context):
        return context.scene.world

    @staticmethod
    def world_poll_ambient_occlusion(context):
        return context.scene.world

    @staticmethod
    def world_poll_environment_lighting(context):
        return context.scene.world

    @staticmethod
    def world_poll_indirect_lighting(context):
        return context.scene.world

    @staticmethod
    def world_poll_gather(context):
        return context.scene.world

    @staticmethod
    def world_poll_mist(context):
        return context.scene.world

    @staticmethod
    def world_poll_game_context_world(context):
        return context.scene.world

    @staticmethod
    def world_poll_game_environment_lighting(context):
        return context.scene.world

    @staticmethod
    def world_poll_game_mist(context):
        return context.scene.world

    @staticmethod
    def world_poll_world_volume(context):
        return context.scene.world.node_tree

    @staticmethod
    def world_poll_world_mist(context):
        mist_pass = True in [renderlayer.use_pass_mist for renderlayer in context.scene.render.layers]
        return context.scene.world and mist_pass

    @staticmethod
    def cyclesworld_poll_preview(context):
        return context.scene.world

    @staticmethod
    def cyclesworld_poll_surface(context):
        return context.scene.world

    @staticmethod
    def cyclesworld_poll_volume(context):
        return context.scene.world and context.scene.world.node_tree

    @staticmethod
    def cyclesworld_poll_ambient_occlusion(context):
        return context.scene.world

    @staticmethod
    def cyclesworld_poll_mist(context):
        mist_pass = True in [renderlayer.use_pass_mist for renderlayer in context.scene.render.layers]
        return context.scene.world and mist_pass

    @staticmethod
    def cyclesworld_poll_ray_visibility(context):
        return context.scene.world

    @staticmethod
    def cyclesworld_poll_settings(context):
        return context.scene.world
    @staticmethod
    def data_poll_context_curve(context):
        return context.active_object.type in {'CURVE', 'SURFACE', 'FONT'} and context.active_object.data

    @staticmethod
    def data_poll_shape_curve(context):
        return context.active_object.type in {'CURVE', 'SURFACE', 'FONT'} and context.active_object.data

    @staticmethod
    def data_poll_curve_texture_space(context):
        return context.active_object.type in {'CURVE', 'SURFACE', 'FONT'} and context.active_object.data

    @staticmethod
    def data_poll_geometry_curve(context):
        return context.active_object.type in {'CURVE', 'FONT'} and context.active_object.data

    @staticmethod
    def data_poll_pathanim(context):
        return context.active_object.type == 'CURVE' and context.active_object.data

    @staticmethod
    def data_poll_active_spline(context):
        return context.active_object.type in {'CURVE', 'SURFACE'} and context.active_object.data and context.active_object.data.splines.active

    @staticmethod
    def data_poll_font(context):
        return context.active_object.type == 'FONT' and context.active_object.data

    @staticmethod
    def data_poll_paragraph(context):
        return context.active_object.type == 'FONT' and context.active_object.data

    @staticmethod
    def data_poll_text_boxes(context):
        return context.active_object.type == 'FONT' and context.active_object.data

    @staticmethod
    def data_poll_context_metaball(context):
        return context.active_object.type == 'META' and context.active_object.data

    @staticmethod
    def data_poll_metaball(context):
        return context.active_object.type == 'META' and context.active_object.data

    @staticmethod
    def data_poll_mball_texture_space(context):
        return context.active_object.type == 'META' and context.active_object.data

    @staticmethod
    def data_poll_metaball_element(context):
        return context.active_object.type == 'META' and context.active_object.data and context.active_object.data.elements.active

    @staticmethod
    def data_poll_context_mesh(context):
        return context.active_object.type == 'MESH' and context.active_object.data

    @staticmethod
    def data_poll_normals(context):
        return context.active_object.type == 'MESH' and context.active_object.data

    @staticmethod
    def data_poll_texture_space(context):
        return context.active_object.type == 'MESH' and context.active_object.data

    @staticmethod
    def data_poll_uv_texture(context):
        return context.active_object.type == 'MESH' and context.active_object.data

    @staticmethod
    def data_poll_vertex_colors(context):
        return context.active_object.type == 'MESH' and context.active_object.data

    @staticmethod
    def data_poll_customdata(context):
        return context.active_object.type == 'MESH' and context.active_object.data


    ###################
    ## END OVERRIDES ##
    ###################


class batchname:


    def __init__(self, operator, context, specials=False):

        option = batchname.options(context)

        layout = operator.layout
        column = layout.column()
        split = column.split(percentage=0.15)
        column = split.column()
        column.prop(option, 'mode', expand=True)

        self.set_height(column, 11)

        column = split.column()

        getattr(self, option.mode.lower())(operator, context, option, column)

    @staticmethod
    def set_height(column, separators):
        for _ in range(0, separators):
            column.separator()

    @staticmethod
    def split_row(column, offset=0.0):

        row = column.row(align=True)
        split = row.split(align=True, percentage=0.275+offset)

        return split

    @staticmethod
    def datablock_buttons(category, option, layout, use_label=True):

        # if category not in {'Objects', 'Objects Data', 'Custom Properties'}:
        if use_label:
            layout.label(text=category + ':')

        row = layout.row(align=True)
        row.scale_x = 5

        if category == 'Objects':
            row.prop(option, 'toggle_objects', text='', icon='RADIOBUT_OFF' if not option.toggle_objects else 'RADIOBUT_ON')
        elif category == 'Objects Data':
            row.prop(option, 'toggle_objects_data', text='', icon='RADIOBUT_OFF' if not option.toggle_objects_data else 'RADIOBUT_ON')
        for target in batchname.catagories[category]:
            if target not in {'line_sets', 'sensors', 'controllers', 'actuators'}:row.prop(option, target, text='', icon=icon(target))
            elif target == 'line_sets':
                row.prop(option, target, text='Line Sets', toggle=True)
            else:
                row.prop(option, target, text=tartitle(), toggle=True)

    @staticmethod
    def search_specials(operator, context):

        layout = operator.layout

        if batchname.options(context).mode == 'NAME':
            naming = batchname.options(context).name_options['options']
            option = naming.operation_options[naming.active_index]

        else:
            option = batchname.options(context).sort_options['options']

        layout.prop(option, 'case_sensitive')
        layout.prop(option, 're')

    @staticmethod
    def move_search_specials(operator, context):

        layout = operator.layout

        naming = batchname.options(context).name_options['options']
        option = naming.operation_options[naming.active_index]

        layout.prop(option, 'move_case_sensitive')
        layout.prop(option, 'move_re')

    @staticmethod
    def swap_search_specials(operator, context):

        layout = operator.layout

        naming = batchname.options(context).name_options['options']
        option = naming.operation_options[naming.active_index]

        layout.prop(option, 'swap_case_sensitive')
        layout.prop(option, 'swap_re')

    @staticmethod
    def operation_specials(operator, context):

        layout = operator.layout

        layout.prop(preferences(context), 'use_last')
        layout.prop(preferences(context), 'auto_name_operations')

        layout.operator('namestack.batchname_rename_operation')
        layout.operator('namestack.batchname_rename_all_operations')


    class mode_row:
        dual_position = True
        sorting = False
        swap = False
        move = False


        def __init__(self, option, column, active=True, dual_position=True, custom_mode='', sorting=False, swap=False, move=False):

            self.dual_position = True if dual_position else False
            self.sorting = True if sorting else False
            self.swap = True if swap else False
            self.move = True if move else False

            if self.sorting and not custom_mode:
                operation_mode = 'placement'
            else:
                operation_mode = '{}_mode'.format(option.operation_mode.lower()) if not custom_mode else custom_mode

            split = batchname.split_row(column)
            split.prop(option, operation_mode, text='')

            row = split.row(align=True)
            row.active = active

            mode = getattr(option, operation_mode).lower()
            getattr(self, mode)(option, row)

        @staticmethod
        def search_prop(option, row, prop):
            row.prop(option, prop, text='', icon='VIEWZOOM')


        def search_specials(self, row):

            menu = 'namestack.batchname_search_specials'
            menu = 'namestack.batchname_move_search_specials' if self.move else menu
            menu = 'namestack.batchname_swap_search_specials' if self.swap else menu

            sub = row.row(align=True)
            sub.menu(menu, text='', icon='COLLAPSEMENU')


        def position_prop(self, option, row):
            if self.dual_position:
                begin = 'begin' if not self.swap else 'swap_begin'
                end = 'end' if not self.swap else 'swap_end'

                row.prop(option, begin)
                row.prop(option, end)

                prop = 'outside' if not self.swap else 'swap_outside'
                row = row.row(align=True)
                icon = 'FULLSCREEN_EXIT' if not option.outside else 'FULLSCREEN_ENTER'
                row.prop(option, prop, text='', icon=icon)

            else:
                prop = 'position' if not self.move else 'move_position'
                row.prop(option, prop)


        def all(self, option, row):

            if not self.sorting:
                self.search_prop(option, row, 'find')
                self.search_specials(row)

            else:
                self.position_prop(option, row)


        def find(self, option, row):

            prop = 'find' if not self.swap else 'swap_find'
            self.search_prop(option, row, prop)
            self.search_specials(row)


        def position(self, option, row):

            self.position_prop(option, row)


        def before(self, option, row):

            prop = 'before'
            prop = 'move_before' if self.move else prop
            prop = 'swap_before' if self.swap else prop
            self.search_prop(option, row, prop)
            self.search_specials(row)


        def after(self, option, row):

            prop = 'after'
            prop = 'move_after' if self.move else prop
            prop = 'swap_after' if self.swap else prop
            self.search_prop(option, row, prop)
            self.search_specials(row)


        def between(self, option, row):

            after = 'after'
            after = 'move_after' if self.move else after
            after = 'swap_after' if self.swap else after
            self.search_prop(option, row, after)

            before = 'before'
            before = 'move_before' if self.move else before
            before = 'swap_before' if self.swap else before
            self.search_prop(option, row, 'before')
            self.search_specials(row)

        @staticmethod
        def insert_prop(option, row):

            row.prop(option, 'insert', text='', icon='ZOOMIN')

        @staticmethod
        def separator_prop(option, row):

            row.prop(option, 'separator', text='', icon='ARROW_LEFTRIGHT')


        def prefix(self, option, row):

            if self.sorting:
                self.separator_prop(option, row)
            else:
                self.insert_prop(option, row)


        def suffix(self, option, row):

            if self.sorting:
                self.separator_prop(option, row)
            else:
                self.insert_prop(option, row)


    class target:


        def __init__(self, operator, context, option, layout):

            option = option.target_options['options']

            row = layout.row()
            row.prop(option, 'target_mode', expand=True)

            layout.separator()

            layout = layout.column(align=True)

            if option.target_mode == 'CONTEXT':
                self.context_area(operator, context, option, layout)

            else:
                batchname.datablock_buttons('Objects', option, layout, use_label=False)
                batchname.datablock_buttons('Objects Data', option, layout, use_label=False)
                batchname.datablock_buttons('Object Related', option, layout)

                layout.separator()

                row = layout.row(align=True)
                row.prop(option, 'display_more')

                if option.display_more:
                    batchname.datablock_buttons('Grease Pencil', option, layout)
                    batchname.datablock_buttons('Animation', option, layout)
                    batchname.datablock_buttons('Node', option, layout)
                    batchname.datablock_buttons('Particle', option, layout)
                    batchname.datablock_buttons('Freestyle', option, layout)
                    batchname.datablock_buttons('Scene', option, layout)
                    batchname.datablock_buttons('Image & Brush', option, layout)
                    batchname.datablock_buttons('Sequence', option, layout)
                    batchname.datablock_buttons('Game Engine', option, layout)
                    batchname.datablock_buttons('Misc', option, layout)
                    # batchname.datablock_buttons('Custom Properties', option, layout, use_label=False)


        class context_area:

            def __init__(self, operator, context, option, layout):
                getattr(self, operator.area_type.lower())(operator, context, option, layout)


            class properties:


                def __init__(self, operator, context, option, layout):
                    getattr(self, context.space_data.context.lower())(operator, context, option, layout)

                @staticmethod
                def render(operator, context, option, layout):

                    layout.label(text='Nothing specific in the properties render context to target')

                @staticmethod
                def render_layer(operator, context, option, layout):

                    layout.label(text='Properties render layer context is not yet implemented')
                    # render layers
                    # views
                    # freestyle

                @staticmethod
                def scene(operator, context, option, layout):

                    layout.label(text='Properties scene context is not yet implemented')
                    # keying sets
                    # custom properties

                @staticmethod
                def world(operator, context, option, layout):

                    layout.label(text='Properties world context is not yet implemented')
                    # worlds
                    # custom properties

                @staticmethod
                def object(operator, context, option, layout):

                    layout.label(text='Properties object context is not yet implemented')
                    # groups
                    # custom properties

                @staticmethod
                def constraint(operator, context, option, layout):

                    layout.label(text='Properties constraint context is not yet implemented')
                    # constraints

                @staticmethod
                def modifier(operator, context, option, layout):

                    layout.label(text='Properties modifier context is not yet implemented')
                    # modifiers

                @staticmethod
                def data(operator, context, option, layout):

                    layout.label(text='Properties object data context is not yet implemented')
                    # vertex groups
                    # shape keys
                    # uv maps
                    # vertex colors
                    # bone groups
                    # pose library
                    # sound * for speaker
                    # font * for text
                    # custom properties

                @staticmethod
                def bone(operator, context, option, layout):

                    layout.label(text='Properties bone context is not yet implemented')
                    # custom properties

                @staticmethod
                def bone_constraint(operator, context, option, layout):

                    layout.label(text='Properties bone constraint context is not yet implemented')
                    # constraints

                @staticmethod
                def material(operator, context, option, layout):

                    layout.label(text='Properties material context is not yet implemented')
                    # materials
                    # custom properties

                @staticmethod
                def texture(operator, context, option, layout):

                    layout.label(text='Properties texture context is not yet implemented')
                    # image
                    # custom properties

                @staticmethod
                def particle(operator, context, option, layout):

                    layout.label(text='Properties particle context is not yet implemented')
                    # particles
                    # cache
                    # textures
                    # custom properties

                @staticmethod
                def physics(operator, context, option, layout):

                    layout.label(text='Properties physics context is not yet implemented')
                    # cloth cache
                    # dynamic paint cache
                    # dynamic paint canvas
                    # soft body cache

            @staticmethod
            def console(operator, context, option, layout):

                layout.label(text='Nothing specific in the console to target')

            @staticmethod
            def text_editor(operator, context, option, layout):

                # texts
                layout.label(text='Text editor is not yet implemented')


            class dopesheet_editor:


                def __init__(self, operator, context, option, layout):
                    getattr(self, context.space_data.mode.lower())(operator, context, option, layout)

                @staticmethod
                def dopesheet(operator, context, option, layout):

                    # object
                    # action
                    # group
                    layout.label(text='Dopesheet\'s dopesheet mode is not yet supported')

                @staticmethod
                def action(operator, context, option, layout):

                    # group
                    layout.label(text='Dopesheet\'s action mode is not yet supported')

                @staticmethod
                def shapekey(operator, context, option, layout):

                    # group
                    layout.label(text='Dopesheet\'s shapekey mode is not yet supported')

                @staticmethod
                def gpencil(operator, context, option, layout):

                    # g pencil
                    # layers
                    layout.label(text='Dopesheet\'s grease pencil mode is not yet supported')

                @staticmethod
                def mask(operator, context, option, layout):

                    # mask
                    # layer
                    layout.label(text='Dopesheet\'s mask file mode is not yet supported')

                @staticmethod
                def cachefile(operator, context, option, layout):

                    layout.label(text='Dopesheet\'s cache file mode is not yet supported')


            class graph_editor:


                def __init__(self, operator, context, option, layout):
                    getattr(self, context.space_data.mode.lower())(operator, context, option, layout)

                @staticmethod
                def fcurves(operator, context, option, layout):

                    # object
                    # action
                    # action groups
                    layout.label(text='Graph editor\'s fcurve mode is not yet implemented')

                @staticmethod
                def drivers(operator, context, option, layout):

                    # object
                    # driver variables
                    layout.label(text='Graph editor\'s driver mode is not yet implemented')

            @staticmethod
            def view_3d(operator, context, option, layout):

                batchname.datablock_buttons('Objects', option, layout, use_label=False)
                batchname.datablock_buttons('Objects Data', option, layout, use_label=False)
                row = layout.row(align=True)
                row.prop(option, 'target_mode', expand=True)
                batchname.datablock_buttons('Object Related', option, layout)
                # batchname.datablock_buttons('Custom Properties', option, layout)


            class image_editor:


                def __init__(self, operator, context, option, layout):
                    getattr(self, context.space_data.mode.lower())(operator, context, option, layout)

                @staticmethod
                def view(operator, context, option, layout):

                    # images
                    # uv's
                    # grease pencil
                    # gp layer
                    # gp pallete
                    # gp brushes
                    layout.label(text='Image editor\'s view mode is not yet implemented')

                @staticmethod
                def paint(operator, context, option, layout):

                    # images
                    # paint curves
                    # pallettes
                    # textures
                    # grease pencil
                    # gp layer
                    # gp pallete
                    # gp brushes
                    layout.label(text='Image editor\'s paint mode is not yet implemented')

                @staticmethod
                def mask(operator, context, option, layout):

                    # images
                    # masks
                    # masks layers
                    # grease pencil
                    # gp layer
                    # gp pallete
                    # gp brushes
                    layout.label(text='Image editor\'s mask mode is not yet implemented')

            @staticmethod
            def node_editor(operator, context, option, layout):

                layout.label(text='Node editor is not yet implemented')
                # nodes & labels
                # objects
                # object related *textures, uv maps, vertex colors
                # images
                # masks
                # worlds
                # scene
                # node input output?

            @staticmethod
            def timeline(operator, context, option, layout):

                layout.label(text='Timeline is not yet implemented')
                # markers

            @staticmethod
            def nla_editor(operator, context, option, layout):

                layout.label(text='NLA editor is not yet implemented')
                # object
                # action
                # tracks
                # strips

            @staticmethod
            def sequence_editor(operator, context, option, layout):

                layout.label(text='Sequence editor is not yet implemented')
                # sequences
                # modifiers
                # grease pencil
                # custom properties

            @staticmethod
            def clip_editor(operator, context, option, layout):

                layout.label(text='Clip editor is not yet implemented')
                # tracks
                # mask layers
                # grease pencil

            @staticmethod
            def logic_editor(operator, context, option, layout):

                layout.label(text='Logic editor is not yet implemented')
                # logic bricks
                # game properties

            @staticmethod
            def outliner(operator, context, option, layout):

                layout.label(text='Outliner is not yet implemented')

            @staticmethod
            def user_preferences(operator, context, option, layout):

                layout.label(text='Nothing specific in user preferences to target')

            @staticmethod
            def info(operator, context, option, layout):

                layout.label(text='Nothing specific in info to target')

            @staticmethod
            def file_browser(operator, context, option, layout):

                layout.label(text='File browser is not yet implemented')


    class name:


        def __init__(self, operator, context, option, layout):

            option = option.name_options['options']

            split = layout.split(percentage=0.7)
            column = split.column()

            self.name_operation(option, column)

            column = split.column(align=True)
            row = column.row(align=True)
            row.template_list('UI_UL_list', 'batchname', option, 'operation_options', option, 'active_index', rows=8)

            column = row.column(align=True)
            column.operator('namestack.batchname_add_operation', text='', icon='ZOOMIN')
            column.operator('namestack.batchname_remove_operation', text='', icon='ZOOMOUT')
            column.menu('namestack.batchname_operation_specials', text='', icon='COLLAPSEMENU')

            column.separator()

            operator = column.operator('namestack.batchname_move_operation', text='', icon='TRIA_UP')
            operator.up = True

            operator = column.operator('namestack.batchname_move_operation', text='', icon='TRIA_DOWN')
            operator.up = False


        class name_operation:


            def __init__(self, option, column):

                option = option.operation_options[option.active_index]

                row = column.row()
                row.prop(option, 'operation_mode', expand=True)
                column.separator()

                getattr(self, option.operation_mode.lower())(option, column)


            def replace(self, option, column):

                batchname.mode_row(option, column, active=option.replace_mode != 'ALL')

                column.label(text='With:')
                column.prop(option, 'replace', text='', icon='FILE_REFRESH')


            def insert(self, option, column):

                batchname.mode_row(option, column, dual_position=False)

                if option.insert_mode not in {'PREFIX', 'SUFFIX'}:
                    column.label(text='Insert:')
                    batchname.mode_row.insert_prop(option, column.row())


            def convert(self, option, column):

                batchname.mode_row(option, column, active=option.convert_mode != 'ALL')

                column.label(text='Case:')

                row = column.row()
                row.prop(option, 'case_mode', text='')

                column.label(text='Separators:')

                if option.separate_mode == 'CUSTOM':
                    row = column.row(align=True)
                    split = row.split(align=True, percentage=0.275)
                    split.prop(option, 'separate_mode', text='')

                    row = split.row(align=True)
                    row.prop(option, 'custom', text='')


                else:
                    row = column.row()
                    row.prop(option, 'separate_mode', text='')


            def move(self, option, column):

                batchname.mode_row(option, column)

                column.label(text='To:')

                batchname.mode_row(option, column, dual_position=False, custom_mode='move_to', move=True)


            def swap(self, option, column):

                batchname.mode_row(option, column)

                column.label(text='With:')

                batchname.mode_row(option, column, custom_mode='swap_to', swap=True)

            @staticmethod
            def transfer(option, column):

                column.label(text='Transfering is not yet implemented')


    class sort:


        def __init__(self, operator, context, option, column):

            option = option.sort_options['options']

            row = column.row()
            row.prop(option, 'sort_mode', expand=True)

            column.separator()

            getattr(self, option.sort_mode.lower())(option, column)

        @staticmethod
        def name_slice(option, column):
            pass

        @staticmethod
        def fallback_mode_prop(option, column):

            column.label(text='Fallback:')

            row = column.row(align=True)
            row.prop(option, 'display_options', text='', icon='SETTINGS')
            row.prop(option, 'fallback_mode', expand=True)

        @staticmethod
        def none(option, column):
            column.label(text='No sorting will be performed')


        def ascend(self, option, column):

            if option.sort_type_mode == 'ALL':
                batchname.mode_row(option, column, active=False, custom_mode='sort_type_mode', sorting=True)
            else:
                batchname.mode_row(option, column, custom_mode='sort_type_mode', sorting=True)


        def descend(self, option, column):

            if option.sort_type_mode == 'ALL':
                batchname.mode_row(option, column, active=False, custom_mode='sort_type_mode', sorting=True)
            else:
                batchname.mode_row(option, column, custom_mode='sort_type_mode')


        def position(self, option, column): # TODO: orientation? contains, rotation, scale, location modes, from viewport perspective?

            if option.display_options:
                getattr(self, option.fallback_mode.lower())(option, column)
            else:
                split = batchname.split_row(column)
                split.prop(option, 'starting_point', text='')

                row = split.row(align=True)
                row.prop(option, 'axis_3d', expand=True)

                if option.starting_point in {'CURSOR', 'CENTER', 'ACTIVE'}:
                    column.separator()

                    if option.axis_3d == 'Z':
                        props = ['top', 'bottom']
                    elif option.axis_3d == 'Y':
                        props = ['front', 'back']
                    else:
                        props = ['left', 'right']

                    split = batchname.split_row(column, offset=-0.01)
                    split.label(text=props[0].title() + ':')

                    row = split.row()
                    row.prop(option, props[0], text='')

                    split = batchname.split_row(column, offset=-0.01)
                    split.label(text=props[1].title() + ':')

                    row = split.row()
                    row.prop(option, props[1], text='')

                    if option.placement not in {'PREFIX', 'SUFFIX'}:
                        split = batchname.split_row(column, offset=-0.01)
                        split.label(text='Separator:')

                        row = split.row()
                        row.prop(option, 'separator', text='', icon='ARROW_LEFTRIGHT')

                    batchname.mode_row(option, column, dual_position=False, sorting=True)

            self.fallback_mode_prop(option, column)


        def hierarchy(self, option, column):

            if option.display_options:
                getattr(self, option.fallback_mode.lower())(option, column)
            else:
                row = column.row()
                row.prop(option, 'hierarchy_mode', expand=True)

            self.fallback_mode_prop(option, column)


        def manual(self, option, column):
            column.label(text='Manual sort options have not yet been implemented')


    class count:


        def __init__(self, operator, context, option, column):

            option = option.count_options['options']

            row = column.row()
            row.prop(option, 'count_mode', expand=True)


            column.separator()

            getattr(self, option.count_mode.lower())(operator, context, option, column)

        @staticmethod
        def position_row(operator, context, option, column):

            column.separator()

            row = column.row(align=True)
            row.prop(option, 'placement', expand=True)

            row = row.row(align=True)
            row.enabled = option.placement == 'POSITION'
            row.prop(option, 'position', text='At')


        def common(self, operator, context, option, column):

            column.prop(option, 'separator')

            column.separator()

            row = column.row(align=True)
            row.prop(option, 'start')
            row.prop(option, 'step')

            self.position_row(operator, context, option, column)

        @staticmethod
        def none(operator, context, option, column):

            column.label(text='No counting will be performed')


        def numeric(self, operator, context, option, column):

            row = column.row(align=True)
            split = row.split(percentage=0.25, align=True)
            split.prop(option, 'auto', toggle=True)
            split.prop(option, 'pad')

            column.separator()

            column.prop(option, 'character')

            self.common(operator, context, option, column)


        def alphabetic(self, operator, context, option, column):

            self.common(operator, context, option, column)


        def roman_numeral(self, operator, context, option, column):

            self.common(operator, context, option, column)

    @staticmethod
    def preview(operator, context, options, column):

        column.label(text='Preview is not yet implemented')


    class options:


        def __init__(self, operator, context, option, column):

            row = column.row()
            row.prop(option, 'options_mode', expand=True)

            column.separator()

            getattr(self, option.options_mode.lower())(operator, context, option, column)

        @staticmethod
        def presets(operator, context, option, column):
            column.label(text='Presets are not yet implemented')

        @staticmethod
        def restore(operator, context, option, column):
            column.label(text='Restore points are not yet implemented')

        @staticmethod
        def importing(operator, context, option, column):
            column.label(text='Importing is not yet implemented')

        @staticmethod
        def exporting(operator, context, option, column):
            column.label(text='Exporting is not yet implemented')

        @staticmethod
        def preferences(operator, context, option, column):

            row = column.row()
            row.prop(preferences(context), 'use_last')
            row.prop(preferences(context), 'auto_name_operations')

            column.prop(preferences(context), 'batchname_popup_width')


class preferences:


    def __init__(self, addon, context):
        addon.preference = preferences(context)

        row = addon.layout.row()
        # row.scale_y = 2
        row.prop(addon.preference, 'mode', expand=True)

        getattr(self, addon.preference.mode.lower())(addon, context)

        row = addon.layout.row(align=True)
        row.scale_y = 1.5
        row.operator('wm.url_open', text='Report a bug').url = remote['bug_report']
        row.operator('wm.url_open', text='Thread').url = remote['thread']
        row.operator('wm.url_open', text='proxeIO').url = remote['proxeIO']


    def general(self, addon, context):

        box = addon.layout.box()

        row = box.row()
        row.prop(addon.preference, 'keep_session_settings')


    def namestack(self, addon, context):

        box = addon.layout.box()

        row = box.row()
        row.label(text='Location:')
        row.prop(addon.preference, 'location', expand=True)

        row = box.row()
        row.prop(addon.preference, 'pin_active')

        row = box.row()
        row.prop(addon.preference, 'remove_item_panel')
        row.prop(addon.preference, 'click_through')

        row = box.row()
        row.label(text='Pop-up Width:')
        row.prop(addon.preference, 'filter_popup_width', text='')

        row = box.row()
        row.label(text='Separators:')
        row.prop(addon.preference, 'separators', text='')


    def datablock(self, addon, context):

        box = addon.layout.box()

        row = box.row()
        row.label(text='Pop-up Width:')
        row.prop(addon.preference, 'datablock_popup_width', text='')


    def batchname(self, addon, context):

        box = addon.layout.box()

        row = box.row()
        row.prop(addon.preference, 'use_last')
        row.prop(addon.preference, 'auto_name_operations')

        row = box.row()
        row.label(text='Pop-up Width:')
        row.prop(addon.preference, 'batchname_popup_width')


    def hotkey(self, addon, context):

        layout = addon.layout.box()
        column = layout.column()

        keyconfig = context.window_manager.keyconfigs.addon
        keymap = keyconfig.keymaps['Window']

        if 'namestack.datablock' in keymap.keymap_items:
            keymapitem = keymap.keymap_items['namestack.datablock']
            column.context_pointer_set('keymap', keymap)
            rna_keymap_ui.draw_kmi([], keyconfig, keymap, keymapitem, column, 0)
        else:
            update.keymap(context, addkey=False)

        if 'namestack.batchname' in keymap.keymap_items:
            keymapitem = keymap.keymap_items['namestack.batchname']
            column.context_pointer_set('keymap', keymap)
            rna_keymap_ui.draw_kmi([], keyconfig, keymap, keymapitem, column, 0)
        else:
            update.keymap(context, addkey=False)


    def updates(self, addon, context):

        box = addon.layout.box()

        row = box.row()
        row.prop(addon, 'update_check')

        row = box.row()
        row.prop(addon, 'update_display_menu')
        row.prop(addon, 'update_display_stack')
