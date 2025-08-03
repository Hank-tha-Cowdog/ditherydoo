# DitheryDoo - process.vpy
# VapourSynth processing script

import vapoursynth as vs
import sys
import os
import time

# Initialize VapourSynth core
core = vs.core

# ==============================================================================
# CONFIGURATION (passed from pipeline.py via environment)
# ==============================================================================
input_path = os.environ.get('VS_INPUT_PATH')
target_format = os.environ.get('VS_TARGET_FORMAT')
use_gpu = os.environ.get('VS_USE_GPU', 'false').lower() == 'true'
dither_mode = os.environ.get('VS_DITHER_MODE', 'floyd_steinberg')
test_frames = int(os.environ.get('VS_TEST_FRAMES', '0'))
enable_debanding = os.environ.get('VS_ENABLE_DEBANDING', 'false').lower() == 'true'
deband_strength = os.environ.get('VS_DEBAND_STRENGTH', 'balanced')

# ==============================================================================
# PLUGIN LOADING (FIXED FOR VSREPO)
# ==============================================================================
# Load required plugins
# ffms2 for source loading
try:
    clip = core.ffms2.Source(source=input_path)
except vs.Error as e:
    sys.stderr.write(f"Error loading video with ffms2: {e}\n")
    sys.exit(1)

# fmtconv for high-quality format conversion and dithering (vsrepo auto-loaded)
if not hasattr(core, 'fmtc'):
    sys.stderr.write("Error: fmtconv plugin not found.\n")
    sys.exit(1)

# vs-placebo for high-quality debanding (vsrepo auto-loaded)
vs_placebo_available = False
try:
    if hasattr(core, 'placebo'):
        vs_placebo_available = True
        sys.stderr.write("vs-placebo detected and available\n")
    else:
        sys.stderr.write("vs-placebo not found\n")
except Exception as e:
    sys.stderr.write(f"vs-placebo check failed: {e}\n")

# TCanny for detail masking (vsrepo auto-loaded)
tcanny_available = False
try:
    if hasattr(core, 'tcanny'):
        tcanny_available = True
        sys.stderr.write("TCanny detected and available\n")
    else:
        sys.stderr.write("TCanny not found\n")
except Exception as e:
    sys.stderr.write(f"TCanny check failed: {e}\n")

# Neo f3kdb fallback debanding (vsrepo auto-loaded)
neo_f3kdb_available = False
try:
    if hasattr(core, 'neo_f3kdb'):
        neo_f3kdb_available = True
        sys.stderr.write("neo_f3kdb detected and available\n")
    else:
        sys.stderr.write("neo_f3kdb not found\n")
except Exception as e:
    sys.stderr.write(f"neo_f3kdb check failed: {e}\n")

# Plugin availability summary
sys.stderr.write(f"Plugin status: placebo={vs_placebo_available}, tcanny={tcanny_available}, neo_f3kdb={neo_f3kdb_available}\n")


# ==============================================================================
# DEBUG INFORMATION
# ==============================================================================
sys.stderr.write(f"Processing configuration:\n")
sys.stderr.write(f"  - GPU enabled: {use_gpu}\n")
sys.stderr.write(f"  - Debanding enabled: {enable_debanding}\n")
sys.stderr.write(f"  - Debanding strength: {deband_strength}\n")
sys.stderr.write(f"  - Test frames: {test_frames}\n")
sys.stderr.write(f"  - Dither mode: {dither_mode}\n")


# ==============================================================================
# SOURCE LOADING
# ==============================================================================
# Limit frames in test mode
if test_frames > 0:
    clip = clip[:test_frames]

# Convert to 16-bit before processing to prevent errors
clip = core.fmtc.bitdepth(clip, bits=16)

