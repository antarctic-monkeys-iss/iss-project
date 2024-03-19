/*From local system: mysql*/
CREATE TABLE images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_name VARCHAR(255) NOT NULL,
    image_content LONGBLOB NOT NULL,
    email VARCHAR(255) NOT NULL,
    time_of_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

/*From cockroach db: postgresql*/
CREATE TABLE public.images (
  id INT8 NOT NULL DEFAULT unique_rowid(),
  image_content BYTES NOT NULL,
  email VARCHAR(255) NOT NULL,
  time_of_upload TIMESTAMP NULL DEFAULT current_timestamp():::TIMESTAMP,
  image_name VARCHAR(255) NULL,
  CONSTRAINT images_pkey PRIMARY KEY (id ASC)
);