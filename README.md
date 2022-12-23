# BadAppleFamitrackerConverter
The tool I wrote in order to make "Bad Apple but its VIDEO is ported to
Famitracker."

This is in no way a general tool; it is a quick and dirty script. You are free
to try to use it, but it is very unlikely to work for your use case without
changes. MANY assumptions about my extremely specific use case (song tempo,
expansion audio, video resolution, file formats, etc.) are baked in. The output
file is track data only, so famitracker module header data must be added
manually, and the last segment's length must be adjusted too. It was easier to
do this manually than to code my script to do it. Sorry!