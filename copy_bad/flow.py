import os
from db_manager import add_song, get_all_songs
from gui import FlowWindow
from gi.repository import Gtk, Gst
from mutagen.flac import FLAC

def extract_metadata(path):
    audio = FLAC(path)
    artist = audio.get('artist', ['Unknown Artist'])[0]
    title = audio.get('title', [os.path.splitext(os.path.basename(path))[0]])[0]
    print(f"Extracted metadata for {path}: Artist={artist}, Title={title}")
    return artist, title

def load_music_library(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".flac"):
                path = os.path.join(root, file)
                try:
                    artist, title = extract_metadata(path)
                    add_song(path, artist, title)
                except Exception as e:
                    print(f"Failed to extract metadata for {path}: {e}")

def main():
    # Initialize GStreamer
    Gst.init(None)

    # Create and run the GUI
    win = FlowWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
