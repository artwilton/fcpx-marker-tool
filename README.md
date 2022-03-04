## FCPX Marker Tool

This script takes FCPX .xml files as an input and prints chapter marker info.

Currently it prints the timecode of each chapter marker. Future updates will allow for the option of exporting this info to a .txt file formatted for DVD Studio Pro, or a YouTube Chapter list.

### Running the script

First cd into the repo directory aftering cloning or downloading, and run `pip install -r requirements.txt`

Then either run the module directly using:
```
Python -m fcpx_marker_tool
```
or run the main script directly with
```
Python fcpx_marker_tool/fcpx_marker_tool_v1.py
```

Then simply drag-and-drop or copy-and-paste the path to an FCPX .xml file when presented with the `Enter xml file path:` prompt.

### Demo

https://user-images.githubusercontent.com/69938486/150892485-56151086-6dde-4cf5-bc40-f5e1625eda28.mp4

---

#### Python Modules Used:

xml.etree.ElementTree - https://docs.python.org/3/library/xml.etree.elementtree.html

timecode - https://github.com/eoyilmaz/timecode
