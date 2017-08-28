#!/bin/bash

# Tested only with nvidia-settings-319.12 and nvidia-drivers-319.17 on Funtoo Linux running XFCE 4.10
#
# Requirements:
# - NVIDIA Drivers (e.g. nvidia-current in Ubuntu)
# - NVIDIA Settings (nvidia-settings in Ubuntu)
# - xrandr (used by default to determine the correct display name)
#
# This script can be used to change the brightness on systems with an NVIDIA graphics card
# that lack the support for changing the brightness (probably needing acpi backlight).
# It uses "nvidia-settings -a" to assign new gamma or brightness values to the display.
#
# "nvidia-brightness.sh" may be run from the command line or can be assigned to the brightness keys on your Keyboard
# e.g. in XFCE4.
#
# Type "nvidia-brightness.sh --help" for valid options.

usage ()
{
cat << ENDMSG
Usage: 
   nvidia-brightness.sh [ options ]
Options:
   [ -gu ] or [ --gamma-up ]         increase gamma by 0.1
   [ -gd ] or [ --gamma-down ]       decrease gamma by 0.1
   [ -bu ] or [ --brightness-up ]    increase brightness by 0.1
   [ -bd ] or [ --brightness-down ]  decrease brightness by 0.1
   [ -i ]  or [ --initialize ]       Must be run once to create the settings file
                                     (~/.nvidia-brightness.cfg).
                                     Brightness settings from ~/.nvidia-settings-rc
                                     will be used if file exists, otherwise 
                                     gamma will be set to 1.0 and brightness to 0.0
                                     (NVIDIA Standard).
   [ -l ]  or [ --load-config ]      Load current settings from ~/.nvidia-brightness.cfg
                                     (e.g. as X11 autostart script)

Examples:
   nvidia-brightness -gd       this will decrease gamma by 0.1
   nvidia-brightness -bu -gd   this will increase brightness by 0.1 and decrease gamma by 0.1
ENDMSG
}

case $1 in 
    -h|--help)
        usage
        exit 0
esac

if [ "$1" != "-i" -a "$1" != "--initialize" ]; then
    if [ ! -f ~/.nvidia-brightness.cfg ]; then 
        echo 'You must run this script with the --initialize option once to create the settings file.'
        echo 'Type "nvidia-brightness.sh --help" for more information.';
        exit 1
    fi
fi

#### INITIALIZE ####
initialize_cfg ()
{
CONNECTED="[`xrandr | grep " connected" | awk '{ print $1 }'`]"
#CONNECTED="`cat ~/.nvidia-settings-rc  | grep RedBrightness | grep -o "\[.*]"`"
#CONNECTED="[DVI-I-1]"
#CONNECTED="[dpy:2]"
#CONNECTED="0"

if [ -f ~/.nvidia-settings-rc ]; then 
    if [ "`grep RedGamma ~/.nvidia-settings-rc`" != "" ]; then
        if [ "`grep RedBrightness ~/.nvidia-settings-rc`" != "" ]; then
            GAMMA_TEMP=`grep RedGamma= ~/.nvidia-settings-rc | sed s/^.*=//`
            BRIGHTNESS_TEMP=`grep RedBrightness= ~/.nvidia-settings-rc | sed s/^.*=//`
            NVIDIA_SETTINGS_OK=1
        fi
    fi
fi


[ "$NVIDIA_SETTINGS_OK" != "1" ] && \
GAMMA_TEMP=1.000000 \
BRIGHTNESS_TEMP=0.000000

echo "\
CONNECTED_DISPLAY=$CONNECTED
GAMMA=$GAMMA_TEMP
BRIGHTNESS=$BRIGHTNESS_TEMP" > ~/.nvidia-brightness.cfg

source ~/.nvidia-brightness.cfg

GAMMACOMMA=`echo $GAMMA | sed s/"\."/"\,"/`
BRIGHTNESSCOMMA=`echo $BRIGHTNESS | sed s/"\."/"\,"/`

nvidia-settings -n -a $CONNECTED_DISPLAY/Gamma=$GAMMACOMMA -a $CONNECTED_DISPLAY/Brightness=$BRIGHTNESSCOMMA 1>/dev/null
}

#### LOAD CONFIGURATION ####
load_cfg ()
{
source ~/.nvidia-brightness.cfg

GAMMACOMMA=`echo $GAMMA | sed s/"\."/"\,"/`
BRIGHTNESSCOMMA=`echo $BRIGHTNESS | sed s/"\."/"\,"/`

nvidia-settings -n -a $CONNECTED_DISPLAY/Gamma=$GAMMACOMMA -a $CONNECTED_DISPLAY/Brightness=$BRIGHTNESSCOMMA 1>/dev/null
}

