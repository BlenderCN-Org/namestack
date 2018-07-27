import bpy

from bpy.types import Menu

from . import interface


class specials(Menu):
    bl_idname = 'namestack.specials'
    bl_label = 'Specials'
    bl_description = 'Tools and Options'


    def draw(self, context):
        interface.namestack.specials(self, context)


class search_specials(Menu):
    bl_idname = 'namestack.batchname_search_specials'
    bl_label = 'Search Options'


    def draw(self, context):
        interface.batchname.search_specials(self, context)


class move_search_specials(Menu):
    bl_idname = 'namestack.batchname_move_search_specials'
    bl_label = 'Search Options'


    def draw(self, context):
        interface.batchname.move_search_specials(self, context)


class swap_search_specials(Menu):
    bl_idname = 'namestack.batchname_swap_search_specials'
    bl_label = 'Search Options'


    def draw(self, context):
        interface.batchname.swap_search_specials(self, context)


class operation_specials(Menu):
    bl_idname = 'namestack.batchname_operation_specials'
    bl_label = 'Name Operation Specials'


    def draw(self, context):
        interface.batchname.operation_specials(self, context)
