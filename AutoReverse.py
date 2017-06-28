import bpy
import math

scn = bpy.context.scene


class AutoReverse(bpy.types.Operator):
    bl_idname = "object.move_operator"
    bl_label = "Auto Reverse"

    def execute(self, context):
        # get all the leyframes from an object
        def get_keyframes(obj_list):
            keyframes = []
            for obj in obj_list:
                anim = obj.animation_data
                if anim is not None and anim.action is not None:
                    for fcu in anim.action.fcurves:
                        for keyframe in fcu.keyframe_points:
                            x, y = keyframe.co
                            if x not in keyframes:
                                keyframes.append((math.ceil(x)))
            return keyframes

        # this just shortens it for use later
        selection = bpy.context.selected_objects

        # this loop goes through all the selected objects
        for i in range(0, len(selection)):
            # and makes each individual one the only one active and selected
            bpy.context.scene.objects.active = selection[i]
            print(bpy.context.scene.objects.active)

            # check if it has animation data or is a rigid body
            if bpy.context.object.animation_data is not None or bpy.context.object.rigid_body.type != 'PASSIVE':
                # using that previous function to get the keyframes and putting them in an array
                keys = get_keyframes(selection)

                # print all keyframes for debugging
                print(keys)

                # gets the first and last frames
                firstFrame = keys[0]
                lastFrame = keys[-1]

                # de-selects all other objects so only the active one is selected
                for i in range(0, len(selection)):
                    if selection[i] != bpy.context.scene.objects.active:
                        selection[i].select = False

                # this is needed so everything else, even the other objects in "selection" are hidden and not disturbed later
                bpy.ops.object.hide_view_set(unselected=True)

                # bakes the rigid bodies to keyframes
                if bpy.context.object.rigid_body is not None:
                    try:
                        bpy.ops.rigidbody.bake_to_keyframes(frame_start=firstFrame, frame_end=lastFrame, step=1)
                    except:
                        pass

                # bakes everything to Action
                bpy.ops.nla.bake(frame_start=firstFrame, frame_end=lastFrame, step=1, bake_types={'OBJECT'})

                # scale it by -1 to reverse it, this is done in the graph editor which is why the context is changed
                old_type = bpy.context.area.type
                bpy.context.area.type = 'GRAPH_EDITOR'
                bpy.ops.graph.interpolation_type(type='CONSTANT')
                bpy.context.scene.frame_current = 1
                bpy.ops.transform.resize(value=(-1, 1, 1))
                bpy.context.area.type = old_type
                # un-hides everything
                bpy.ops.object.hide_view_clear()

        return {'FINISHED'}

        # else:
        # self.report({'ERROR'}, 'There is no animation')
        # return {'CANCELLED'}


def register():
    bpy.utils.register_class(AutoReverse)


if __name__ == "__main__":
    register()