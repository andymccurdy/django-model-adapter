from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models, router
from django.db.models import loading
from django.db.models.fields import related
from django.db.models.query import QuerySet

_ADAPTED_MODEL_COUNT = 0

def _overridden_equality_check(self, other):
    "Overrides our proxy models __eq__ comparrison, allowing equality comparisons both ways"
    return (isinstance(other, self.__class__) or isinstance(self, other.__class__)) and \
            self._get_pk_val() == other._get_pk_val()

def set_rel_target(field, model, field_name):
    # called by contribute_to_class(), this checks to see if we should repoint the
    # related model based on what's in settings
    field.rel._proxy = None
    lookup = '.'.join((model._meta.app_label, model._meta.object_name, field_name))
    if lookup in settings.ADAPTIVE_MODELS:
        data = settings.ADAPTIVE_MODELS[lookup]
        # data can be a string, which should represent the target related model
        # or i can be a dict with a 'to' key representing the target related model
        if isinstance(data, basestring):
            field.rel.to = data
            field.rel._field_map = {}
        else:
            try:
                field.rel.to = data['to']
            except KeyError:
                raise ImproperlyConfigured("AdaptiveForeignKey (%s) has no 'to' key" % lookup)
            field.rel._field_map = data.get('properties', {})
        field.rel._is_adaptive = True

def get_adapted_model(other, field):
    global _ADAPTED_MODEL_COUNT
    # called by do_related_class, which is the first point we're
    # guarenteed to have the real model class of the relationship.
    # build a meta class for the object
    class Meta:
        app_label = other._meta.app_label
        proxy = True

    attrs = {
        '__module__': 'model_adapter',
        'Meta': Meta,
        '__eq__': _overridden_equality_check,
        }
    # setup the properties for
    field_map = field.rel._field_map
    for attr_name, target_field in field_map.iteritems():
        if callable(target_field):
            attrs[attr_name] = target_field
        else:
            attrs[attr_name] = AdaptiveDescriptor(attr_name, target_field)
    new_class = type(other._meta.object_name, (other,), attrs)
    # everything below is a complete hack to get the proxy to work correctly
    # our new proxy class just took over the real classes slot in django's
    # model registry. it shouldn't exist here, so purge it.
    app_model_registry = loading.cache.app_models[other._meta.app_label]
    del app_model_registry[other._meta.object_name.lower()]
    # and replace it with the original
    loading.register_models(other._meta.app_label, other)
    # and finally, so models validate, register the new class
    # with a unique name inside our own app. we need to do some
    # tricks with the new classes object_name, which is used in
    # the registration process
    obj_name = new_class._meta.object_name
    _ADAPTED_MODEL_COUNT += 1
    new_class._meta.object_name = 'model-%s' % _ADAPTED_MODEL_COUNT
    loading.register_models('__model_adapter__', new_class)
    new_class._meta.object_name = obj_name
    return new_class

class AdaptiveDescriptor(object):
    def __init__(self, attr_field, target_field):
        self.attr_field = attr_field
        self.target_field = target_field

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return getattr(instance, self.target_field)

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self.attr_field)
        setattr(instance, self.target_field, value)

class AdaptiveReverseSingleRelatedObjectDescriptor(related.ReverseSingleRelatedObjectDescriptor):
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        cache_name = self.field.get_cache_name()
        try:
            return getattr(instance, cache_name)
        except AttributeError:
            val = getattr(instance, self.field.attname)
            if val is None:
                # If NULL is an allowed value, return it.
                if self.field.null:
                    return None
                raise self.field.rel.to.DoesNotExist
            other_field = self.field.rel.get_related_field()
            if other_field.rel:
                params = {'%s__pk' % self.field.rel.field_name: val}
            else:
                params = {'%s__exact' % self.field.rel.field_name: val}

            # If the related manager indicates that it should be used for
            # related fields, respect that.
            model_to_query = self.field.rel._proxy or self.rel.to
            rel_mgr = model_to_query._default_manager
            db = router.db_for_read(model_to_query, instance=instance)
            if getattr(rel_mgr, 'use_for_related_fields', False):
                rel_obj = rel_mgr.using(db).get(**params)
            else:
                rel_obj = QuerySet(model_to_query).using(db).get(**params)
            setattr(instance, cache_name, rel_obj)
            return rel_obj

class AdaptiveForeignKey(models.ForeignKey):
    def contribute_to_class(self, cls, name):
        set_rel_target(self, cls, name)
        super(AdaptiveForeignKey, self).contribute_to_class(cls, name)
        setattr(cls, self.name, AdaptiveReverseSingleRelatedObjectDescriptor(self))

    def do_related_class(self, other, cls):
        # at this point, we have the final other model object.
        # if we need to wrap it with our custom class, we can
        if getattr(self.rel, '_is_adaptive', False) and self.rel._field_map:
            self.rel._proxy = get_adapted_model(other, self)
        super(AdaptiveForeignKey, self).do_related_class(other, cls)

class AdaptiveOneToOneField(models.OneToOneField):
    def contribute_to_class(self, cls, name):
        set_rel_target(self, cls, name)
        super(AdaptiveOneToOneField, self).contribute_to_class(cls, name)

    def do_related_class(self, other, cls):
        # at this point, we have the final other model object.
        # if we need to wrap it with our custom class, we can
        if getattr(self.rel, '_is_adaptive', False) and self.rel._field_map:
            self.rel._proxy = get_adapted_model(other, self)
        super(AdaptiveOneToOneField, self).do_related_class(other, cls)

class AdaptiveManyToManyField(models.ManyToManyField):
    def contribute_to_class(self, cls, name):
        set_rel_target(self, cls, name)
        super(AdaptiveManyToManyField, self).contribute_to_class(cls, name)

    def do_related_class(self, other, cls):
        # at this point, we have the final other model object.
        # if we need to wrap it with our custom class, we can
        if getattr(self.rel, '_is_adaptive', False) and self.rel._field_map:
            self.rel._proxy = get_adapted_model(other, self)
        super(AdaptiveManyToManyField, self).do_related_class(other, cls)

