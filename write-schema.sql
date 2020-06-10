create table if not exists posts (
    id varchar(32) primary key not null,
    title varchar(100) not null,
    content varchar(500) not null,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp on update current_timestamp
);

GRANT REPLICATION SLAVE ON *.* TO 'read-mysql'@'%' IDENTIFIED BY 'password';

FLUSH PRIVILEGES;
