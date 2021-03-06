import numpy as np
from astropy.io import fits
from scipy.stats import binned_statistic
import matplotlib.pyplot as plt

__all__ = ['EchelleSpectrum', 'Spectrum']


def read_wavelengths_from_HARPS_header(h):
    """
    This reads the wavelength solution from the HARPS header keywords that
    encode the coefficients as a 4-th order polynomial.

    Courtesy of Jens Hoeijmakers, 2019.

    Parameters
    ----------
    h : `~astropy.io.fits.Header`
        FITS header object

    Returns
    -------
    wave : `~numpy.ndarray`
        Wavelength array in Angstroms
    """
    npx = h['NAXIS1']
    no = h['NAXIS2']
    x = np.arange(npx)
    wave = np.zeros((npx, no))

    key_counter = 0
    for i in range(no):
        lam = x*0.0
        for j in range(4):
            lam += h['ESO DRS CAL TH COEFF LL{0}'.format(key_counter)]*x**j
            key_counter += 1
        wave[:, i] = lam
    wave = wave.T
    return wave


def read_wavelengths_from_HARPS_N_header(h):
    """
    This reads the wavelength solution from the HARPS header keywords that
    encode the coefficients as a 4-th order polynomial.

    Courtesy of Jens Hoeijmakers, 2019.

    Parameters
    ----------
    h : `~astropy.io.fits.Header`
        FITS header object

    Returns
    -------
    wave : `~numpy.ndarray`
        Wavelength array in Angstroms
    """
    npx = h['NAXIS1']
    no = h['NAXIS2']
    x = np.arange(npx)
    wave = np.zeros((npx, no))

    key_counter = 0
    for i in range(no):
        lam = x*0.0
        for j in range(4):
            lam += h['TNG DRS CAL TH COEFF LL{0}'.format(key_counter)]*x**j
            key_counter += 1
        wave[:, i] = lam
    wave = wave.T
    return wave


class Spectrum(object):
    """
    Simple spectrum object.
    """
    def __init__(self, wavelength, flux, header=None):
        """

        Parameters
        ----------
        wavelength : `~numpy.ndarray`
            Wavelengths in Angstroms
        flux : `~numpy.ndarray`
            Fluxes
        """
        self.wavelength = wavelength
        self.flux = flux
        self.header = header

    def plot(self, ax=None, **kwargs):
        """
        Plot the spectrum

        Parameters
        ----------
        ax : `~matplotlib.axes.Axes` (optional)
            Axis object
        kwargs : dict
            Keyword arguments to pass to the `plot` command

        Returns
        -------
        ax : axis
        """
        if ax is None:
            ax = plt.gca()

        ax.plot(self.wavelength, self.flux, **kwargs)

        return ax


class EchelleSpectrum(object):
    """
    Echelle spectrum object, which stores each order as a
    `~hipparchus.Spectrum` object.
    """
    def __init__(self, orders, header=None):
        self.orders = orders
        self.header = header

    @classmethod
    def from_e2ds(cls, path, harps=True):
        """
        Read HARPS(-N) spectrum from an E2DS FITS file.

        Parameters
        ----------
        path : str
            Path to FITS file
        harps : bool (optional)
            True for HARPS, False for HARPS-N

        Returns
        -------
        sp : `~hipparchus.EchelleSpectrum`
            Echelle spectrum object
        """
        data = fits.getdata(path)
        header = fits.getheader(path)
        if harps:
            wl = read_wavelengths_from_HARPS_header(header)
        else:
            wl = read_wavelengths_from_HARPS_N_header(header)

        spectra = []
        for i in range(data.shape[0]):
            sp = Spectrum(wl[i, :], data[i, :], header)
            spectra.append(sp)

        return cls(orders=sorted(spectra, key=lambda x: x.wavelength.mean()),
                   header=header)

    def plot(self, ax=None, **kwargs):
        """
        Plot the echelle spectrum

        Parameters
        ----------
        ax : `~matplotlib.axes.Axes` (optional)
            Axis object
        kwargs : dict
            Keyword arguments to pass to the `plot` command

        Returns
        -------
        ax : axis
        """
        if ax is None:
            ax = plt.gca()

        for sp in self.orders:
            ax.plot(sp.wavelength, sp.flux, **kwargs)

        return ax

    def continuum_normalize(self, bins=5, order=2):
        """
        Normalize the continuum in each echelle order to unity.

        Parameters
        ----------
        bins : int
            Number of bins used to compute maxes for continuum tracing
        order : int
            Polynomial order fit to the binned-maxes
        """
        for spectrum in self.orders:

            wl = spectrum.wavelength

            # Bin spectrum, take max in wide bins to approximate the continuum
            bs = binned_statistic(wl - wl.mean(), spectrum.flux, bins=bins,
                                  statistic='median')
            bincenters = 0.5 * (bs.bin_edges[1:] + bs.bin_edges[:-1])

            fit = np.polyval(np.polyfit(bincenters, bs.statistic, order),
                             wl - wl.mean())
            spectrum.flux /= fit

    def nearest_order(self, wavelength):
        """
        Return the order with the central wavelength nearest to `wavelength`.

        Parameters
        ----------
        wavelength : float
            Reference wavelength

        Returns
        -------
        spectrum : `~hipparchus.Spectrum`
        """
        min_ind = np.argmin(np.abs([sp.wavelength.mean() - wavelength
                                    for sp in self.orders]))

        return self.orders[min_ind]
