"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Tools for Producer (ETP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

import os
import shutil
import tempfile
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

import mock

from rest_framework import status
from rest_framework.test import APIClient

from ESSArch_Core.configuration.models import Path
from ESSArch_Core.ip.models import InformationPackage, Order, Workarea


class AccessTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.root = os.path.dirname(os.path.realpath(__file__))
        self.datadir = os.path.join(self.root, 'datadir')

        self.ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        self.url = reverse('informationpackage-detail', args=(str(self.ip.pk),))
        self.url = self.url + 'access/'

    @mock.patch('ip.views.ProcessStep.run')
    def test_no_valid_option_set(self, mock_step):
        res = self.client.post(self.url, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_step.assert_not_called()

    @mock.patch('ip.views.ProcessStep.run')
    def test_no_valid_option_set_to_true(self, mock_step):
        res = self.client.post(self.url, {'tar': False}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_step.assert_not_called()

    @mock.patch('ip.views.ProcessStep.run')
    def test_not_in_workarea(self, mock_step):
        res = self.client.post(self.url, {'tar': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        mock_step.assert_called_once()

    @mock.patch('ip.views.ProcessStep.run')
    def test_already_in_workarea(self, mock_step):
        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.post(self.url, {'tar': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_step.assert_not_called()


class WorkareaViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.ip = InformationPackage.objects.create(generation=0)
        self.url = reverse('workarea-list')

    def test_empty(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_post(self):
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invalid_workarea(self):
        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'non-existing-workarea'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ip_in_workarea_by_other_user(self):
        user2 = User.objects.create()
        Workarea.objects.create(user=user2, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_ip_in_workarea_by_current_user_aic_view_type(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'aic'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(self.ip.pk))

    def test_ip_in_workarea_by_current_user_ip_view_type(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'ip'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 0)

    def test_ip_in_workarea_by_current_user_ip_view_type_first_generation_not_in_workarea(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'ip'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(ip2.pk))

    def test_ip_in_workarea_by_current_user_ip_view_type_global_search(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(Label='bar', package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.Label = 'foo'
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)
        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'ip', 'search': 'foo'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 0)

    def test_ip_in_workarea_by_current_user_aic_view_type_global_search(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(Label='second', package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.Label = 'first'
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)
        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'aic', 'search': 'first'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(self.ip.pk))

class WorkareaFilesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password='admin')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.datadir = tempfile.mkdtemp()
        Path.objects.create(entity='access', value=self.datadir)

        self.path = os.path.join(self.datadir, str(self.user.pk))
        os.mkdir(self.path)

        self.url = reverse('workarea-files-list')

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

    def test_no_type_parameter(self):
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_type_parameter(self):
        res = self.client.get(self.url, {'type': 'invalidtype'})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_file(self):
        _, path = tempfile.mkstemp(dir=self.path)
        res = self.client.get(self.url, {'type': 'access'})

        self.assertEqual(res.data, [{'type': 'file', 'name': os.path.basename(path)}])

    def test_list_file_content(self):
        _, path = tempfile.mkstemp(dir=self.path)
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_folder(self):
        path = tempfile.mkdtemp(dir=self.path)
        res = self.client.get(self.url, {'type': 'access'})

        self.assertEqual(res.data, [{'type': 'dir', 'name': os.path.basename(path)}])

    def test_list_folder_content(self):
        path = tempfile.mkdtemp(dir=self.path)
        _, filepath = tempfile.mkstemp(dir=path)
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.data, [{'type': 'file', 'name': os.path.basename(filepath)}])

    def test_illegal_path(self):
        path = os.path.join(self.path, '..')
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_existing_path(self):
        path = os.path.join(self.path, 'does/not/exist')
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_to_dip_not_responsible(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo.txt'

        ip = InformationPackage.objects.create(ObjectPath=dstdir, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(os.path.isfile(os.path.join(dstdir, dst)))

    def test_add_to_dip_file_to_file(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo.txt'

        ip = InformationPackage.objects.create(ObjectPath=dstdir, Responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isfile(os.path.join(dstdir, dst)))

    def test_add_to_dip_file_to_file_overwrite(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo.txt'

        open(os.path.join(dstdir, dst), 'a').close()

        ip = InformationPackage.objects.create(ObjectPath=dstdir, Responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isfile(os.path.join(dstdir, dst)))

    def test_add_to_dip_file_to_dir(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = os.path.basename(tempfile.mkdtemp(dir=dstdir))

        ip = InformationPackage.objects.create(ObjectPath=dstdir, Responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isfile(os.path.join(dstdir, dst, os.path.basename(src))))

    def test_add_to_dip_dir_to_dir(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        src = tempfile.mkdtemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo'

        ip = InformationPackage.objects.create(ObjectPath=dstdir, Responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isdir(os.path.join(dstdir, dst)))

    def test_add_to_dip_dir_to_dir_overwrite(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        src = tempfile.mkdtemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = os.path.basename(tempfile.mkdtemp(dir=dstdir))

        ip = InformationPackage.objects.create(ObjectPath=dstdir, Responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isdir(os.path.join(dstdir, dst)))


class InformationPackageViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password='admin')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse('informationpackage-list')

    def test_empty(self):
        res = self.client.get(self.url)
        self.assertEqual(res.data, [])

    def test_aic_view_type_aic_no_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)

        res = self.client.get(self.url, data={'view_type': 'aic'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(res.data[0]['information_packages'], [])

    def test_aic_view_type_aic_multiple_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)

    def test_aic_view_type_aic_multiple_aips_same_state_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(State='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    def test_aic_view_type_aic_multiple_aips_different_states_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(State='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_view_type_aic_no_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)

        res = self.client.get(self.url, data={'view_type': 'ip'})
        self.assertEqual(len(res.data), 0)

    def test_ip_view_type_aic_multiple_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_same_state_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=2, State='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip3.pk))

    def test_ip_view_type_aic_multiple_aips_different_states_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=2, State='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_view_type_aic_multiple_aips_different_states_first_ip_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_different_states_all_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='baz', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_different_labels_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'label': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 0)

    def test_ip_view_type_aic_multiple_aips_different_labels_all_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='baz', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'foo'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_different_labels_global_search(self):
        aic1 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip11 = InformationPackage.objects.create(generation=0, Label='first1', aic=aic1, package_type=InformationPackage.AIP)
        aip12 = InformationPackage.objects.create(generation=1, Label='first2', aic=aic1, package_type=InformationPackage.AIP)

        aic2 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip21 = InformationPackage.objects.create(generation=0, Label='second1', aic=aic2, package_type=InformationPackage.AIP)
        aip22 = InformationPackage.objects.create(generation=1, Label='second2', aic=aic2, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'search': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic1.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip11.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip12.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_global_search(self):
        aic1 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip11 = InformationPackage.objects.create(generation=0, Label='first1', aic=aic1, package_type=InformationPackage.AIP)
        aip12 = InformationPackage.objects.create(generation=1, Label='first2', aic=aic1, package_type=InformationPackage.AIP)

        aic2 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip21 = InformationPackage.objects.create(generation=0, Label='second1', aic=aic2, package_type=InformationPackage.AIP)
        aip22 = InformationPackage.objects.create(generation=1, Label='second2', aic=aic2, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'search': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip11.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip12.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_global_search_and_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='foo', State='first', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='bar', State='second', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'search': 'bar', 'state': 'second'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_aic_view_type_aic_aips_different_labels_same_aic_global_search(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(Label='first', package_type=InformationPackage.AIP, aic=aic, generation=1)
        aip2 = InformationPackage.objects.create(Label='second', package_type=InformationPackage.AIP, aic=aic, generation=1)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'aic', 'search': 'first'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_no_label(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_prepare.assert_not_called()

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_no_object_identifier_value(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'
        res = self.client.post(self.url, {'label': 'foo'})

        mock_prepare.assert_called_once_with(label='foo', object_identifier_value=None, orders=[])

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_object_identifier_value(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'
        res = self.client.post(self.url, {'label': 'foo', 'object_identifier_value': 'bar'})

        mock_prepare.assert_called_once_with(label='foo', object_identifier_value='bar', orders=[])

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_existing_object_identifier_value(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'

        InformationPackage.objects.create(ObjectIdentifierValue='bar')
        res = self.client.post(self.url, {'label': 'foo', 'object_identifier_value': 'bar'})

        mock_prepare.assert_not_called()

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_orders(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'

        orders = [str(Order.objects.create(responsible=self.user).pk)]
        res = self.client.post(self.url, {'label': 'foo', 'orders': orders}, format='json')

        mock_prepare.assert_called_once_with(label='foo', object_identifier_value=None, orders=orders)

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_non_existing_order(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'

        orders = [str(Order.objects.create(responsible=self.user).pk), str(uuid.uuid4())]
        res = self.client.post(self.url, {'label': 'foo', 'orders': orders}, format='json')

        mock_prepare.assert_not_called()


class InformationPackageViewSetFilesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password='admin')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.datadir = tempfile.mkdtemp()

        self.ip = InformationPackage.objects.create(ObjectPath=self.datadir, package_type=InformationPackage.DIP)
        self.url = reverse('informationpackage-detail', args=(str(self.ip.pk),))
        self.url = self.url + 'files/'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

    def test_delete_file(self):
        _, path = tempfile.mkstemp(dir=self.datadir)
        res = self.client.delete(self.url, {'path': path})

        self.assertFalse(os.path.exists(path))

    def test_delete_folder(self):
        path = tempfile.mkdtemp(dir=self.datadir)
        res = self.client.delete(self.url, {'path': path})

        self.assertFalse(os.path.exists(path))

    def test_delete_no_path(self):
        res = self.client.delete(self.url)
        res.status = status.HTTP_400_BAD_REQUEST

    def test_list_file(self):
        _, path = tempfile.mkstemp(dir=self.datadir)
        res = self.client.get(self.url)

        self.assertEqual(res.data, [{'type': 'file', 'name': os.path.basename(path)}])

    def test_list_folder(self):
        path = tempfile.mkdtemp(dir=self.datadir)
        res = self.client.get(self.url)

        self.assertEqual(res.data, [{'type': 'dir', 'name': os.path.basename(path)}])

    def test_list_folder_content(self):
        path = tempfile.mkdtemp(dir=self.datadir)
        _, filepath = tempfile.mkstemp(dir=path)
        res = self.client.get(self.url, {'path': path})

        self.assertEqual(res.data, [{'type': 'file', 'name': os.path.basename(filepath)}])

    def test_create_folder(self):
        path = 'foo'
        res = self.client.post(self.url, {'path': path, 'type': 'dir'})

        self.assertTrue(os.path.isdir(os.path.join(self.ip.ObjectPath, path)))

    def test_create_file(self):
        path = 'foo.txt'
        res = self.client.post(self.url, {'path': path, 'type': 'file'})

        self.assertTrue(os.path.isfile(os.path.join(self.ip.ObjectPath, path)))
