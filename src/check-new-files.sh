#!/bin/bash

TARGET=/home/jfgout/Pictures/t_crb/2024-04-15/Light/V/

inotifywait -m -e create -e moved_to --format "%f" $TARGET \
| while read FILENAME
do
    echo Detected $FILENAME
    cd $TARGET
    fName=`basename $FILENAME`
    magnitude=$(python /home/jfgout/Astro/Scripts/jf-photometry/check-tcrb.py $TARGET/$FILENAME)
    echo "Magnitude: $magnitude"
    if (( $(echo "$magnitude < 9.1" | bc -l) )); then
	echo "SEND ALARM!"
	python /home/jfgout/Astro/Scrtips/jf-photometry/send-telegram-message.py $magnitude
    fi
done
