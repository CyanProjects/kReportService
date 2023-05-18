import datetime
import enum
import pickle
import pathlib
import random
import uuid
from dataclasses import dataclass, field, InitVar
from hashlib import sha256
from enum import StrEnum
from typing import Optional, Literal


class OAuthStorage:
    base_storage_path = pathlib.Path('./data')
    clients: dict[str, "Client"] = {}
    users: dict[str, "User"] = {}
    grants: dict[int, "Grant"] = {}
    tokens: dict[int, "Token"] = {}

    @classmethod
    def save(cls):
        grants_path = cls.base_storage_path / 'grants.dat'
        tokens_path = cls.base_storage_path / 'tokens.dat'
        users_path = cls.base_storage_path / 'users.dat'
        clients_path = cls.base_storage_path / 'clients.dat'

        if not grants_path.is_file():
            grants_path.unlink(True)
        with grants_path.open('wb') as grants_fp:
            pickle.dump(cls.grants, grants_fp)

        if not tokens_path.is_file():
            tokens_path.unlink(True)
        with tokens_path.open('wb') as tokens_fp:
            pickle.dump(cls.tokens, tokens_fp)

        if not users_path.is_file():
            users_path.unlink(True)
        with users_path.open('wb') as users_fp:
            pickle.dump(cls.users, users_fp)

        if not clients_path.is_file():
            clients_path.unlink(True)
        with clients_path.open('wb') as clients_fp:
            pickle.dump(cls.clients, clients_fp)

    @classmethod
    def load(cls):
        grants_path = cls.base_storage_path / 'grants.dat'
        tokens_path = cls.base_storage_path / 'tokens.dat'
        users_path = cls.base_storage_path / 'users.dat'
        clients_path = cls.base_storage_path / 'clients.dat'

        if grants_path.is_file():
            with grants_path.open('rb') as grants_fp:
                cls.grants = pickle.load(grants_fp)

        if tokens_path.is_file():
            with tokens_path.open('rb') as tokens_fp:
                cls.tokens = pickle.load(tokens_fp)

        if users_path.is_file():
            with users_path.open('rb') as users_fp:
                cls.users = pickle.load(users_fp)

        if clients_path.is_file():
            with clients_path.open('rb') as clients_fp:
                cls.clients = pickle.load(clients_fp)

        cls.save()


@dataclass
class User:
    uid: uuid.UUID
    name: str
    password_hash: str
    description: Optional[str] = ''
    owned_services: list[uuid.UUID] = field(default_factory=list)

    def check_auth(self, password: str):
        return sha256(sha256(password).digest()).hexdigest() == self.password_hash

    @property
    def user_id(self) -> str:
        return str(self.uid)

    def __hash__(self):
        return hash(self.uid)


class Scopes(StrEnum):
    ...


class ClientType(StrEnum):
    public = 'public'
    confidential = "confidential"


"""
The client should contain at least these properties:

client_id: A random string
client_secret: A random string
client_type: A string represents if it is confidential
redirect_uris: A list of redirect uris
default_redirect_uri: One of the redirect uris
default_scopes: Default scopes of the client
"""


@dataclass
class Client:
    default_scopes: list[str]
    client_type: ClientType = field(init=False)
    name: str
    user: User
    description: Optional[str]
    cid: uuid.UUID
    client_secret: str
    redirect_uris: list[str]
    default_redirect_uri: str

    def __post_init__(self):
        self.client_type = ClientType.public

    @property
    def user_id(self) -> str:
        return self.user.user_id

    @property
    def default_redirect_uri(self) -> str:
        return self.redirect_uris[0]

    @property
    def client_id(self) -> str:
        return str(self.cid)

    def __hash__(self):
        return hash(self.cid)


"""
A grant token should contain at least this information:

client_id: A random string of client_id
code: A random string
user: The authorization user
scopes: A list of scope
expires: A datetime.datetime in UTC
redirect_uri: A URI string
delete: A function to delete itself
"""


@dataclass
class Grant:
    user: User
    code: str
    scopes: list[str]
    redirect_uri: str
    expires: datetime.datetime
    client: Client
    id: int = field(default_factory=lambda: random.randint(10, 1000000))

    def delete(self):
        OAuthStorage.grants.pop(self.id)

    @property
    def client_id(self):
        return self.client.client_id


"""
A bearer token requires at least this information:

access_token: A string token
refresh_token: A string token
client_id: ID of the client
scopes: A list of scopes
expires: A datetime.datetime object
user: The user object
delete: A function to delete itself
"""


@dataclass
class Token:
    access_token: str
    refresh_token: str
    client: Client
    scopes: list[str]
    expires: datetime.datetime
    user: User
    token_type: Literal["Bearer"] = 'Bearer'
    id: int = field(default_factory=lambda: random.randint(10, 1000000))

    def add(self):
        if self.id not in OAuthStorage.tokens:
            OAuthStorage.tokens[self.id] = self

    def delete(self):
        OAuthStorage.tokens.pop(self.id)

    @property
    def client_id(self) -> str:
        return self.client.client_id

    @property
    def user_id(self) -> str:
        return self.client.user_id
