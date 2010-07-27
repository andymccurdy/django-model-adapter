def test_func(self):
    return self.id

ADAPTIVE_MODELS = {
    'test_app_one.FKAdaptedViaString.user': 'test_app_two.MyUser',
    'test_app_one.FKAdaptedViaDict.user': {
        'to': 'test_app_two.MyUser',
    },
    'test_app_one.FKAdaptedViaDictWithMap.user': {
        'to': 'test_app_two.MyUser',
        'properties': {
            'test_id': 'id', # point new_id to id
            'test_func': test_func
        },
    }
}
