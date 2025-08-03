# DitheryDoo - pipeline.py
# Main controller with configuration

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# ==============================================================================
# USER CONFIGURATION SECTION
# ==============================================================================

# INPUT/OUTPUT SETTINGS
# ------------------------------------------------------------------------------
# Single file input path (used when batch_process_directory = False)
input_file = "G:/YOUTUBE_CHANNEL_MEDIA/DitheryDoo/src/FULL MOON VIDEO HD.mkv"

# Directory for batch processing (used when batch_process_directory = True)
input_directory = "G:/00_development_projects/DitheryDoo/input"

# Base output directory where timestamped folders will be created
output_base_directory = "G:/YOUTUBE_CHANNEL_MEDIA/DitheryDoo/vapourized"

# BATCH PROCESSING
# ------------------------------------------------------------------------------
# Process all video files in input_directory
# If False, only process input_file
batch_process_directory = False

# Include subdirectories when batch processing
# Only used when batch_process_directory = True
process_subdirectories = False

# PROCESSING MODE
# ------------------------------------------------------------------------------
# Enable test mode: Only process first N frames for testing
# Set to False for full video processing
test_mode = False

# Number of frames to process in test mode
# Only used when test_mode = True
test_frames = 200

# OUTPUT FORMAT SELECTION
# ------------------------------------------------------------------------------
# Enable only ONE format at a time
# Each format has specific bit depth and chroma subsampling

# ProRes 422 HQ 10-bit (4:2:2 chroma)
# High quality intermediate codec, widely compatible
enable_prores_422_hq_10bit = True

# ProRes 4444 16-bit (4:4:4 chroma)
# Maximum quality ProRes with alpha channel support
enable_prores_444_16bit = False

# FFV1 10-bit 4:2:2
# Lossless compression, smaller files than ProRes
enable_ffv1_10bit_422 = False

# FFV1 12-bit 4:4:4
# Lossless compression with higher bit depth
enable_ffv1_12bit_444 = False

# GPU ACCELERATION
# ------------------------------------------------------------------------------
# Enable NVIDIA GPU acceleration for processing
# Requires NVIDIA GPU and CUDA-capable VapourSynth plugins
use_nvidia_gpu = True # Enable for vs-placebo access

# QUALITY SETTINGS
# ------------------------------------------------------------------------------
# Dithering algorithm for bit depth conversion
# Options: "floyd_steinberg", "sierra", "stucki"
dithering_algorithm = "floyd_steinberg"

# DEBANDING SETTINGS
# ------------------------------------------------------------------------------
# Enable debanding for contoured source material
enable_debanding = True

# Debanding strength: "conservative", "balanced", "aggressive", "maximum"
debanding_strength = "maximum" # Highest quality regardless of cost

# LOGGING
# ------------------------------------------------------------------------------
# Logging verbosity
# Options: "DEBUG", "INFO", "WARNING", "ERROR"
log_level = "INFO"

# ==============================================================================
# SCRIPT LOGIC
# ==============================================================================
import ffmpeg_encode

def check_dependencies():
    """Checks for required command-line tools."""
    for cmd in ['ffmpeg', 'vspipe']:
        try:
            subprocess.run([cmd, '-h'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            logging.error(f"Dependency not found: {cmd}. Please ensure it is installed and in your system's PATH.")
            return False
    return True

def get_selected_format():
    """Determines which output format is enabled."""
    formats = {
        'prores_422_hq_10bit': enable_prores_422_hq_10bit,
        'prores_444_16bit': enable_prores_444_16bit,
        'ffv1_10bit_422': enable_ffv1_10bit_422,
        'ffv1_12bit_444': enable_ffv1_12bit_444,
    }
    selected = [name for name, enabled in formats.items() if enabled]
    if len(selected) == 1:
        return selected[0]
    return None

def find_video_files(directory, recursive):
    """Finds all supported video files in a directory."""
    supported_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.mxf', '.m2v']
    files = []
    glob_pattern = '**/*' if recursive else '*'
    for path in Path(directory).glob(glob_pattern):
        if path.is_file() and path.suffix.lower() in supported_extensions:
            files.append(path)
    return files

def process_file(input_path, output_path, selected_format, vpy_script_path):
    """Prepares environment and calls the encoder for a single file."""
    logging.info(f"Processing file: {input_path}")
    
    # Set environment variables for VapourSynth script
    env = os.environ.copy()
    env['VS_INPUT_PATH'] = str(input_path)
    env['VS_TARGET_FORMAT'] = selected_format
    env['VS_USE_GPU'] = str(use_nvidia_gpu)
    env['VS_DITHER_MODE'] = dithering_algorithm
    env['VS_TEST_FRAMES'] = str(test_frames) if test_mode else '0'
    env['VS_ENABLE_DEBANDING'] = str(enable_debanding)
    env['VS_DEBAND_STRENGTH'] = debanding_strength

    try:
        success = ffmpeg_encode.encode_video(
            str(input_path),
            str(output_path),
            selected_format,
            str(vpy_script_path),
            env
        )
        if success:
            logging.info(f"Successfully processed and saved to {output_path}")
        else:
            logging.error(f"Failed to process file: {input_path}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {input_path}: {e}")


def main():
    """
    Main function to orchestrate the video processing pipeline.
    """
    # Create a timestamped output directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = Path(output_base_directory) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = output_dir / "process.log"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("DitheryDoo processing started.")
    logging.info(f"Output directory: {output_dir}")

    # --- Configuration Validation ---
    logging.info("Validating configuration...")
    selected_format = get_selected_format()
    if not selected_format:
        logging.error("Configuration error: Exactly one output format must be enabled.")
        sys.exit(1)
    logging.info(f"Selected output format: {selected_format}")

    # --- Dependency Checks ---
    logging.info("Checking dependencies (VapourSynth, FFmpeg)...")
    if not check_dependencies():
        sys.exit(1)
    logging.info("Dependencies check passed.")

    # --- File Discovery ---
    files_to_process = []
    if batch_process_directory:
        logging.info(f"Starting batch processing for directory: {input_directory}")
        files_to_process = find_video_files(input_directory, process_subdirectories)
        if not files_to_process:
            logging.warning("No video files found in the specified directory.")
    else:
        logging.info(f"Starting single file processing for: {input_file}")
        p = Path(input_file)
        if p.is_file():
            files_to_process.append(p)
        else:
            logging.error(f"Input file not found: {input_file}")
            sys.exit(1)
    
    # --- Process Orchestration ---
    vpy_script_path = Path(__file__).parent / "process.vpy"
    total_files = len(files_to_process)
    logging.info(f"Found {total_files} file(s) to process.")

    for i, file_path in enumerate(files_to_process):
        logging.info(f"--- Processing file {i+1}/{total_files} ---")
        
        # Determine output path
        if batch_process_directory:
            relative_path = file_path.relative_to(input_directory)
            output_file_dir = output_dir / relative_path.parent
        else:
            output_file_dir = output_dir
        
        output_file_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = ffmpeg_encode.ENCODING_PROFILES[selected_format].get('codec', 'mov')
        if 'prores' in selected_format:
            file_ext = 'mov'
        elif 'ffv1' in selected_format:
            file_ext = 'mkv'

        output_filename = f"{file_path.stem}_{timestamp}_{selected_format}.{file_ext}"
        output_path = output_file_dir / output_filename

        process_file(file_path, output_path, selected_format, vpy_script_path)

    logging.info("DitheryDoo processing finished.")


if __name__ == "__main__":
    main()
