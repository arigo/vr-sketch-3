Folder for files with the .vrsketch extension.
These are the files that show up in the VR menu.

Use

    python ..\Python\vrconv.py  INPUTFILE  OUTPUTFILE

to convert between a .vrsketch and a .skp (SketchUp) file.  Note that many
features in the .skp file are lost in this conversion.  If OUTPUTFILE
already exists, the old version is first renamed to ``OUTPUTFILE~``.
