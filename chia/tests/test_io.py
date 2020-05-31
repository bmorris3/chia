import pytest
import numpy as np

from astropy.utils.data import download_file

from ..io import EchelleSpectrum

lkca4_id = "1x3nIg1P5tYFQqJrwEpQU11XQOs3ImH3v"
proxima_id = "1I7E1x1XRjcxXNQXiuaajb_Jz7Wn2N_Eo"

base_url = "https://drive.google.com/uc?export=download&id={0}"

lkca4_url = base_url.format(lkca4_id)
proxima_url = base_url.format(proxima_id)


@pytest.mark.remote_data
@pytest.mark.parametrize("url,", [
    lkca4_url,
    proxima_url,
])
def test_ingest_e2ds(url):
    spectrum_path = download_file(url)
    spectrum = EchelleSpectrum.from_e2ds(spectrum_path)

    assert hasattr(spectrum.orders[0], 'wavelength')
    assert hasattr(spectrum.orders[0], 'flux')
    assert len(spectrum.orders) == 72
    assert spectrum.header['DATE-OBS'].startswith('2004')
    assert (spectrum.orders[1].wavelength.mean() >
            spectrum.orders[0].wavelength.mean())


@pytest.mark.remote_data
@pytest.mark.parametrize("url,", [
    lkca4_url,
    proxima_url,
])
def test_continuum_normalize(url):
    spectrum_path = download_file(url)
    spectrum = EchelleSpectrum.from_e2ds(spectrum_path)
    spectrum.continuum_normalize()

    # Confirm that each echelle order is roughly continuum normalized (roughly
    # distributed about unity):
    for order in spectrum.orders:
        assert abs(np.median(order.flux) - 1) < 1
