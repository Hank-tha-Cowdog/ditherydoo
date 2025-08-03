# ditherydoo

# 🎬 DitheryDoo

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![VapourSynth](https://img.shields.io/badge/VapourSynth-R57+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**High-quality video processing pipeline with advanced dithering and debanding**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration) • [Examples](#-examples)

</div>

---

## 🎯 Overview

DitheryDoo is a professional-grade video processing tool that leverages VapourSynth's powerful filtering capabilities to produce exceptionally high-quality video outputs. It specializes in bit depth conversion with advanced dithering algorithms and sophisticated debanding techniques to eliminate banding artifacts while preserving fine details.

### 🔑 Key Benefits
- **Eliminate banding** in gradients and smooth areas
- **Preserve fine details** with intelligent masking
- **Professional codecs** including ProRes and FFV1
- **GPU acceleration** for faster processing
- **Batch processing** for entire directories
- **Cross-platform** Python implementation

## ✨ Features

### 🎨 Video Processing
- **Advanced Dithering**: Floyd-Steinberg, Sierra, and Stucki algorithms
- **Multi-level Debanding**: Conservative to Maximum strength with detail preservation
- **Bit Depth Conversion**: 10-bit, 12-bit, and 16-bit support
- **Chroma Subsampling**: 4:2:2 and 4:4:4 formats

### 🚀 Performance
- **NVIDIA GPU Acceleration**: via vs-placebo plugin
- **Progress Tracking**: Real-time processing statistics
- **Test Mode**: Process only first N frames for quick preview

### 📦 Output Formats
- **ProRes 422 HQ** (10-bit 4:2:2) - Industry standard intermediate codec
- **ProRes 4444** (16-bit 4:4:4) - Maximum quality with alpha support
- **FFV1** (10-bit 4:2:2 / 12-bit 4:4:4) - Lossless compression

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (with ProRes support)
- VapourSynth R57 or higher

### Step 1: Create Virtual Environment

```bash
# Windows
python -m venv dithery_env
dithery_env\Scripts\activate

# macOS/Linux
python3 -m venv dithery_env
source dithery_env/bin/activate
```

### Step 2: Install VapourSynth

```bash
# Install VapourSynth (platform-specific)
# Windows: Download installer from https://github.com/vapoursynth/vapoursynth/releases
# macOS: brew install vapoursynth
# Linux: Check your distribution's package manager

# Install Python bindings
pip install vapoursynth
```

### Step 3: Install VapourSynth Plugins

```bash
# Using vsrepo (recommended)
vsrepo install ffms2
vsrepo install fmtconv
vsrepo install neo_f3kdb
vsrepo install tcanny

# Optional: GPU-accelerated debanding
vsrepo install vs-placebo
```

### Step 4: Clone and Setup DitheryDoo

```bash
git clone https://github.com/yourusername/DitheryDoo.git
cd DitheryDoo
```

## 📖 Usage

### Basic Usage

1. **Activate your virtual environment**:
   ```bash
   # Windows
   dithery_env\Scripts\activate
   
   # macOS/Linux
   source dithery_env/bin/activate
   ```

2. **Configure your settings** in `pipeline.py`:
   ```python
   # Set your input file
   input_file = "path/to/your/video.mp4"
   
   # Choose output format (enable only one)
   enable_prores_422_hq_10bit = True
   
   # Set output directory
   output_base_directory = "path/to/output"
   ```

3. **Run the processing**:
   ```bash
   python pipeline.py
   ```

### Batch Processing

Process an entire directory of videos:

```python
# Enable batch mode
batch_process_directory = True
input_directory = "path/to/video/folder"
process_subdirectories = True  # Include subfolders
```

### Test Mode

Quickly test settings on first 200 frames:

```python
test_mode = True
test_frames = 200
```

## ⚙️ Configuration

### 🎯 Debanding Strength Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `conservative` | Minimal debanding | High-quality sources with minor banding |
| `balanced` | Moderate debanding | General purpose, good detail preservation |
| `aggressive` | Strong debanding | Visible banding in gradients |
| `maximum` | Highest quality | Severe banding, computational cost no concern |

### 🎨 Dithering Algorithms

- **Floyd-Steinberg**: Classic error diffusion, good general purpose
- **Sierra**: Less artifacts in dark areas
- **Stucki**: Best for preserving fine details

### 🔧 Advanced Settings

```python
# GPU Acceleration (requires NVIDIA GPU)
use_nvidia_gpu = True

# Logging verbosity
log_level = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
```

## 📸 Examples

### Example 1: High-Quality ProRes Master
```python
input_file = "raw_footage.mkv"
enable_prores_444_16bit = True
enable_debanding = True
debanding_strength = "maximum"
```

### Example 2: Efficient Batch Processing
```python
batch_process_directory = True
input_directory = "D:/VideoProjects/Season1"
enable_ffv1_10bit_422 = True  # Lossless compression
process_subdirectories = True
```

### Example 3: Quick Quality Test
```python
test_mode = True
test_frames = 300
enable_debanding = True
debanding_strength = "aggressive"
```

## 🔍 Troubleshooting

### Common Issues

**"Dependency not found: vspipe"**
- Ensure VapourSynth is installed and in your system PATH
- Try running `vspipe --version` to verify installation

**"Plugin not found" errors**
- Install missing plugins using vsrepo
- Check plugin compatibility with your VapourSynth version

**GPU acceleration not working**
- Verify NVIDIA GPU and CUDA support
- Ensure vs-placebo plugin is properly installed
- Set `use_nvidia_gpu = False` to disable

### Performance Tips

1. **Start with test mode** to verify settings before full processing
2. **Use GPU acceleration** when available for significant speed improvements
3. **Adjust debanding strength** based on source material quality
4. **Monitor the log file** in the output directory for detailed information

## 📝 Output Structure

```
output_base_directory/
└── 2024-01-15_14-30-00/
    ├── process.log
    ├── video1_2024-01-15_14-30-00_prores_422_hq_10bit.mov
    └── video2_2024-01-15_14-30-00_prores_422_hq_10bit.mov
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- VapourSynth community for the excellent video processing framework
- FFmpeg team for the robust encoding capabilities
- Plugin developers for fmtconv, vs-placebo, TCanny, and neo_f3kdb

---

<div align="center">

**Made with ❤️ for video professionals who demand quality**

*Tested on Windows 11, compatible with macOS and Linux*

</div>
