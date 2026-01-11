"""
Version 1.0.0
Samuel LaMonde 1/11/26
NOT MY WORK; ~80% coded by ChatGPT
"""
import os
import random
from pydub import AudioSegment

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

START_VOLUME_DB = -18
MUSIC_TARGET_DB = -6
DJ_GAIN_DB = 0
MUSIC_FADE_DURATION_MS = 1500
PAUSE_BETWEEN_SEGMENTS_MS = 0

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")

def select_subfolder(root, label, exclude=None):
    if exclude is None:
        exclude = []

    # Only include directories not in the exclude list
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
    music_target_db=MUSIC_TARGET_DB
):
    dj_clip = dj_clip + dj_gain_db
    dj_length = len(dj_clip)

    # Music under DJ
    music_under_dj = music_track[:dj_length].apply_gain(start_volume_db)
    intro = music_under_dj.overlay(dj_clip)

    # Music after DJ
    tail = music_track[dj_length:]
    if len(tail) > 0:
        tail = tail.apply_gain(start_volume_db)
        fade_gain = music_target_db - start_volume_db
        tail = tail.fade(from_gain=0, to_gain=fade_gain, start=0, duration=music_fade_duration_ms)

    return intro + tail

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load music
    music_tracks = load_audio_files(MUSIC_DIR)
    if not music_tracks:
        raise RuntimeError(f"No music files found in: {MUSIC_DIR}")
    music_list = list(music_tracks.values())
    random.shuffle(music_list)

    # Select DJ
    dj_name = select_subfolder(DJ_ROOT_DIR, "DJ")
    dj_dir = os.path.join(DJ_ROOT_DIR, dj_name)

    # Select season, excluding stingers and barnfind
    season = select_subfolder(dj_dir, "season", exclude=["stingers", "barnfind"])
    selected_dj_dir = os.path.join(dj_dir, season)

    print(f"\nUsing DJ: {dj_name}")
    print(f"Using season: {season}")

    # Load DJ clips
    dj_clips = load_audio_files(selected_dj_dir)
    dj_items = list(dj_clips.items())
    random.shuffle(dj_items)
    dj_index = 0

    # Load stingers (next to seasonal folders)
    stinger_dir = os.path.join(dj_dir, "stingers")
    stingers = load_audio_files(stinger_dir) if os.path.isdir(stinger_dir) else {}
    stinger_items = list(stingers.values())
    random.shuffle(stinger_items)
    stinger_index = 0

    print(f"Found {len(stinger_items)} stingers.")

    final_mix = AudioSegment.silent(0)
    use_dj_next = True  # flag to alternate DJ and stinger on even songs

    # Loop through music tracks
    for i, music_track in enumerate(music_list):
        if i % 2 == 0:
            # Odd-numbered song (1,3,5...) → plain music
            print(f"Adding plain music track #{i+1}")
            final_mix += music_track
        else:
            # Even-numbered song (2,4,6...) → insert DJ or stinger before song
            if use_dj_next and dj_items:
                dj_filename, dj_clip = dj_items[dj_index]
                print(f"Mixing DJ clip: {dj_filename} with song #{i+1}")
                mixed = mix_dj_with_music(dj_clip, music_track)
                final_mix += mixed
                dj_index = (dj_index + 1) % len(dj_items)
            elif not use_dj_next and stinger_items:
                stinger = stinger_items[stinger_index]
                print(f"Adding stinger before song #{i+1}")
                final_mix += stinger
                final_mix += music_track
                stinger_index = (stinger_index + 1) % len(stinger_items)
            else:
                # fallback if DJ or stinger missing
                final_mix += music_track

            # Toggle for next even song
            use_dj_next = not use_dj_next

        # Optional pause
        final_mix += AudioSegment.silent(PAUSE_BETWEEN_SEGMENTS_MS)

    # Export final mix
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_mix.export(output_path, format="mp3", bitrate="192k")
    print(f"\n✅ DJ mix exported to: {output_path}")

if __name__ == "__main__":
    main()
