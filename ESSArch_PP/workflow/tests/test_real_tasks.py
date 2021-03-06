# -*- coding: utf-8 -*-

"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation (EPP)
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

import errno
import filecmp
import os
import shutil
import tarfile
import tempfile
import zipfile

from django.contrib.auth.models import User
from django.test import tag, TransactionTestCase, override_settings

from unittest import mock

from ESSArch_Core.configuration.models import (
    ArchivePolicy, Path,
)

from ESSArch_Core.ip.models import (
    ArchivistOrganization,
    InformationPackage,
    Order,
    Workarea,
)

from ESSArch_Core.storage.exceptions import (
    TapeMountedError,
    TapeMountedAndLockedByOtherError,
)

from ESSArch_Core.storage.models import (
    DISK,
    TAPE,

    IOQueue,

    Robot,
    RobotQueue,
    TapeDrive,
    TapeSlot,

    StorageMedium,
    StorageMethod,
    StorageObject,
    StorageTarget,
    StorageMethodTargetRelation,
)

from ESSArch_Core.WorkflowEngine.models import (
    ProcessTask,
)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class ReceiveSIPTestCase(TransactionTestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

        self.gate = Path.objects.create(
            entity='gate',
            value=os.path.join(self.root, 'gate')
        )

        self.ingest = Path.objects.create(
            entity='ingest',
            value=os.path.join(self.root, 'ingest')
        )

        self.cache = Path.objects.create(
            entity='cache',
            value=os.path.join(self.root, 'cache')
        )

        self.xmldata = '''
            <mets:mets
                xmlns:mets="http://www.loc.gov/METS/"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://www.loc.gov/METS/ http://xml.essarch.org/METS/info.xsd"
                ID="IDbc94f115-d6c0-43a1-9be8-a073c467bf1b"
                OBJID="UUID:2259f52c-39c6-4a82-a9c3-3e7d29742c21"
                LABEL="test-ip"
                TYPE="SIP"
                PROFILE="my profile">
                <mets:metsHdr CREATEDATE="2016-12-01T11:54:31+01:00">
                </mets:metsHdr>
                <agent ROLE="ARCHIVIST" TYPE="ORGANIZATION">
                    <name>my_archivist_organization</name>
                </agent>
            </mets:mets>
            '''

        for path in [self.gate, self.ingest, self.cache]:
            try:
                os.makedirs(path.value)
            except OSError as e:
                if e.errno != 17:
                    raise

    def tearDown(self):
        try:
            shutil.rmtree(self.root)
        except BaseException:
            pass

    def test_receive_sip(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        open(container, 'a').close()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )

        aip = InformationPackage.objects.create(
            object_identifier_value=sip,
            package_type=InformationPackage.AIP,
            generation=0,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            args=[aip.pk, xml, container, policy.pk]
        )

        task.run().get()

        expected_aip = os.path.join(self.ingest.value, sip)

        aip.refresh_from_db()
        aic = aip.aic
        self.assertEqual(str(aic.pk), aic.object_identifier_value)
        self.assertEqual(aic.package_type, InformationPackage.AIC)

        self.assertEqual(aip.object_path, expected_aip)

        self.assertEqual(sip, aip.object_identifier_value)
        self.assertTrue(os.path.isdir(expected_aip))

        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertTrue(os.path.isfile(expected_tar))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertFalse(os.path.isdir(expected_content_dir))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))

        self.assertEqual(ArchivistOrganization.objects.get().name, 'my_archivist_organization')
        self.assertIsNotNone(aip.archivist_organization)

    def test_receive_sip_extract_tar(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        files = []

        for name in ["foo", "bar", "baz"]:
            fpath = os.path.join(self.gate.value, name)
            open(fpath, 'a').close()
            files.append(fpath)

        with tarfile.open(container, 'w') as tar:
            tar.add(self.gate.value, sip)

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            receive_extract_sip=True
        )

        aip = InformationPackage.objects.create(
            object_identifier_value=sip,
            package_type=InformationPackage.AIP,
            generation=0,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            args=[aip.pk, xml, container, policy.pk]
        )

        task.run()

        aip.refresh_from_db()

        expected_aip = os.path.join(self.ingest.value, sip)
        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        self.assertEqual(aip.object_path, expected_aip)

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertFalse(os.path.isfile(expected_tar))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertTrue(os.path.isdir(expected_content_dir))

        for f in files:
            expected_file = os.path.join(expected_content_dir, os.path.basename(f))
            self.assertTrue(os.path.isfile(expected_file))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))

    def test_receive_sip_extract_tar_containing_non_ascii_filenames(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        files = []

        for name in ['bar.txt', 'åäö']:
            fpath = os.path.join(self.gate.value, name)
            open(fpath, 'a').close()
            files.append(fpath)

        with tarfile.open(container, 'w', encoding='UTF-8') as tar:
            tar.add(self.gate.value, sip)

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            receive_extract_sip=True
        )

        aip = InformationPackage.objects.create(
            object_identifier_value=sip,
            package_type=InformationPackage.AIP,
            generation=0,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            args=[aip.pk, xml, container, policy.pk]
        )

        task.run()

        aip.refresh_from_db()

        expected_aip = os.path.join(self.ingest.value, sip)
        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        self.assertEqual(aip.object_path, expected_aip)

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertFalse(os.path.isfile(expected_tar))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertTrue(os.path.isdir(expected_content_dir))

        for f in files:
            expected_file = os.path.join(expected_content_dir, os.path.basename(f))
            self.assertTrue(os.path.isfile(expected_file))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))

    def test_receive_sip_extract_zip(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.zip')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        files = []

        for name in ["foo", "bar", "baz"]:
            fpath = os.path.join(self.gate.value, name)
            open(fpath, 'a').close()
            files.append(fpath)

        with zipfile.ZipFile(container, 'w') as zipf:
            for f in files:
                arc = os.path.join(sip, os.path.relpath(f, self.gate.value))
                zipf.write(f, arc)

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            receive_extract_sip=True
        )

        aip = InformationPackage.objects.create(
            object_identifier_value=sip,
            package_type=InformationPackage.AIP,
            generation=0,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            args=[aip.pk, xml, container, policy.pk]
        )

        task.run()

        aip.refresh_from_db()

        expected_aip = os.path.join(self.ingest.value, sip)
        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        self.assertEqual(aip.object_path, expected_aip)

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertFalse(os.path.isfile(expected_tar))

        expected_zip = os.path.join(expected_content, sip + '.zip')
        self.assertFalse(os.path.isfile(expected_zip))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertTrue(os.path.isdir(expected_content_dir))

        for f in files:
            expected_file = os.path.join(expected_content_dir, os.path.basename(f))
            self.assertTrue(os.path.isfile(expected_file))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))

    def test_receive_sip_extract_zip_containing_non_ascii_files(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.zip')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        files = []

        for name in ["åäö"]:
            fpath = os.path.join(self.gate.value, name)
            open(fpath, 'a').close()
            files.append(fpath)

        with zipfile.ZipFile(container, 'w') as zipf:
            for f in files:
                arc = os.path.join(sip, os.path.relpath(f, self.gate.value))
                zipf.write(f, arc)

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            receive_extract_sip=True
        )

        aip = InformationPackage.objects.create(
            object_identifier_value=sip,
            package_type=InformationPackage.AIP,
            generation=0,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            args=[aip.pk, xml, container, policy.pk]
        )

        task.run()

        aip.refresh_from_db()

        expected_aip = os.path.join(self.ingest.value, sip)
        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        self.assertEqual(aip.object_path, expected_aip)

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertFalse(os.path.isfile(expected_tar))

        expected_zip = os.path.join(expected_content, sip + '.zip')
        self.assertFalse(os.path.isfile(expected_zip))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertTrue(os.path.isdir(expected_content_dir))

        for f in files:
            expected_file = os.path.join(expected_content_dir, os.path.basename(f))
            self.assertTrue(os.path.isfile(expected_file))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class CacheAIPTestCase(TransactionTestCase):
    def setUp(self):
        self.root = os.path.dirname(os.path.realpath(__file__))

        self.ingest = Path.objects.create(
            entity='ingest',
            value=os.path.join(self.root, 'ingest')
        )

        self.cache = Path.objects.create(
            entity='cache',
            value=os.path.join(self.root, 'cache')
        )

        for path in [self.ingest, self.cache]:
            try:
                os.makedirs(path.value)
            except OSError as e:
                if e.errno != 17:
                    raise

    def tearDown(self):
        for path in [self.ingest, self.cache]:
            try:
                shutil.rmtree(path.value)
            except BaseException:
                pass

    def test_cache_aip(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        objid = 'custom_obj_id'
        aip = InformationPackage.objects.create(
            object_identifier_value=objid, policy=policy,
            object_path=os.path.join(self.ingest.value, objid)
        )

        aip_dir = os.path.join(policy.ingest_path.value, aip.object_identifier_value)
        os.mkdir(aip_dir)
        os.mkdir(os.path.join(aip_dir, 'content'))
        os.mkdir(os.path.join(aip_dir, 'metadata'))

        contentfile = os.path.join(
            aip_dir, 'content', 'myfile.txt'
        )

        with open(contentfile, 'a') as f:
            f.write('foo')

        task = ProcessTask.objects.create(
            name='workflow.tasks.CacheAIP',
            params={
                'aip': aip.pk
            },
        )

        task.run()

        cached_dir = os.path.join(aip.policy.cache_storage.value, aip.object_identifier_value)
        self.assertTrue(os.path.isdir(cached_dir))

        equal_content = filecmp.cmp(
            os.path.join(aip_dir, 'content', 'myfile.txt'),
            os.path.join(cached_dir, 'content', 'myfile.txt'),
            False
        )
        self.assertTrue(equal_content)

        extracted = os.path.join(aip.policy.cache_storage.value, 'extracted')
        os.mkdir(extracted)

        cached_container = os.path.join(aip.policy.cache_storage.value, aip.object_identifier_value + '.tar')
        self.assertTrue(os.path.isfile(cached_container))

        with tarfile.open(cached_container) as tar:
            tar.extractall(extracted)

        equal_content = filecmp.cmp(
            os.path.join(aip_dir, 'content', 'myfile.txt'),
            os.path.join(extracted, aip.object_identifier_value, 'content', 'myfile.txt'),
            False
        )
        self.assertTrue(equal_content)

    def test_cache_aip_nested_dir(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        objid = 'custom_obj_id'
        aip = InformationPackage.objects.create(
            object_identifier_value=objid, policy=policy,
            object_path=os.path.join(self.ingest.value, objid)
        )

        os.makedirs(os.path.join(aip.object_path, 'root', 'nested'))

        task = ProcessTask.objects.create(
            name='workflow.tasks.CacheAIP',
            params={
                'aip': aip.pk
            },
        )

        task.run()

        cached_dir = os.path.join(aip.policy.cache_storage.value, aip.object_identifier_value)
        self.assertTrue(os.path.isdir(os.path.join(cached_dir, 'root', 'nested')))

        with tarfile.open(cached_dir + '.tar') as tar:
            expected_members = [
                os.path.join(objid, 'root'),
                os.path.join(objid, 'root', 'nested')
            ]
            self.assertItemsEqual(tar.getnames(), expected_members)

    def test_cache_aip_nested_file(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        objid = 'custom_obj_id'
        aip = InformationPackage.objects.create(
            object_identifier_value=objid, policy=policy,
            object_path=os.path.join(self.ingest.value, objid)
        )

        os.makedirs(os.path.join(aip.object_path, 'root'))
        open(os.path.join(aip.object_path, 'root', 'nested.txt'), 'a').close()

        task = ProcessTask.objects.create(
            name='workflow.tasks.CacheAIP',
            params={
                'aip': aip.pk
            },
        )

        task.run()

        cached_dir = os.path.join(aip.policy.cache_storage.value, aip.object_identifier_value)
        self.assertTrue(os.path.isfile(os.path.join(cached_dir, 'root', 'nested.txt')))

        with tarfile.open(cached_dir + '.tar') as tar:
            expected_members = [
                os.path.join(objid, 'root'),
                os.path.join(objid, 'root', 'nested.txt')
            ]
            self.assertItemsEqual(tar.getnames(), expected_members)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class StoreAIPTestCase(TransactionTestCase):
    def setUp(self):
        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

        self.datadir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except BaseException:
            pass

        try:
            shutil.rmtree(self.storagedir)
        except BaseException:
            pass

    def test_store_aip_no_policy(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(policy=policy)

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
        )

        with self.assertRaises(StorageMethod.DoesNotExist):
            task.run().get()

    def test_store_aip_no_storage_method(self):
        aip = InformationPackage.objects.create()

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
        )

        with self.assertRaises(ArchivePolicy.DoesNotExist):
            task.run().get()

    def test_store_aip_disk(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            object_path=self.datadir,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )

        self.assertTrue(queue_entry.exists())

    def test_store_aip_disk_and_tape(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            object_path=self.datadir,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        method2 = StorageMethod.objects.create(archive_policy=policy, type=TAPE)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )
        method_target2 = StorageMethodTargetRelation.objects.create(
            storage_method=method2, storage_target=target, status=2
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )
        queue_entry2 = IOQueue.objects.filter(
            req_type=10, status=0, ip=aip, storage_method_target=method_target2,
        )

        self.assertTrue(queue_entry.exists())
        self.assertTrue(queue_entry2.exists())

    def test_store_aip_with_same_existing(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            object_path=self.datadir,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task.run().get()
        task.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )

        self.assertEqual(queue_entry.count(), 1)

    def test_store_aip_with_different_existing(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            object_path=self.datadir,
        )
        aip2 = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id_2', policy=policy,
            object_path=self.datadir
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task2 = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip2.pk
            },
            responsible=user,
        )

        task.run().get()
        task2.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )

        queue_entry2 = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip2, storage_method_target=method_target,
        )

        self.assertTrue(queue_entry.exists())
        self.assertTrue(queue_entry2.exists())


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class AccessAIPTestCase(TransactionTestCase):
    def setUp(self):
        self.access = Path.objects.create(entity='access', value='access')

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

    def test_no_storage_objects(self):
        ip = InformationPackage.objects.create()
        User.objects.create()

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk
            },
        )

        with self.assertRaises(StorageObject.DoesNotExist):
            task.run().get()

        self.assertFalse(Workarea.objects.exists())

    @mock.patch('ESSArch_Core.tasks.CopyFile.run', side_effect=lambda *args, **kwargs: None)
    @mock.patch('workflow.tasks.os.mkdir', side_effect=lambda *args, **kwargs: None)
    @mock.patch('workflow.tasks.os.path.exists', return_value=True)
    def test_in_cache(self, mock_exists, mock_mkdir, mock_copy):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy)
        target = StorageTarget.objects.create(type=DISK)

        StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=50,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        StorageObject.objects.create(
            storage_medium=medium, ip=ip,
            content_location_type=DISK,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk
            },
            responsible=user
        )

        task.run().get()

        self.assertFalse(IOQueue.objects.exists())
        mock_copy.assert_called_once_with(
            src=os.path.join(self.cache.value, ip.object_identifier_value + '.tar'),
            dst=os.path.join(self.access.value, str(user.pk), ip.object_identifier_value + '.tar')
        )

        self.assertTrue(Workarea.objects.filter(ip=ip, user=user, type=Workarea.ACCESS, read_only=True).exists())

    @mock.patch('workflow.tasks.os.mkdir', side_effect=lambda *args, **kwargs: None)
    def test_on_disk(self, mock_mkdir):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy)
        target = StorageTarget.objects.create(type=DISK)

        StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=50,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, ip=ip,
            content_location_type=DISK,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk
            },
            responsible=user,
        )

        task.run().get()

        self.assertTrue(IOQueue.objects.filter(
            ip=ip, storage_object=obj, req_type=25,
            status=0, object_path=os.path.join(self.access.value, str(user.pk), ip.object_identifier_value + '.tar'),
        ).exists())

        self.assertTrue(Workarea.objects.filter(ip=ip, user=user, type=Workarea.ACCESS, read_only=True).exists())

    @mock.patch('workflow.tasks.os.mkdir', side_effect=lambda *args, **kwargs: None)
    def test_on_tape(self, mock_mkdir):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy)
        target = StorageTarget.objects.create(type=TAPE)

        StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=50,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, ip=ip,
            content_location_type=TAPE,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk
            },
            responsible=user,
        )

        task.run().get()

        self.assertTrue(IOQueue.objects.filter(
            ip=ip, storage_object=obj, req_type=20,
            status=0, object_path=os.path.join(self.access.value, str(user.pk), ip.object_identifier_value + '.tar'),
        ).exists())

        self.assertTrue(Workarea.objects.filter(ip=ip, user=user, type=Workarea.ACCESS, read_only=True).exists())

    @mock.patch('workflow.tasks.os.mkdir', side_effect=lambda *args, **kwargs: None)
    def test_new_generation_from_storage(self, mock_mkdir):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            generation=0,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy)
        target = StorageTarget.objects.create(type=DISK)

        StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=50,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, ip=ip,
            content_location_type=DISK,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk,
                'new': True,
            },
            responsible=user,
        )

        task.run().get()

        new_ip = InformationPackage.objects.exclude(pk=ip.pk).first()

        self.assertTrue(IOQueue.objects.filter(
            ip=ip, storage_object=obj, req_type=25, status=0,
            object_path=os.path.join(self.access.value, str(user.pk), new_ip.object_identifier_value + '.tar'),
        ).exists())

        self.assertFalse(Workarea.objects.filter(ip=ip).exists())
        self.assertTrue(Workarea.objects.filter(
            ip__generation=1, user=user, type=Workarea.ACCESS, read_only=False
        ).exists())

    @mock.patch('ESSArch_Core.tasks.CopyFile.run', side_effect=lambda *args, **kwargs: None)
    @mock.patch('workflow.tasks.os.mkdir', side_effect=lambda *args, **kwargs: None)
    @mock.patch('workflow.tasks.os.path.exists', return_value=True)
    def test_new_generation_from_cache(self, mock_exists, mock_mkdir, mock_copy):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            generation=0,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy)
        target = StorageTarget.objects.create(type=DISK)

        StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=50,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        StorageObject.objects.create(
            storage_medium=medium, ip=ip,
            content_location_type=DISK,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk,
                'new': True
            },
            responsible=user
        )

        task.run().get()

        new_ip = InformationPackage.objects.exclude(pk=ip.pk).first()

        self.assertFalse(IOQueue.objects.exists())
        mock_copy.assert_called_once_with(
            src=os.path.join(self.cache.value, ip.object_identifier_value + '.tar'),
            dst=os.path.join(self.access.value, str(user.pk), new_ip.object_identifier_value + '.tar')
        )

        self.assertTrue(Workarea.objects.filter(ip=new_ip, user=user, type=Workarea.ACCESS, read_only=False).exists())

    @mock.patch('ESSArch_Core.tasks.CopyFile.run', side_effect=lambda *args, **kwargs: None)
    @mock.patch('workflow.tasks.os.mkdir', side_effect=lambda *args, **kwargs: None)
    @mock.patch('workflow.tasks.os.path.exists', return_value=True)
    def test_new_generation_twice(self, mock_exists, mock_mkdir, mock_copy):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(
            object_identifier_value='custom_obj_id', policy=policy,
            generation=0,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy)
        target = StorageTarget.objects.create(type=DISK)

        StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=50,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        StorageObject.objects.create(
            storage_medium=medium, ip=ip,
            content_location_type=DISK,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': ip.pk,
                'new': True
            },
            responsible=user
        )

        task.run().get()
        task.run().get()

        self.assertEqual(InformationPackage.objects.filter(aic=ip.aic, generation=0).count(), 1)
        self.assertEqual(InformationPackage.objects.filter(aic=ip.aic, generation=1).count(), 1)
        self.assertEqual(InformationPackage.objects.filter(aic=ip.aic, generation=2).count(), 1)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PrepareDIPTestCase(TransactionTestCase):
    def setUp(self):
        self.disseminations = Path.objects.create(entity='disseminations', value='disseminations')
        self.task = "workflow.tasks.PrepareDIP"

    @mock.patch('workflow.tasks.os.mkdir')
    def test_prepare_dip(self, mock_mkdir):
        ProcessTask.objects.create(
            name=self.task,
            args=['new dip'],
        ).run().get()

        mock_mkdir.assert_called_once()
        self.assertTrue(InformationPackage.objects.filter(package_type=InformationPackage.DIP).exists())

    @mock.patch('workflow.tasks.os.mkdir')
    def test_with_object_identifier_value(self, mock_mkdir):
        ProcessTask.objects.create(
            name=self.task,
            args=['new dip'],
            params={
                'object_identifier_value': 'myobjid'
            },
        ).run().get()

        mock_mkdir.assert_called_once()
        self.assertTrue(InformationPackage.objects.filter(
            package_type=InformationPackage.DIP, object_identifier_value='myobjid'
        ).exists())

    @mock.patch('workflow.tasks.os.mkdir')
    def test_with_orders(self, mock_mkdir):
        user = User.objects.create(username="admin")

        order1 = Order.objects.create(label='first', responsible=user)
        order2 = Order.objects.create(label='second', responsible=user)

        ProcessTask.objects.create(
            name=self.task,
            args=['new dip'],
            params={
                'orders': [order1, order2]
            },
        ).run().get()

        mock_mkdir.assert_called_once()

        ip = InformationPackage.objects.filter(package_type=InformationPackage.DIP)
        self.assertTrue(ip.exists())
        self.assertIn(order1, ip.get().orders.all())
        self.assertIn(order2, ip.get().orders.all())


