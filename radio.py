"""
Version 1.0.0
Samuel LaMonde 1/11/26
NOT MY WORK; ~80% coded by ChatGPT
"""
import os
import random
from pydub import AudioSegment
import numpy as np
import pyloudnorm as pyln

# =========================
# Base Directories
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MUSIC_DIR = os.path.join(BASE_DIR, "music")
DJ_ROOT_DIR = os.path.join(BASE_DIR, "dj")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = "dj_mix.mp3"

# =========================
# Audio Settings
# =========================

START_VOLUME_DB = -10
MUSIC_TARGET_DB = 0  # used for fades, not loudness normalization
DJ_GAIN_DB = 6
MUSIC_FADE_DURATION_MS = 1500
MUSIC_INTRO_FADE_MS = 3000
PAUSE_BETWEEN_SEGMENTS_MS = 0
CROSSFADE_DURATION_MS = 1000
DJ_MUSIC_OVERLAP_MS = 10000
TARGET_LUFS = -16  # target loudness for all music tracks

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")

# =========================
# Functions
# =========================

def normalize_loudness(audio, target_lufs):
    """
    Normalize a pydub AudioSegment to the target LUFS using pyloudnorm.
    """
    # Convert pydub AudioSegment to float32 array in range [-1.0, 1.0]
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= 2 ** (8 * audio.sample_width - 1)  # normalize to -1.0..1.0

    if audio.channels == 2:
        samples = samples.reshape((-1, 2))

    meter = pyln.Meter(audio.frame_rate)
    loudness = meter.integrated_loudness(samples)

    # Calculate gain to reach target LUFS
    gain = target_lufs - loudness

    # Apply gain in dB
    return audio.apply_gain(gain)

def select_subfolder(root, label, exclude=None):
    if exclude is None:
        exclude = []

    options = [
        d for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d)) and d.lower() not in [e.lower() for e in exclude]
    ]

    if not options:
        raise RuntimeError(f"No {label} folders found in: {root} (after excluding {exclude})")

    print(f"\nAvailable {label}:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")

    while True:
        choice = input(f"\nSelect {label} by number: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        print("Invalid selection. Try again.")

def load_audio_files(folder):
    if not os.path.isdir(folder):
        raise RuntimeError(f"Folder does not exist: {folder}")

    audio_files = [f for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_FORMATS)]

    if not audio_files:
        subdirs = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
        if subdirs:
            raise RuntimeError(
                f"{folder} contains subfolders but no audio files. "
                f"Did you mean to select one of: {subdirs}?"
            )
        return {}

    return {f: AudioSegment.from_file(os.path.join(folder, f)) for f in audio_files}

def mix_dj_with_music(
    dj_clip,
    music_track,
    start_volume_db=START_VOLUME_DB,
    dj_gain_db=DJ_GAIN_DB,
    music_fade_duration_ms=MUSIC_FADE_DURATION_MS,
    music_target_db=MUSIC_TARGET_DB,
    overlap_ms=DJ_MUSIC_OVERLAP_MS,
    intro_fade_ms=MUSIC_INTRO_FADE_MS
):
    dj_clip = dj_clip + dj_gain_db
    dj_length = len(dj_clip)

    overlap_ms = min(overlap_ms, dj_length)

    # DJ-only portion
    dj_only = dj_clip[:-overlap_ms]

    # DJ tail (last overlap_ms)
    dj_tail = dj_clip[-overlap_ms:]

    # Music starts overlap_ms before DJ ends
    music_intro = music_track[:overlap_ms].apply_gain(start_volume_db)

    # Fade music in behind DJ
    music_intro = music_intro.fade_in(min(intro_fade_ms, overlap_ms))

    # Overlay DJ tail on music intro
    overlap = music_intro.overlay(dj_tail)

    # Remaining music after DJ finishes
    tail = music_track[overlap_ms:]
    if len(tail) > 0:
        tail = tail.apply_gain(start_volume_db)
        fade_gain = music_target_db - start_volume_db
        tail = tail.fade(
            from_gain=0,
            to_gain=fade_gain,
            start=0,
            duration=music_fade_duration_ms
        )

    return dj_only + overlap + tail

# =========================
# Main
# =========================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load and LUFS-normalize music
    music_tracks = load_audio_files(MUSIC_DIR)
    if not music_tracks:
        raise RuntimeError(f"No music files found in: {MUSIC_DIR}")

    music_list = [
        normalize_loudness(track, TARGET_LUFS)
        for track in music_tracks.values()
    ]
    random.shuffle(music_list)

    # Select DJ
    dj_name = select_subfolder(DJ_ROOT_DIR, "DJ")
    dj_dir = os.path.join(DJ_ROOT_DIR, dj_name)

    # Select season
    season = select_subfolder(dj_dir, "season", exclude=["stingers", "barnfind"])
    selected_dj_dir = os.path.join(dj_dir, season)

    print(f"\nUsing DJ: {dj_name}")
    print(f"Using season: {season}")

    # Load DJ clips
    dj_clips = load_audio_files(selected_dj_dir)
    dj_items = list(dj_clips.items())
    random.shuffle(dj_items)
    dj_index = 0

    # Load stingers
    stinger_dir = os.path.join(dj_dir, "stingers")
    stingers = load_audio_files(stinger_dir) if os.path.isdir(stinger_dir) else {}
    stinger_items = list(stingers.values())
    random.shuffle(stinger_items)
    stinger_index = 0

    print(f"\nFound {len(stinger_items)} stingers.")

    final_mix = AudioSegment.silent(0)
    last_segment_was_plain = False

    for i, music_track in enumerate(music_list):
        if i % 2 == 0:
            print(f"Adding plain music track #{i+1}")
            final_mix += music_track
            last_segment_was_plain = True
        else:
            if stinger_items and (i // 2) % 2 == 1:
                stinger = stinger_items[stinger_index]
                print(f"Adding stinger before song #{i+1}")
                final_mix += stinger
                stinger_index = (stinger_index + 1) % len(stinger_items)
                last_segment_was_plain = False

            if dj_items:
                dj_filename, dj_clip = dj_items[dj_index]
                print(f"Mixing DJ clip: {dj_filename} with song #{i+1}")
                mixed = mix_dj_with_music(dj_clip, music_track)

                if last_segment_was_plain:
                    final_mix = final_mix.append(mixed, crossfade=CROSSFADE_DURATION_MS)
                else:
                    final_mix += mixed

                dj_index = (dj_index + 1) % len(dj_items)
            else:
                final_mix += music_track

            last_segment_was_plain = False

        final_mix += AudioSegment.silent(PAUSE_BETWEEN_SEGMENTS_MS)
        last_segment_was_plain = False

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_mix.export(output_path, format="mp3", bitrate="192k")
    print(f"\n✅ DJ mix exported to: {output_path}")

if __name__ == "__main__":
    main()
