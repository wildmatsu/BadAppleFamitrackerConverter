# Bad Apple Famitracker Conversion Script (c) by Wild Matsu
#
# Bad Apple Famitracker Conversion Script is licensed under a
# Creative Commons Attribution-ShareAlike 3.0 Unported License.
#
# You should have received a copy of the license along with this
# work.  If not, see <http://creativecommons.org/licenses/by-sa/3.0/>.

"""This is in no way a general tool; it is a quick and dirty script.
You are free to try to use it, but it is very unlikely to work for your use case
without changes. MANY assumptions about my extremely specific use case (song
tempo, expansion audio, video resolution, file formats, etc.) are baked in. The
output file is track data only, so famitracker module header data must be added
manually, and the last segment's length must be adjusted too. It was easier to
do this manually than to code my script to do it. Sorry!"""

import math
from PIL import Image

# Global constants

rows_per_pattern = 64
max_patterns_per_segment = 256
# Subtract 1 for the "start pattern"
patterns_per_segment = math.floor(
    (max_patterns_per_segment - 1) / rows_per_pattern)
rows_per_segment = rows_per_pattern * patterns_per_segment

used_n163_channels = 4
max_n163_channels = 8
unused_n163_channels = 0  # Default: No N163
if used_n163_channels > 0:
    unused_n163_channels = max_n163_channels - used_n163_channels

# Left-to-right: 2A03, VRC6, MMC5, N163, FDS, S5B
used_channels = 5 + 3 + 2 + used_n163_channels + 1 + 3
num_channels = used_channels + unused_n163_channels

# Location to pad with unused n163 channels
n163_padding_idx = 5 + 3 + 2 + used_n163_channels

noise_idx = 3  # 2A03 Noise Channel ID (zero-indexed)
dpcm_idx = 4  # 2A03 DPCM Channel ID (zero-indexed)

two_digit_hex = "{:02X}"  # Two hex digits
blank_channel_row = " : ... .. . ..."

# File paths
root = "D:\\vids\\BAFTConverter\\"
images_root = root + "\\badapple120p30dithered"
music_file = open(root + "in.txt", "r")
out = open(root + "out.txt", "w")


def is_pixel_on(pixels, row, col):
    """ Determine if a pixel of the input image is on or not.
    This method assumes the image is grayscale and uses a
    single 8-bit value to represent a shade of gray."""

    # This ignores gamma, but my input images are strictly black and white
    gray50percent = 127

    return pixels[col, row] > gray50percent


def print_note(channel_idx, pixels, row, col):
    """Convert three pixels of the input image into a meaningless note,
    designed to visually resemble the input pixels as much as possible."""

    p1 = is_pixel_on(pixels, row, col)
    p2 = is_pixel_on(pixels, row, col+1)
    p3 = is_pixel_on(pixels, row, col+2)

    # Specially handle the 2A03 noise channel,
    # as it uses the "notes" 0 through F instead of A through G.
    if channel_idx == noise_idx:
        if p1:
            out.write("0-#")
        else:
            if p3:
                out.write("1-#")
            else:
                out.write("...")
        return col + 3

    # Handle regular channels.
    if p1:
        if p2:
            if p3:
                out.write("G#6")
            else:
                out.write("G#1")
        else:
            if p3:
                out.write("G-6")
            else:
                # First pixel should be on,
                # but sacrifices that for the sake of the rest.
                out.write("...")  # F-1
    else:
        if p2:
            if p3:
                out.write("F#6")
            else:
                # Middle pixel should be on,
                # but sacrifices that for the sake of the rest.
                out.write("...")  # F#1
        else:
            if p3:
                # Last pixel should be on,
                # but sacrifices that for the sake of the rest.
                out.write("...")  # F-6
            else:
                out.write("...")

    return col + 3


def print_inst(pixels, row, col):
    """Convert two pixels of the input image into a meaningless instrument,
    designed to visually resemble the input pixels as much as possible."""

    p1 = is_pixel_on(pixels, row, col)
    p2 = is_pixel_on(pixels, row, col+1)

    # Set an on pixel to '0'.
    # 0 can't sit next to an off pixel, so if one is on and the other is off,
    # use 1 for the dark pixel, the number that is "darkest."
    # If both are off, then just print two dots.
    if p1:
        if p2:
            out.write("00")
        else:
            out.write("01")
    else:
        if p2:
            out.write("10")
        else:
            out.write("..")

    return col + 2


