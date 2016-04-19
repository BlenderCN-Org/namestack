
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation; either version 2 of the License, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# imports
import bpy
import bmesh
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty, EnumProperty
from ..interface.popup.constraints import ConstraintButtons
from ..interface.popup.modifiers import ModifierButtons

# operator
class operator(Operator):
  '''
    Assigns an active object.
  '''
  bl_idname = 'view3d.name_panel_icon'
  bl_label = 'Name Panel Icon'
  bl_description = 'Changes active object.'
  bl_options = {'REGISTER', 'UNDO'}

  # owner
  owner = StringProperty(
    name = 'Owner',
    description = 'The owner of the target datablock.',
    default = ''
  )

  # target
  target = StringProperty(
    name = 'Target',
    description = 'Datablock target belonging to the object.',
    default = ''
  )

  # extend
  extend = BoolProperty(
    name = 'Extend',
    description = 'Keep old selection.',
    default = True
  )

  # view
  view = BoolProperty(
    name = 'View',
    description = 'Center the 3D view on the object.',
    default = False
  )

  # type
  type = EnumProperty(
    name = 'Type',
    description = 'The type of datablock for the icon.',
    items = [
      ('OBJECT', 'Object', '', 'OBJECT_DATA', 0),
      ('GROUP', 'Group', '', 'GROUP', 1),
      ('ACTION', 'Action', '', 'ACTION', 2),
      ('GREASE_PENCIL', 'Grease Pencil', '', 'GREASEPENCIL', 3),
      ('CONSTRAINT', 'Constraint', '', 'CONSTRAINT', 4),
      ('MODIFIER', 'Modifier', '', 'MODIFIER', 5),
      ('OBJECT_DATA', 'Object Data', '', 'MESH_DATA', 6),
      ('BONE_GROUP', 'Bone Group', '', 'GROUP_BONE', 7),
      ('BONE', 'Bone', '', 'BONE_DATA', 8),
      ('BONE_CONSTRAINT', 'Bone Constraint', '', 'CONSTRAINT_BONE', 9),
      ('VERTEX_GROUP', 'Vertex Group', '', 'GROUP_VERTEX', 10),
      ('SHAPEKEY', 'Shapekey', '', 'SHAPEKEY_DATA', 11),
      ('UV', 'UV Map', '', 'GROUP_UVS', 12),
      ('VERTEX_COLOR', 'Vertex Colors', '', 'GROUP_VCOL', 13),
      ('MATERIAL', 'Material', '', 'MATERIAL', 14),
      ('TEXTURE', 'Texture', '', 'TEXTURE', 15),
      ('PARTICLE_SYSTEM', 'Particle System', '', 'PARTICLES', 16),
      ('PARTICLE_SETTING', 'Particle Settings', '', 'DOT', 17)
    ],
    default = 'OBJECT'
  )

  # poll
  @classmethod
  def poll(cls, context):
    '''
      Space data type must be in 3D view.
    '''
    return context.space_data.type in 'VIEW_3D'

  # draw
  def draw(self, context):
    '''
      Operator options.
    '''

    # layout
    layout = self.layout

    # extend
    layout.prop(self, 'extend')

    # view
    layout.prop(self, 'view')

  # execute
  def execute(self, context):
    '''
      Execute the operator.
    '''
    # object
    if self.type not in {'BONE', 'BONE_CONSTRAINT'}: # temporary

      # extend
      if self.extend:

        # select active
        context.active_object.select = True

        # extend
      else:

        # deselect all
        for object in context.scene.objects[:]:
          object.select = False

      # active object
      context.scene.objects.active = bpy.data.objects[self.owner]

      # select objects
      context.active_object.select = True

      # view
      if self.view:

        # view selected
        bpy.ops.view3d.view_selected()

    # group
    # action
    # grease pencil

    # constraint
    if self.type == 'BONE_CONSTRAINT':

      # extend
      if self.extend:

        # select active
        context.active_object.data.bones.active.select = True

      else:

        for bone in context.selected_pose_bones[:]:
          bone.bone.select = False

      # target
      context.scene.objects[context.active_object.name].data.bones.active = bpy.data.armatures[context.active_object.data.name].bones[self.owner]

      # select
      context.active_object.data.bones.active.select = True

      # view
      if self.view:
        bpy.ops.view3d.view_selected()

    # modifier
    # object data

    # bone
    if self.type == 'BONE': # temporary

      # edit mode
      if context.object.mode in 'EDIT':

        # extend
        if self.extend:
          # select
          context.active_object.data.edit_bones.active.select = True

          # select head
          context.active_object.data.edit_bones.active.select_head = True

          # select tail
          context.active_object.data.edit_bones.active.select_tail = True

        # extend
        else:
          for bone in context.selected_editable_bones[:]:

            # deselect
            bone.select = False

            # deselect head
            bone.select_head = False

            # deselect tail
            bone.select_tail = False

        # active bone
        context.scene.objects[context.active_object.name].data.edit_bones.active = bpy.data.armatures[context.active_object.data.name].edit_bones[self.target]

        # select
        context.active_object.data.edit_bones.active.select = True

        # select head
        context.active_object.data.edit_bones.active.select_head = True

        # select tail
        context.active_object.data.edit_bones.active.select_tail = True

      # pose mode
      else:

        # extend
        if self.extend:

          # select active
          context.active_object.data.bones.active.select = True

        # extend
        else:

          for bone in context.selected_pose_bones[:]:
            bone.bone.select = False

        # target
        context.scene.objects[context.active_object.name].data.bones.active = bpy.data.armatures[context.active_object.data.name].bones[self.target]

        # select
        context.active_object.data.bones.active.select = True

      # view
      if self.view:
        bpy.ops.view3d.view_selected()


    # vertex group
    # warning
    # try:
    #
    #   # not active
    #   if bpy.data.objects[self.object] != context.scene.objects.active:
    #
    #     # object mode
    #     if context.mode != 'OBJECT':
    #       bpy.ops.object.mode_set(mode='OBJECT')
    #
    #     # extend
    #     if self.extend:
    #
    #       # select
    #       context.scene.objects.active.select = True
    #
    #     # extend
    #     else:
    #
    #       # object
    #       for object in context.scene.objects[:]:
    #
    #         # deselect
    #         object.select = False
    #
    #     # select
    #     bpy.data.objects[self.object].select = True
    #
    #     # active object
    #     context.scene.objects.active = bpy.data.objects[self.object]
    #
    # # report
    # except:
    #   self.report({'WARNING'}, 'Invalid object.')
    #
    # # edit mode
    # if context.mode != 'EDIT':
    #   bpy.ops.object.mode_set(mode='EDIT')
    #
    # # bmesh
    # mesh = bmesh.from_edit_mesh(context.active_object.data)
    #
    # # extend
    # if not self.extend:
    #
    #   # clear vertex
    #   for vertex in mesh.verts:
    #     vertex.select = False
    #
    #   # clear edge
    #   for edge in mesh.edges:
    #     edge.select = False
    #
    #   # clear face
    #   for face in mesh.faces:
    #     face.select = False
    #
    # # warning
    # try:
    #
    #   # group index
    #   groupIndex = context.active_object.vertex_groups[self.target].index
    #
    #   # active index
    #   context.active_object.vertex_groups.active_index = groupIndex
    #
    # # report
    # except:
    #   self.report({'WARNING'}, 'Invalid target.')
    #
    # # deform layer
    # deformLayer = mesh.verts.layers.deform.active
    #
    # # select vertices
    # for vertex in mesh.verts:
    #   try:
    #     deformVertex = vertex[deformLayer]
    #     if groupIndex in deformVertex:
    #       vertex.select = True
    #   except:
    #     pass
    #
    # # flush selection
    # mesh.select_flush(True)
    #
    # # update viewport
    # context.scene.objects.active = context.scene.objects.active
    #
    # # properties
    # if self.properties:
    #
    #   # screen
    #   if self.screen != '':
    #
    #     # warning
    #     try:
    #
    #       # area
    #       for area in bpy.data.screens[self.screen].areas:
    #
    #         # type
    #         if area.type in 'PROPERTIES':
    #
    #           # context
    #           area.spaces.active.context = 'DATA'
    #
    #     # report
    #     except:
    #       self.report({'WARNING'}, 'Invalid screen')
    #
    #   # screen
    #   else:
    #
    #     # area
    #     for area in context.window.screen.areas:
    #
    #       # type
    #       if area.type in 'PROPERTIES':
    #
    #         # context
    #         area.spaces.active.context = 'DATA'
    #
    # # layout
    # if self.layout:
    #
    #   # screen
    #   if self.screen != '':
    #
    #     # warning
    #     try:
    #
    #       # active screen
    #       context.window.screen = bpy.data.screens[self.screen]
    #
    #     # report
    #     except:
    #       self.report({'WARNING'}, 'Invalid screen')

    # shapekey
    # uv
    # vertex color
    # material
    # texture
    # particle system
    # particle setting

    return {'FINISHED'}

