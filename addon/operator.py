import bpy

from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty


from . import interface
from .utilities import get, update
from .config import defaults


class clear_find(Operator):
    bl_idname = 'namestack.clear_find'
    bl_label = 'Clear Find'
    bl_description = 'Clear the find field'


    def execute(self, context):

        get.namestack.options(context).find = ''

        return {'FINISHED'}


class clear_replace(Operator):
    bl_idname = 'namestack.clear_replace'
    bl_label = 'Clear Replace'
    bl_description = 'Clear the replace field'


    def execute(self, context):

        get.namestack.options(context).replace = ''

        return {'FINISHED'}


class options(Operator):
    bl_idname = 'namestack.options'
    bl_label = 'Display Options'
    bl_description = 'Adjust display options for the name stack'


    def check(self, context):
        return True


    def draw(self, context):
        interface.namestack.options(self, context)


    def invoke(self, context, event):

        context.window_manager.invoke_popup(self, width=get.preferences(context).filter_popup_width)

        return {'RUNNING_MODAL'}


    def execute(self, context):
        return {'FINISHED'}


class datablock(Operator):
    bl_idname = 'namestack.datablock'
    bl_label = 'Datablock Settings'
    bl_description = 'Adjust datablock settings\n  Ctrl \N{Rightwards Arrow} Display pop-up\n  Alt \N{Rightwards Arrow} Center view on selected\n  Shift \N{Rightwards Arrow} Add/Remove selection'
    bl_options = {'REGISTER', 'UNDO'}

    click_through = BoolProperty(
        name = 'Click Through',
        description = 'Do not activate the pop-up when clicking the datablock icon in the stack',
        default = False)

    context_override = StringProperty(
        name = 'Context',
        description = 'Context to load',
        default = 'render')

    object_name = StringProperty(
        name = 'Object',
        description = 'Base object',
        default = '')

    target_name = StringProperty(
        name = 'Target',
        description = 'Target datablock',
        default = '')

    identifier = StringProperty(
        name = 'Identifier',
        description = 'RNA type identifier for the target datablock',
        default = '')


    def check(self, context):
        return True


    def draw(self, context):
        interface.datablock(self, context)


    def invoke(self, context, event):

        if self.object_name:
            update.selection(self, context, event)

            if event.alt:
                bpy.ops.view3d.view_selected()

            if self.click_through:
                self.click_through = False
                if event.ctrl:
                    context.window_manager.invoke_popup(self, width=get.preferences(context).datablock_popup_width)
                    return {'RUNNING_MODAL'}
                else:
                    return {'FINISHED'}
            elif event.ctrl:
                return {'FINISHED'}
            else:
                context.window_manager.invoke_popup(self, width=get.preferences(context).datablock_popup_width)
                return {'RUNNING_MODAL'}

        else:
            context.window_manager.invoke_popup(self, width=get.preferences(context).datablock_popup_width)
        return {'RUNNING_MODAL'}


    def execute(self, context):
        return {'FINISHED'}


class info_update(Operator):
    bl_idname = 'namestack.info_update'
    bl_label = 'Update Info'
    bl_description = 'Get Latest update information'
    bl_options = {'INTERNAL'}


    def check(self, context):
        return True


    def draw(self, context):

        layout = self.layout

        column = layout.column(align=True)
        row = column.row()

        if get.preferences(context).update_ready:

            row.alignment = 'CENTER'
            row.label(text='New Update! ({})'.format(get.version.remote_string()))

            for line in get.version.remote_info().split('\n'):
                row = column.row()
                row.scale_y = 0.6
                row.label(line)

            row = column.row()
            row.scale_y = 1.5
            row.operator('wm.name_stack_update_addon', text='Update')

        elif not update.check.connection():

            row.alignment = 'CENTER'
            row.label(text='Unable to connect to github', icon='ERROR')


        else:

            row.alignment = 'CENTER'
            row.label(text='Your version is up to date!')


    def invoke(self, context, event):
        context.window_manager.invoke_popup(self, width=get.preferences(context).batchname_popup_width)
        return {'RUNNING_MODAL'}


    def execute(self, context):
        return {'FINISHED'}


class confirm_update(Operator):
    bl_idname = 'namestack.confirm_update'
    bl_label = ''
    bl_description = ''
    bl_options = {'INTERNAL'}


    def check(self, context):
        return True


    def draw(self, context):

        layout = self.layout

        layout.separator()
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text='Successfully updated')
        layout.separator()


    def invoke(self, context, event):
        context.window_manager.invoke_popup(self, width=get.preferences(context).batchname_popup_width)
        return {'RUNNING_MODAL'}


    def execute(self, context):
        return {'FINISHED'}


