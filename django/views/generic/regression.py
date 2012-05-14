class RegressionViewBase(type):

    def __call__(cls, *args, **kwargs):
        instance = getattr(cls, '__instance', None)
        if instance is None:
            instance = type.__call__(cls)
            setattr(cls, '__instance', instance)
        return instance(*args, **kwargs)
    

class RegressionView(object):
    __metaclass__ = RegressionViewBase


