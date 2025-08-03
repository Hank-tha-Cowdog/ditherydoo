#!/usr/bin/env python3
# DitheryDoo - ffmpeg_encode.py
# FFmpeg Encoding Wrapper
# Handles format-specific encoding parameters and pipe management

import subprocess
import sys
import os
import json

# ==============================================================================
# ENCODING PROFILES
# ==============================================================================
# Each profile contains FFmpeg parameters for specific output format
ENCODING_PROFILES = {
    'prores_422_hq_10bit': {
        'codec': 'prores_ks',
        'profile': '3',  # HQ profile
        'pix_fmt': 'yuv422p10le',
        'extra_args': ['-vendor', 'apl0']  # Apple vendor ID
    },
    'prores_444_16bit': {
        'codec': 'prores_ks',
        'profile': '4',  # 4444 profile
        'pix_fmt': 'yuv444p16le',
        'extra_args': ['-vendor', 'apl0']
    },
    'ffv1_10bit_422': {
        'codec': 'ffv1',
        'level': '3',
        'pix_fmt': 'yuv422p10le',
        'extra_args': ['-coder', '1', '-context', '1', '-g', '1']
    },
    'ffv1_12bit_444': {
        'codec': 'ffv1',
        'level': '3',
        'pix_fmt': 'yuv444p12le',
        'extra_args': ['-coder', '1', '-context', '1', '-g', '1']
    }
}

# ==============================================================================
# MAIN ENCODING FUNCTION
# ==============================================================================
def encode_video(input_path, output_path, format_name, vpy_script, process_env):
    """
    Encode video using VapourSynth pipe and FFmpeg.

    Args:
        input_path (str): Source video file path.
        output_path (str): Destination file path.
        format_name (str): Output format key from ENCODING_PROFILES.
        vpy_script (str): Path to the VapourSynth script.
        process_env (dict): Environment variables for the VapourSynth script.
    """
    # Get encoding profile
    profile = ENCODING_PROFILES.get(format_name)
    if not profile:
        print(f"Error: Encoding profile for '{format_name}' not found.", file=sys.stderr)
        return False

    # Build vspipe command
    # -c y4m: Output Y4M format for pipe
    vspipe_cmd = ['vspipe', '-c', 'y4m', vpy_script, '-']

    # Build FFmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', 'pipe:0',  # Input from pipe
        '-i', input_path,  # Also read original for audio/metadata
        '-map', '0:v',  # Video from pipe
        '-map', '1:a?',  # Audio from original (if exists)
        '-map', '1:s?',  # Subtitles from original (if exists)
        '-c:v', profile['codec'],
        '-pix_fmt', profile['pix_fmt']
    ]

    # Add codec-specific parameters
    if 'profile' in profile:
        ffmpeg_cmd.extend(['-profile:v', profile['profile']])
    if 'level' in profile:
        ffmpeg_cmd.extend(['-level:v', profile['level']])

    # Add extra arguments
    ffmpeg_cmd.extend(profile.get('extra_args', []))

    # Audio and subtitle copy
    ffmpeg_cmd.extend([
        '-c:a', 'copy',  # Copy audio streams
        '-c:s', 'copy',  # Copy subtitle streams
        '-y',  # Overwrite output
        output_path
    ])

    print(f"VSPipe command: {' '.join(vspipe_cmd)}")
    print(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")

    # Execute pipeline: VapourSynth -> FFmpeg
    try:
        vspipe_process = subprocess.Popen(vspipe_cmd, stdout=subprocess.PIPE, env=process_env)
        ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=vspipe_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Allow vspipe to write to stdin of ffmpeg
        vspipe_process.stdout.close()

        # Get output and errors from FFmpeg
        stdout, stderr = ffmpeg_process.communicate()

        if ffmpeg_process.returncode != 0:
            print(f"Error during FFmpeg execution:", file=sys.stderr)
            print(stderr.decode('utf-8'), file=sys.stderr)
            return False

        return True

    except FileNotFoundError as e:
        print(f"Error: Command not found. Is FFmpeg or VapourSynth in your system's PATH?", file=sys.stderr)
        print(e, file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    # This allows the script to be called directly for testing if needed.
    # Example: python ffmpeg_encode.py <input> <output> <format> <vpy_script>
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <input_path> <output_path> <format_name> <vpy_script>")
        sys.exit(1)

    # Reconstruct the environment from the main pipeline script's perspective for standalone testing
    test_env = os.environ.copy()
    test_env['VS_INPUT_PATH'] = sys.argv[1]
    test_env['VS_TARGET_FORMAT'] = sys.argv[3]
    # Add other env vars if needed for testing

    success = encode_video(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], test_env)
    sys.exit(0 if success else 1)