class batchname(Operator):
    bl_idname = 'namestack.batchname'
    bl_label = 'Batch Name'
    bl_description = 'Batch name datablocks'


    def check(self, context):
        return True


    def draw(self, context):
        interface.batchname(self, context)


    def invoke(self, context, event):

        self.area_type = context.area.type

        context.window_manager.invoke_props_dialog(self, width=get.preferences(context).batchname_popup_width)

        return {'RUNNING_MODAL'}


    def execute(self, context):
        return {'FINISHED'}


class add_operation(Operator):
    bl_idname = 'namestack.batchname_add_operation'
    bl_label = 'Add'
    bl_description = 'Add another name operation to the list'
    bl_options = {'INTERNAL'}


    def execute(self, context):

        naming = get.batchname.options(context).name_options['options']

        if naming.operation_options:
            prior_operation = naming.operation_options[naming.active_index]
            active_index = len(naming.operation_options) - 1

            prior_operation.name = get.batchname.operation_name(prior_operation)
            naming.operation_options.add().name = get.batchname.operation_name(prior_operation)

            active_index += 1

            if get.preferences(context).use_last:
                options = [option for option in defaults['batchname']['operation']]

                for option in options:
                    setattr(naming.operation_options[active_index], option, getattr(prior_operation, option))

            else:
                naming.operation_options[active_index].name = 'Default'

            naming.active_index = active_index

        else:
            naming.operation_options.add().name = 'Default'
            naming.active_index = 0

        return {'FINISHED'}


class remove_operation(Operator):
    bl_idname = 'namestack.batchname_remove_operation'
    bl_label = 'Remove'
    bl_description = 'Remove active name operation from the list\n  Alt \N{Rightwards Arrow} to clear all)'
    bl_options = {'INTERNAL'}

    all = BoolProperty()


    def invoke(self, context, event):

        self.all = True if event.alt else False
        self.execute(context)

        return {'FINISHED'}


    def execute(self, context):

        naming = get.batchname.options(context).name_options['options']

        if len(naming.operation_options):
            if not self.all:
                naming.operation_options.remove(naming.active_index)
                naming.active_index -= 1 if naming.active_index != 0 else 0

            else:
                naming.active_index = 0
                naming.operation_options.clear()


class rename_operation(Operator):
    bl_idname = 'namestack.batchname_rename_operation'
    bl_label = 'Rename Active'
    bl_description = 'Automatically rename active name operation'
    bl_options = {'INTERNAL'}


    def execute(self, context):

        naming = get.batchname.options(context).name_options['options']
        operation = naming.operation_options[naming.active_index]

        operation.name = get.batchname.operation_name(operation)

        return {'FINISHED'}


class rename_all_operations(Operator):
    bl_idname = 'namestack.batchname_rename_all_operations'
    bl_label = 'Rename All'
    bl_description = 'Automatically rename all naming operations'
    bl_options = {'INTERNAL'}


    def execute(self, context):

        naming = get.batchname.options(context).name_options['options']

        for operation in naming.operation_options:
            operation.name = get.batchname.operation_name(operation)
        return {'FINISHED'}


class move_operation(Operator):
    bl_idname = 'namestack.batchname_move_operation'
    bl_label = 'Move'
    bl_description = 'Move active name operation'
    bl_options = {'INTERNAL'}

    up = BoolProperty()


    def execute(self, context):

        naming = get.batchname.options(context).name_options['options']

        if self.up:
            naming.operation_options.move(naming.active_index, naming.active_index - 1)
            naming.active_index -= 1 if naming.active_index > 0 else 0

        else:
            naming.operation_options.move(naming.active_index, naming.active_index + 1)
            naming.active_index += 1 if naming.active_index < len(naming.operation_options) - 1 else 0

        return {'FINISHED'}


class use_shading_nodes(Operator):
    bl_idname = 'namestack.datablock_use_shading_nodes'
    bl_label = 'Use Nodes'

    context = EnumProperty(
        name = 'Context',
        description = 'Context the datablock pop up is in',
        items = [
            ('WORLD', 'World', ''),
            ('MATERIAL', 'Material', ''),
            ('DATA', 'Data', '')],
        default = 'WORLD')

    def execute(self, context):
        if self.context == 'WORLD':
            context.scene.world.use_nodes = True
        if self.context == 'MATERIAL':
            context.active_object.material_slots.data.active_material.use_nodes = True
        if self.context == 'DATA':
            context.active_object.data.use_nodes = True

        return {'FINISHED'}
