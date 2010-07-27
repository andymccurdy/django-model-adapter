from django.test.testcases import TestCase
from django.contrib.auth.models import User
# relative import hack since the tests module refers to itself
from model_adapter.fields import AdaptiveDescriptor
from ..test_app_one.models import FKAdaptedViaString, FKAdaptedViaDict, FKAdaptedViaDictWithMap, FKNotAdapted
from ..test_app_two.models import MyUser

class ForeignKeyTestCase(TestCase):
    def test_not_adapted(self):
        self.assertEquals(FKNotAdapted._meta.get_field('user').rel.to, User)

    def test_adapted_string(self):
        self.assertEquals(FKAdaptedViaString._meta.get_field('user').rel.to, MyUser)

    def test_adapted_dict(self):
        self.assertEquals(FKAdaptedViaDict._meta.get_field('user').rel.to, MyUser)
        
    def test_adapted_with_field_map(self):
        self.assertEquals(FKAdaptedViaDictWithMap._meta.get_field('user').rel.to, MyUser)

    def test_proxy(self):
        # assign a normal user
        user = MyUser.objects.create()
        t = FKAdaptedViaDictWithMap.objects.create(user=user)
        self.assertEquals(t.user_id, user.id)

        t = FKAdaptedViaDictWithMap.objects.get(pk=t.id)
        # t.user should be our proxy object with appropriate accessors
        self.assertEquals(t.user.test_id, user.id)
        self.assertEquals(t.user.test_func(), user.id)

        # our proxy should test positively for equality when comapring to
        # the normal model
        self.assertEquals(user, t.user)

        # and we should be able to assign our proxy object to another instance
        t2 = FKAdaptedViaDictWithMap.objects.create(user=t.user)
        t2 = FKAdaptedViaDictWithMap.objects.get(pk=t2.id)
        self.assertEquals(t.user, t2.user)
        
