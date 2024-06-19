import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, Gdk, GdkPixbuf
from db_manager import get_all_songs, get_favorite_songs, mark_as_favorite, add_song
import os
from mutagen.flac import FLAC

class FlowWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Flow Music Player")
        self.set_border_width(10)
        self.set_default_size(800, 600)

        # Main Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Directory Selection Button
        self.select_dir_button = Gtk.Button(label="Select Music Directory")
        self.select_dir_button.connect("clicked", self.on_select_dir_clicked)
        vbox.pack_start(self.select_dir_button, False, False, 0)

        # Artist List
        self.artist_liststore = Gtk.ListStore(str)
        self.artist_treeview = Gtk.TreeView(model=self.artist_liststore)
        artist_renderer = Gtk.CellRendererText()
        artist_column = Gtk.TreeViewColumn("Artists", artist_renderer, text=0)
        self.artist_treeview.append_column(artist_column)
        self.artist_treeview.connect("row-activated", self.on_artist_selected)
        artist_scroll = Gtk.ScrolledWindow()
        artist_scroll.add(self.artist_treeview)
        vbox.pack_start(artist_scroll, True, True, 0)

        # Songs List
        self.song_liststore = Gtk.ListStore(str, str, GdkPixbuf.Pixbuf)
        self.song_treeview = Gtk.TreeView(model=self.song_liststore)
        song_renderer = Gtk.CellRendererText()
        title_column = Gtk.TreeViewColumn("Title", song_renderer, text=0)
        self.song_treeview.append_column(title_column)
        icon_renderer = Gtk.CellRendererPixbuf()
        icon_column = Gtk.TreeViewColumn("Favorite", icon_renderer, pixbuf=2)
        self.song_treeview.append_column(icon_column)
        self.song_treeview.connect("row-activated", self.on_song_selected)
        self.song_treeview.connect("button-press-event", self.on_song_icon_clicked)
        song_scroll = Gtk.ScrolledWindow()
        song_scroll.add(self.song_treeview)
        vbox.pack_start(song_scroll, True, True, 0)

        # Favorite Songs List
        self.favorite_liststore = Gtk.ListStore(str, str)
        self.favorite_treeview = Gtk.TreeView(model=self.favorite_liststore)
        favorite_renderer = Gtk.CellRendererText()
        favorite_column = Gtk.TreeViewColumn("Favorite Songs", favorite_renderer, text=0)
        self.favorite_treeview.append_column(favorite_column)
        self.favorite_treeview.connect("row-activated", self.on_favorite_song_selected)
        favorite_scroll = Gtk.ScrolledWindow()
        favorite_scroll.add(self.favorite_treeview)
        vbox.pack_start(favorite_scroll, True, True, 0)

        # Control Buttons
        control_box = Gtk.Box(spacing=6)
        self.play_button = Gtk.Button(label="Play")
        self.play_button.connect("clicked", self.on_play_clicked)
        control_box.pack_start(self.play_button, True, True, 0)

        self.pause_button = Gtk.Button(label="Pause")
        self.pause_button.connect("clicked", self.on_pause_clicked)
        control_box.pack_start(self.pause_button, True, True, 0)

        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        control_box.pack_start(self.stop_button, True, True, 0)

        self.previous_button = Gtk.Button(label="Previous")
        self.previous_button.connect("clicked", self.on_previous_clicked)
        control_box.pack_start(self.previous_button, True, True, 0)

        self.next_button = Gtk.Button(label="Next")
        self.next_button.connect("clicked", self.on_next_clicked)
        control_box.pack_start(self.next_button, True, True, 0)

        vbox.pack_start(control_box, False, False, 0)

        # Initialize GStreamer
        self.player = Gst.ElementFactory.make("playbin", "player")
        
        # Initialize Playlist
        self.playlist = []
        self.current_song_index = -1

        # Load songs from the database on startup
        self.load_artists()
        self.load_favorite_songs()

    def on_select_dir_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            music_directory = dialog.get_filename()
            self.load_music_library(music_directory)
        dialog.destroy()

    def extract_metadata(self, path):
        audio = FLAC(path)
        artist = audio.get('artist', ['Unknown Artist'])[0]
        title = audio.get('title', [os.path.splitext(os.path.basename(path))[0]])[0]
        print(f"Extracted metadata for {path}: Artist={artist}, Title={title}")
        return artist, title

    def load_music_library(self, directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".flac"):
                    path = os.path.join(root, file)
                    try:
                        artist, title = self.extract_metadata(path)
                        add_song(path, artist, title)
                    except Exception as e:
                        print(f"Failed to extract metadata for {path}: {e}")
        self.load_artists()

    def load_artists(self):
        self.artist_liststore.clear()
        songs = get_all_songs()
        artists = sorted(set(song[2] for song in songs))  # Assuming artist is in the 3rd column
        for artist in artists:
            self.artist_liststore.append([artist])
        self.load_songs_by_artist()

    def on_artist_selected(self, treeview, path, column):
        model = treeview.get_model()
        artist = model[path][0]
        # Load songs by the selected artist
        self.load_songs_by_artist(artist)

    def on_song_selected(self, treeview, path, column):
        model = treeview.get_model()
        song_title = model[path][0]
        # Find the song path by title
        songs = get_all_songs()
        song_path = None
        for song in songs:
            if song[3] == song_title:  # Assuming title is in the 4th column
                song_path = song[1]  # Assuming path is in the 2nd column
                break
        if song_path:
            self.play_song(song_path)

    def on_favorite_song_selected(self, treeview, path, column):
        model = treeview.get_model()
        song_title = model[path][0]
        # Find the song path by title
        songs = get_favorite_songs()
        song_path = None
        for song in songs:
            if song[3] == song_title:  # Assuming title is in the 4th column
                song_path = song[1]  # Assuming path is in the 2nd column
                break
        if song_path:
            self.play_song(song_path)

    def load_songs_by_artist(self, artist=None):
        # Clear the current song list
        self.song_liststore.clear()
        self.playlist = []  # Clear the playlist
        songs = get_all_songs()
        for song in songs:
            if artist is None or song[2] == artist:  # Assuming artist is in the 3rd column
                icon = self.get_scaled_pixbuf("corazon.png" if not song[4] else "done.png", 10)
                self.song_liststore.append([song[3], song[1], icon])  # Assuming title is in the 4th column
                self.playlist.append(song[1])  # Add song path to playlist

    def mark_song_as_favorite(self, song):
        # Assuming song is the song title, find the song id
        songs = get_all_songs()
        for s in songs:
            if s[3] == song:
                song_id = s[0]
                mark_as_favorite(song_id)
                break
        # Reload the songs and favorite songs list
        self.load_songs_by_artist()
        self.load_favorite_songs()

    def load_favorite_songs(self):
        # Clear the current favorite song list
        self.favorite_liststore.clear()
        # Add favorite songs to the favorite song list
        songs = get_favorite_songs()
        for song in songs:
            self.favorite_liststore.append([song[3], song[1]])  # Assuming title is in the 4th column

    def play_song(self, path):
        self.player.set_state(Gst.State.NULL)  # Stop the current song
        self.player.set_property("uri", "file://" + path)
        self.player.set_state(Gst.State.PLAYING)
        if path in self.playlist:
            self.current_song_index = self.playlist.index(path)

    def on_play_clicked(self, widget):
        self.player.set_state(Gst.State.PLAYING)

    def on_pause_clicked(self, widget):
        self.player.set_state(Gst.State.PAUSED)

    def on_stop_clicked(self, widget):
        self.player.set_state(Gst.State.NULL)

    def on_next_clicked(self, widget):
        if self.playlist and self.current_song_index < len(self.playlist) - 1:
            self.current_song_index += 1
            self.play_song(self.playlist[self.current_song_index])

    def on_previous_clicked(self, widget):
        if self.playlist and self.current_song_index > 0:
            self.current_song_index -= 1
            self.play_song(self.playlist[self.current_song_index])

    def on_song_icon_clicked(self, treeview, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is not None:
                path, column, cell_x, cell_y = path_info
                if column == self.song_treeview.get_column(1):  # Only handle clicks on the favorite column
                    model = treeview.get_model()
                    song_title = model[path][0]
                    self.mark_song_as_favorite(song_title)
                    return True
        return False

    def get_scaled_pixbuf(self, filepath, width):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)
        scaled_pixbuf = pixbuf.scale_simple(width, int(pixbuf.get_height() * (width / pixbuf.get_width())), GdkPixbuf.InterpType.BILINEAR)
        return scaled_pixbuf

if __name__ == "__main__":
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-xft-dpi", int(120 * 1024))  # 120% scaling
    win = FlowWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
