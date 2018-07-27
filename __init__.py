# TODO: implement multi-object bone selection
'''
Copyright (C) 2018 Trentin Shaun Frederick

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    'name': 'Name Stack',
    'author': 'proxe',
    'version': (0, 9),
    'blender': (2, 79, 0),
    'location': '3D View > Tool (T) | Property (N)',
    'description': 'In panel datablock name stack with additional naming and productivity tools.',
    'tracker_url': 'https://github.com/proxeIO/name-stack/issues',
    'category': '3D View'}

import bpy

from bpy.props import PointerProperty
from bpy.utils import register_module, unregister_module, unregister_class

from . addon import menu, operator, panel, preferences
from . properties import options
from . addon.utilities import preferences, update


def register():
    register_module(__name__)

    context = bpy.context
    update.handlers(context)

    if preferences(context).remove_item_panel:
        update.item_panel_poll()

    bpy.types.WindowManager.namestack = PointerProperty(
        type = options,
        name = 'Name Stack Addon',
        description = 'Storage location for name stack addon options')

    update.keymap(context)


def unregister():
    context = bpy.context
    update.handlers(context, remove=True)
    update.item_panel_poll(restore=True)

    del bpy.types.WindowManager.namestack

    update.keymap(context, remove=True)

    unregister_module(__name__)
