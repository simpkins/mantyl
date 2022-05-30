import bpy
import importlib
import sys
import traceback
from pathlib import Path
from typing import Dict, Optional


class ScriptMonitorOperator(bpy.types.Operator):
    """Monitor external scripts for changes and re-run on change."""
    bl_idname = "script.monitor_external_script"
    bl_label = "Monitor External Script"
    # The REGISTER option allows our messages to be logged to the info console
    bl_options = {"REGISTER"}

    _timer = None
    path: bpy.props.StringProperty(name="path")
    
    _abs_path: Path
    _timestamps: Dict[Path, Optional[float]] = {}

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            self.report({"INFO"}, f"cancelling monitoring of {self._abs_path}")
            return {'CANCELLED'}

        if event.type == 'TIMER':
            self.check_for_updates()

        return {'PASS_THROUGH'}

    def execute(self, context):
        dir_path = Path(bpy.data.filepath).parent
        self._abs_path = dir_path / self.path
        self._monitor_modules = {
            dir_path / "cad.py": "cad",
            dir_path / "oukey2.py": "oukey2",
        }
              
        self.report({"INFO"}, f"monitoring external script {self._abs_path}")
        self._timestamps = self._get_timestamps()
        self.run_script()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        
    def check_for_updates(self):
        current = self._get_timestamps()
        if current == self._timestamps:
            return
        
        self._timestamps = current
        
        # Reload all modules.
        # Do this twice to make sure that we load the new versions of all modules,
        # and then we reprocess everything so that if one module uses another, it sees
        # the new version of its dependency when we reload it the second time.
        for n in (1, 2):
            for module_name in self._monitor_modules.values():
                mod = sys.modules[module_name]
                try:
                    importlib.reload(mod)
                except Exception as ex:
                    self._report_error(f"error reloading {module_name}")
                    return

        self._timestamps = current
        self.run_script()
        
    def _get_timestamps(self) -> Dict[Path, Optional[float]]:
        ts = self._get_timestamp(self._abs_path)
        result = {self._abs_path: ts}
        for path in self._monitor_modules:
            result[path] = self._get_timestamp(path)
        return result
        
    def _get_timestamp(self, path: Path) -> Optional[float]:
        try:
            s = path.stat()
        except IOError:
            return None
        return s.st_mtime
    
    def run_script(self):
        self.report({"INFO"}, f"running {self._abs_path}")
        try:
            self._execute_script()
        except Exception as ex:
            self._report_error(f"error running {self._abs_path}")
            
    def _report_error(self, msg: str) -> None:
        err_str = traceback.format_exc()
        self.report({"INFO"}, f"{msg}: {err_str}")
        print(f"{msg}: {err_str}")
        
    def _execute_script(self):
        global_namespace = {"__file__": str(self._abs_path), "__name__": "__main__"}
        src_code = self._abs_path.read_text()
        exec(compile(src_code, str(self._abs_path), "exec"), global_namespace)


def menu_func(self, context):
    self.layout.operator(ScriptMonitorOperator.bl_idname, text=ScriptMonitorOperator.bl_label)


def register():
    bpy.utils.register_class(ScriptMonitorOperator)
    bpy.types.VIEW3D_MT_view.append(menu_func)


# Register and add to the "view" menu (required to also use F3 search "Modal Timer Operator" for quick access)
def unregister():
    bpy.utils.unregister_class(ScriptMonitorOperator)
    bpy.types.VIEW3D_MT_view.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.script.monitor_external_script(path="blender.py")
