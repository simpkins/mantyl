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


_instance: Optional[MonitorOperatorBase] = None

MONITOR_PATH = "main.py"

# Additional dependencies to monitor.
# These should be listed in dependency order: if module A imports module B,
# B should be listed first in this list.
#
# In theory it would be nice to use the modulefinder library to automatically
# find the dependencies of the script.  Unfortunately modulefinder cannot
# currently handle numpy: https://bugs.python.org/issue40350
_DEPENDENCIES: List[Tuple[Path, str]] = [
    (Path("mantyl/cad.py"), "mantyl.cad"),
    (Path("mantyl/blender_util.py"), "mantyl.blender_util"),
    (Path("mantyl/keyboard.py"), "mantyl.keyboard"),
    (Path("mantyl/foot.py"), "mantyl.foot"),
    (Path("mantyl/i2c_conn.py"), "mantyl.i2c_conn"),
    (Path("mantyl/screw_holes.py"), "mantyl.screw_holes"),
    (Path("mantyl/key_socket_holder.py"), "mantyl.key_socket_holder"),
    (Path("mantyl/kbd_halves.py"), "mantyl.kbd_halves"),
    (Path("mantyl/testing.py"), "mantyl.testing"),
]


class MonitorOperatorBase(bpy.types.Operator):
    """Monitor an external script for changes and re-run on change."""

    # The REGISTER option allows our messages to be logged to the info console
    bl_options = {"REGISTER"}

    _timer = None
    stop: bool = False

    _timestamps: Dict[Path, Optional[float]]
    _name: str = ""

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
            self.report({"INFO"}, f"cancelling monitoring of {self._name}")
            return {"CANCELLED"}

        self.check_for_updates()
        return {"PASS_THROUGH"}

    def execute(self, context):
        global _instance
        if _instance is not None:
            self.report({"Error"}, f"Script monitor is already running")
            return {"CANCELLED"}
        _instance = self

        self._timestamps = {}
        self._monitor_modules = self._init_monitor_modules()

        self.report({"INFO"}, f"monitoring external script {self._name}")
        self._timestamps = self._get_timestamps()
        self.on_change()

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
        importlib.invalidate_caches()
        for _path, module_name in self._monitor_modules:
            if module_name is None:
                continue
            mod = sys.modules.get(module_name, None)
            if mod is None:
                # This module isn't loaded, so we don't need to reload it.
                continue
            try:
                importlib.reload(mod)
            except Exception as ex:
                self._report_error(f"error reloading {module_name}")
                return

        self._timestamps = current
        self.on_change()

    def _get_timestamps(self) -> Dict[Path, Optional[float]]:
        result: Dict[Path, Optional[float]] = {}
        for path, _mod_name in self._monitor_modules:
            result[path] = self._get_timestamp(path)
        return result

    def _get_timestamp(self, path: Path) -> Optional[float]:
        try:
            s = path.stat()
        except IOError:
            return None
        return s.st_mtime

    def on_change(self):
        print("=" * 60, file=sys.stderr)
        print(f"Running {self._name}...", file=sys.stderr)
        self.report({"INFO"}, f"running {self._name}")
        try:
            self._run()
            print(f"Finished {self._name}")
        except Exception as ex:
            self._report_error(f"error running {self._name}")

    def _run(self):
        raise NotImplementedError("must be implemented by a subclass")

    def _report_error(self, msg: str) -> None:
        err_str = traceback.format_exc()
        self.report({"INFO"}, f"{msg}: {err_str}")
        print(f"{msg}: {err_str}")


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


class ScriptMonitorOperator(MonitorOperatorBase):
    bl_idname = "script.external_script_monitor"
    bl_label = "Monitor External Script"

    _local_dir: Path
    _abs_path: Path
    path: bpy.props.StringProperty(name="path")

    def _init_monitor_modules(self):
        self._local_dir = Path(bpy.data.filepath).parent.resolve()
        if self.path:
            self._abs_path = self._local_dir / self.path
        else:
            self._abs_path = self._local_dir / MONITOR_PATH
        self._name = self._abs_path

        monitor_modules = [
            (self._local_dir / path, mod_name)
            for path, mod_name in _DEPENDENCIES
        ]
        monitor_modules[self._abs_path] = None

        return monitor_modules

    def _run(self):
        global_namespace = {
            "__file__": str(self._abs_path),
            "__name__": "__main__",
        }
        src_code = self._abs_path.read_text()
        exec(compile(src_code, str(self._abs_path), "exec"), global_namespace)


class FunctionMonitorOperator(MonitorOperatorBase):
    bl_idname = "script.external_function_monitor"
    bl_label = "Monitor External Function"

    function: bpy.props.StringProperty(name="function")
    delete_all: bpy.props.BoolProperty(name="delete_all", default=True)

    _local_dir: Path
    _mod_name: str
    _fn_name: str

    def _init_monitor_modules(self):
        self._name = self.function

        parts = self.function.rsplit(".", 1)
        if len(parts) != 2:
            raise Exception(
                "invalid function name: must be of the form <module>.<name>"
            )
        self._mod_name, self._fn_name = parts

        importlib.import_module(self._mod_name)

        self._local_dir = Path(bpy.data.filepath).parent.resolve()
        monitor_modules = [
            (self._local_dir / path, mod_name)
            for path, mod_name in _DEPENDENCIES
        ]

        return monitor_modules

    def _run(self):
        if self.delete_all:
            if bpy.context.object is not None:
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete(use_global=False)

        module = sys.modules[self._mod_name]
        fn = getattr(module, self._fn_name)
        fn()


def menu_func(self, context):
    self.layout.operator(
        ScriptMonitorOperator.bl_idname, text=ScriptMonitorOperator.bl_label
    )
    self.layout.operator(
        CancelMonitorOperator.bl_idname, text=CancelMonitorOperator.bl_label
    )


def register():
    bpy.utils.register_class(ScriptMonitorOperator)
    bpy.utils.register_class(FunctionMonitorOperator)
    bpy.utils.register_class(CancelMonitorOperator)
    bpy.types.TOPBAR_MT_edit.append(menu_func)


# Register and add to the "view" menu (required to also use F3 search "Modal Timer Operator" for quick access)
def unregister():
    bpy.utils.unregister_class(ScriptMonitorOperator)
    bpy.utils.unregister_class(FunctionMonitorOperator)
    bpy.utils.unregister_class(CancelMonitorOperator)
    bpy.types.TOPBAR_MT_edit.remove(menu_func)


def main(fn_name: str) -> None:
    try:
        register()
        bpy.ops.script.external_function_monitor(function=fn_name)
    except Exception as ex:
        import logging

        logging.exception(f"unhandled exception: {ex}")
        sys.exit(1)
