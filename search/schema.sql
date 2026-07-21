-- Esquema de la capa vectorial en Postgres + pgvector.
--
-- Grano: una fila por expediente (entry_id), con el texto de la licitación
-- (título + objeto), su embedding denso y una columna tsvector en español para
-- la parte léxica de la búsqueda híbrida.
--
-- La dimensión del vector (1024) va acoplada al modelo de embeddings
-- (BAAI/bge-m3). Si se cambia el modelo hay que cambiar `vector(N)` aquí y
-- `embedding_dim` en api/settings.py.

create extension if not exists vector;

create table if not exists licitacion_embeddings (
    entry_id        text primary key,
    expediente      text,
    objeto          text,
    organo          text,
    cpv_division    text,
    anio            integer,
    presupuesto     numeric,

    -- texto realmente embebido (título + objeto), y su hash para ingesta
    -- incremental: solo re-embebemos filas cuyo contenido cambió.
    contenido       text not null,
    contenido_hash  text not null,

    embedding       vector(1024),

    -- tsvector materializado: Postgres lo recalcula solo al cambiar `contenido`.
    fts             tsvector generated always as (to_tsvector('spanish', contenido)) stored,

    actualizado_en  timestamptz not null default now()
);

-- Índice léxico (GIN sobre el tsvector) para `@@` y `ts_rank`.
create index if not exists idx_lic_emb_fts
    on licitacion_embeddings using gin (fts);

-- Índice vectorial aproximado (HNSW, distancia coseno) para el `<=>`.
create index if not exists idx_lic_emb_hnsw
    on licitacion_embeddings using hnsw (embedding vector_cosine_ops);
