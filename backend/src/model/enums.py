import enum

class UserRole(enum.Enum):
    superuser = 'superuser'
    admin = 'admin'
    operator = 'operator'


class SystemLang(enum.Enum):
    en = 'en'
    ru = 'ru'
    tr = 'tr'
    de = 'de'


class MediaType(enum.Enum):
    image = 'image'
    video = 'video'


class ContactStatus(enum.Enum):
    new = 'new'
    read = 'read'
    archived = 'archived'


class AuditAction(enum.Enum):
    create = 'create'
    update = 'update'
    delete = 'delete'
    login = 'login'
    login_failed = 'login_failed'
    logout = 'logout'
    contact_submitted = 'contact_submitted'