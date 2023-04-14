create table cakes
(
    id          int auto_increment,
    title       varchar(127)  null,
    description varchar(1023) null,
    cost        int           null,
    constraint table_name_pk
        primary key (id)
);

create table password
(
    pass_hash varchar(1023) not null
);