import sqlite3

def create_tables():
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            artist TEXT,
            title TEXT,
            album TEXT,
            favorite BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def add_song(path, artist, title, album, favorite=False):
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO songs (path, artist, title, album, favorite)
        VALUES (?, ?, ?, ?, ?)
    ''', (path, artist, title, album, favorite))
    conn.commit()
    conn.close()

def get_all_songs():
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM songs')
    songs = c.fetchall()
    conn.close()
    return songs

def get_albums_by_artist(artist):
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT album FROM songs WHERE artist = ?', (artist,))
    albums = c.fetchall()
    conn.close()
    return albums

def get_songs_by_album(artist, album):
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM songs WHERE artist = ? AND album = ?', (artist, album))
    songs = c.fetchall()
    conn.close()
    return songs

def mark_as_favorite(song_id, favorite=True):
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('UPDATE songs SET favorite = ? WHERE id = ?', (favorite, song_id))
    conn.commit()
    conn.close()

def get_favorite_songs():
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM songs WHERE favorite = 1')
    songs = c.fetchall()
    conn.close()
    return songs

def remove_favorite(song_id):
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('UPDATE songs SET favorite = 0 WHERE id = ?', (song_id,))
    conn.commit()
    conn.close()

def add_album_column():
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(songs)")
    columns = [column[1] for column in c.fetchall()]
    if 'album' not in columns:
        c.execute('ALTER TABLE songs ADD COLUMN album TEXT')
    conn.commit()
    conn.close()

# Create tables and add album column if it doesn't exist
create_tables()
add_album_column()
