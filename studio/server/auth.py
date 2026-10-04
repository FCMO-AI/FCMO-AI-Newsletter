"""Per-person identity, scrypt passwords, bounded sessions and CSRF."""
import hashlib
import hmac
import secrets
from .storage import NAMES

COOKIE = '__Host-studio'
TTL = 30 * 24 * 3600

def password_hash(password, salt=None):
    if not isinstance(password, str) or not 12 <= len(password) <= 1024: raise ValueError('La contraseña necesita al menos 12 caracteres.')
    salt = secrets.token_bytes(16) if salt is None else salt
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64*1024*1024)
    return salt.hex() + ':' + digest.hex()

def verify_password(password, stored):
    try:
        salt, digest = stored.split(':')
        computed = password_hash(password, bytes.fromhex(salt)).split(':')[1]
        return hmac.compare_digest(computed, digest)
    except (ValueError, TypeError, AttributeError): return False

class Auth:
    def __init__(self, store, session_key):
        if not isinstance(session_key, str) or len(session_key) < 32: raise ValueError('Configura una clave de sesión de al menos 32 caracteres.')
        self.store = store; self.key = session_key.encode()
        self.dummy = password_hash('invalid-password-placeholder')
    def digest(self, token): return hmac.new(self.key, token.encode(), hashlib.sha256).hexdigest()
    def add_user(self, user, password, gh_login='', ui_lang='es'):
        if user not in NAMES or ui_lang not in ('es', 'en'): raise ValueError('La cuenta no es válida.')
        with self.store.mutex:
            self.store.db.execute('INSERT OR REPLACE INTO users VALUES(?,?,?,?,?,0,0)', (user, NAMES[user], password_hash(password), gh_login, ui_lang))
            self.store.db.execute('DELETE FROM sessions WHERE user=?', (user,)); self.store.db.commit()
    def login(self, user, password, ua='', tailnet=''):
        with self.store.mutex:
            db = self.store.db; now = self.store.clock()
            row = db.execute('SELECT * FROM users WHERE key=?', (user,)).fetchone()
            if row and row['locked_until'] > now: return None
            valid = verify_password(password, row['pw_scrypt'] if row else self.dummy)
            if not row or not valid:
                if row:
                    count = row['failures'] + 1 if row['locked_until'] == 0 else 1
                    db.execute('UPDATE users SET failures=?,locked_until=? WHERE key=?', (count, now+900 if count >= 5 else 0, user))
                self.store.audit(user if user in NAMES else '', 'login_failed'); db.commit(); return None
            token = secrets.token_urlsafe(32); csrf = secrets.token_urlsafe(32)
            db.execute('UPDATE users SET failures=0,locked_until=0 WHERE key=?', (user,))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)', (self.digest(token), user, now, now, str(ua)[:300], csrf))
            self.store.audit(user, 'login', details={'tailnet_login': str(tailnet)[:200]}); db.commit()
            return {'token': token, 'csrf': csrf, 'user': user, 'name': row['name'], 'ui_lang': row['ui_lang']}
    def session(self, token):
        if not token or len(token) > 200: return None
        with self.store.mutex:
            db = self.store.db; now = self.store.clock()
            row = db.execute('SELECT sessions.*,users.name,users.ui_lang FROM sessions JOIN users ON sessions.user=users.key WHERE id_hash=?', (self.digest(token),)).fetchone()
            if not row or now - row['created'] >= TTL: return None
            db.execute('UPDATE sessions SET last_seen=? WHERE id_hash=?', (now, row['id_hash'])); db.commit()
            return dict(row)
    def logout(self, token):
        with self.store.mutex:
            self.store.db.execute('DELETE FROM sessions WHERE id_hash=?', (self.digest(token),)); self.store.db.commit()
    @staticmethod
    def csrf(session, received, origin, expected):
        return bool(session and origin == expected and isinstance(received, str) and hmac.compare_digest(session['csrf'], received))
