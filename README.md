# 🎬 Video to 1080p Converter with Hardcoded Subtitles

A fast Python script that batch converts MP4 and MKV files to 1920x1080 resolution with GPU acceleration and automatic subtitle hardcoding.

## ✨ Features

- **🚀 GPU Accelerated**: Auto-detects NVIDIA NVENC, AMD AMF, Intel QuickSync, or falls back to CPU
- **📁 Batch Processing**: Converts all video files in a directory automatically
- **📐 Aspect Ratio Preservation**: Maintains original aspect ratio with black bars when needed
- **📝 Automatic Subtitle Hardcoding**: Finds and embeds matching SRT files with font size 20
- **📊 Real-time Progress**: Shows conversion progress and encoding FPS
- **⚡ Smart Skipping**: Skips files already at target resolution
- **🖥️ Cross-platform**: Works on Windows, macOS, and Linux

## 🎯 What it does

1. Scans directory for MP4/MKV files
2. Looks for matching SRT subtitle files (`video.srt` for `video.mp4`)
3. Converts videos to 1920x1080 with GPU acceleration
4. Hardcodes subtitles with font size 20 if found
5. Saves to `converted/` folder with descriptive filenames

## 📋 Requirements

- **Python 3.6+**
- **FFmpeg** (with ffprobe)

### Installing FFmpeg

**Windows:**
```bash
# Download from https://ffmpeg.org/download.html
# Or use chocolatey:
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install ffmpeg
# or
sudo dnf install ffmpeg
```

## 🚀 Quick Start

1. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/henkdetenk12345/video-converter/main/video_converter.py
   # or clone the repo
   git clone https://github.com/henkdetenk12345/video-converter.git
   ```

2. **Place your videos and subtitles in the same folder:**
   ```
   my_videos/
   ├── movie1.mp4
   ├── movie1.srt
   ├── movie2.mkv
   ├── movie2.srt
   └── video_converter.py
   ```

3. **Run the script:**
   ```bash
   python video_converter.py
   ```

4. **Find converted videos in the `converted/` folder:**
   ```
   converted/
   ├── movie1_1080p_subs.mp4
   └── movie2_1080p_subs.mp4
   ```

## ⚙️ Configuration

Edit these variables at the top of the script:

```python
INPUT_DIR = "."           # Source directory (current directory by default)
OUTPUT_DIR = None         # Output directory (None = auto-create 'converted' folder)
SUBTITLE_FONT_SIZE = 20   # Font size for hardcoded subtitles
SUPPORTED_FORMATS = ['.mp4', '.mkv']  # Supported input formats
```

## 📝 Subtitle Requirements

- Subtitle files must be in **SRT format**
- Must have the **same filename** as the video file
- Examples:
  - `The.Movie.2023.mp4` → `The.Movie.2023.srt`
  - `episode01.mkv` → `episode01.srt`

## 🎛️ GPU Acceleration

The script automatically detects and uses the best available encoder:

| GPU Brand | Encoder Used | Performance |
|-----------|-------------|-------------|
| **NVIDIA** | h264_nvenc | 🚀🚀🚀 Fastest |
| **AMD** | h264_amf | 🚀🚀 Fast |
| **Intel** | h264_qsv | 🚀 Good |
| **None/Fallback** | libx264 (CPU) | ⏳ Slower |

## 📊 Output Examples

**With subtitles:**
```
Input:  movie.mp4 (1280x720) + movie.srt
Output: movie_1080p_subs.mp4 (1920x1080, hardcoded subs)
```

**Without subtitles:**
```
Input:  movie.mp4 (1280x720)
Output: movie_1080p.mp4 (1920x1080)
```

**Already 1080p with subtitles:**
```
Input:  movie.mp4 (1920x1080) + movie.srt
Output: movie_1080p_subs.mp4 (subtitles hardcoded)
```

## 🔧 Advanced Usage

### Custom Input/Output Directories

```python
INPUT_DIR = "/path/to/videos"
OUTPUT_DIR = "/path/to/output"
```

### Different Font Size

```python
SUBTITLE_FONT_SIZE = 24  # Larger subtitles
SUBTITLE_FONT_SIZE = 16  # Smaller subtitles
```

### Command Line Usage

```bash
# Process specific directory
python video_converter.py

# Check what encoder will be used
python video_converter.py --dry-run  # (if you add this feature)
```

## 🐛 Troubleshooting

**"FFmpeg not found" error:**
- Make sure FFmpeg is installed and in your system PATH
- Test with: `ffmpeg -version`

**Unicode/encoding errors on Windows:**
- Script handles this automatically with UTF-8 encoding
- If issues persist, check video filenames for special characters

**GPU encoder not detected:**
- Update your GPU drivers
- For NVIDIA: Install latest GeForce drivers
- For AMD: Install latest Radeon drivers
- Script will fall back to CPU encoding automatically

**Subtitle issues:**
- Ensure SRT file has exact same name as video file
- Check SRT file is valid UTF-8 encoded
- Subtitle font size can be adjusted in configuration

## 📈 Performance Tips

1. **Use SSD storage** for faster I/O
2. **Close other applications** during batch conversion
3. **Update GPU drivers** for best hardware acceleration
4. **Use original quality videos** for best results

## 🎯 Use Cases

- **Media Server Preparation**: Convert mixed resolution libraries to consistent 1080p
- **Archive Creation**: Standardize old video collections with embedded subtitles
- **Streaming Optimization**: Prepare videos for Plex, Jellyfin, or other media servers
- **Mobile Device Compatibility**: Ensure videos play on all devices
- **Storage Optimization**: Reduce file sizes while maintaining quality

## 📄 License

MIT License - Feel free to modify and distribute!

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

---

**⭐ Star this repo if it helped you organize your video library!**
