import astrometry


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

import sys
import statistics


def direct_solve(hdulist, min_number_of_sources = 20, fwhm = 4.0, source_snr = 20, field_of_view = 90, lower_sampling = 2.7, upper_sampling = 2.8, raHint = 239.87, decHint = 25.92):

    verbose = False

    solver = astrometry.Solver(
        astrometry.series_4200.index_files(
            cache_directory="/home/jfgout/.local/share/kstars/astrometry/",
            scales={5,6,7,8,9},
        )
    )
    
    data = hdulist[0].data.astype(float)
    header = hdulist[0].header
    wcs = WCS(header)
    bkg_sigma = mad_std(data)
    daofind = DAOStarFinder(fwhm=fwhm, threshold=source_snr*bkg_sigma)
    sources = daofind(data)
    nb_sources_detected = len(sources)
    roundness1 = abs(statistics.median(sources['roundness1']))
    roundness2 = abs(statistics.median(sources['roundness2']))

    RA_CENTER = wcs.wcs.crval[0]
    DEC_CENTER = wcs.wcs.crval[1]
    
    if verbose == True:
        print("source_snr: " + str(source_snr))
        print( str(len(sources)) + " sources found.")
        #print(sources)
        print("roundness 1: ", roundness1)
        print("roundness 2: ", roundness2)

    if nb_sources_detected < min_number_of_sources or roundness1 > 0.8 or roundness2 > 0.5:
        if verbose == True:
            print("Aborting due to number of sources or roundness...")
        return False, nb_sources_detected, wcs
    else:
        if verbose == True:
            print("Number of sources and roundness OK. Proceeding to solving...")
        
    xcenters = np.array(sources['xcentroid'])
    ycenters = np.array(sources['ycentroid'])
    positions = [(xcenters[i], ycenters[i]) for i in range(len(xcenters))]
    stars = positions
    #print(stars)



    solution = solver.solve(
        stars=stars,
        size_hint=astrometry.SizeHint(lower_arcsec_per_pixel=2.7, upper_arcsec_per_pixel=2.8,),
        position_hint=astrometry.PositionHint(
            ra_deg=RA_CENTER,
            dec_deg=DEC_CENTER,
            radius_deg=3.0,
        ),
        solution_parameters=astrometry.SolutionParameters(
            logodds_callback=lambda logodds_list: (
                astrometry.Action.STOP
                if logodds_list[0] > 100.0
                else astrometry.Action.CONTINUE
            ),
        ),
    )

    if solution.has_match():
        #print(f"{solution.best_match().center_ra_deg=}")
        #print(f"{solution.best_match().center_dec_deg=}")
        #print(f"{solution.best_match().scale_arcsec_per_pixel=}")
        wcs = solution.best_match().astropy_wcs()
        return True, nb_sources_detected, wcs
    else:
        return False, nb_sources_detected, wcs



