"""
Automatically re-run blender.py within Blender whenever it changes.

This is a blender operator that monitors an external script and its
dependencies for any changes, and automatically re-runs the script any time a
change is made to any of these files.

This makes it easy to work on the CAD code in an external editor, and have the
changes automatically reflected in Blender whenever you save the files.

This automatically starts monitoring when you first run the script.
It adds entries to the main Edit menu to allow stopping and re-starting
monitoring.
"""

from __future__ import annotations

import bpy
import importlib
import sys
import traceback
from pathlib import Path
from typing import Dict, Optional


_instance: Optional[ScriptMonitorOperator] = None

MONITOR_PATH = "main.py"

# Additional dependencies to monitor.
# These should be listed in dependency order: if module A imports module B,
# B should be listed first in this list.
#
# In theory it would be nice to use the modulefinder library to automatically
# find the dependencies of the script.  Unfortunately modulefinder cannot
# currently handle numpy: https://bugs.python.org/issue40350
_DEPENDENCIES: Dict[Path, str] = {
    (Path("mantyl/cad.py"), "mantyl.cad"),
    (Path("mantyl/blender_util.py"), "mantyl.blender_util"),
    (Path("mantyl/keyboard.py"), "mantyl.keyboard"),
    (Path("mantyl/foot.py"), "mantyl.foot"),
    (Path("mantyl/i2c_conn.py"), "mantyl.i2c_conn"),
    (Path("mantyl/screw_holes.py"), "mantyl.screw_holes"),
    (Path("mantyl/kbd_halves.py"), "mantyl.kbd_halves"),
}


class ScriptMonitorOperator(bpy.types.Operator):
    """Monitor an external script for changes and re-run on change."""

    bl_idname = "script.external_script_monitor"
    bl_label = "Monitor External Script"
    # The REGISTER option allows our messages to be logged to the info console
    bl_options = {"REGISTER"}

    _timer = None
    stop: bool = False
    path: bpy.props.StringProperty(name="path")

    _local_dir: Path
    _abs_path: Path
    _timestamps: Dict[Path, Optional[float]]

    @classmethod
    def poll(cls, context):
        global _instance
        return _instance is None

    def modal(self, context, event):
        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        if self.stop:
            global _instance
            _instance = None
            self.cancel(context)
            self.report({"INFO"}, f"cancelling monitoring of {self._abs_path}")
            return {"CANCELLED"}

        self.check_for_updates()
        return {"PASS_THROUGH"}

    def execute(self, context):
        global _instance
        if _instance is not None:
            self.report({"Error"}, f"Script monitor is already running")
            return {"CANCELLED"}
        _instance = self

        self._local_dir = Path(bpy.data.filepath).parent.resolve()
        if self.path:
            self._abs_path = self._local_dir / self.path
        else:
            self._abs_path = self._local_dir / MONITOR_PATH

        self._timestamps = {}
        self._monitor_modules = [
            (self._local_dir / path, mod_name)
            for path, mod_name in _DEPENDENCIES
        ]

        self.report({"INFO"}, f"monitoring external script {self._abs_path}")
        self._timestamps = self._get_timestamps()
        self.run_script()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def check_for_updates(self):
        current = self._get_timestamps()
        if current == self._timestamps:
            return

        self._timestamps = current

        # Reload all modules.
        # This has to be done in the proper order, where modules are reloaded
        # after any other modules they depend on.
        for _path, module_name in self._monitor_modules:
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
        for path, _mod_name in self._monitor_modules:
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
        global_namespace = {
            "__file__": str(self._abs_path),
            "__name__": "__main__",
        }
        src_code = self._abs_path.read_text()
        exec(compile(src_code, str(self._abs_path), "exec"), global_namespace)


class CancelMonitorOperator(bpy.types.Operator):
    """Monitor an external script for changes and re-run on change."""

    bl_idname = "script.cancel_external_script_monitor"
    bl_label = "Cancel External Script Monitor"

    @classmethod
    def poll(cls, context):
        global _instance
        return _instance is not None

    def execute(self, context):
        global _instance
        if _instance is not None:
            _instance.stop = True

        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(
        ScriptMonitorOperator.bl_idname, text=ScriptMonitorOperator.bl_label
    )
    self.layout.operator(
        CancelMonitorOperator.bl_idname, text=CancelMonitorOperator.bl_label
    )


def register():
    bpy.utils.register_class(ScriptMonitorOperator)
    bpy.utils.register_class(CancelMonitorOperator)
    bpy.types.TOPBAR_MT_edit.append(menu_func)


# Register and add to the "view" menu (required to also use F3 search "Modal Timer Operator" for quick access)
def unregister():
    bpy.utils.unregister_class(ScriptMonitorOperator)
    bpy.utils.unregister_class(CancelMonitorOperator)
    bpy.types.TOPBAR_MT_edit.remove(menu_func)


if __name__ == "__main__":
    register()

    # Start the operator
    bpy.ops.script.external_script_monitor()