class CreateDIPTestCase(TransactionTestCase):
    def setUp(self):
        self.orders = Path.objects.create(entity='orders', value='orders').value
        self.task = "workflow.tasks.CreateDIP"
        self.ip = InformationPackage.objects.create(
            state='initial', object_path='workarea',
            package_type=InformationPackage.DIP
        )
        self.user = User.objects.create(username="admin")

    @mock.patch('workflow.tasks.shutil.copytree')
    def test_no_orders(self, mock_copy):
        ProcessTask.objects.create(
            name=self.task,
            args=[str(self.ip.pk)],
        ).run().get()

        mock_copy.assert_not_called()
        self.ip.refresh_from_db()
        self.assertEqual(self.ip.state, 'Created')

    @mock.patch('workflow.tasks.shutil.copytree')
    def test_with_order(self, mock_copy):
        order = Order.objects.create(label='foo', responsible=self.user)
        self.ip.orders.add(order)

        ProcessTask.objects.create(
            name=self.task,
            args=[str(self.ip.pk)],
        ).run().get()

        mock_copy.assert_called_once_with(
            self.ip.object_path,
            os.path.join(self.orders, str(order.pk), self.ip.object_identifier_value)
        )
        self.ip.refresh_from_db()
        self.assertEqual(self.ip.state, 'Created')

    @mock.patch('workflow.tasks.shutil.copytree')
    def test_with_multiple_orders(self, mock_copy):
        order1 = Order.objects.create(label='foo', responsible=self.user)
        order2 = Order.objects.create(label='bar', responsible=self.user)
        self.ip.orders.add(order1, order2)

        ProcessTask.objects.create(
            name=self.task,
            args=[str(self.ip.pk)],
        ).run().get()

        calls = [
            mock.call(self.ip.object_path, os.path.join(self.orders, str(order1.pk), self.ip.object_identifier_value)),
            mock.call(self.ip.object_path, os.path.join(self.orders, str(order2.pk), self.ip.object_identifier_value))
        ]
        mock_copy.assert_has_calls(calls, any_order=True)
        self.ip.refresh_from_db()
        self.assertEqual(self.ip.state, 'Created')

    @mock.patch('workflow.tasks.shutil.copytree')
    def test_not_dip(self, mock_copy):
        self.ip.package_type = InformationPackage.SIP
        self.ip.save()

        order = Order.objects.create(label='foo', responsible=self.user)
        self.ip.orders.add(order)

        with self.assertRaises(ValueError):
            ProcessTask.objects.create(
                name=self.task,
                args=[str(self.ip.pk)],
            ).run().get()

        mock_copy.assert_not_called()
        self.ip.refresh_from_db()
        self.assertEqual(self.ip.state, 'initial')


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollRobotQueueTestCase(TransactionTestCase):
    def setUp(self):
        self.datadir = tempfile.mkdtemp()

        self.label_dir = Path.objects.create(
            entity='label', value=os.path.join(self.datadir, 'label')
        )

        self.ingest = Path.objects.create(
            entity='ingest', value='ingest'
        )

        self.cache = Path.objects.create(
            entity='cache', value='cache',
        )

        try:
            os.mkdir(self.datadir)
        except OSError as e:
            if e.errno != 17:
                raise

        try:
            os.mkdir(self.label_dir.value)
        except OSError as e:
            if e.errno != 17:
                raise

        self.robot = Robot.objects.create(device='/dev/sg6')
        self.device = '/dev/nst0'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except BaseException:
            pass

    def test_no_entry(self):
        ProcessTask.objects.create(
            name='workflow.tasks.PollRobotQueue',
        ).run().get()

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_mount(self, mock_mount_task):
        mock_mount_task.side_effect = lambda *args, **kwargs: None

        user = User.objects.create()

        tape_drive = TapeDrive.objects.create(
            id=0, robot=self.robot, device=self.device
        )

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create(type=301)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        medium = StorageMedium.objects.create(
            medium_id='AAA001', storage_target=target,
            status=20, location_status=50, block_size=128,
            format=103, agent=user, tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue,
        )

        ProcessTask.objects.create(
            name='workflow.tasks.PollRobotQueue',
        ).run().get()

        robot_queue.refresh_from_db()
        tape_drive.refresh_from_db()

        mock_mount_task.assert_called_once_with(drive=tape_drive.pk, medium=medium.pk)

        self.assertEqual(robot_queue.status, 20)
        self.assertIsNone(robot_queue.robot)
        self.assertEqual(tape_drive.io_queue_entry, io_queue)

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_failing_mount(self, mock_mount_task):
        mock_mount_task.side_effect = Exception()

        user = User.objects.create()

        tape_drive = TapeDrive.objects.create(
            id=0, robot=self.robot, device=self.device
        )

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create(type=301)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        medium = StorageMedium.objects.create(
            medium_id='AAA001', storage_target=target,
            status=20, location_status=50, block_size=128,
            format=103, agent=user, tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue,
        )

        with self.assertRaises(Exception):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

        robot_queue.refresh_from_db()
        tape_drive.refresh_from_db()

        mock_mount_task.assert_called_once_with(drive=tape_drive.pk, medium=medium.pk)

        self.assertEqual(robot_queue.status, 100)
        self.assertIsNotNone(robot_queue.robot)
        self.assertEqual(tape_drive.io_queue_entry, io_queue)

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_mounting_already_mounted_medium(self, mock_mount_task):
        user = User.objects.create()

        target = StorageTarget.objects.create()

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot, tape_drive=tape_drive
        )

        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
        )

        with self.assertRaises(TapeMountedError):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

        robot_queue.refresh_from_db()

        self.assertEqual(robot_queue.status, 20)
        self.assertIsNone(robot_queue.robot)
        mock_mount_task.assert_not_called()

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_mounting_already_mounted_and_locked_medium(self, mock_mount_task):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot, tape_drive=tape_drive
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue,
        )

        with self.assertRaises(TapeMountedAndLockedByOtherError):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

        robot_queue.refresh_from_db()

        self.assertEqual(robot_queue.status, 0)
        self.assertIsNone(robot_queue.robot)
        mock_mount_task.assert_not_called()

    def test_no_robot_available(self):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue, robot=self.robot,
        )

        with self.assertRaisesRegexp(ValueError, 'No robot available'):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

    def test_no_drive_available(self):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue
        )

        with self.assertRaisesRegexp(ValueError, 'No tape drive available'):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.ingest = Path.objects.create(
            entity='ingest', value='ingest'
        )

        self.cache = Path.objects.create(
            entity='cache', value='cache',
        )

    def test_no_entry(self):
        ProcessTask.objects.create(name=self.taskname,).run().get()
        self.assertFalse(RobotQueue.objects.exists())

    def test_completed_entry(self):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=0,
            status=20
        )

        ProcessTask.objects.create(name=self.taskname,).run().get()
        self.assertFalse(RobotQueue.objects.exists())


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueWriteTapeTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

        self.robot = Robot.objects.create(device='/dev/sg6')
        self.device = '/dev/nst0'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def test_write_no_available_tape(self):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target='target')

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        TapeSlot.objects.create(slot_id=1, robot=self.robot)

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path='objpath', ip=ip,
        )

        with self.assertRaisesRegexp(ValueError, 'No tape available for allocation'):
            ProcessTask.objects.create(
                name=self.taskname,
                responsible=user,
            ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 100)
        self.assertFalse(StorageMedium.objects.filter(storage_target=target).exists())
        self.assertFalse(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())

    def test_write_unmounted_tape(self):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target='target')

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path='objpath', ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 0)
        self.assertTrue(StorageMedium.objects.filter(storage_target=target).exists())
        self.assertTrue(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())

    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.WriteToTape.run')
    def test_write_mounted_tape(self, mock_write, mock_set_file_number):
        mock_write.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None

        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user, tape_slot=tape_slot, tape_drive=tape_drive,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path=ip.object_path, ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(content_location_value='1').exists())

        mock_write.assert_called_once_with(medium=medium.pk, path=self.datadir)
        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=1)

    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.WriteToTape.run')
    def test_write_mounted_tape_twice(self, mock_write, mock_set_file_number):
        mock_write.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None

        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user, tape_slot=tape_slot, tape_drive=tape_drive,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path=ip.object_path, ip=ip,
        )

        io_queue2 = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path=ip.object_path, ip=ip,
        )

        ProcessTask.objects.create(name=self.taskname,).run().get()

        write_calls = [mock.call(medium=medium.pk, path=self.datadir), mock.call(medium=medium.pk, path=self.datadir)]
        file_num_calls = [mock.call(medium=medium.pk, num=1), mock.call(medium=medium.pk, num=2)]

        mock_write.assert_has_calls(write_calls)
        mock_set_file_number.assert_has_calls(file_num_calls)

        io_queue.refresh_from_db()
        io_queue2.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertEqual(io_queue2.status, 20)

        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(content_location_value='1').exists())
        self.assertTrue(StorageObject.objects.filter(content_location_value='2').exists())


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueReadTapeTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value=tempfile.mkdtemp(dir=self.datadir))

        self.robot = Robot.objects.create(device='/dev/sg6')
        self.device = '/dev/nst0'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_tape_without_storage_object(self, mock_read):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)

        StorageMedium.objects.create(
            storage_target=target, status=20,
            location_status=20,
            block_size=target.default_block_size,
            format=target.default_format,
            agent=user, tape_slot=tape_slot,
        )

        TapeDrive.objects.create(
            id=0, device=self.device, robot=self.robot,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=20,
            object_path=ip.object_path, ip=ip,
        )

        with self.assertRaises(ValueError):
            ProcessTask.objects.create(
                name=self.taskname,
                responsible=user,
            ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 100)
        self.assertFalse(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())
        mock_read.assert_not_called()

    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_unmounted_tape(self, mock_read):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20,
            location_status=20,
            block_size=target.default_block_size,
            format=target.default_format,
            agent=user, tape_slot=tape_slot,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, content_location_value='1', ip=ip,
            content_location_type=TAPE,
        )

        TapeDrive.objects.create(
            id=0, device=self.device, robot=self.robot,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target,
            storage_object=obj, req_type=20, object_path=ip.object_path,
            ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 0)
        self.assertTrue(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())
        mock_read.assert_not_called()

    @mock.patch('workflow.tasks.tarfile')
    @mock.patch('ESSArch_Core.tasks.CopyFile.run')
    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_mounted_tape(self, mock_read, mock_set_file_number, mock_copy, mock_tar):
        mock_read.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None
        mock_copy.side_effect = lambda *args, **kwargs: None

        mocked_tar = mock.Mock()
        mock_tar.open.return_value.__enter__.return_value = mocked_tar

        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user, tape_slot=tape_slot, tape_drive=tape_drive,
        )
        obj = StorageObject.objects.create(
            storage_medium=medium, content_location_value='1', ip=ip,
            content_location_type=TAPE,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target,
            storage_object=obj, req_type=20, object_path=ip.object_path,
            ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=1)
        mock_read.assert_called_once_with(medium=medium.pk, path=self.cache.value)
        mock_copy.assert_called_once_with(
            src=os.path.join(self.cache.value, ip.object_identifier_value) + '.tar',
            dst=self.datadir
        )

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())

    @mock.patch('workflow.tasks.tarfile')
    @mock.patch('ESSArch_Core.tasks.CopyFile.run')
    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_mounted_tape_twice(self, mock_read, mock_set_file_number, mock_copy, mock_tar):
        mock_read.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None
        mock_copy.side_effect = lambda *args, **kwargs: None

        mocked_tar = mock.Mock()
        mock_tar.open.return_value.__enter__.return_value = mocked_tar

        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        ip2 = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot, tape_drive=tape_drive,
        )

        obj = StorageObject.objects.create(
            content_location_value='1', content_location_type=TAPE, ip=ip,
            storage_medium=medium,
        )

        obj2 = StorageObject.objects.create(
            content_location_value='2', content_location_type=TAPE, ip=ip2,
            storage_medium=medium,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_medium=medium, req_type=20, ip=ip,
            storage_method_target=method_target, storage_object=obj,
            object_path=ip.object_path,
        )

        io_queue2 = IOQueue.objects.create(
            user=user, storage_medium=medium, req_type=20, ip=ip2,
            storage_method_target=method_target, storage_object=obj2,
            object_path=ip2.object_path,
        )

        ProcessTask.objects.create(
            name=self.taskname,
        ).run().get()

        read_calls = [
            mock.call(medium=medium.pk, path=self.cache.value),
            mock.call(medium=medium.pk, path=self.cache.value)
        ]
        copy_calls = [
            mock.call(src=os.path.join(self.cache.value, ip.object_identifier_value) + '.tar', dst=self.datadir),
            mock.call(src=os.path.join(self.cache.value, ip2.object_identifier_value) + '.tar', dst=self.datadir)
        ]
        file_num_calls = [
            mock.call(medium=medium.pk, num=1),
            mock.call(medium=medium.pk, num=2)
        ]

        mock_read.assert_has_calls(read_calls)
        mock_copy.assert_has_calls(copy_calls)
        mock_set_file_number.assert_has_calls(file_num_calls)

        io_queue.refresh_from_db()
        io_queue2.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertEqual(io_queue2.status, 20)
        self.assertFalse(RobotQueue.objects.exists())


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueWriteDiskTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()
        self.storagedir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

        try:
            shutil.rmtree(self.storagedir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @mock.patch('ESSArch_Core.tasks.CopyFile.run')
    def test_write(self, mock_copy):
        mock_copy.side_effect = lambda *args, **kwargs: None

        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        method = StorageMethod.objects.create(
            archive_policy=policy, type=DISK
        )
        target = StorageTarget.objects.create(target=self.storagedir)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=15,
            object_path=self.datadir, ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(storage_medium=medium, ip=ip).exists())

        mock_copy.assert_called_once_with(src=ip.object_path, dst=target.target)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueReadDiskTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()
        self.storagedir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

        try:
            shutil.rmtree(self.storagedir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @mock.patch('workflow.tasks.tarfile')
    @mock.patch('ESSArch_Core.tasks.CopyFile.run')
    def test_read(self, mock_copy, mock_tar):
        mock_copy.side_effect = lambda *args, **kwargs: None

        mocked_tar = mock.Mock()
        mock_tar.open.return_value.__enter__.return_value = mocked_tar

        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        ip = InformationPackage.objects.create(object_path=self.datadir, policy=policy)
        method = StorageMethod.objects.create(
            archive_policy=policy, type=DISK
        )
        target = StorageTarget.objects.create(target=self.datadir)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20,
            location_status=20,
            block_size=target.default_block_size,
            format=target.default_format,
            agent=user,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, content_location_value=self.storagedir, ip=ip,
            content_location_type=DISK,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=25,
            object_path=self.datadir, ip=ip, storage_object=obj,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(storage_medium=medium, ip=ip).exists())

        mock_copy.assert_any_call(src=obj.content_location_value, dst=self.cache.value)
        mock_copy.assert_any_call(
            src=os.path.join(self.cache.value, ip.object_identifier_value) + '.tar',
            dst=ip.object_path
        )
