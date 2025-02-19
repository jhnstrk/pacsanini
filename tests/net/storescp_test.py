# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the storescp class functions correctly."""
import os

import pytest

from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts

from pacsanini.models import StorageSortKey
from pacsanini.net.storescp import StoreSCPServer, run_server


@pytest.fixture(scope="module")
def dcm(dicom_path: str):
    """Return a test DICOM file."""
    return dcmread(dicom_path, stop_before_pixels=True)


@pytest.mark.net
class TestStoreSCPServer:
    """Test the overall storescp server module."""

    def setup(self):  # pylint: disable=attribute-defined-outside-init
        """Run prior to every test."""
        self.server: StoreSCPServer = None

    def teardown(self):
        """Ensure that the server is stopped after each test."""
        if self.server is not None:
            self.server.shutdown()

    def test_storescp_server_patient_sort(self, tmpdir: os.PathLike, dcm):
        """Test that the storescp server can correcyl persist files."""
        dcm_node = {"ip": "localhost", "port": 11112, "aetitle": "myserver"}
        self.server = run_server(
            dcm_node, data_dir=str(tmpdir), sort_by=StorageSortKey.PATIENT
        )
        assert self.server.scp

        ae = AE()
        assoc = ae.associate("localhost", 11112, contexts=StoragePresentationContexts)
        assert assoc.is_established

        status = assoc.send_c_store(dcm)
        assert status.Status == 0

        assoc.release()

        dest_path = os.path.join(
            str(tmpdir),
            dcm.PatientID,
            dcm.StudyInstanceUID,
            dcm.SeriesInstanceUID,
            dcm.SOPInstanceUID,
        )
        dest_path += ".dcm"
        assert os.path.exists(dest_path)

        written_dcm = dcmread(dest_path, stop_before_pixels=True)
        assert written_dcm.SOPClassUID == dcm.SOPClassUID

    def test_storescp_server_study_sort(self, tmpdir: os.PathLike, dcm):
        """Test that the storescp server can correcyl persist files."""
        dcm_node = {"ip": "localhost", "port": 11112, "aetitle": "myserver"}
        self.server = run_server(
            dcm_node, data_dir=str(tmpdir), sort_by=StorageSortKey.STUDY
        )
        assert self.server.scp

        ae = AE()
        assoc = ae.associate("localhost", 11112, contexts=StoragePresentationContexts)
        assert assoc.is_established

        status = assoc.send_c_store(dcm)
        assert status.Status == 0

        assoc.release()

        dest_path = os.path.join(
            str(tmpdir), dcm.StudyInstanceUID, dcm.SeriesInstanceUID, dcm.SOPInstanceUID
        )
        dest_path += ".dcm"
        assert os.path.exists(dest_path)

    def test_storescp_server_image_sort(self, tmpdir: os.PathLike, dcm):
        """Test that the storescp server can correcyl persist files."""
        dcm_node = {"ip": "localhost", "port": 11112, "aetitle": "myserver"}
        self.server = run_server(
            dcm_node, data_dir=str(tmpdir), sort_by=StorageSortKey.IMAGE
        )
        assert self.server.scp

        ae = AE()
        assoc = ae.associate("localhost", 11112, contexts=StoragePresentationContexts)
        assert assoc.is_established

        status = assoc.send_c_store(dcm)
        assert status.Status == 0

        assoc.release()

        dest_path = os.path.join(str(tmpdir), dcm.SOPInstanceUID)
        dest_path += ".dcm"
        assert os.path.exists(dest_path)
