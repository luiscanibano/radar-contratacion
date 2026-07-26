-- Esquema de la capa de aplicación (auth, etc.) en Postgres.
--
-- Separado de search/schema.sql (capa vectorial): comparten instancia de
-- Postgres pero tienen ciclos de vida y dueños distintos.

create table if not exists usuarios (
    id             bigint generated always as identity primary key,
    email          text not null unique,
    password_hash  text not null,
    creado_en      timestamptz not null default now()
);