# bone
class bone(Operator):
  '''
    Assigns an active bone.
  '''
  bl_idname = 'view3d.name_panel_active_bone'
  bl_label = 'Active Bone'
  bl_description = 'Make this bone the active bone.'
  bl_options = {'REGISTER', 'UNDO'}

  # target
  target = StringProperty(
    name = 'Target',
    description = 'The target bone that will become the active object.',
    default = ''
  )

  # view
  view = BoolProperty(
    name = 'Center View',
    description = 'Center the 3D view on the bone.',
    default = True
  )

  # properties
  properties = BoolProperty(
    name = 'Properties',
    description = 'Change any property window\s context to bone.',
    default = False
  )

  # poll
  @classmethod
  def poll(cls, context):
    '''
      Space data type must be in 3D view and there must be an active bone.
    '''
    return context.space_data.type in 'VIEW_3D'

  # execute
  def execute(self, context):
    '''
      Execute the operator.
    '''


    return {'FINISHED'}

# pop up constraint
class constraint(ConstraintButtons, Operator):
  '''
    This is operator is used to create the required pop-up panel.
  '''
  bl_idname = 'view3d.name_panel_constraint_settings'
  bl_label = 'Constraint'
  bl_description = 'Adjust the options for this constraint. (Experimental)'
  bl_options = {'REGISTER', 'UNDO'}

  # object
  object = StringProperty(
    name = 'Object',
    description = 'The object that the constraint is attached to.',
    default = ''
  )

  # bone
  bone = StringProperty(
    name = 'Bone',
    description = 'The bone that the constraint is attached to.'
  )

  # target
  target = StringProperty(
    name = 'Target',
    description = 'The constraint you wish to edit the settings of.',
    default = ''
  )

  # properties
  properties = BoolProperty(
    name = 'Properties',
    description = 'Change any property window\'s context to constraint',
    default = False
  )

  # draw
  def draw(self, context):
    '''
      Draw the constraint options.
    '''

    # layout
    layout = self.layout

    # column
    column = layout.column()

    # label
    column.label(text=self.target + ':')

    # constraint
    if self.bone == '':
      ConstraintButtons.main(ConstraintButtons, context, layout, bpy.data.objects[self.object].constraints[self.target])

    elif context.mode == 'POSE':
      ConstraintButtons.main(ConstraintButtons, context, layout, bpy.data.objects[self.object].pose.bones[self.bone].constraints[self.target])

  # execute
  def execute(self, context):
    '''
      Execute the operator.
    '''

    # properties
    if self.properties:
      for area in context.screen.areas:
        if area.type in 'PROPERTIES':
          if self.bone == '':
            area.spaces.active.context = 'CONSTRAINT'
          elif context.mode == 'POSE':
            area.spaces.active.context = 'BONE_CONSTRAINT'
          else:
            area.spaces.active.context = 'CONSTRAINT'
    return {'FINISHED'}

  # invoke
  def invoke(self, context, event):
    '''
      Invoke the operator panel/menu, control its width.
    '''
    context.window_manager.invoke_popup(self, width=350)
    return {'RUNNING_MODAL'}

