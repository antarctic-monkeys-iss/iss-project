/*From local system: mysql*/
CREATE TABLE songs (
    id INT PRIMARY KEY,
    song_name VARCHAR(255) NOT NULL,
    song_content LONGBLOB NOT NULL,
    email VARCHAR(255) NOT NULL
);

/*From cockroach db: postgresql*/
CREATE TABLE public.songs (
  id INT8 NOT NULL DEFAULT unique_rowid(),
  song_name VARCHAR(255) NOT NULL,
  song_content BYTES NOT NULL,
  email VARCHAR(255) NOT NULL,
  CONSTRAINT songs_pkey PRIMARY KEY (id ASC)
);