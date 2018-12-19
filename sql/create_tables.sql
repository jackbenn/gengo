drop table move;
drop table game;
drop table player;



create table player (
    id serial primary key,
    name varchar unique not null
);

create table game (
    id serial primary key,
    name varchar,
    player1 int references player(id) not null,
    player2 int references player(id) not null,
    score int
);

create table move (
    game int references game(id),
    row int,
    col int,
    sequence int not null,
    primary key(game, sequence)
);

insert into player (name) values ('foo');
insert into player (name) values ('bar');

