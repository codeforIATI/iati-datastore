# http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
from sqlalchemy.types import TypeDecorator, UnicodeText
import six
from requests.structures import CaseInsensitiveDict


class EnumSymbol(object):
    """Define a fixed symbol tied to a parent class."""

    def __init__(self, cls_, name, value, description, translations=None):
        self.cls_ = cls_
        self.name = name
        self.value = value
        self.description = description
        if translations:
            self.translations = translations
        else:
            self.translations = {}

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if other is None:
            return False
        return self.value == other.value

    def __ne__(self, other):
        if other is None:
            return True
        return self.value != other.value

    def __reduce__(self):
        """Allow unpickling to return the symbol
        linked to the DeclEnum class."""
        return getattr, (self.cls_, self.name)

    def __iter__(self):
        return iter([self.value, self.description])

    def __repr__(self):
        return "<%s>" % self.name


class EnumMeta(type):
    """Generate new DeclEnum classes."""

    def __init__(cls, classname, bases, dict_):
        cls._reg = reg = cls._reg.copy()
        for k, v in dict_.items():
            if isinstance(v, tuple):
                sym = reg[v[0]] = EnumSymbol(cls, k, *v)
                setattr(cls, k, sym)
        return type.__init__(cls, classname, bases, dict_)

    def __iter__(cls):
        return iter(cls._reg.values())


class DeclEnum(object, metaclass=EnumMeta):
    """Declarative enumeration."""

    _reg = CaseInsensitiveDict()

    @classmethod
    def from_string(cls, value):
        try:
            return cls._reg[value]
        except (KeyError, AttributeError):
            return EnumSymbol(cls, None, value, None)

    @classmethod
    def values(cls):
        return cls._reg.keys()

    @classmethod
    def db_type(cls):
        return DeclEnumType(cls)


class DeclEnumType(TypeDecorator):
    def __init__(self, enum):
        self.enum = enum
        self.impl = UnicodeText()

    def copy(self):
        return DeclEnumType(self.enum)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif isinstance(value, six.string_types):
            return value
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum.from_string(value.strip())