def print_vol(channel_idx, pixels, row, col):
    """Convert one pixel of the input image into a meaningless volume,
    designed to represent the input pixel as much as possible."""

    if channel_idx == dpcm_idx:
        # The DPCM channel has no volume column, so print a . but don't
        # increment the column. The DPCM column is inevitably blank; this
        # causes a "gap" in the image instead of just losing a column of pixels.
        # Since I had extra space at the end of the row anyway, this seemed
        # like the right approach.
        out.write(".")
        return col

    # This one's real simple. '0' for on, '.' for off.
    if is_pixel_on(pixels, row, col):
        out.write("0")
    else:
        out.write(".")

    return col + 1


def print_effect(pixels, row, col):
    """Convert three pixels of the input image into a meaningless effect,
    designed to visually resemble the input pixels as much as possible."""

    p1 = is_pixel_on(pixels, row, col)
    p2 = is_pixel_on(pixels, row, col+1)
    p3 = is_pixel_on(pixels, row, col+2)

    # Gxx is used because G is a "bright" letter, and Gxx effects won't turn red in any channel.
    # The equals sign WILL turn red, but since we want that pixel to be "off," that actually helps.
    if p1:
        if p2:
            if p3:
                out.write("G00")
            else:
                out.write("G01")
        else:
            if p3:
                out.write("G10")
            else:
                # First pixel should be on,
                # but sacrifices that for the sake of the rest.
                out.write("...")  # G11
    else:
        if p2:
            if p3:
                out.write("=00")
            else:
                # = is dark enough to sacrifice the first and last pixels
                # for the sake of the middle one.
                out.write("=01")
        else:
            if p3:
                # = is dark enough to sacrifice the first and middle pixels
                # for the sake of the last one.
                out.write("=10")
            else:
                out.write("...")

    return col+3


def print_last_effect(pixels, row, col):
    """Special case handling for the final effect in a row, which only has 2 pixels
    of input instead of 3. Very much targeted at my specific use case."""

    p1 = is_pixel_on(pixels, row, col)
    p2 = is_pixel_on(pixels, row, col+1)

    # As the method above, but treat the third column as always off.
    if p1:
        if p2:
            out.write("G01")
        else:
            # First pixel should be on,
            # but sacrifices that for the sake of the rest.
            out.write("...")  # G11
    else:
        if p2:
            # = is dark enough to sacrifice the first and last pixels
            # for the sake of the middle one.
            out.write("=01")
        else:
            out.write("...")

    return col + 2


def print_channel_row(channel_idx, image, pixels, row, col):
    """Convert a single channel's worth of pixels into
    a channel in a row in a Famitracker module."""

    width = image.size[0]
    col = print_note(channel_idx, pixels, row, col)
    out.write(" ")
    col = print_inst(pixels, row, col)
    out.write(" ")
    col = print_vol(channel_idx, pixels, row, col)
    out.write(" ")
    if col+3 < width:
        col = print_effect(pixels, row, col)
    else:
        col = print_last_effect(pixels, row, col)
    return col


def pixel_row_to_text(image, pixels, row):
    """Convert a single row of an image into a row of a Famitracker module."""

    width = image.size[0]
    col = print_channel_row(0, image, pixels, row, 0)
    channel_idx = 1

    while (col < width):
        if channel_idx == n163_padding_idx:
            # I use 4 N163 channels but famitracker dumps all 8 to text anyway,
            # so I have to insert the 4 blank channels here...
            for i in range(unused_n163_channels):
                out.write(blank_channel_row)

        # Print the text for the channel.
        out.write(" : ")
        col = print_channel_row(channel_idx, image, pixels, row, col)
        channel_idx += 1

    out.write('\n')


def image_to_text(image, pixels):
    """Convert a loaded image to a Famitracker pattern."""

    height = image.size[1]
    for row in range(height):
        out.write("ROW " + two_digit_hex.format(row) + " : ")
        pixel_row_to_text(image, pixels, row)


def process_image_number(i):
    """Read input image file with index i, then render it as a Famitracker pattern."""

    # Constants
    image_prefix = "ba ("
    image_suffix = ").png"

    # Open the image
    image_name = ''.join([image_prefix, str(i), image_suffix])
    image_path = '\\'.join([images_root, image_name])
    image = Image.open(image_path)
    pixels = image.load()
    print("Opened image:", image_name, image.format, image.size, image.mode)

    # Convert the image
    image_to_text(image, pixels)


def get_next_music_row(music_file):
    """Parse the input music file for the next row of music.
    Skips any line of text that doesn't denote a row in a pattern."""

    result = " "
    while (not result.startswith("ROW ")):
        if len(result) == 0:
            return ""  # EOF
        result = music_file.readline()
    return result


def print_blank_row_with_effect(effect):
    """Print a blank row with the desired effect in the DPCM channel."""

    for i in range(num_channels):
        if i == dpcm_idx:
            out.write(" : ... .. . " + effect)
        else:
            out.write(blank_channel_row)