# ==============================================================================
# DEBANDING
# ==============================================================================
if enable_debanding:
    # Strength configurations optimized for detail preservation
    strength_configs = {
        'conservative': {'iterations': 2, 'threshold': 2.0, 'radius': 8.0, 'grain': 2.0},
        'balanced': {'iterations': 3, 'threshold': 3.0, 'radius': 12.0, 'grain': 4.0},
        'aggressive': {'iterations': 4, 'threshold': 4.0, 'radius': 16.0, 'grain': 6.0},
        'maximum': {'iterations': 6, 'threshold': 3.5, 'radius': 20.0, 'grain': 4.0}
    }
    config = strength_configs.get(deband_strength, strength_configs['balanced'])

    if vs_placebo_available and tcanny_available:
        # vs-placebo high-quality debanding
        try:
            # Create detail mask to protect edges
            detail_mask = core.tcanny.TCanny(clip, sigma=1.0, mode=1, op=2)
            detail_mask = core.std.Maximum(detail_mask, threshold=65535//4)
            detail_mask = core.std.Inflate(detail_mask)

            # Apply debanding with masking
            debanded = core.placebo.Deband(
                clip,
                planes=7, # Process all planes
                iterations=config['iterations'],
                threshold=config['threshold'],
                radius=config['radius'],
                grain=config['grain'],
                dither=True, # Built-in dithering
                dither_algo=1 # Use orderer dithering (0=none, 1=ordered, 2=error_diffusion)
            )
            # Blend original detail back using mask
            clip = core.std.MaskedMerge(debanded, clip, detail_mask)
            sys.stderr.write(f"Applied vs-placebo debanding: {deband_strength} strength\n")
        except Exception as e:
            sys.stderr.write(f"vs-placebo debanding failed: {e}\n")
            # Fall through to neo_f3kdb fallback
            vs_placebo_available = False
    
    if not vs_placebo_available and neo_f3kdb_available:
        # neo_f3kdb fallback with detail preservation
        try:
            # Multiple passes for quality
            for i in range(min(config['iterations'], 3)):
                clip = core.neo_f3kdb.Deband(
                    clip,
                    range=int(config['radius']),
                    y=int(config['threshold'] * 16), # Scale for f3kdb
                    cb=int(config['threshold'] * 12),
                    cr=int(config['threshold'] * 12),
                    grainy=int(config['grain']),
                    grainc=int(config['grain'] * 0.7),
                    sample_mode=4 # Highest quality sampling
                )
            sys.stderr.write(f"Applied neo_f3kdb debanding: {deband_strength} strength\n")
        except Exception as e:
            sys.stderr.write(f"neo_f3kdb debanding failed: {e}\n")


# ==============================================================================
# FORMAT DETECTION AND PLANNING
# ==============================================================================
# Detect source properties
source_format = clip.format
source_width = clip.width
source_height = clip.height

# Determine target properties based on output format
format_configs = {
    'prores_422_hq_10bit': {'bits': 10, 'subsampling': vs.YUV422P10},
    'prores_444_16bit': {'bits': 16, 'subsampling': vs.YUV444P16},
    'ffv1_10bit_422': {'bits': 10, 'subsampling': vs.YUV422P10},
    'ffv1_12bit_444': {'bits': 12, 'subsampling': vs.YUV444P12}
}
target_config = format_configs.get(target_format)

if not target_config:
    sys.stderr.write(f"Error: Invalid target format '{target_format}'\n")
    sys.exit(1)

# ==============================================================================
# CHROMA UPSAMPLING (if needed)
# ==============================================================================
# Use bicubic filter for smooth chroma upsampling
if source_format.subsampling_w > 0 or source_format.subsampling_h > 0:
    clip = core.resize.Bicubic(
        clip,
        format=target_config['subsampling'],
        filter_param_a=0,  # b parameter (Mitchell-Netravali)
        filter_param_b=0.5, # c parameter (Mitchell-Netravali)
        chromaloc_in_s="center", # Assume center chroma location
        chromaloc_s="center"
    )

# ==============================================================================
# BIT DEPTH CONVERSION (KEEP EXISTING AGGRESSIVE SETTINGS)
# ==============================================================================
# Note: Maintaining aggressive dithering since debanding may not add enough
# visible grain at the target bit depths
if clip.format.bits_per_sample != target_config['bits']:
    dither_modes = {
        'floyd_steinberg': 1,
        'sierra': 2,
        'stucki': 3
    }
    clip = core.fmtc.bitdepth(
        clip,
        bits=target_config['bits'],
        dmode=dither_modes.get(dither_mode, 1),
        ampo=1.0, # Full error diffusion
        ampn=3.0, # KEEP: Strong noise amplitude as requested
        dyn=True, # Dynamic patterns
        staticnoise=True, # Additional static noise
        corplane=3 # Apply to all color planes
    )

import functools

# ==============================================================================
# PROGRESS TRACKING (STABLE FRAMEEVAL IMPLEMENTATION)
# ==============================================================================
progress_state = {
    'start_time': time.time(),
    'processed_frames': set(),
    'last_reported': 0,
    'total_frames': len(clip)
}

def progress_update(n, state, clip_to_return):
    """
    Frame evaluation function for progress tracking.
    Called for each frame n. Returns the clip.
    """
    state['processed_frames'].add(n)
    current = len(state['processed_frames'])

    # Only update display if we've processed new unique frames
    if current > state['last_reported']:
        state['last_reported'] = current
        
        progress = (current / state['total_frames']) * 100
        elapsed_time = time.time() - state['start_time']
        
        if current > 0:
            fps = current / elapsed_time
        else:
            fps = 0

        # Build and display progress line
        bar_width = 50
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "-" * (bar_width - filled)
        
        progress_line = f"\r[{bar}] {progress:6.2f}% ({current}/{state['total_frames']}) | {fps:.2f} fps"
        sys.stderr.write(progress_line)
        sys.stderr.flush()

    if current >= state['total_frames']:
        sys.stderr.write("\n✓ Processing complete!\n")
        sys.stderr.flush()
        
    return clip_to_return

# Initialize progress display
sys.stderr.write(f"Starting processing: {progress_state['total_frames']} frames\n")
sys.stderr.flush()

# Apply progress tracking using the stable eval(n) -> clip pattern
clip = core.std.FrameEval(
    clip,
    functools.partial(progress_update, state=progress_state, clip_to_return=clip)
)







# ==============================================================================
# OUTPUT
# ==============================================================================
# Set output for piping to FFmpeg
clip.set_output()

