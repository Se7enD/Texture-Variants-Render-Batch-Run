# -------------------------------------------------
#   Render batch run
# -------------------------------------------------

bl_info = {
    'name': 'Textures Variants Render Batch Run',
    'description': 'Renders scene variations based on textures stored in a directory',
    'author': 'Svend Richter',
    'version': (0, 1, 2),
    'blender': (2, 79, 0),
    'location': 'Properties > Render',
    'warning': 'Alpha Version', # used for warning icon and text in addons panel
    #'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/'
    #            'Scripts/My_Script',
    #'tracker_url': 'https://developer.blender.org/maniphest/task/edit/form/2/',
    #'support': 'COMMUNITY',
    'category': 'Render'
    }


# -------------------------------------------------
#   Initial
# -------------------------------------------------

# Imports
import bpy, os

from bpy.props import (
    StringProperty,
    PointerProperty,
    CollectionProperty,
    EnumProperty
    )

from bpy.utils import (
    register_class,
    unregister_class
    )


# Pick object
bpy.types.Scene.picked_object = PointerProperty(
    type = bpy.types.Object,
    name = 'Pick object'
    )

# Global variables
picked_object_global = None
message = ''


# Define input fields
bpy.types.Scene.in_dir_path = StringProperty (
    name = 'Input directory',
    default = '',
    description  = 'Define the input path of the batch',
    subtype = 'DIR_PATH'
    )

bpy.types.Scene.out_dir_path = StringProperty (
    name = 'Output directory',
    default = '',
    description  = 'Define the output path of the batch',
    subtype = 'DIR_PATH'
    )


# Print object dump
def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))


# Clear property
def reset():
    bpy.context.scene.collection.clear()
    print('####### Cleared the whole collection. #######')


# -------------------------------------------------
#   Render batch function
# -------------------------------------------------

def renderBatch(context):

    texture_list = os.listdir(context.scene.in_dir_path)
    texture_count = len([f for f in texture_list if os.path.isfile(os.path.join(context.scene.in_dir_path, f))])

    global message

    #Render with all textures in directory
    for texture in texture_list:

        # Get texture node from picked object
        if picked_object_global.active_material != None:
            material = picked_object_global.active_material
            if material.use_nodes:
                node_tree = material.node_tree
                texture_node = node_tree.nodes.get('Image Texture', None)
                if texture_node != None:
                    message = 'Texture node found: ' + str(texture_node)
                    print(message)

                    # Get texture path
                    texture_path = context.scene.in_dir_path + '\\' + texture
                    new_texture = bpy.data.images.load(texture_path, check_existing=False)
                    texture_node.image = new_texture

                    print('Picked object: ' + str(picked_object_global.active_material))
                    print('Rendering texture: ' + texture)

                	# Set output filename
                    bpy.data.scenes['Scene'].render.filepath = context.scene.out_dir_path + '//Output_' + texture

                    # Render and store the scene
                    bpy.ops.render.render(write_still=True)

                    print('Finished: ' + texture)

                else:
                    message = 'No image texture node found in ' + str(material.name)
                    print(message)
            else:
                message = str(picked_object_global.name) + ' does not use nodes'
                print(message)
        else:
            message = str(picked_object_global.name) + ' has no material'
            print(message)

    print('####### Rendered images with ' + str(texture_count) + ' textures successfully! #######')
    return {'FINISHED'}



# -------------------------------------------------
#   Button classes
# -------------------------------------------------

# Scene items
class SceneItems(bpy.types.PropertyGroup):
    value = bpy.props.IntProperty()


# Add new object Button
class AddButtonOperator(bpy.types.Operator):
    bl_idname = 'scene.add_button_operator'
    bl_label = 'Add new object'

    def execute(self, context):
        id = len(context.scene.collection)+1
        new = context.scene.collection.add()
        new.name = str(id)
        new.value = id
        print('Added object no.', id)
        return {'FINISHED'}