#### GAMMA CHANGE ####
gamma_up ()
{
source ~/.nvidia-brightness.cfg

GAMMANEW=`echo $GAMMA | awk '{printf "%f", $GAMMA + 0.100000}'`

GAMMACOMMA=`echo $GAMMANEW | sed s/"\."/"\,"/`

nvidia-settings -n -a $CONNECTED_DISPLAY/Gamma=$GAMMACOMMA  1>/dev/null 

sed -i  s/.*GAMMA=.*/GAMMA=$GAMMANEW/g ~/.nvidia-brightness.cfg
}

gamma_down ()
{
source ~/.nvidia-brightness.cfg

GAMMANEW=`echo $GAMMA | awk '{printf "%f", $GAMMA - 0.100000}'`

GAMMACOMMA=`echo $GAMMANEW | sed s/"\."/"\,"/`

nvidia-settings -n -a $CONNECTED_DISPLAY/Gamma=$GAMMACOMMA  1>/dev/null

sed -i  s/.*GAMMA=.*/GAMMA=$GAMMANEW/g ~/.nvidia-brightness.cfg
}

#### BRIGHTNESS CHANGE ####
brightness_up ()
{
source ~/.nvidia-brightness.cfg

BRIGHTNESSNEW=`echo $BRIGHTNESS | awk '{printf "%f", $BRIGHTNESS + 0.100000}'`

BRIGHTNESSCOMMA=`echo $BRIGHTNESSNEW | sed s/"\."/"\,"/`

nvidia-settings -n -a $CONNECTED_DISPLAY/Brightness=$BRIGHTNESSCOMMA 1>/dev/null

sed -i  s/.*BRIGHTNESS=.*/BRIGHTNESS=$BRIGHTNESSNEW/g ~/.nvidia-brightness.cfg
}

brightness_down ()
{
source ~/.nvidia-brightness.cfg

BRIGHTNESSNEW=`echo $BRIGHTNESS | awk '{printf "%f", $BRIGHTNESS - 0.100000}'`

BRIGHTNESSCOMMA=`echo $BRIGHTNESSNEW | sed s/"\."/"\,"/`

nvidia-settings -n -a $CONNECTED_DISPLAY/Brightness=$BRIGHTNESSCOMMA 1>/dev/null

sed -i  s/.*BRIGHTNESS=.*/BRIGHTNESS=$BRIGHTNESSNEW/g ~/.nvidia-brightness.cfg
}

if [ "$3" != "" ]; then
    usage
    exit 1
fi

error_mixed_gamma ()
{
    echo "Error: [ --gamma-up ] and [ --gamma-down ] can't be used together."
}

error_mixed_brightness ()
{
    echo "Error: [ --brightness-up ] and [ --brightness-down ] can't be used together."
}


if [ "$2" != "" ]; then
    [ "$2" != "-bu" -a "$2" != "--brightness-up" -a "$2" != "-bd" -a "$2" != "--brightness-down" \
    -a "$2" != "-gu" -a "$2" != "--gamma-up" -a "$2" != "-gd" -a "$2" != "--gamma-down" ] && usage && exit 1
fi

case $1 in
    -gu|--gamma-up) 
        [ "$2" == "-gd" ] && error_mixed_gamma && exit 1
        [ "$2" == "--gamma-down" ] && error_mixed_gamma && exit 1
        gamma_up
        ;;
    -gd|--gamma-down) 
        [ "$2" == "-gu" ] && error_mixed_gamma && exit 1
        [ "$2" == "--gamma-up" ] && error_mixed_gamma && exit 1
        gamma_down
        ;;
    -bu|--brightness-up) 
        [ "$2" == "-bd" ] && error_mixed_brightness && exit 1
        [ "$2" == "--brightness-down" ] && error_mixed_brightness && exit 1
        brightness_up
        ;;
    -bd|--brightness-down) 
        [ "$2" == "-bu" ] && error_mixed_brightness && exit 1
        [ "$2" == "--brightness-up" ] && error_mixed_brightness && exit 1
        brightness_down
        ;;
    -h|--help) 
        usage
        exit 0
        ;;
    -i|--initialize)
        if [ "$2" != "" ]; then usage; exit 1; fi   
        initialize_cfg
        exit 0
        ;;
    -l|--load-config)
        if [ "$2" != "" ]; then usage; exit 1; fi   
        load_cfg
        exit 0
        ;;
    *) 
        usage
        exit 1
esac

case $2 in
    -gu|--gamma-up) 
        gamma_up
        ;;
    -gd|--gamma-down) 
        gamma_down
        ;;
    -bu|--brightness-up) 
        brightness_up
        ;;
    -bd|--brightness-down) 
        brightness_down
        ;;
    -h|--help) 
        usage
        exit 0
        ;;
    "")
        ;;
    *) 
        usage
        exit 1
esac