def print_music_row(music_row, volume_cache, end_of_segment):
    """Print a row of the source music module.
    Correct volumes and add any needed effects,
    primarily the D78 effect to each row."""

    # Constants
    vol_idx = 2
    effect_idx = 3

    channels = music_row.split(" : ")
    processed_channels = []
    encountered_halt_effect = False

    for channel_idx, channel in enumerate(channels):
        # Skip the row header ("ROW XX : ")
        if channel_idx == 0:
            continue

        cols = channel.split(" ")
        if channel_idx == (dpcm_idx+1):
            if cols[effect_idx] == "C00":
                # If there's a C00 effect in the DPCM channel, finish this row then halt.
                encountered_halt_effect = True
            else:
                if cols[effect_idx] != "...":
                    # We assume the DPCM channel is blank otherwise...
                    print("Unexpected effect in DPCM channel!")
                    print(music_row)
                    exit()

                if end_of_segment:
                    # Put the song halt command
                    cols[effect_idx] = "C00"
                else:
                    # Put the jump command here
                    cols[effect_idx] = "D78"

        else:
            # Make sure volumes carry across segments,
            # and don't get messed up by the "video",
            # by writing the volume on every row.
            if cols[vol_idx] == ".":
                cached_vol = volume_cache[channel_idx-1]
                cols[vol_idx] = cached_vol
            else:
                # There's already a volume here, so update the cache
                volume_cache[channel_idx-1] = cols[vol_idx]

        # Join the columns array to render the text for this channel
        processed_channels.append(" ".join(cols))

    # Join the processed channels array to render the text for this row
    out.write(" : ".join(processed_channels))

    return encountered_halt_effect


def get_image_for(music_row_idx):
    """Choose the proper source video frame index for the provided row index.
    This method is where the source video frame rate is converted to line up to
    rows in the source Famitracker module."""

    # Constants

    # I use a [7,6] groove, so this is the average framerate.
    rows_per_second = 6.5
    engine_speed = 60  # Standard 60Hz NTSC Famitracker engine speed.
    video_fps = 30  # Bad Apple source video frame rate.
    conversion_factor = video_fps / engine_speed

    # Length of my cover, first kick drum to final cymbal, measured in samples at 44.1kHz
    audio_length = 9173852
    # Length of audio in Bad Apple source video, same start point/end point/unit
    video_length = 9204526
    fudge_factor = (video_length / audio_length)

    # Compute the frame from the music row index, using the constants above.
    frames_to_advance = rows_per_second * conversion_factor * fudge_factor
    result = math.floor(music_row_idx * frames_to_advance)

    result += 1  # Convert from zero-indexed rows to one-indexed images

    # In the event of slight A/V mismatch,
    # repeating the last frame once or twice won't matter.
    # (The last frame consists entirel of black pixels anyway.)
    lastimage = 6480  # Number of frames in Bad Apple source video
    if result > lastimage:
        return lastimage

    return result


# Iterators
image_idx = 0
music_row_idx = 0
segment_idx = 0

volume_cache = ["F"] * num_channels  # Initialize all volumes to the default, F
finished = False

# Iterate over segments
while (not finished):
    out.write("TRACK 121   0 150 \"Segment " + str(segment_idx+1) + "\"\n")
    out.write("COLUMNS :")
    for i in range(num_channels):
        out.write(" 1")
    out.write("\n\n")
    for i in range(rows_per_segment+1):
        order = two_digit_hex.format(i)
        out.write("ORDER " + order + " :")
        for j in range(num_channels):
            out.write(" " + order)
        out.write("\n")
    out.write("\n")

    out.write("PATTERN 00\n")
    out.write("ROW 00")
    print_blank_row_with_effect("D78")
    out.write("\n\n\n")

    while ((not finished) and (music_row_idx < (rows_per_segment * (segment_idx + 1)))):
        pattern_idx = (music_row_idx % rows_per_segment) + 1
        out.write("PATTERN " + two_digit_hex.format(pattern_idx) + "\n")
        image_idx = get_image_for(music_row_idx)
        process_image_number(image_idx)
        music_row = get_next_music_row(music_file)

        if len(music_row) == 0:
            print("EOF at music row index " + str(music_row_idx))
            out.write("ROW 78")
            print_blank_row_with_effect("C00")
            out.write("\n\n\n")
            finished = True
        else:
            end_of_segment = (pattern_idx == rows_per_segment)
            out.write("ROW 78 : ")
            finished = print_music_row(music_row, volume_cache, end_of_segment)

        out.write("\n\n")
        music_row_idx += 1

    segment_idx += 1
