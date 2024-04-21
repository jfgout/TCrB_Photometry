import requests, math, glob
import pandas as pd
import numpy as np
from photutils.detection import DAOStarFinder
from photutils.aperture import aperture_photometry
from photutils.aperture import CircularAperture

from astropy.stats import mad_std
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u
import matplotlib.pyplot as plt


from astroquery.simbad import Simbad
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import jf_photometry as jf
import direct_solver as ds

import sys

def main():
    # DEFINE INPUT
    #FITS_FILE = '/home/jfgout/Pictures/t_crb/Light/2024-02-15/solved/t_crb_Light_2024-02-15T03-53-57_3_secs_001.fits'
    #FITS_FILE = '/home/jfgout/Pictures/t_crb/2024-02-22/Light/V/t_crb_Light_V2024-02-22T04-37-50_107.fits'
    #FITS_FILE = '/home/jfgout/Pictures/t_crb/2024-02-22/Light/V/mini/solved/t_crb_Light_V2024-02-22T04-36-59_104.fits'
    warnings.filterwarnings('ignore')
    FITS_FILE = sys.argv[1]
    fwhm = 1.0
    aperture_radius = 4.0
    source_snr = 10
    min_number_of_sources = 15
    field_of_view = 90
    targetName = 'T CrB'
    #targetName = 'HD 143352'
    BRIGHTEST_COMPARISON_STAR_MAG = 8.0
    DIMMEST_COMPARISON_STAR_MAG = 13.0

    hdulist = fits.open(FITS_FILE)
    success, number_sources_found, wcs = ds.direct_solve(hdulist, min_number_of_sources = min_number_of_sources, source_snr = source_snr)
    #print("Soler results:")
    #print(wcs)
    if success == False:
        print("Solving failed with " + str(number_sources_found) + " sources found for " + FITS_FILE)
        return ""
    else:
        target_instrumental_magnitude, target_magnitude, residuals = jf.getMagnitudeFromHDU(hdulist, wcs, targetName, field_of_view, fwhm, source_snr, aperture_radius, BRIGHTEST_COMPARISON_STAR_MAG, DIMMEST_COMPARISON_STAR_MAG)
        print(str(target_magnitude) + " " + FITS_FILE)
        return target_magnitude

main()
