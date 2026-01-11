"""
ForzaRadio 1.0.0
Samuel LaMonde 1/11/2026
NOT MY WORK - ~80% VIBECODED BY CHATGPT
"""
import os
import random
from pydub import AudioSegment

MUSIC_DIR = "music"
DJ_DIR = "dj"
OUTPUT_DIR = "output"
OUTPUT_FILE = "dj_mix.mp3"

# Global settings
START_VOLUME_DB = -18         # Music volume under DJ (negative = quieter)
MUSIC_TARGET_DB = -6          # Music volume after fade (negative = quieter than full track)
DJ_GAIN_DB = 0                # DJ voice volume (0 = unchanged, + = louder, - = quieter)
MUSIC_FADE_DURATION_MS = 1500 # Duration of music fade-in after DJ in ms
PAUSE_BETWEEN_SEGMENTS_MS = 0 # Optional pause between segments

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg")

def load_audio_files(folder):
    return {
        f: AudioSegment.from_file(os.path.join(folder, f))
        for f in os.listdir(folder)
        if f.lower().endswith(SUPPORTED_FORMATS)
    }

def mix_dj_with_music(dj_clip, music_track,
                      start_volume_db=START_VOLUME_DB,
                      dj_gain_db=DJ_GAIN_DB,
                      music_fade_duration_ms=MUSIC_FADE_DURATION_MS,
                      music_target_db=MUSIC_TARGET_DB):

    # Apply DJ gain
    dj_clip = dj_clip + dj_gain_db
    dj_length = len(dj_clip)

    # --- Part 1: quiet music under DJ ---
    music_under_dj = music_track[:dj_length].apply_gain(start_volume_db)
    intro_segment = music_under_dj.overlay(dj_clip)

    # --- Part 2: music after DJ ---
    song_tail = music_track[dj_length:]

    if len(song_tail) > 0:
        # Start quiet and fade to target volume
        song_tail = song_tail.apply_gain(start_volume_db)
        fade_gain = music_target_db - start_volume_db
        song_tail = song_tail.fade(from_gain=0, to_gain=fade_gain, start=0, duration=music_fade_duration_ms)

    full_segment = intro_segment + song_tail
    return full_segment

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    music_tracks = load_audio_files(MUSIC_DIR)
    dj_clips = load_audio_files(DJ_DIR)

    if not music_tracks:
        raise RuntimeError("No music files found in folder: " + MUSIC_DIR)
    if not dj_clips:
        raise RuntimeError("No DJ files found in folder: " + DJ_DIR)

    final_mix = AudioSegment.silent(0)
    used_tracks = []

    music_list = list(music_tracks.values())

    for dj_filename, dj_clip in dj_clips.items():
        # Pick a random music track, avoid immediate repeats
        available_tracks = [m for m in music_list if m not in used_tracks]
        if not available_tracks:
            used_tracks = []
            available_tracks = music_list
        music_track = random.choice(available_tracks)
        used_tracks.append(music_track)

        print(f"Mixing DJ clip: {dj_filename}")

        # Mix DJ + music
        mixed_segment = mix_dj_with_music(
            dj_clip,
            music_track,
            start_volume_db=START_VOLUME_DB,
            dj_gain_db=DJ_GAIN_DB,
            music_fade_duration_ms=MUSIC_FADE_DURATION_MS,
            music_target_db=MUSIC_TARGET_DB
        )

        # Append to final mix
        final_mix += mixed_segment

        # Optional pause between segments
        final_mix += AudioSegment.silent(duration=PAUSE_BETWEEN_SEGMENTS_MS)

    # Export final mix
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_mix.export(output_path, format="mp3", bitrate="192k")
    print(f"\n✅ DJ mix exported to: {output_path}")

if __name__ == "__main__":
    main()