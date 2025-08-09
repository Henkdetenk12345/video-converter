#!/usr/bin/env python3
"""
MP4/MKV to 1920x1080 Converter with GPU Acceleration and Hardcoded Subtitles
============================================================================

A fast Python script that batch converts MP4 and MKV files to 1920x1080 resolution 
with GPU acceleration, maintaining aspect ratio using black bars when needed.
Automatically hardcodes matching SRT subtitle files with FontSize 24.

Features:
- Supports both MP4 and MKV input files
- GPU Accelerated: Auto-detects and uses NVIDIA NVENC, AMD AMF, or Intel QuickSync
- Batch Processing: Converts all video files in a directory
- Aspect Ratio Preservation: Adds black bars to maintain original aspect ratio
- Hardcoded Subtitles: Automatically finds and embeds matching SRT files (FontSize 24)
- Real-time Progress: Shows percentage completion and encoding FPS
- Smart Skipping: Skips files already at 1920x1080 resolution
- Cross-platform: Works on Windows, macOS, and Linux

Requirements:
- Python 3.6+
- FFmpeg (with ffprobe)
"""

import os
import sys
import subprocess
import re
import glob
from pathlib import Path

# Configuration
INPUT_DIR = "."  # Source directory (current directory by default)
OUTPUT_DIR = None  # Output directory (None = auto-create 'converted' folder)
SUPPORTED_FORMATS = ['.mp4', '.mkv']  # Supported input formats
SUBTITLE_FONT_SIZE = 20  # Font size for hardcoded subtitles

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ERROR: FFmpeg not found!")
        print("Please install FFmpeg:")
        print("- Windows: Download from https://ffmpeg.org/download.html")
        print("- macOS: brew install ffmpeg")
        print("- Linux: sudo apt install ffmpeg (Ubuntu/Debian)")
        return False

def detect_gpu_encoder():
    """Detect the best available GPU encoder."""
    encoders = [
        ('h264_nvenc', 'NVIDIA NVENC'),
        ('h264_amf', 'AMD AMF'),
        ('h264_qsv', 'Intel QuickSync'),
        ('libx264', 'CPU (libx264)')
    ]
    
    for encoder, name in encoders:
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
            )
            if encoder in result.stdout:
                return encoder, name
        except subprocess.CalledProcessError:
            continue
    
    return 'libx264', 'CPU (libx264)'

def find_subtitle_file(video_path):
    """Find matching SRT subtitle file for the video."""
    video_file = Path(video_path)
    video_stem = video_file.stem
    video_dir = video_file.parent
    
    # Look for SRT file with same name
    srt_path = video_dir / f"{video_stem}.srt"
    
    if srt_path.exists():
        return str(srt_path)
    
    return None

