import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, Gdk, GdkPixbuf, GLib
from db_manager import get_all_songs, get_favorite_songs, mark_as_favorite, add_song, remove_favorite
import os
from mutagen.flac import FLAC

class FlowWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Flow Music Player")
        self.set_border_width(10)
        self.set_default_size(800, 600)

     #   self.set_icon_from_file("logo.jpg")

        self.current_artist = None  # Store the currently selected artist
        self.current_playlist = []  # To store the current playlist
        self.playlist_type = 'all'  # To keep track of the current playlist type

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
        self.favorite_liststore = Gtk.ListStore(str, str, GdkPixbuf.Pixbuf)
        self.favorite_treeview = Gtk.TreeView(model=self.favorite_liststore)
        favorite_renderer = Gtk.CellRendererText()
        favorite_column = Gtk.TreeViewColumn("Favorite Songs", favorite_renderer, text=0)
        self.favorite_treeview.append_column(favorite_column)

        delete_renderer = Gtk.CellRendererPixbuf()
        delete_column = Gtk.TreeViewColumn("Delete", delete_renderer, pixbuf=2)
        self.favorite_treeview.append_column(delete_column)
        self.favorite_treeview.connect("row-activated", self.on_favorite_song_selected)
        self.favorite_treeview.connect("button-press-event", self.on_favorite_delete_clicked)
        favorite_scroll = Gtk.ScrolledWindow()
        favorite_scroll.add(self.favorite_treeview)
        vbox.pack_start(favorite_scroll, True, True, 0)

        # Song Information (at the bottom)
        self.song_info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.cover_art_image = Gtk.Image()
        self.cover_art_image.set_size_request(100, 100)  # Ensure space for the image
        self.song_info_box.pack_start(self.cover_art_image, False, False, 0)
        
        # Box for controls and song info
        self.control_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.play_button = Gtk.Button(label="Play")
        self.play_button.connect("clicked", self.on_play_clicked)
        self.controls_box.pack_start(self.play_button, True, True, 0)

        self.pause_button = Gtk.Button(label="Pause")
        self.pause_button.connect("clicked", self.on_pause_clicked)
        self.controls_box.pack_start(self.pause_button, True, True, 0)

        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        self.controls_box.pack_start(self.stop_button, True, True, 0)

        self.previous_button = Gtk.Button(label="Previous")
        self.previous_button.connect("clicked", self.on_previous_clicked)
        self.controls_box.pack_start(self.previous_button, True, True, 0)

        self.next_button = Gtk.Button(label="Next")
        self.next_button.connect("clicked", self.on_next_clicked)
        self.controls_box.pack_start(self.next_button, True, True, 0)

        self.control_info_box.pack_start(self.controls_box, False, False, 0)
        
        self.song_info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.song_title_label = Gtk.Label()
        self.song_title_label.set_justify(Gtk.Justification.CENTER)
        self.artist_name_label = Gtk.Label()
        self.artist_name_label.set_justify(Gtk.Justification.CENTER)
        self.song_info_vbox.pack_start(self.song_title_label, False, False, 0)
        self.song_info_vbox.pack_start(self.artist_name_label, False, False, 0)
        self.control_info_box.pack_start(self.song_info_vbox, True, True, 0)
        
        self.progress_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress_scale.set_range(0, 100)
        self.progress_scale.set_draw_value(False)
        self.progress_scale.connect("button-release-event", self.on_progress_scale_released)
        self.control_info_box.pack_start(self.progress_scale, False, False, 0)

        self.song_info_box.pack_start(self.control_info_box, True, True, 0)
        vbox.pack_end(self.song_info_box, False, False, 0)

        # Initialize GStreamer
        self.player = Gst.ElementFactory.make("playbin", "player")
        
        # Set up GStreamer bus
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)

        # Initialize Playlist
        self.playlist = []
        self.current_song_index = -1

        # Load songs from the database on startup
        self.load_artists()
        self.load_favorite_songs()

        # Update the progress bar periodically
        GLib.timeout_add(1000, self.update_progress)

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
        self.current_artist = artist  # Set the currently selected artist
        self.playlist_type = 'all'  # When selecting an artist, the playlist is 'all' songs
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
            self.playlist = self.current_playlist  # Set playlist to the current loaded playlist
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
            self.playlist_type = 'favorites'
            self.playlist = [song[1] for song in songs]  # Update playlist to favorite songs
            self.play_song(song_path)

    def load_songs_by_artist(self, artist=None):
        # Clear the current song list
        self.song_liststore.clear()
        self.playlist = []  # Clear the playlist
        self.current_playlist = []  # Clear the current playlist
        songs = get_all_songs()
        for song in songs:
            if artist is None or song[2] == artist:  # Assuming artist is in the 3rd column
                icon = self.get_scaled_pixbuf("corazon.png" if not song[4] else "done.png", 10)
                self.song_liststore.append([song[3], song[1], icon])  # Assuming title is in the 4th column
                self.playlist.append(song[1])  # Add song path to playlist
                self.current_playlist.append(song[1])  # Also add to the current playlist

    def mark_song_as_favorite(self, song):
        # Assuming song is the song title, find the song id
        songs = get_all_songs()
        for s in songs:
            if s[3] == song:
                song_id = s[0]
                current_favorite_status = s[4]
                mark_as_favorite(song_id, not current_favorite_status)
                break
        # Reload the songs by the current artist and favorite songs list
        self.load_songs_by_artist(self.current_artist)
        self.load_favorite_songs()

    def load_favorite_songs(self):
        # Clear the current favorite song list
        self.favorite_liststore.clear()
        # Add favorite songs to the favorite song list
        songs = get_favorite_songs()
        for song in songs:
            delete_icon = self.get_scaled_pixbuf("borrar.png", 10)
            self.favorite_liststore.append([song[3], song[1], delete_icon])  # Assuming title is in the 4th column

    def remove_favorite_song(self, song_title):
        songs = get_favorite_songs()
        for song in songs:
            if song[3] == song_title:
                song_id = song[0]
                remove_favorite(song_id)
                break
        # Update all song and favorite song lists
        self.load_songs_by_artist(self.current_artist)
        self.load_favorite_songs()

    def play_song(self, path):
        self.player.set_state(Gst.State.NULL)  # Stop the current song
        self.player.set_property("uri", "file://" + path)
        self.player.set_state(Gst.State.PLAYING)
        if path in self.playlist:
            self.current_song_index = self.playlist.index(path)
            self.update_song_info(path)

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

    def on_favorite_delete_clicked(self, treeview, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is not None:
                path, column, cell_x, cell_y = path_info
                if column == self.favorite_treeview.get_column(1):  # Only handle clicks on the delete column
                    model = treeview.get_model()
                    song_title = model[path][0]
                    self.remove_favorite_song(song_title)
                    return True
        return False

    def on_progress_scale_released(self, scale, event):
        value = scale.get_value()
        self.seek_to_position(value)

    def seek_to_position(self, value):
        success, duration_nanoseconds = self.player.query_duration(Gst.Format.TIME)
        if success:
            new_position = duration_nanoseconds * value / 100
            self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, new_position)

    def update_progress(self):
        success, current_nanoseconds = self.player.query_position(Gst.Format.TIME)
        success, duration_nanoseconds = self.player.query_duration(Gst.Format.TIME)
        if success:
            current_seconds = current_nanoseconds / Gst.SECOND
            duration_seconds = duration_nanoseconds / Gst.SECOND
            progress_percentage = (current_seconds / duration_seconds) * 100
            self.progress_scale.set_value(progress_percentage)
        return True  # Continue calling this function periodically

    def update_song_info(self, path):
        # Update song title and artist name
        artist, title = self.extract_metadata(path)
        self.song_title_label.set_text(f"Title: {title}")
        self.artist_name_label.set_text(f"Artist: {artist}")

        # Update cover art
        cover_path_jpg = os.path.join(os.path.dirname(path), "cover.jpg")

        if os.path.exists(cover_path_jpg):
            cover_pixbuf = GdkPixbuf.Pixbuf.new_from_file(cover_path_jpg)
            print(f"Found cover.jpg for {path}")
        elif os.path.exists(cover_path_png):
            cover_pixbuf = GdkPixbuf.Pixbuf.new_from_file(cover_path_png)
            print(f"Found cover.png for {path}")
        elif os.path.exists(cover_path_jpeg):
            cover_pixbuf = GdkPixbuf.Pixbuf.new_from_file(cover_path_jpeg)
            print(f"Found cover.jpeg for {path}")
        else:
            cover_pixbuf = None
            print(f"No cover art found for {path}")

        if cover_pixbuf:
            scaled_cover_pixbuf = cover_pixbuf.scale_simple(100, 100, GdkPixbuf.InterpType.BILINEAR)
            self.cover_art_image.set_from_pixbuf(scaled_cover_pixbuf)
        else:
            self.cover_art_image.clear()

    def get_scaled_pixbuf(self, filepath, width):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)
        scaled_pixbuf = pixbuf.scale_simple(width, int(pixbuf.get_height() * (width / pixbuf.get_width())), GdkPixbuf.InterpType.BILINEAR)
        return scaled_pixbuf

    def on_about_to_finish(self, player):
        print("Song about to finish")
        self.on_next_clicked(None)

    def on_eos(self, bus, msg):
        print("End of song")
        self.on_next_clicked(None)

    def on_error(self, bus, msg):
        err, debug = msg.parse_error()
        print("Error:", err, debug)

if __name__ == "__main__":
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-xft-dpi", int(120 * 1024))  # 120% scaling
    win = FlowWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
