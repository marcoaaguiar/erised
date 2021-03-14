from erised.proxy import Proxy


class Dog:
    def bark(self, loud: bool):
        sound = "woof-woof"
        if loud:
            return sound.upper()
        return sound


class Person:
    def __init__(self, dog: Dog = None):
        self.dog = dog


if __name__ == "__main__":
    person = Person()
    person.dog = Dog()
    proxy = Proxy(obj=person)

    # call method remotely
    call_future = proxy.dog.bark(loud=True)
    print(call_future.result())

    # set attributes into remote object, even if they didn't exist originally
    proxy.dog.age = 3  # it generates a future that can't be retrieved

    # get attributes from remote object
    get_future = proxy.dog.age.retrieve()
    print(get_future.result())

    # if running multiprocessing mode (local=False), terminates child process
    proxy.terminate()
