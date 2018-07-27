import bpy

from bpy.types import PropertyGroup, AddonPreferences
from bpy.props import *

from . import interface

from .config import defaults
from .utilities import get, update


class panel_options(PropertyGroup):
    id = StringProperty()
    id_org = StringProperty()

    label = StringProperty(
        name = 'Label',
        description = 'Name to display in the box panel header',
        default = '')

    hidden = BoolProperty(
        name = 'Hide',
        description='Hide this panel in the datablock popup',
        default = False)

    hide_header = BoolProperty(
        name = 'Hide Header',
        description='Hide this panels header & box background in the datablock popup',
        default = False)

    collapsed = BoolProperty(
        name = 'Collapse',
        description = 'Callapse this box panel',
        default = True)


class datablock(PropertyGroup):

    context = EnumProperty(
        name = 'Context',
        description = 'Type of active data to display and edit',
        items = get.datablock.contexts)

    render = CollectionProperty(
        name = 'Render',
        type = panel_options)

    render_layer = CollectionProperty(
        name = 'Render Layer',
        type = panel_options)

    scene = CollectionProperty(
        name = 'Scene',
        type = panel_options)

    world = CollectionProperty(
        name = 'World',
        type = panel_options)

    object = CollectionProperty(
        name = 'Object',
        type = panel_options)

    constraint = CollectionProperty(
        name = 'Constraint',
        type = panel_options)

    modifier = CollectionProperty(
        name = 'Modifier',
        type = panel_options)

    data = CollectionProperty(
        name = 'Data',
        type = panel_options)

    bone = CollectionProperty(
        name = 'Bone',
        type = panel_options)

    bone_constraint = CollectionProperty(
        name = 'Bone Constraint',
        type = panel_options)

    material = CollectionProperty(
        name = 'Material',
        type = panel_options)

    texture = CollectionProperty(
        name = 'Texture',
        type = panel_options)

    particles = CollectionProperty(
        name = 'Particles',
        type = panel_options)

    physics = CollectionProperty(
        name = 'Physics',
        type = panel_options)


class namestack(AddonPreferences):
    bl_idname = __name__.partition('.')[0]

    default = defaults['preferences']

    mode = EnumProperty(
        name = 'Mode',
        description = 'Adjust preferences',
        items = [
            ('GENERAL', 'General', ''),
            ('NAMESTACK', 'Name Stack', ''),
            ('DATABLOCK', 'Datablock', ''),
            ('BATCHNAME', 'Batch Name', ''),
            ('HOTKEY', 'Hotkeys', ''),
            ('UPDATES', 'Updates', '')],
        default = default['mode'])

    keep_session_settings = BoolProperty(
        name = 'Keep Session Settings',
        description = 'Keep common settings values related to this addon consistent across blend files\n  Note: resets on exit',
        default = default['keep_session_settings'])

    location = EnumProperty(
        name = 'Location',
        description = 'The 3D view shelf to use for the name stack',
        items = [
            ('TOOLS', 'Tool Shelf', 'Places the name stack in the tool shelf under the tab labeled \'Name\''),
            ('UI', 'Property Shelf', 'Places the name stack in the property shelf')],
        default = default['location'])

    pin_active = BoolProperty(
        name = 'Pin Active',
        description = 'Keep the active object/bone at the top of the name stack',
        default = default['pin_active'])

    click_through = BoolProperty(
        name = 'Click Through',
        description = 'Do not activate the pop-up when clicking a name stack icon',
        default = default['click_through'])

    remove_item_panel = BoolProperty(
        name = 'Remove Item Panel',
        description = 'Remove the item panel from the properties shelf when the name stack is present',
        update = update.prop_item_panel_poll,
        default = default['remove_item_panel'])

    filter_popup_width = IntProperty(
        name = 'Pop Up Width',
        description = 'Width of the filter pop up in pixels',
        min = 200,
        max = 1000,
        subtype = 'PIXEL',
        default = default['filter_popup_width'])

    separators = IntProperty(
        name = 'Separators',
        description = 'Number of separators between objects in the name stack',
        min = 0,
        max = 10,
        default = default['separators'])

    use_last = BoolProperty(
        name = 'Use Last Settings',
        description = 'When adding a naming operation use the previous settings',
        default = default['use_last'])

    datablock_popup_width = IntProperty(
        name = 'Pop Up Width',
        description = 'Width of the datablock properties pop up in pixels',
        min = 200,
        max = 1000,
        subtype = 'PIXEL',
        default = default['datablock_popup_width'])

    auto_name_operations = BoolProperty(
        name = 'Auto Name Operations',
        description = 'Automatically name operation entries based on operation modes',
        default = default['auto_name_operations'])

    batchname_popup_width = IntProperty(
        name = 'Pop Up Width',
        description = 'Width of the batch name pop up in pixels',
        min = 200,
        max = 1000,
        subtype = 'PIXEL',
        default = default['batchname_popup_width'])

    datablock_options = CollectionProperty(
        name = 'Datablock',
        type = datablock)

    update_check = BoolProperty(
        name = 'Check at startup',
        description = 'Check at blender startup for updates',
        default = default['update_check'])

    update_display_menu = BoolProperty(
        name = 'Display menu notification',
        description = 'Display update notification in the name panel specials menu',
        default = default['update_display_menu'])

    update_display_stack = BoolProperty(
        name = 'Display stack notification',
        description = 'Display update notificiation in the name stack',
        default = default['update_display_stack'])

    update_ready = BoolProperty(
        name = 'update_ready',
        description = 'Used internally to determine if an update is ready',
        default = False)


    def draw(self, context):
        interface.preferences(self, context)