def get_video_info(filepath):
    """Get video information using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', str(filepath)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        
        import json
        if not result.stdout:
            return None, None, None
            
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None, None, None
        
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        duration = float(data['format']['duration'])
        
        return width, height, duration
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        print(f"❌ Error getting video info: {e}")
        return None, None, None

def calculate_video_filters(width, height, subtitle_path=None):
    """Calculate video filters including scaling and subtitles."""
    target_width, target_height = 1920, 1080
    filters = []
    
    # Scaling filter
    if width != target_width or height != target_height:
        # Calculate scaling ratios
        scale_w = target_width / width
        scale_h = target_height / height
        scale = min(scale_w, scale_h)
        
        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Make dimensions even (required for some codecs)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        
        # Calculate padding
        pad_x = (target_width - new_width) // 2
        pad_y = (target_height - new_height) // 2
        
        filters.append(f"scale={new_width}:{new_height},pad={target_width}:{target_height}:{pad_x}:{pad_y}:black")
    
    # Subtitle filter
    if subtitle_path:
        # Escape path for FFmpeg (handle spaces and special characters)
        escaped_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
        subtitle_filter = f"subtitles='{escaped_path}':force_style='FontSize={SUBTITLE_FONT_SIZE}'"
        filters.append(subtitle_filter)
    
    # Combine filters
    if filters:
        return ','.join(filters)
    else:
        return None

def get_encoder_settings(encoder):
    """Get encoder-specific settings for maximum speed."""
    settings = {
        'h264_nvenc': [
            '-preset', 'p1',  # Fastest preset
            '-tune', 'hq',    # High quality
            '-rc', 'vbr',     # Variable bitrate
            '-cq', '23',      # Quality level
            '-b:v', '0',      # Let CQ control bitrate
            '-maxrate', '10M', # Max bitrate cap
            '-bufsize', '20M', # Buffer size
        ],
        'h264_amf': [
            '-quality', 'speed',
            '-rc', 'vbr_peak',
            '-qp_i', '23',
            '-qp_p', '23',
        ],
        'h264_qsv': [
            '-preset', 'veryfast',
            '-global_quality', '23',
        ],
        'libx264': [
            '-preset', 'veryfast',
            '-crf', '23',
        ]
    }
    return settings.get(encoder, settings['libx264'])

def convert_video(input_path, output_path, encoder, video_filter):
    """Convert video using FFmpeg with progress tracking."""
    cmd = ['ffmpeg', '-y', '-i', str(input_path)]
    
    # Add video filters if needed
    if video_filter:
        cmd.extend(['-vf', video_filter])
    
    # Add encoder and settings
    cmd.extend(['-c:v', encoder])
    cmd.extend(get_encoder_settings(encoder))
    
    # Audio settings (copy to avoid re-encoding)
    cmd.extend(['-c:a', 'copy'])
    
    # Output settings
    cmd.extend(['-movflags', '+faststart'])  # Web optimization
    cmd.append(str(output_path))
    
    # Run conversion with progress
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, bufsize=1, encoding='utf-8', errors='ignore'
        )
        
        return process
    except Exception as e:
        print(f"❌ Error starting conversion: {e}")
        return None

def parse_ffmpeg_progress(line, duration):
    """Parse FFmpeg progress output."""
    # Look for time progress
    time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = float(time_match.group(3))
        current_time = hours * 3600 + minutes * 60 + seconds
        
        if duration > 0:
            progress = min((current_time / duration) * 100, 100)
            return progress
    
    return None

def monitor_conversion(process, duration, filename):
    """Monitor conversion progress and display updates."""
    print(f"🔄 Starting conversion...")
    
    last_progress = 0
    fps_pattern = re.compile(r'fps=\s*(\d+\.?\d*)')
    
    while True:
        output = process.stderr.readline()
        if output == '' and process.poll() is not None:
            break
        
        if output:
            # Parse progress
            progress = parse_ffmpeg_progress(output, duration)
            if progress is not None and progress > last_progress + 1:  # Update every 1%
                last_progress = int(progress)
                
                # Extract FPS
                fps_match = fps_pattern.search(output)
                fps = fps_match.group(1) if fps_match else "0"
                
                print(f"\r🔄 Progress: {last_progress:.1f}% - {fps} fps", end='', flush=True)
    
    print()  # New line after progress
    
    return process.returncode == 0

def find_video_files(directory):
    """Find all supported video files in directory."""
    files = []
    
    # Use case-insensitive search to avoid duplicates on Windows
    for ext in SUPPORTED_FORMATS:
        pattern = os.path.join(directory, f"*{ext}")
        files.extend(glob.glob(pattern, recursive=False))
        
        # On case-sensitive systems (Linux/macOS), also check uppercase
        if os.name != 'nt':  # Not Windows
            pattern_upper = os.path.join(directory, f"*{ext.upper()}")
            files.extend(glob.glob(pattern_upper, recursive=False))
    
    # Remove duplicates (in case there are any) and sort
    return sorted(list(set(files)))

def main():
    """Main conversion function."""
    print("🎬 Video to 1920x1080 Converter with GPU Acceleration & Hardcoded Subtitles")
    print("=" * 76)
    
    # Check FFmpeg
    if not check_ffmpeg():
        return 1
    
    # Detect encoder
    encoder, encoder_name = detect_gpu_encoder()
    print(f"✅ Using encoder: {encoder_name} ({encoder})")
    print(f"📝 Subtitle font size: {SUBTITLE_FONT_SIZE}")
    
    # Setup directories
    input_dir = Path(INPUT_DIR).resolve()
    if OUTPUT_DIR:
        output_dir = Path(OUTPUT_DIR).resolve()
    else:
        output_dir = input_dir / "converted"
    
    # Find video files
    video_files = find_video_files(input_dir)
    if not video_files:
        print(f"❌ No supported video files found in: {input_dir}")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return 1
    
    print(f"Found {len(video_files)} video file(s)")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("-" * 50)
    
    # Process each file
    converted_count = 0
    skipped_count = 0
    
    for i, input_path in enumerate(video_files, 1):
        input_file = Path(input_path)
        print(f"\n[{i}/{len(video_files)}] Processing: {input_file.name}")
        
        # Get video info
        width, height, duration = get_video_info(input_path)
        if width is None:
            print("❌ Could not read video information")
            continue
        
        print(f"📹 Original resolution: {width}x{height}")
        print(f"⏱️ Duration: {duration:.1f} seconds")
        
        # Look for subtitle file
        subtitle_path = find_subtitle_file(input_path)
        if subtitle_path:
            print(f"📝 Found subtitles: {Path(subtitle_path).name}")
        else:
            print("📝 No subtitle file found")
        
        # Check if already target resolution and no subtitles to embed
        if width == 1920 and height == 1080 and not subtitle_path:
            print("✅ Already 1920x1080 with no subtitles to embed, skipping")
            skipped_count += 1
            continue
        
        # Create output filename (always .mp4)
        if subtitle_path:
            output_filename = input_file.stem + "_1080p_subs.mp4"
        else:
            output_filename = input_file.stem + "_1080p.mp4"
        output_path = output_dir / output_filename
        
        # Skip if output already exists
        if output_path.exists():
            print(f"✅ Output already exists, skipping")
            skipped_count += 1
            continue
        
        # Calculate video filters
        video_filter = calculate_video_filters(width, height, subtitle_path)
        
        # Start conversion
        process = convert_video(input_path, output_path, encoder, video_filter)
        if process is None:
            continue
        
        # Monitor progress
        if monitor_conversion(process, duration, input_file.name):
            print(f"✅ Conversion completed: {output_filename}")
            converted_count += 1
        else:
            print(f"❌ Conversion failed: {input_file.name}")
            # Clean up failed output
            if output_path.exists():
                output_path.unlink()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"   Converted: {converted_count} files")
    print(f"   Skipped: {skipped_count} files")
    print(f"   Total processed: {converted_count + skipped_count}/{len(video_files)} files")
    
    if converted_count > 0:
        print(f"✅ All conversions completed!")
        print(f"📁 Output directory: {output_dir}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ Conversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)