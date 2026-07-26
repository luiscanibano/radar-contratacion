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

-- Suscripción de Stripe del usuario. Una fila por usuario (upsert en cada
-- evento de webhook): sin fila = plan gratuito. `plan` y `estado` reflejan el
-- último evento visto de Stripe (ver api/billing.py); `estado` usa los mismos
-- valores que `subscription.status` de Stripe (active, past_due, canceled...).
create table if not exists suscripciones (
    usuario_id             bigint primary key references usuarios(id),
    stripe_customer_id     text not null,
    stripe_subscription_id text unique,
    plan                   text not null,
    estado                 text not null,
    periodo_fin            timestamptz,
    actualizado_en         timestamptz not null default now()
);

-- Cuota de preguntas del agente, contada por usuario y mes natural (formato
-- 'YYYY-MM'). Un plan sin límite (cuota None en api/planes.py) nunca consulta
-- esta tabla para bloquear, pero sí se sigue contando para analítica.
create table if not exists uso_mensual (
    usuario_id  bigint not null references usuarios(id),
    mes         text not null,
    preguntas   integer not null default 0,
    primary key (usuario_id, mes)
);

-- Búsqueda guardada por un usuario. Se reejecuta periódicamente (ver
-- orchestration/definitions.py) contra la búsqueda híbrida y avisa por email
-- de los resultados que no se habían visto antes.
create table if not exists alertas (
    id             bigint generated always as identity primary key,
    usuario_id     bigint not null references usuarios(id),
    consulta_texto text not null,
    creado_en      timestamptz not null default now()
);

-- Resultados ya notificados de cada alerta. Se guarda el conjunto completo de
-- entry_id vistos (no solo "el último"): el ranking de la búsqueda híbrida no
-- es estable entre ejecuciones (RRF puede reordenar), así que no hay una
-- noción de "más reciente" fiable en la que apoyarse.
create table if not exists alertas_vistos (
    alerta_id  bigint not null references alertas(id) on delete cascade,
    entry_id   text not null,
    visto_en   timestamptz not null default now(),
    primary key (alerta_id, entry_id)
);
