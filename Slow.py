bl_info = {
    "name": "Slow Time",
    "description": "Automatically 'slows' time in any animation or rigid body simulation",
    "author": "Freddie Rawlins",
    "version": (1.0),
    "blender": (2, 7, 6),
    "api": 31236,
    "location": "View3D > Specials > Slow",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Animation"
}

import bpy
import math
from bpy.props import *

scn = bpy.context.scene

# initialising the variables that will be in the dialog
firstSlowFrame = 40
lastSlowFrame = 60
scaleFactor = 1
globalSelect = False


class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "Slow Operator"

    # create the sliders (and checkbox) in the dialog box so the user can change where the slo-mo starts and ends
    firstSlowFrameP = bpy.props.IntProperty(
        name="First Slow Frame:",  # as you want it to appear on the slider
        default=40,  # optional
        description="This is the first frame that will be in slow motion"
    )

    lastSlowFrameP = bpy.props.IntProperty(
        name="Last Slow Frame:",  # as you want it to appear on the slider
        default=60,  # optional
        description="This is the last frame that will be in slow motion"
    )

    scaleFactorP = bpy.props.IntProperty(
        name="Slow Factor",  # as you want it to appear on the slider
        default=1,  # optional
        description="This is how much it will be slowed down by; 1 is nothing, 2 is half as fast"
    )

    globalSelect = bpy.props.BoolProperty(
        name="Global",  # affect all objects in scene
        default=False,
        description="If true, all available objects will be affected"
    )

    def execute(self, context):
        # first thing is to globalise the variables needed, and yes I know this isn't the best way
        global firstSlowFrame, lastSlowFrame, scaleFactor, globalSelect

        # this is just for troubleshooting
        print("Dialog Runs")
        print(self.firstSlowFrameP, self.lastSlowFrameP, self.scaleFactorP, self.globalSelect)

        # reassign the variables based on the user's input on the sliders
        firstSlowFrame = self.firstSlowFrameP
        lastSlowFrame = self.lastSlowFrameP
        scaleFactor = self.scaleFactorP
        globalSelect = self.globalSelect

        # this actually calls the operator that does the editing
        bpy.ops.slow.move_operator()
        return {'FINISHED'}

    def invoke(self, context, event):
        # call itself and run
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


# this just exists so that when you click on "Slow" in the menu, it calls the dialog instead of just executing
class slowClick(bpy.types.Operator):
    bl_idname = "slowclick.move_operator"
    bl_label = "Slow"

    def execute(self, context):
        # Default can be used since I only have a single dialog
        bpy.ops.object.dialog_operator('INVOKE_DEFAULT')

        return {'FINISHED'}


class Slow(bpy.types.Operator):
    bl_idname = "slow.move_operator"
    bl_label = "OK"

    # get the global variables since this is in a class
    global firstSlowFrame, lastSlowFrame, scaleFactor, globalSelect

    # this is here to get all the keyframes in any given animation, really useful
    def execute(self, context):
        # get keyframes of object list
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

        # select ALL objects if the checkbox for "global" is ticked in the dialog
        if globalSelect == True:
            for obj in bpy.data.objects:
                obj.select = False

        # this just shortens it for use later
        selection = bpy.context.selected_objects

        # this loop goes through all the selected objects
        for i in range(0, len(selection)):
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

                # which is needed so everything else, even the other objects in "selection" are hidden and not disturbed later
                bpy.ops.object.hide_view_set(unselected=True)

                # bakes the rigid bodies to keyframes
                if bpy.context.object.rigid_body is not None:
                    try:
                        bpy.ops.rigidbody.bake_to_keyframes(frame_start=firstFrame, frame_end=lastFrame, step=1)
                    except:
                        pass

                # bakes everything to Action
                bpy.ops.nla.bake(frame_start=firstFrame, frame_end=lastFrame, step=1, bake_types={'OBJECT'})

                # "total" variable used in working out how far keyframes should be moved
                total = (lastSlowFrame - firstSlowFrame)

                # setting context
                old_type = bpy.context.area.type
                bpy.context.area.type = 'DOPESHEET_EDITOR'
                print(bpy.context.area.type)

                # Here, all the moving takes place first so the scaling doesn't affect any other keyframes

                # selecting second outer strip and moving it so it won't be disturbed in scaling and will be in the right position after
                bpy.context.scene.frame_current = lastSlowFrame
                bpy.ops.action.select_leftright(mode='RIGHT', extend=False)
                bpy.ops.transform.transform(mode='TIME_TRANSLATE', value=(
                ((total * scaleFactor) - (total)), 0, 0, 0))  # this works out how far it should move

                # select slow frames
                bpy.context.scene.frame_current = firstSlowFrame
                bpy.ops.action.select_leftright(mode='RIGHT', extend=False)
                bpy.context.scene.frame_current = lastSlowFrame
                bpy.ops.action.select_leftright(mode='LEFT', extend=True)
                bpy.ops.action.select_all_toggle(invert=True)

                # moving and then scaling the slow frames
                bpy.ops.transform.transform(mode='TIME_TRANSLATE', value=(
                (((total * scaleFactor) - (total)) / 2), 0, 0, 0))  # similar equation

                # set the frame to be in the centre for proper scaling
                bpy.ops.action.frame_jump()
                bpy.ops.transform.transform(mode='TIME_SCALE', value=((scaleFactor), 0, 0, 0))

                # reverts back to old type (3D Viewport)
                bpy.context.area.type = old_type

                # un-hides everything
                bpy.ops.object.hide_view_clear()

                # used to determine which iteration you are on for debugging
                print(selection)

        return {'FINISHED'}

        # Currently unneccessary since you can use "Global" when there's nothing selected, but exists if people want it
        # else:
        # self.report({'ERROR'}, 'There is no animation')
        # return {'CANCELLED'}


# registers everything
def register():
    bpy.utils.register_class(Slow)
    bpy.utils.register_class(slowClick)
    bpy.utils.register_class(DialogOperator)


if __name__ == "__main__":
    register()


