from erised.proxy import Proxy


class Model:
    def simulate(self, val):
        print(self.__dict__)
        return 3 * val


class OCP:
    def __init__(self, model):
        self.model = model


if __name__ == "__main__":
    a = OCP(Model())
    proxy = Proxy(obj=a)
    proxy.model.foo = 3
    #  print(proxy.model.simulate)
    print((proxy.model.simulate(32).result()))
    #  print((proxy.model.foo.retrieve().result()))
    proxy.terminate()
