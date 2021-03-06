from pybamboo.dataset import Dataset
from pybamboo.exceptions import PyBambooException
from pybamboo.tests.test_base import TestBase


class TestDataset(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._create_dataset_from_file()

    def _create_dataset_from_file(self):
        self.dataset = Dataset(path=self.CSV_FILE,
                               connection=self.connection)
        self.wait()

    def _create_aux_dataset_from_file(self):
        self.aux_dataset = Dataset(path=self.AUX_CSV_FILE,
                                   connection=self.connection)
        self.wait()

    def _wait_for_dataset_ready(self):
        while self.dataset.state == 'pending':
            self.wait()

    def test_create_dataset_from_json(self):
        dataset = Dataset(path=self.JSON_FILE, data_format='json',
                          connection=self.connection)
        self.assertTrue(dataset.id is not None)
        self._cleanup(dataset)

    def test_create_dataset_from_schema(self):
        dataset = Dataset(schema_path=self.SCHEMA_FILE,
                          connection=self.connection)
        self.assertTrue(dataset.id is not None)
        self._cleanup(dataset)

        # schema string
        schema_str = open(self.SCHEMA_FILE).read()
        dataset = Dataset(schema_content=schema_str,
                          connection=self.connection)
        self.assertTrue(dataset.id is not None)
        self._cleanup(dataset)

    def test_create_dataset_from_schema_with_data(self):
        # schema + JSON data
        dataset = Dataset(path=self.JSON_FILE, data_format='json',
                          schema_path=self.SCHEMA_FILE,
                          connection=self.connection)
        self.assertTrue(dataset.id is not None)
        self._cleanup(dataset)

        # schema + CSV data
        dataset = Dataset(path=self.CSV_FILE, data_format='csv',
                          schema_path=self.SCHEMA_FILE,
                          connection=self.connection)
        self.assertTrue(dataset.id is not None)
        self._cleanup(dataset)

    def test_create_dataset_default_connection(self):
        dataset = Dataset(path=self.CSV_FILE,
                          connection=self.default_connection)
        self._cleanup(dataset)

    def test_create_dataset_no_info(self):
        with self.assertRaises(PyBambooException):
            Dataset()

    def test_create_dataset_bad_data_format(self):
        with self.assertRaises(PyBambooException):
            Dataset(path=self.CSV_FILE, data_format='BAD',
                    connection=self.connection)

    def test_create_dataset_from_file(self):
        # created in TestDataset.setUp()
        self.assertTrue(self.dataset.id is not None)

    def test_create_dataset_from_url(self):
        dataset = Dataset(
            url='http://formhub.org/mberg/forms/good_eats/data.csv',
            connection=self.connection)
        self.assertTrue(self.dataset.id is not None)
        self._cleanup(dataset)

    def test_reset_dataset(self):
        dataset_id = self.dataset._id
        self.dataset.reset(path=self.CSV_FILE,
                           connection=self.connection)
        self.assertEqual(self.dataset._id, dataset_id)

    def test_reset_dataset_no_dataset_id(self):
        self.dataset.delete()
        with self.assertRaises(PyBambooException):
            self.dataset.reset()

    def test_na_values(self):
        dataset = Dataset(
            path=self.CSV_FILE,
            connection=self.connection,
            na_values=['n/a'])
        self.wait()
        first_row = dataset.get_data(query={'food_type': 'street_meat',
                                            'amount': 2,
                                            'rating': 'delectible',
                                            'risk_factor': 'low_risk'},
                                     limit=1)[-1]
        self.assertEqual(first_row.get('comments'), 'null')
        self._cleanup(dataset)

    def test_resample(self):
        data = self.dataset.resample(date_column='submit_date',
                                     interval='D',
                                     how='mean')
        self.assertTrue(data)

    def test_resample_with_query(self):
        data = self.dataset.resample(date_column='submit_date',
                                     interval='D',
                                     query={"food_type": "street_meat"},
                                     how='sum')
        self.assertTrue(data)

    def test_rolling(self):
        data = self.dataset.rolling(win_type='boxcar', window=3)
        self.assertTrue(isinstance(data, list))

    def test_set_info(self):
        description = u"Meals rating worldwide"
        attribution = u"mberg"
        label = u"Good Eats"
        license = u"Public Domain"
        self.dataset.set_info(attribution=attribution,
                              description=description,
                              label=label,
                              license=license)
        infos = self.dataset.get_info()
        self.assertEqual(infos['description'], description)
        self.assertEqual(infos['attribution'], attribution)
        self.assertEqual(infos['label'], label)
        self.assertEqual(infos['license'], license)

    def test_index_present(self):
        data = self.dataset.get_data(index=True)
        self.assertTrue('index' in data[-1].keys())

    def test_str(self):
        self.assertEqual(str(self.dataset), self.dataset.id)

    def test_version(self):
        self.assert_keys_in_dict(self.VERSION_KEYS,
                                 self.dataset.version)

    def test_columns(self):
        self.wait()  # have to wait, bamboo issue #284
        cols = self.dataset.columns
        keys = self.dataset.get_info()['schema'].keys()
        for key in keys:
            self.assertTrue(key in cols)
        for col in cols:
            self.assertTrue(col in keys)

    def test_state(self):
        self.assertEqual(self.dataset.state, 'ready')

    def test_num_columns(self):
        self.assertEqual(self.dataset.num_columns, 15)

    def test_num_rows(self):
        self.assertEqual(self.dataset.num_rows, 19)

    def test_count(self):
        self.wait()
        count = self.dataset.count(field='food_type', method='count')
        self.assertEqual(count, 19)

    def test_data_count(self):
        self._wait_for_dataset_ready()  # TODO: is this necessary?
        count = self.dataset.get_data(count=True)
        self.assertEqual(count, 19)

    def test_delete_dataset(self):
        self.dataset.delete()
        self.assertTrue(self.dataset._id is None)

    def test_invalid_dataset(self):
        self.dataset.delete()
        with self.assertRaises(PyBambooException):
            self.dataset.delete()

    def test_add_calculation(self):
        result = self.dataset.add_calculation(name='double_amount',
                                              formula='amount * 2')
        self.assertTrue(result)

    def test_add_calculations(self):
        formulae = [
            {'name': 'double_amount', 'formula': 'amount * 2'},
            {'name': 'triple_amount', 'formula': 'amount * 3'},
        ]
        result = self.dataset.add_calculations(json=formulae)
        self.assertTrue(result)

    def test_add_invalid_calculation_a_priori(self):
        bad_calcs = [
            {'name': None, 'formula': 'ok'},
            {'name': 'number', 'formula': 3},
            {'name': 'number', 'formula': 'ok', 'groups': 3},
        ]
        for calc in bad_calcs:
            with self.assertRaises(PyBambooException):
                self.dataset.add_calculation(**calc)

        with self.assertRaises(PyBambooException):
            self.dataset.add_calculations()

    def test_add_invalid_calculation_a_posteriori(self):
        result = self.dataset.add_calculation(name='double_amount',
                                              formula='BAD')
        self.assertEqual(result, False)

    def test_add_aggregation(self):
        result = self.dataset.add_calculation(name='sum_amount',
                                              formula='sum(amount)')
        self.assertTrue(result)
        self.dataset.has_aggs_to_remove = True

    def test_add_aggregation_with_groups(self):
        result = self.dataset.add_calculation(
            name='sum_amount',
            formula='sum(amount)',
            groups=['food_type'])
        self.assertTrue(result)
        result = self.dataset.add_calculation(
            name='sum_amount',
            formula='sum(amount)',
            groups=['food_type', 'rating'])
        self.assertTrue(result)
        self.dataset.has_aggs_to_remove = True

    def test_add_aggregation_invalid_groups(self):
        with self.assertRaises(PyBambooException):
            self.dataset.add_calculation(
                name='sum_amount',
                formula='sum(amount)',
                groups='BAD')

    def test_remove_calculation(self):
        name = 'double_amount'
        self.dataset.add_calculation(name=name,
                                     formula='amount * 2')
        result = self.dataset.remove_calculation(name)
        self.assertTrue(result)

    def test_remove_aggregation(self):
        name = 'sum_amount'
        result = self.dataset.add_calculation(name=name,
                                              formula='sum(amount)')
        self.assertTrue(result)
        result = self.dataset.remove_calculation(name)
        self.assertTrue(result)
        self.dataset.has_aggs_to_remove = True

    def test_remove_calculation_fail(self):
        result = self.dataset.remove_calculation('bad')
        self.assertFalse(result)

    def test_get_calculations(self):
        calc_keys = ['state', 'formula', 'group', 'name']
        result = self.dataset.add_calculation(name='double_amount',
                                              formula='amount * 2')
        self.assertEqual(result, True)
        result = self.dataset.get_calculations()
        self.assertTrue(isinstance(result, list))
        for calc in result:
            self.assertTrue(isinstance(calc, dict))
            keys = calc.keys()
            for key in calc_keys:
                self.assertTrue(key in keys)
        self.assertEqual(result[0]['state'], 'pending')
        self.wait()
        self.wait()
        result = self.dataset.get_calculations()
        self.assertEqual(result[0]['state'], 'ready')

    def test_get_aggregate_datasets(self):
        result = self.dataset.get_aggregate_datasets()
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(result), 0)
        self.dataset.add_calculation(name='sum_amount',
                                     formula='sum(amount)')
        self.wait()
        self.wait()
        result = self.dataset.get_aggregate_datasets()
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(result), 1)
        self.assertTrue('' in result.keys())
        self.assertTrue(isinstance(result[''], Dataset))
        self.dataset.add_calculation(
            name='sum_amount', formula='sum(amount)', groups=['food_type'])
        self.wait()
        self.wait()
        result = self.dataset.get_aggregate_datasets()
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(result), 2)
        self.assertTrue('food_type' in result.keys())
        self.assertTrue(isinstance(result['food_type'], Dataset))
        self.dataset.has_aggs_to_remove = True

    def test_get_aggregate_datasets_no_aggregations(self):
        result = self.dataset.get_aggregate_datasets()
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(result), 0)

    def test_get_summary(self):
        self.wait()  # TODO: remove (bamboo issue #276)
        result = self.dataset.get_summary()
        self.assertTrue(isinstance(result, dict))
        cols = self.dataset.columns
        keys = result.keys()
        for col in cols:
            self.assertTrue(col in keys)

    def test_get_summary_with_select(self):
        self.wait()  # TODO: remove (bamboo issue #276)
        result = self.dataset.get_summary(select=['food_type'])
        self.assertEqual(len(result), 1)
        self.assertTrue('food_type' in result.keys())
        result = self.dataset.get_summary(select=['food_type', 'rating'])
        self.assertEqual(len(result), 2)
        result_keys = result.keys()
        self.assertTrue('food_type' in result_keys)
        self.assertTrue('food_type' in result_keys)

    def test_get_summary_bad_select(self):
        with self.assertRaises(PyBambooException):
            self.dataset.get_summary(select='BAD')

    def test_get_summary_with_query(self):
        self.wait()  # TODO: remove (bamboo issue #276)
        self.dataset.get_summary(query={'food_type': 'lunch'})

    def test_get_summary_bad_query(self):
        with self.assertRaises(PyBambooException):
            self.dataset.get_summary(query='BAD')

    def test_get_summary_with_groups(self):
        self.wait()  # TODO: remove (bamboo issue #276)
        result = self.dataset.get_summary(groups=['food_type'])
        self.assertEqual(len(result), 1)
        values = self.dataset.get_summary(
            select=['food_type'])['food_type']['summary'].keys()
        self.assertTrue('food_type' in result.keys())
        self.assertTrue(isinstance(result['food_type'], dict))
        keys = result['food_type'].keys()
        for val in values:
            self.assertTrue(val in keys)

    def test_get_summary_bad_groups(self):
        with self.assertRaises(PyBambooException):
            self.dataset.get_summary(groups='BAD')

    def test_get_info(self):
        info_keys = [
            'attribution',
            'description',
            'license',
            'created_at',
            'updated_at',
            'label',
            'num_columns',
            'num_rows',
            'id',
            'schema',
        ]
        schema_keys = [
            'simpletype',
            'olap_type',
            'label',
        ]
        self.wait()  # have to wait, bamboo issue #284
        result = self.dataset.get_info()
        self.assertTrue(isinstance(result, dict))
        for key in info_keys:
            self.assertTrue(key in result.keys())
        self.assertEqual(result['num_columns'], 15)
        self.assertEqual(result['num_rows'], 19)
        schema = result['schema']
        self.assertTrue(isinstance(schema, dict))
        self.assertEqual(len(schema.keys()), 15)
        for col_name, col_info in schema.iteritems():
            for key in schema_keys:
                self.assertTrue(key in col_info.keys())

    def test_get_data(self):
        self.wait()
        result = self.dataset.get_data()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 19)

    def test_get_data_with_select(self):
        self.wait()
        result = self.dataset.get_data(select=['food_type', 'amount'])
        self.assertEqual(len(result), 19)
        for row in result:
            self.assertEqual(len(row), 2)
            cols = row.keys()
            self.assertTrue('food_type' in cols)
            self.assertTrue('amount' in cols)

    def test_get_data_with_query(self):
        self.wait()  # TODO: remove (bamboo issue #285)
        result = self.dataset.get_data(query={'food_type': 'lunch'})
        self.assertEqual(len(result), 7)

    def test_get_data_with_select_and_query(self):
        self.wait()  # TODO: remove (bamboo issue #285)
        result = self.dataset.get_data(
            select=['food_type', 'amount'], query={'food_type': 'lunch'})
        self.assertEqual(len(result), 7)
        for row in result:
            self.assertEqual(len(row), 2)
            cols = row.keys()
            self.assertTrue('food_type' in cols)
            self.assertTrue('amount' in cols)

    def test_get_data_with_format(self):
        self.wait()  # TODO: remove (bamboo issue #285)
        result = self.dataset.get_data(format='csv')
        self.assertTrue(isinstance(result, basestring))

    def test_get_data_invalid_select(self):
        with self.assertRaises(PyBambooException):
            self.dataset.get_data(select='BAD')

    def test_get_data_invalid_query(self):
        with self.assertRaises(PyBambooException):
            self.dataset.get_data(query='BAD')

    def test_get_data_with_invalid_format(self):
        with self.assertRaises(PyBambooException):
            self.dataset.get_data(format='BAD')

    def test_get_data_bad_query(self):
        self.wait()  # TODO: remove (bamboo issue #285)
        result = self.dataset.get_data(query={'BAD': 'BAD'})
        self.assertFalse(result)

    def test_update_data(self):
        row = {
            'food_type': 'morning_food',
            'amount': 10.0,
            'risk_factor': 'high_risk',
            'rating': 'delectible',
        }
        result = self.dataset.update_data([row])
        self.wait(15)
        result = self.dataset.get_data()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 20)

    def test_update_data_no_data(self):
        with self.assertRaises(PyBambooException):
            self.dataset.update_data([])

    def test_update_data_bad_data(self):
        bad_rows = [
            {},
            [[]],
            [{'exception': Exception()}]
        ]
        for rows in bad_rows:
            with self.assertRaises(PyBambooException):
                self.dataset.update_data(rows)

    def test_merge(self):
        # already have one dataset in self.dataset
        dataset = Dataset(path=self.CSV_FILE,
                          connection=self.connection)
        result = Dataset.merge([self.dataset, dataset],
                               connection=self.connection)
        self.assertTrue(isinstance(result, Dataset))
        self._cleanup(dataset)
        self._cleanup(result)

    def test_merge_default_connection(self):
        dataset = Dataset(path=self.CSV_FILE,
                          connection=self.default_connection)
        other_dataset = Dataset(path=self.CSV_FILE,
                                connection=self.default_connection)
        result = Dataset.merge([dataset, other_dataset])
        self.assertTrue(isinstance(result, Dataset))
        self._cleanup(dataset)
        self._cleanup(other_dataset)
        self._cleanup(result)

    def test_merge_bad_datasets(self):
        dataset = {}
        other_dataset = []
        with self.assertRaises(PyBambooException):
            Dataset.merge([dataset, other_dataset],
                          connection=self.connection)

    def test_merge_fail(self):
        other_dataset = Dataset('12345', connection=self.connection)
        result = Dataset.merge([self.dataset, other_dataset],
                               connection=self.connection)
        self.assertFalse(result)

    def test_join(self):
        self._create_aux_dataset_from_file()
        self.wait()
        result = Dataset.join(self.dataset, self.aux_dataset,
                              'food_type', connection=self.connection)
        self.assertTrue(isinstance(result, Dataset))
        self._cleanup(result)

    def test_join_default_connection(self):
        dataset = Dataset(path=self.CSV_FILE,
                          connection=self.default_connection)
        aux_dataset = Dataset(path=self.AUX_CSV_FILE,
                              connection=self.default_connection)
        self.wait()
        result = Dataset.join(dataset, aux_dataset, 'food_type')
        self.wait()
        self.assertTrue(isinstance(result, Dataset))
        self._cleanup(dataset)
        self._cleanup(aux_dataset)
        self._cleanup(result)

    def test_join_bad_other_dataset(self):
        with self.assertRaises(PyBambooException):
            Dataset.join(self.dataset, Exception(), 'food_type',
                         connection=self.connection)

    def test_join_bad_on(self):
        self._create_aux_dataset_from_file()
        self.wait()
        result = Dataset.join(self.dataset, self.aux_dataset,
                              'BAD', connection=self.connection)
        self.assertFalse(result)

    # /row/INDEX tests.
    def test_get_row(self):
        self.assertEqual(self.dataset.get_row(0)['comments'],
                         u"Try the yogurt drink")

    def test_update_row(self):
        index = 2
        comment = 'test'
        self.dataset.update_row(index, {'comments': comment})
        self.assertEqual(self.dataset.get_row(index)['comments'], comment)

    def test_delete_row(self):
        self._wait_for_dataset_ready()  # TODO: is this necessary?
        index = 10
        self.dataset.delete_row(index=index)
        result = self.dataset.get_row(index)
        self.assertTrue('error' in result)
