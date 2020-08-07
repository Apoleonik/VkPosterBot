import os
import sqlite3

from typing import Dict, List, Tuple


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

        with open("../config/create_db.sql") as f:
            sql_data = f.read()
        with self._connection:
            self._cursor.executescript(sql_data)

    def _get_channel_columns(self) -> Tuple:
        """get channel table columns names"""

        self._cursor.execute("SELECT * FROM 'channels'")
        columns = tuple(map(lambda row: row[0], self._cursor.description))
        return columns

    @staticmethod
    def _rows_to_dict(rows: List[Tuple], columns: Tuple) -> List[Dict]:
        """convert sql row tuple to dict"""
        channels = []
        for row in rows:
            row_dict = {}
            for index, column in enumerate(columns):
                row_dict[column] = row[index]
            channels.append(row_dict)
        return channels

    def _insert(self, table: str, column_values: Dict):
        """insert values to selected table"""
        with self._connection:
            joined_columns = ", ".join(column_values.keys())
            values = tuple(column_values.values())
            placeholders = ", ".join("?" * len(column_values.keys()))
            self._cursor.execute(f"INSERT INTO '{table}' ({joined_columns}) VALUES ({placeholders})", values)

    def _delete(self, table: str, row_id: int):
        """delete row from selected table"""
        with self._connection:
            self._cursor.execute(f"delete from '{table}' where id={row_id}")

    def _fetch(self, table: str, columns: List[str] = ''):
        """get columns from selected table"""
        joined_columns = ', '.join(columns) if columns else '*'
        self._cursor.execute(f"SELECT {joined_columns} from '{table}'")
        rows = self._cursor.fetchall()
        return rows

    def get_cursor(self):
        """get db cursor"""
        return self._cursor

    def get_all_channels(self) -> List[Dict]:
        """get all channels rows from db"""
        rows = self._fetch('channels')
        channels = self._rows_to_dict(rows, self._channel_columns)
        return channels

    def get_channel(self, row_id: int) -> List[Dict]:
        """get channel by row from db"""
        self._cursor.execute(f"SELECT * from 'channels' where id='{row_id}'")
        rows = self._cursor.fetchall()
        return self._rows_to_dict(rows, self._channel_columns)

    def get_channel_by_tg_vk_channel_key(self, telegram_channel: str, vk_channel: str):
        """get channel row from db filtered by telegram_channel and vk_channel key"""
        self._cursor.execute(f"SELECT * from 'channels' where telegram_channel='{telegram_channel}' "
                             f"and vk_channel='{vk_channel}'")
        rows = self._cursor.fetchall()
        return self._rows_to_dict(rows, self._channel_columns)

    def add_channel(self, channel_data: Dict):
        """add channel row to channels table"""
        self._insert('channels', channel_data)

    def delete_channel(self, row_id: int):
        """delete channel row from channels table"""
        self._delete('channels', row_id)

    def update_channel(self, row_id: int, channel_data: Dict):
        """update channel row in channels table"""
        with self._connection:
            keys = ', '.join(map(lambda x: f'{x} = ?', channel_data.keys()))
            values = tuple(channel_data.values())
            self._cursor.execute(f"UPDATE channels SET {keys} WHERE id = {row_id}", values)

    def get_blacklist_words(self, get_id=False) -> List:
        """get all blacklist words from blacklist table"""
        rows = self._fetch('blacklist', ['id', 'word'])
        words = list(map(lambda x: x[1], rows))
        words_dict = list(map(lambda x: {'id': x[0], 'word': x[1]}, rows))
        if get_id:
            return words_dict
        return words

    def add_blacklist_word(self, word: str):
        """add blacklist word row to blacklist table"""
        self._insert('blacklist', {'word': word})

    def delete_blacklist_word(self, row_id: int):
        """delete blacklist word row from blacklist table"""
        self._delete('blacklist', row_id)

    def create_db_dump(self):
        with open('dump.sql', 'w') as f:
            for line in self._connection.iterdump():
                f.write(f'{line}\n')
