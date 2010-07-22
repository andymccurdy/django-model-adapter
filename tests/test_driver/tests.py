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
        self.assertNotEquals(FKAdaptedViaDictWithMap._meta.get_field('user').rel.to, MyUser)
        self.assert_(issubclass(FKAdaptedViaDictWithMap._meta.get_field('user').rel.to, MyUser))

        self.assert_(getattr(FKAdaptedViaDictWithMap, 'new_id', None) is None)
        self.assert_(isinstance(
            getattr(FKAdaptedViaDictWithMap._meta.get_field('user').rel.to, 'new_id', None),
            AdaptiveDescriptor
            ))

    def test_save_and_restore(self):
        user = MyUser.objects.create()
        t = FKAdaptedViaDictWithMap.objects.create(user=user)
        t.user_id = user.id

        t = FKAdaptedViaDictWithMap.objects.get(pk=t.id)
        self.assertEquals(t.user.new_id, user.id)
        