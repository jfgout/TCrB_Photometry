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
import matplotlib
import matplotlib.pyplot as plt


from astroquery.simbad import Simbad
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# FUNCTION TO DOWNLOAD COMP CHART FROM AAVSO:
def get_comp_stars(ra,dec,filter_band='V',field_of_view=18.5):
    result = []
    vsp_template = 'https://www.aavso.org/apps/vsp/api/chart/?format=json&fov={}&maglimit=18.5&ra={}&dec={}'
    #print(vsp_template.format(field_of_view, ra, dec))
    r = requests.get(vsp_template.format(field_of_view, ra, dec))
    chart_id = r.json()['chartid']
    #print('Downloaded Comparison Star Chart ID {}'.format(chart_id))
    for star in r.json()['photometry']:
        comparison = {}
        comparison['auid'] = star['auid']
        comparison['ra'] = star['ra']
        comparison['dec'] = star['dec']
        for band in star['bands']:
            if band['band'] == filter_band:
                comparison['vmag'] = band['mag']
                comparison['error'] = band['error']
        result.append(comparison)
    return result, chart_id


def getMagnitudeFromResults(results, BRIGHTEST_COMPARISON_STAR_MAG, DIMMEST_COMPARISON_STAR_MAG):
    # Compute the ensemble:
    # now perform ensemble photometry by linear regression of the comparison stars' instrumental mags
    to_linear_fit = results.query('auid != "target" and vmag > {} and vmag < {}'.format(BRIGHTEST_COMPARISON_STAR_MAG, DIMMEST_COMPARISON_STAR_MAG)) 
    x = to_linear_fit['instrumental_mag'].values
    y = to_linear_fit['vmag'].values
    fit, residuals, rank, singular_values, rcond = np.polyfit(x, y, 1, full=True)
    fit_fn = np.poly1d(fit) 
    # fit_fn is now a function which takes in x and returns an estimate for y, 
    # we use this later to calculate the target mag

    # Use the ensembl fit to compute mag:
    # fit_fn from above is a function which takes in x and returns an estimate for y, lets feed in the 'target' instrumental mag
    target_instrumental_magnitude = results[results.auid=='target']['instrumental_mag'].values[0]
    target_magnitude = fit_fn(target_instrumental_magnitude)
    #print('Magnitude estimate: {} error from residuals {}'.format(target_magnitude, residuals))
    #x = np.append(x,target_instrumental_magnitude)
    #y = np.append(y,target_magnitude)
    return target_instrumental_magnitude, target_magnitude, residuals


def getMagnitudeFromHDU(hdulist, wcs, targetName, field_of_view=90, fwhm=4, source_snr = 20, aperture_radius = 4, BRIGHTEST_COMPARISON_STAR_MAG = 2, DIMMEST_COMPARISON_STAR_MAG = 18):
    data = hdulist[0].data.astype(float)
    header = hdulist[0].header
    #wcs = WCS(header)

    side_margin = 5
    max_x = header['NAXIS1']
    max_y = header['NAXIS2']

    bkg_sigma = mad_std(data)    
    daofind = DAOStarFinder(fwhm=fwhm, threshold=source_snr*bkg_sigma)    
    sources = daofind(data)


    astroquery_results = Simbad.query_object(targetName)
    TARGET_RA = str(astroquery_results[0]['RA'])
    TARGET_DEC = str(astroquery_results[0]['DEC']).replace('+','').replace('-','')
    results, chart_id = get_comp_stars(TARGET_RA, TARGET_DEC, field_of_view = field_of_view)
    results.append({'auid': 'target', 'ra': TARGET_RA, 'dec': TARGET_DEC})
    
    # FIND THE SOURCES THAT CORRESPOND TO COMP STARS:
    for star in results:
        star_coord = SkyCoord(star['ra'],star['dec'], unit=(u.hourangle, u.deg))
        xy = SkyCoord.to_pixel(star_coord, wcs=wcs, origin=1)
        x = xy[0].item(0)
        y = xy[1].item(0)
        if( x < side_margin or y < side_margin or x > (max_x - side_margin) or y > (max_y - side_margin) ):
            #print("Need to remove star from results (outside field of view: ", x, " - ", y)
            isOutside = True
        for source in sources:
            if(source['xcentroid']-6.0 < x < source['xcentroid']+6.0 and source['ycentroid']-6.0 < y < source['ycentroid']+6.0):
                star['x'] = x
                star['y'] = y
                star['peak'] = source['peak']
                fount_it = True

    results = pd.DataFrame(results)
    results = results.dropna(subset=['x', 'y', 'peak'])


    # PERFORM APERTURE PHOTOMETRY AND ADD TO RESULTS:
    positions = np.transpose((results['x'], results['y'])    )
    apertures = CircularAperture(positions, r=aperture_radius)    
    phot_table = aperture_photometry(data, apertures)     
    results['aperture_sum'] = phot_table['aperture_sum']
    # add a col with calculation for instrumental mag
    results['instrumental_mag'] = results.apply(lambda x: -2.5 * math.log10(x['aperture_sum']), axis = 1)

    
    target_instrumental_magnitude, target_magnitude, residuals = getMagnitudeFromResults(results, BRIGHTEST_COMPARISON_STAR_MAG, DIMMEST_COMPARISON_STAR_MAG)
    return target_instrumental_magnitude, target_magnitude, residuals




