# Erised: the magic mirror

This is light-weight library to work to put objects in a different Process and iteract with it asynchronously.


## Example

This is a work in progress but herer it is a small snippet.
Define some objects as usual

```python
class Dog:
    def bark(self, loud: bool):
        sound = "woof-woof"
        if loud:
            return sound.upper()
        return sound


class Person:
    def __init__(self, dog: Dog = None):
        self.dog = dog
```

Create your objects and do wathever operations with it, when you want to send it to another Process create a proxy for it

```python
person = Person()
person.dog = Dog()

proxy = Proxy(obj=person)
```

Now you can call the methods of the proxy like normal.
Just remember that all operations on proxies return a Future object, similar to `concurrent.futures.Future`.
To obtain the the result use `.result()` in the future object.

```python
call_future = proxy.dog.bark(loud=True)
print(call_future.result())  # WOOF-WOOF
```

Attributes can be set into the remote object by setting the attribute in the proxy object.
Setting attributes works even if it was not defined originally.

```python
proxy.dog.age = 3
```

It's also possible to retrieve attributes from the remote object by including a `.retrieve()` at the end of a proxy.
`.retrieve()` was purposely chosen to avoid name conflict with the underlying object.

```python
get_future = proxy.dog.age.retrieve()
print(get_future.result())  # 3
```

Since an process was created, make sure to terminate the process by calling `.terminate()` on the proxy object.

```python
proxy.terminate()
```

## Debugging

To facilitate debugging you can create a local proxy by passing `local=True` to the proxy object.

```python
proxy = Proxy(obj=person, local=True)
```

Notice that in local mode, when you you execute a `.result()` in a Future object, it will run all previous pending tasks from that proxy.
Task are not executed on creation/request.
For instance:

```python
proxy = Proxy(obj=person, local=True)

call_future = proxy.dog.bark(loud=True)  # the method is not called yet

print(call_future.result())  # the method is called here -> WOOF-WOOF
```

You don't need to call `proxy.terminate()` on local proxies, but it is encouraged because it makes sure that all pending tasks are finished.
