import datetime
import enum
import pickle
import pathlib
import random
import uuid
from dataclasses import dataclass, field
from authlib.oauth2.rfc6749 import TokenMixin, ClientMixin
from hashlib import sha256
from enum import StrEnum
from typing import Optional, Literal


class OAuthStorage:
    base_storage_path = pathlib.Path('./data')
    clients: dict[uuid.UUID, "Client"] = {}
    users: dict[uuid.UUID, "User"] = {}
    tokens: dict[uuid.UUID, "Token"] = {}

    @classmethod
    def save(cls):
        cls.base_storage_path.mkdir(parents=True, exist_ok=True)
        tokens_path = cls.base_storage_path / 'tokens.dat'
        users_path = cls.base_storage_path / 'users.dat'
        clients_path = cls.base_storage_path / 'clients.dat'

        if not tokens_path.is_file():
            tokens_path.unlink(True)
            tokens_path.touch()
        with tokens_path.open('wb') as tokens_fp:
            pickle.dump(cls.tokens, tokens_fp)

        if not users_path.is_file():
            users_path.unlink(True)
            users_path.touch()
        with users_path.open('wb') as users_fp:
            pickle.dump(cls.users, users_fp)

        if not clients_path.is_file():
            clients_path.unlink(True)
            clients_path.touch()
        with clients_path.open('wb') as clients_fp:
            pickle.dump(cls.clients, clients_fp)

    @classmethod
    def load(cls):
        tokens_path = cls.base_storage_path / 'tokens.dat'
        users_path = cls.base_storage_path / 'users.dat'
        clients_path = cls.base_storage_path / 'clients.dat'

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
        return sha256(sha256(password.encode('u8')).digest()).hexdigest() == self.password_hash

    @property
    def user_id(self) -> str:
        return str(self.uid)

    def get_user_id(self) -> int:
        return self.uid.int

    def __hash__(self):
        return hash(self.uid)


class Scopes(StrEnum):
    ...


@dataclass
class Client(ClientMixin):
    user: User
    redirect_uris: list[str]
    scopes: list[str]
    cid: Optional[uuid.UUID] = None
    client_secret: Optional[str] = ''

    def __post_init__(self):
        if not self.cid:
            self.cid = uuid.uuid4()

    def add(self):
        if self.cid not in OAuthStorage.users:
            OAuthStorage.users[self.cid] = self

    @property
    def grant_types(self):
        return ["password"]

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.redirect_uris[0]

    def get_allowed_scope(self, scope: Optional[str]):
        if not scope:
            return ''
        allowed = set(self.scopes)
        return ','.join(([s for s in scope.split() if s in allowed]))

    def check_redirect_uri(self, redirect_uri: str):
        return True

    def check_client_secret(self, client_secret: str):
        return sha256(client_secret.encode()).hexdigest() \
            == sha256(self.client_secret.encode()).hexdigest()

    def check_endpoint_auth_method(self, method, endpoint):
        pass

    def check_response_type(self, response_type):
        return True

    def check_grant_type(self, grant_type):
        return grant_type in self.grant_types

    @property
    def user_id(self) -> str:
        return self.user.user_id

    @property
    def client_id(self) -> str:
        return str(self.cid)

    def __hash__(self):
        return hash(self.cid)


@dataclass
class Token(TokenMixin):
    tid: uuid.UUID
    access_token: str
    refresh_token: str
    client: Client
    scopes: list[str]
    expires_at: datetime.datetime
    token_type: Literal["Bearer"] = 'Bearer'
    revoked: bool = False

    def check_client(self, client: Client):
        return self.client_id == client.client_id

    def get_scope(self):
        return ','.join(self.scopes)

    def get_expires_in(self):
        return self.expires_at.timestamp()

    def is_expired(self):
        return self.expires_at < datetime.datetime.utcnow()

    def is_revoked(self):
        return self.revoked

    def add(self):
        if self.tid not in OAuthStorage.tokens:
            OAuthStorage.tokens[self.tid] = self

    def delete(self):
        OAuthStorage.tokens.pop(self.tid)

    @property
    def client_id(self) -> str:
        return self.client.client_id

    @property
    def user_id(self) -> str:
        return self.client.user_id
