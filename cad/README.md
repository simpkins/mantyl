# Running the Mesh Generation Code

This code requires Blender 2.91+ for its improved boolean operator support.
I have primarily been using Blender 3.1.2 for development.

## Generating STL Files

The `generate_stl.py` file will export STL files for all of the keyboard parts.
It will place them inside an `_out/` directory.

This script can be run from the command line as follows:

```
blender -b -P generate_stl.py
```

## Development

If you want to make changes to the CAD logic, using the `test.py` script is the
easiest way to do this.

You can start it from the command line as follows:

```
blender -P test.py
```

This will launch blender and run the code from
[`mantyl/testing.py`](mantyl/testing.py).  Whenever
any of the source code files are updated it will reload and re-run the code to
redisplay the generated objects.

This makes it easy to edit the Python source code and have blender
automatically redisplay changes each time you save any of the files.

The logic for monitoring source code changes is in
[`mantyl/auto_update.py`](mantyl/auto_update.py).

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

## Units

My scripts are written with the units in millimeters.  Historically this was
because I initially developed the keyboard model in OpenSCAD rather than
Blender, which uses units in millimeters rather than meters.

However, using millimeters works nicely in practice for Blender too: this
avoids having to scale the units by 1000 when exporting to an STL file, as 3D
print software generally assumes the STL units are in millimeters, while
Blender emits the units as meters by default.

## OpenSCAD

I initially attempted to build the keyboard model using OpenSCAD.  However, it
unfortunately has many more problems than Blender with generating bad geometry
after performing hull, union, and difference operations on objects in arbitrary
locations.  These problems unfortunately typically don't manifest themselves
until after you generate an STL file and attempt to slice it for 3D printing.
With OpenSCAD it was also much harder to detect which faces / facets were
problematic.
