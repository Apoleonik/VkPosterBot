BEGIN TRANSACTION;
CREATE TABLE blacklist (
    id integer primary key,
    word varchar(255) UNIQUE NOT NULL
);
CREATE TABLE channels (
    id integer primary key,
    is_active boolean default false,
    telegram_channel varchar(255) NOT NULL,
    vk_channel varchar(255) NOT NULL,
    vk_channel_id int default 0,
    last_post_id integer default 0,
    send_video_post boolean default false,
    send_video_post_text boolean default false,
    send_photo_post boolean default false,
    send_photo_post_text boolean default false,
    send_text_post boolean default false,
    timer integer default 60
);
COMMIT;