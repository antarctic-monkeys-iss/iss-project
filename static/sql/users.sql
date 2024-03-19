/*From local system: mysql*/
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

/*From cockroach db: postgresql*/
CREATE TABLE public.users (
  id INT8 NOT NULL DEFAULT unique_rowid(),
  username VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (id ASC),
  UNIQUE INDEX email_unique (email ASC)
);