# pop up modifier
class modifier(ModifierButtons, Operator):
  '''
    This is operator is used to create the required pop-up panel.
  '''
  bl_idname = 'view3d.name_panel_modifier_settings'
  bl_label = 'Modifier'
  bl_description = 'Adjust the options for this modifier. (Experimental)'
  bl_options = {'REGISTER', 'UNDO'}

  # object
  object = StringProperty(
    name = 'Object',
    description = 'The object that the modifier is attached to.',
    default = ''
  )

  # target
  target = StringProperty(
    name = 'Target',
    description = 'The modifier you wish to edit the settings of.',
    default = ''
  )

  # properties
  properties = BoolProperty(
    name = 'Properties',
    description = 'Change any property window\'s context to modifier',
    default = False
  )

  # draw
  def draw(self, context):
    '''
      Draw the modifier options.
    '''

    # layout
    layout = self.layout

    # column
    column = layout.column()

    # label
    column.label(text=self.target + ':')

    # modifier
    ModifierButtons.main(ModifierButtons, context, layout, bpy.data.objects[self.object].modifiers[self.target], bpy.data.objects[self.object])


  # execute
  def execute(self, context):
    '''
      Execute the operator.
    '''

    # properties
    if self.properties:
      for area in context.screen.areas:
        if area.type in 'PROPERTIES':
          area.spaces.active.context = 'MODIFIER'

    return {'FINISHED'}

  # invoke
  def invoke(self, context, event):
    '''
      Invoke the operator panel/menu, control its width.
    '''
    context.window_manager.invoke_popup(self, width=350)
    return {'RUNNING_MODAL'}
