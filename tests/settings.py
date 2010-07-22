ADAPTIVE_MODELS = {
    'test_app_one.FKAdaptedViaString.user': 'test_app_two.MyUser',
    'test_app_one.FKAdaptedViaDict.user': {
        'to': 'test_app_two.MyUser',
    },
    'test_app_one.FKAdaptedViaDictWithMap.user': {
        'to': 'test_app_two.MyUser',
        'fields': {
            'new_id': 'id', # point new_id to id
        },
    }
}
