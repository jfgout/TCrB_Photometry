# TCrB_Photometry
Tracking T CrB through automatic photometry

The goal of this repository is to share the code that I use to automatically track the brightness of T CrB. T CrB is a recurrent nova with an about 80 years period. It is expected to go nova again in the near future (see here: [https://en.wikipedia.org/wiki/T_Coronae_Borealis](https://en.wikipedia.org/wiki/T_Coronae_Borealis) ).  

I use an Orion ED80T CF refractor (480mm focal length) with an Atik 414EX, V/B/R/I/U Johnson/Cousins filters and an Avalon M-Zero to acquire data from Starkville, MS. Here is an example of the images taken in the V band (T CrB is centered in the image):

![Example field of view](https://github.com/jfgout/TCrB_Photometry/blob/main/images/t_crb_v.jpg)  


## General strategy

Images are obtained with KStars/Ekos, using a sequence that rotates between V, B, R, I and U bands. Every time a new image is taken in the V band, it is automatically plate-solved and photometry is performed. If the estimated magnitude of T CrB crosses a certain threshold, a message is sent to a Telegram channel to alert me of the abnormal behavior. The entire code runs on a mini PC running Linux Ubuntu 22.04. 

**Checking for new files**: I use **inotifywait** to detect new files in the folder with V images. See "check-new-files.sh" in the src folder. You would have to modify the "TARGET" variable to point at the folder in which new images are stored. For every new image, the script calls the "check-tcrb.py" script to obtain the magnitude of T CrB. Note that this script depends on "jf_photometry.py" and "direct_solver.py", which are also provided.  
If the magnitude crosses a certain threshold (set at 9.1 here), the program will send a telegram message, using the "send-telegram-message.py" script.  I use the app "awake now" to alert me if I receive a Telegram message with the key word "TCrB_ALERT" so that I can be alerted at night, even when my phone is in silent mode and all other notifications are silent. I want to be waken up if T CrB is crossing magnitude 9, not if I receive a random email or any other notification.  

All these programs rely on a number of Python libraries, including: photutils, requests, panda, numpy, astropy and astroquery. These can easily be installed with pipp.

## Troubleshoting

### Plate solving  

Make sure to adjust the fwhm, aperture radius, field_of_view and other parameters in "check-tcrb.py" to fit your setup. The most important one is likely to be the field of view (in arc minutes). You can also adjust the limits for brightest and dimmest comparison stars to use in the photometry.