# Remove object Button
class RemoveButtonOperator(bpy.types.Operator):
    bl_idname = 'scene.remove_button_operator'
    bl_label = 'Remove object'
    id = bpy.props.IntProperty()

    def execute(self, context):
        for i, obj in enumerate(bpy.context.scene.collection):
            if str(self.id) == str(obj.name):
                bpy.context.scene.collection.remove(i)
                print('Removed object at index no.', i + 1)
        return {'FINISHED'}


# Start render button
class RenderButtonOperator(bpy.types.Operator):
    bl_idname = 'start.batch'
    bl_label = 'Start batch run'

    def execute(self, context):
        print('')
        print('Rendering images from ' + str(len(context.scene.in_dir_path)) + ' textures.')
        print('Input directory: ' + context.scene.in_dir_path)
        print('Output directory: ' + context.scene.out_dir_path)
        print('')
        renderBatch(context)
        return {'FINISHED'}


# Print collection button
class PrintCollectionOperator(bpy.types.Operator):
    bl_idname = 'print.collection'
    bl_label = 'Print collection'

    def execute(self, context):
        print('')
        print('Items in scene collection: ')
        for obj in bpy.context.scene.collection:
            print(obj)
        print('')
        return {'FINISHED'}


# Reset collection button
class ResetCollectionOperator(bpy.types.Operator):
    bl_idname = 'reset.collection'
    bl_label = 'Reset collection'

    def execute(self, context):
        reset()
        return {'FINISHED'}


# -------------------------------------------------
#   Panel
# -------------------------------------------------

class FancyPanel(bpy.types.Panel):
    bl_label = 'Render batch run'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        row = self.layout.row(align=True)
        row.operator('scene.add_button_operator')
        row.operator('print.collection')
        row.operator('reset.collection')

        global message

        for item in context.scene.collection:
            box = self.layout.box()
            boxrow = box.row(align=True)

            # Panel Header
            boxrow.label(text = 'Object ' + item.name)
            boxrow.operator('scene.remove_button_operator', text='', emboss=False, icon='X').id = item.value

            # Search field
            box.prop_search(context.scene, 'picked_object', context.scene, 'objects')

            # Object Info
            picked_object = context.scene.picked_object
            global picked_object_global
            picked_object_global = context.scene.picked_object

            # Message label
            if picked_object != None:
                if picked_object.active_material != None:

                    # Material selection
                    if picked_object:
                        is_sortable = len(picked_object.material_slots) > 1
                        rows = 1
                        if (is_sortable):
                            rows = 4

                        row = box.row()
                        row.template_list('MATERIAL_UL_matslots', '', picked_object, 'material_slots', picked_object, 'active_material_index', rows=rows)

                        col = row.column(align=True)

                        if is_sortable:
                            col.separator()

                            col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                            col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

                        row = box.row(align=True)
                        row.operator("object.material_slot_assign", text="Assign as active material")

                    material = picked_object.active_material
                    if material.use_nodes:
                        node_tree = material.node_tree
                        texture_node = node_tree.nodes.get('Image Texture', None)
                        if texture_node != None:
                            message = 'Image texture node found'
                            box.label(text = message)

                            # Input directory field
                            box.prop(context.scene, 'in_dir_path')
                        else:
                            message = 'No image texture node found in ' + str(material.name)
                            box.label(text = message, icon='ERROR')
                    else:
                        message = str(picked_object_global.name) + ' does not use nodes'
                        box.label(text = message, icon='ERROR')
                else:
                    message = str(picked_object_global.name) + ' has no material'
                    box.label(text = message, icon='ERROR')
            else:
                message = 'No object selected'
                box.label(text = message, icon='ERROR')



        row = self.layout.row(align=True)
        row.prop(context.scene, 'out_dir_path')

        row = self.layout.row(align=True)
        row.alignment = 'EXPAND'
        row.scale_y = 1.5
        row.operator('start.batch')


# -------------------------------------------------
#   Register / unregister
# -------------------------------------------------

classes = (
    SceneItems,
    AddButtonOperator,
    RemoveButtonOperator,
    PrintCollectionOperator,
    ResetCollectionOperator,
    RenderButtonOperator,
    FancyPanel
)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.collection = bpy.props.CollectionProperty(type=SceneItems)


def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.collection

if __name__ == "__main__":
    register()
