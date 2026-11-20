# Decoding Untrusted JSON

kajson rebuilds Python objects from the `__class__` and `__module__` markers its encoder writes. By default, the decoder trusts those markers completely, which is right for JSON your own program wrote and wrong for JSON anyone else could have written. This page explains what the default decoder executes, how safe mode limits it, and what safe mode still leaves to you.

## What the default decoder executes

When the decoder meets a marker such as `{"__class__": "Popen", "__module__": "subprocess", "args": ["rm", "-rf", "/tmp/data"]}`, it does three things:

1. It finds the class. If the named module is not already imported, the decoder imports it, which runs the module's top-level code.
2. It picks a way to rebuild the object: a registered decoder, the class's `__json_decode__` hook, validation for pydantic models and dataclasses, a lookup for enums, and otherwise a call to the class with the payload's keys as keyword arguments.
3. If that call fails, it tries the class's no-argument constructor and replaces the new object's `__dict__` with the payload's keys.

The last two steps are what make kajson round-trip almost any object, and they are also why decoding JSON written by someone else runs code that person chose. The marker above makes the default decoder start the command. A marker naming `io.FileIO` truncates a file. Any class whose constructor has an effect can be reached.

Use the default decoder only for JSON your own program produced, or that came from a party you trust as much as your own code.

## Turning on safe mode

Pass `safe=True` to `kajson.loads` or `kajson.load`:

```python
import kajson

data = kajson.loads(untrusted_text, safe=True)
```

The same option works on the decoder class itself, so `json.loads(untrusted_text, cls=kajson.UniversalJSONDecoder, safe=True)` behaves the same way. Every other keyword argument still reaches the standard library's `json.JSONDecoder`, including its own `strict` argument, which controls control characters inside strings and has nothing to do with safe mode.

With `safe=True`, the decoder still resolves classes in the same order: the explicit `class_registry` you pass, then a module that is already imported, then the global class registry, and finally an import. Two things change.

**Imports are limited to the packages you name.** A module that is not already imported is imported only when it is one of the packages listed in `importable_packages`, or lies inside one of them. Without `importable_packages`, safe mode imports nothing.

```python
data = kajson.loads(
    untrusted_text,
    safe=True,
    importable_packages=["my_app.models", "my_shared_types"],
)
```

Entries match on package boundaries: `my_app.models` admits `my_app.models` and `my_app.models.orders`, but not `my_app.models_legacy` and not `my_app.views`. Importing `my_app.models.orders` also runs the code of its parent packages, `my_app` and `my_app.models`, so name only packages whose import-time code you trust.

**Only classes kajson rebuilds by validation or by a decoding hook are rebuilt.** Safe mode looks at the first strategy kajson would use for the class and uses that strategy alone:

| The class is | Safe mode |
| --- | --- |
| A class with a registered decoder (`UniversalJSONDecoder.register`) | Calls the decoder |
| A class with a `__json_decode__` hook | Calls the hook |
| A pydantic `BaseModel` | `model_validate`, with no constructor fallback |
| A generic pydantic model, under its subscripted name such as `Box[int]` | `model_validate` on the parametrized class when its module holds it, and otherwise on the unparametrized base `Box`, whose type parameter is then not checked |
| A pydantic `RootModel` | Validates the payload's `root` value |
| A pydantic dataclass | Runs the dataclass's validator |
| An `Enum` | Looks the member up by name or by value |
| `datetime`, `date`, `time`, `timezone`, `timedelta`, `ZoneInfo` | kajson's registered decoders |
| Anything else: plain classes, stdlib dataclasses, builtins such as `type` | Refused |

A failed decoder or hook raises an error, even if the module constant `IS_DECODER_FALLBACK_ENABLED` is set. The constructor call, the no-argument constructor and the raw-dict fallback are never reached.

**A pydantic class or enum whose construction is not the library's own is refused.** pydantic's `model_validate` runs a model's own `__init__` and `__new__` when the class overrides them, so validation alone does not keep a payload away from that code. pydantic-settings' `BaseSettings` is the standard example: its `__init__` reads the `.env` file named by the `_env_file` argument, so a payload naming `BaseSettings` could make the process read any file. Safe mode therefore refuses a pydantic model whose `__init__`, `__new__`, `model_validate` or metaclass `__call__` is not pydantic's own, a pydantic dataclass whose `__new__` or metaclass `__call__` is overridden, and an enum whose metaclass overrides `__call__` or `__getitem__`. This check applies when safe mode would rebuild the class by validation or lookup; a class with a registered decoder or its own `__json_decode__` is rebuilt by that hook instead, so the hook is the code you vouch for. If one of your own models needs construction logic, write it as a `model_validator(mode="before")`, which runs inside validation and is allowed.

Every refusal raises `KajsonDecoderError` before the import or the call it refuses. The message names the module and class the marker gave, and never includes the payload's values. A refused marker nested anywhere in the document, in a model field, a list or a dict, fails the whole decode.

## Making a refused type decodable

If safe mode refuses a type you need, give kajson a way to rebuild it that does not call its constructor with arbitrary keys:

- make it a pydantic model or a pydantic dataclass;
- give it a `__json_decode__` static method that reads exactly the fields it expects;
- or register a decoder for it with `UniversalJSONDecoder.register`.

```python
from kajson import UniversalJSONDecoder


class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


def decode_point(data: dict) -> Point:
    return Point(float(data["x"]), float(data["y"]))


UniversalJSONDecoder.register(Point, decode_point)
```

A decoder or hook you write runs on payload data, so it should check what it reads and build nothing else.

## What safe mode does not protect against

Safe mode narrows the code a payload can cause to run down to code your process has already loaded, in classes that are built to be decoded. It does not reduce that code to nothing.

- **Code in the allowed kinds, in modules that are already imported.** A payload can name any allowed class in any imported module, whether or not that module is in `importable_packages`. Decoding such a class runs its pydantic validators, its `model_post_init`, a pydantic dataclass's `__post_init__`, an enum's `_missing_`, `__json_decode__` hooks and registered decoders. Keep side effects out of that code.
- **Imports inside the packages you name.** Importing a module runs its top-level code and that of its parent packages. You vouch for every package you list.
- **Process-wide registrations.** Decoders registered with `UniversalJSONDecoder.register` and classes in the global class registry are shared by everything in the process. Whatever any library put there applies to safe decodes too, after the same kind check.
- **The type of the result.** The payload still chooses which allowed class it becomes, and a generic model's type parameter is not checked when the decoder falls back to the unparametrized base. If you expect an `Order`, check the result with `isinstance`, or validate it into the type you expect.
- **Resource exhaustion.** Deep nesting, very large documents and expensive validators are not bounded. Limit the size of untrusted input before you decode it.

## Checklist

- Decode JSON from anyone you do not trust with `safe=True`.
- List in `importable_packages` only the packages your wire types live in, as narrowly as you can.
- Check the type of what comes back.
- Bound the size of the input before decoding.
- Catch `KajsonDecoderError` around the decode; safe mode reports every refusal and every malformed marker that way.

## See also

- [Class Registry](class-registry.md), for resolving classes without importing their modules.
- [Custom Types](custom-types.md), for registering decoders.
- [Error Handling](error-handling.md), for the errors safe mode raises.
