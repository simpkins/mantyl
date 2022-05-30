# Running the Mesh Generation Code

This code requires Blender 2.91+ for its improved boolean operator support.
I have primarily been using Blender 3.1.2 for development.

## One-off Generation

If you simply want to generate the keyboard mesh, the simplest way is
by starting blender with the script on the command line:

```
blender -P main.py
```
## Development

If you want to modify the Python code that generates the mesh, you could add
main.py as a script in Blender and then run it.  However, I find it easier to
do development using the `auto_update.py` script.  This script monitors
`main.py` and the modules it depends on, and re-runs main.py whenever the files
change.  This makes it easy to edit the scripts with an external editor, and
have blender re-render the mesh any time you save the files.

To do this, simply open `auto_update.py` in a blender text area, and then use
Alt-P to run it.  It will start monitoring `main.py` when invoked.  Monitoring
can be canceled through the Edit menu, if desired.

# Checking for Errors

Blender's boolean operators can occasionally generate bad geometry.  This
sometimes happens if the operation generates new vertices at the mesh
intersection points that are very close to existing vertices.  This can result
in faces that intersect, which may cause problems when attempting to slice the
model for 3D printing.

The easiest way to detect this problem is with Blender's
[3D Print Toolbox](https://docs.blender.org/manual/en/latest/addons/mesh/3d_print_toolbox.html).
Enable the toolbox in the Add-On preferences.  After enabling it, press `N` in
an 3D view area to show the sidebar, and a "3D-Print" tab will be available.
This tab has buttons to check for intersections, and can highlight intersecting
faces.

# Other Notes

I initially attempted to build the keyboard model using OpenSCAD.  However, it
unfortunately has many more problems than Blender with generating bad geometry
after performing hull, union, and difference operations on objects in arbitrary
locations.  These problems unfortunately typically don't manifest themselves
until after you generate an STL file and attempt to slice it for 3D printing.
With OpenSCAD it was also much harder to detect which faces / facets were
problematic.
