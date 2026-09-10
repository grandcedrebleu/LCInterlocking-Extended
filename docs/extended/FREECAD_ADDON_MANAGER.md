# Distribution through FreeCAD Addon Manager

The generated workbench contains a standard FreeCAD `package.xml` with a Workbench
content item. No program-files or AppData path is embedded.

Publication steps:

1. Publish this maintenance repository to GitHub.
2. Let the workflow generate the `dist` branch and release ZIP.
3. Test that generated tree using Addon Manager developer/custom-source facilities.
4. Submit the installable repository/branch to the current FreeCAD Addons catalog.
5. After catalog inclusion, users install and update it from FreeCAD itself.

The current Addon Manager obtains its main catalog from the FreeCAD/Addons repository
and uses `package.xml` metadata to describe workbenches.
