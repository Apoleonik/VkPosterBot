BEGIN TRANSACTION;
CREATE TABLE blacklist (
    id integer primary key,
    word varchar(255) UNIQUE NOT NULL
);
INSERT INTO "blacklist" VALUES(1,'club');
INSERT INTO "blacklist" VALUES(2,'https');
INSERT INTO "blacklist" VALUES(3,'vk');
INSERT INTO "blacklist" VALUES(4,'сохр');
INSERT INTO "blacklist" VALUES(5,'трек');
INSERT INTO "blacklist" VALUES(6,'коменты');
INSERT INTO "blacklist" VALUES(7,'комменты');
INSERT INTO "blacklist" VALUES(9,'ru');
INSERT INTO "blacklist" VALUES(10,'com');
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
, set_last_post_id boolean default true);
INSERT INTO "channels" VALUES(1,1,'animememss','animemes',0,1438969,0,0,1,0,0,60,0);
INSERT INTO "channels" VALUES(2,1,'animewebmm','animewebm',0,794185,1,0,0,0,0,60,0);
INSERT INTO "channels" VALUES(3,1,'gameswebmm','gameswebm',0,306311,1,0,0,0,0,60,0);
INSERT INTO "channels" VALUES(4,1,'historyshaverma','history_shaverma',0,776146,0,0,1,1,0,60,0);
INSERT INTO "channels" VALUES(5,1,'loliess','lolichan',0,1237284,0,0,1,0,0,30,0);
COMMIT;
