import os
import sqlite3

from typing import Dict, List


class DbController:
    def __init__(self):
        self._connection = sqlite3.connect(os.path.join('db', 'channels.db'))
        self._cursor = self._connection.cursor()

        self._check_db_exists()

        self._channel_columns = self._get_channel_columns()

    def _check_db_exists(self):
        """check db exists"""
        self._cursor.execute("SELECT name from sqlite_master where type='table' AND name='channels'")
        db_exists = self._cursor.fetchall()
        if not db_exists:
            self._init_db()

    def _init_db(self):
        """initialize db"""

        with open("create_db.sql") as f:
            sql_data = f.read()
        with self._connection:
            self._cursor.executescript(sql_data)

    def _get_channel_columns(self) -> List[str]:
        """get channel table columns names"""

        self._cursor.execute("SELECT * FROM 'channels'")
        columns = list(map(lambda row: row[0], self._cursor.description))
        return columns

    def _rows_to_dict(self, rows) -> List[Dict]:
        """convert sql row tuple to dict"""
        channels = []
        for row in rows:
            row_dict = {}
            for index, column in enumerate(self._channel_columns):
                row_dict[column] = row[index]
            channels.append(row_dict)
        return channels

    def get_cursor(self):
        """get db cursor"""
        return self._cursor

    def get_all_channels(self) -> List[Dict]:
        """get all channels rows from db"""
        self._cursor.execute("SELECT * from 'channels'")
        rows = self._cursor.fetchall()
        channels = self._rows_to_dict(rows)
        return channels

    def get_channel(self, telegram_channel: str) -> List[Dict]:
        """get channel row from db and filtered by telegram_channel key"""
        self._cursor.execute(f"SELECT * from 'channels' where telegram_channel='{telegram_channel}'")
        rows = self._cursor.fetchall()
        return self._rows_to_dict(rows)

    def add_channel(self, channel_data: Dict):
        """add channel row to channels table"""
        with self._connection:
            joined_columns = ", ".join(channel_data.keys())
            values = tuple(channel_data.values())
            placeholders = ", ".join("?" * len(channel_data.keys()))
            self._cursor.execute(f"INSERT INTO 'channels' ({joined_columns}) VALUES ({placeholders})", values)

    def delete_channel(self, row_id: int):
        """delete channel row from channels table"""
        with self._connection:
            self._cursor.execute(f"delete from 'channels' where id={row_id}")

    def update_channel(self, row_id: int, channel_data: Dict):
        """update channel row in channels table"""
        with self._connection:
            keys = ', '.join(map(lambda x: f'{x} = ?', channel_data.keys()))
            values = tuple(channel_data.values())
            self._cursor.execute(f"UPDATE channels SET {keys} WHERE id = {row_id}", values)

    def create_db_dump(self):
        with open('dump.sql', 'w') as f:
            for line in self._connection.iterdump():
                f.write(f'{line}\n')
