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
            favorite BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def add_song(path, artist, title, favorite=False):
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO songs (path, artist, title, favorite)
        VALUES (?, ?, ?, ?)
    ''', (path, artist, title, favorite))
    conn.commit()
    conn.close()

def get_all_songs():
    conn = sqlite3.connect('music_library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM songs')
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

create_tables()
