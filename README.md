## FCPX Marker Tool

This package allows for parsing, displaying, and saving marker metadata from FCPXML files in both .fcpxml and .fcpxmld formats.

Version 2 has now been released, and was completely rewritten and redesigned to allow for new features to be added much more easily. One notable addition is the ability to export a YouTube chapter list.

In future updates users will be able to `import fcpx_marker_tool` for use in their own scripts, as this module extracts and formats metadata pertaining to all timelines, clips, and markers found in the FCPXML file. (Note: this is technically possible now but the API is subject to change until a future release.)

----

### Installation

First cd into the repo directory aftering cloning or downloading, and run `pip install .` which will run `setup.py` and install necessary dependencies along with the `fcpx-marker-tool` package.

Now you can simply run `fcpx-marker-tool` in your terminal, which by default will bring up a command prompt where you can drag-and-drop or copy-and-paste the path to an FCPXML file when presented with the `Enter xml file path:` prompt.

### Run Module Without Installing:

Future updates will allow passing arguments directly to `fcpx-marker-tool` but if the built in menu options are all you need simply install necessary requirements with `pip install -r requirements.txt`

Then run the module directly using `Python -m fcpx_marker_tool`

### Demo

Full demo for version 2.0.0 coming soon.

---

#### Python Modules Used:

timecode - https://github.com/eoyilmaz/timecode