create table if not exists posts (
    id varchar(36) primary key not null,
    title varchar(100) not null,
    content varchar(500) not null,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp on update current_timestamp
);
create unique index posts_id_idx on posts(id) using btree;
create unique index posts_title_idx on posts(title) using btree;
