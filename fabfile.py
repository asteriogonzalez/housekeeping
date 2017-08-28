#! /usr/bin/env python
# -*- coding: utf-8  -*-

#try:
    ## pylint: disable-msg=W0611
    #import wingdbstub
#except ImportError:
    #print "No Remote debug support found"

from fabric.api import *
from fabric.contrib.files import *
from fabric.contrib.console import *

import time
import re
import os

env.hosts = [
]
env.passwords = {
}
env.sudo_passwords = {
}

env.roledefs.update({
    'mac': ['agp@mac', ],
    'ubuntu': ['agp@ubuntutest', ],
    #'ubuntu': ['agp@mac', 'agp@ubuntutest'],
    'home': [],
    'work': [''],
})

env.colorize_errors = True
env.connection_attempts = 10
env.command_timeout = 300
env.timeout = 10
env.keepalive = False

#---------------------------------------------------------------------
# Helpers
#---------------------------------------------------------------------

DOWNLOADS='/tmp/downloads'
APT_SOURCE_LIST = '/etc/apt/sources.list'
def add_source_list(line, update=True):
    "Add a repository to APT source.list"
    if not contains(APT_SOURCE_LIST, line):
        append(APT_SOURCE_LIST, line, partial=True, use_sudo=True)
        if update:
            sudo('apt-get update')

        return 1
    return 0

def dpkg(*args):
    with  warn_only():
        result = sudo('DEBIAN_FRONTEND=noninteractive dpkg -i %s' % ' '.join(args))
        if not result.failed:
            return result

        result = sudo('apt-get --fix-broken install -y')
        if result.failed:
            return result
        result = sudo('dpkg --configure -a')
        return result

def apt(*args):
    errors = True
    while errors:
        for attempt in range(10):
            errors = False
            try:
                if errors:
                    dpkg('--configure -a')
                    sudo('apt-get --fix-broken install -y')

                sudo('apt -y %s' % ' '.join(args))
                break
            except SystemExit, why:
                print why.__class__
                print why
                print "Attemp %s, Waiting 20 secs before retrying ..." % attempt
                errors = True
                time.sleep(20)
        else:
            reboot(wait=120)


def apt_key(url):
    sudo('wget -O - %s | sudo apt-key add -' % url)

def apt_source(name, url):
    sudo('echo "%s" >> /etc/apt/sources.list.d/%s.list' % (url, name))


def easy_install(*args):
    sudo('easy_install %s' % ' '.join(args))

def pip_install(*args):
    sudo('pip install -U %s' % ' '.join(args), shell=True)

def wget_install_deb(url):
    wget(url)
    filename = url.split('/')[-1]

    for attempts in range(10):
        result = dpkg('%s/%s' % (DOWNLOADS, filename))
        if 'lock' in result:
            print "Waiting for other apt process to finish ..."
            time.sleep(10)
            continue
        break


def wget(url):
    if not exists(DOWNLOADS):
        sudo('mkdir -p %s' % DOWNLOADS)

    sudo('wget -c -P %s %s' % (DOWNLOADS, url))

def safe_cp(source, remote):
    if os.path.exists(source):
        put(source, remote)


def configure_apt():
    "Configure APT source.list file"

    # comment(APT_SOURCE_LIST, '^deb cdrom:')
    #lines = [
    #    'deb http://ftp.us.debian.org/debian/ squeeze main non-free contrib',
    #    'deb-src http://ftp.us.debian.org/debian/ squeeze main non-free contrib',
    #    'deb http://security.debian.org/ squeeze/updates main contrib non-free',
    #    'deb-src http://security.debian.org/ squeeze/updates main contrib non-free',
    #    'deb http://ftp.us.debian.org/debian/ squeeze-updates main contrib non-free',
    #    'deb-src http://ftp.us.debian.org/debian/ squeeze-updates main contrib non-free'
    #    ]

    #n = 0
    #for line in lines:
    #    n += add_source_list(line, update=False)

    #if False or n > 0:
    #    run('apt-get update')

@task
def ssh_keys():
    "Add SSH keys to root user"


#---------------------------------------------------------------------
# Tasks
#---------------------------------------------------------------------
@roles('ubuntu', 'home', )
@task
def base():
    "Common base system for any host"
    execute(configure_apt)

    # 1st of all
    apt('update')
    #apt('upgrade')
    #reboot(wait=120)

    apt('install', 'etckeeper')
    apt('install', 'python-pip')
    apt('install', 'rsync screen')

    # installers
    #apt('install', 'python-setuptools')  # easy_install
    #easy_install('pip')

    # dev and admin support
    #apt('install', 'python-tk')
    #apt('install', 'git-core git-gui git-doc subversion')

    # system maintenance
    #apt('install', 'debian-archive-keyring')
    #apt('install', 'etckeeper')

    #run('git config --global user.name "agp"')
    #run('git config --global user.email asterio.gonzalez@gmail.com')

    # java
    #apt('install', 'openjdk-6-jre')

    # crypto
    #apt('install', 'libgmp3-dev')
    #apt('install', 'cryptsetup')

    # misc
    apt('install', 'rar zip p7zip bzip2')
    #apt('install', 'mysql-client')
    #apt('install', 'dos2unix')
    #apt('install', 'python-argparse')
    apt('install', 'meld')

    # power management
    #apt('install', 'powermgmt-base')
    #apt('install', 'cpufrequtils')
    #apt('install', 'fancontrol')
    #apt('install', 'fancontrol')




@roles('ubuntu', 'home')
@task
def admin():
    "Install admin tools"
    # search packages that contais a file
    apt('install', 'apt-file')
    sudo('apt-file update')

    # users and other stuff
    #apt('install', 'gnome-system-tools')
    #apt('install', 'synaptic')

    # compilers
    #apt('install', 'gcc')

    # remote access
    #apt('install', 'gnome-rdp')
    #apt('install', 'rdesktop')
    #apt('install', 'grdesktop')
    #apt('install', 'vino')


    # misc
    #apt('install', 'enscript')
    #apt('install', 'iptraf')

    apt('install', 'net-tools')




@roles('ubuntu', 'home', )
@task
def install_opera():
    wget_install_deb('http://download3.operacdn.com/pub/opera/desktop/47.0.2631.55/linux/opera-stable_47.0.2631.55_amd64.deb')

@roles('ubuntu', 'home', )
@task
def install_vivaldi():
    apt_source('vivaldi', 'deb http://repo.vivaldi.com/stable/deb/ stable main')
    apt_key('http://repo.vivaldi.com/stable/linux_signing_key.pub')

    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1397BC53640DB551')

    apt('update')
    apt('install vivaldi-stable')

@roles('ubuntu', 'home', )
@task
def install_chrome():
    wget_install_deb('https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb')


@roles('ubuntu', 'home', )
@task
def install_wingide():
    # for 32-kernel version (otherwise debuger will not work!)
    # wget_install_deb('http://wingware.com/pub/wingide/5.1.12/wingide5_5.1.12-1_i386.deb')

    # for 64-kernel version
    wget_install_deb('http://wingware.com/pub/wingide/5.1.12/wingide5_5.1.12-1_amd64.deb')

    with warn_only():
        run('mkdir ~/.wingide5')
        run('mkdir ~/.wingide5/scripts')

    put('wingide5/preferences', '~/.wingide5/preferences')

    # PEP8
    pip_install('pep8')
    # wget('https://bitbucket.org/sdeibel/pep8panel-wingware/get/2029431c0288.zip')

    put('wingide5/scripts/pep8panel.py', '~/.wingide5/scripts/')

@roles('ubuntu', 'home', )
@task
def remove_tracking():
    sudo('apt-get remove -y zeitgeist zeitgeist-core zeitgeist-datahub python-zeitgeist rhythmbox-plugin-zeitgeist geoclue geoclue-ubuntu-geoip geoip-database')


@roles('ubuntu', 'home', )
@task
def protection():
    # misc
    apt('install', 'clamav clamav-freshclam')
    apt('install', 'meld')


@roles('ubuntu')
@task
def documentation():
    ## sphinx
    #apt('install', 'python-simplejson')
    #apt('install', 'texlive-latex-base texlive-extra-utils')
    #easy_install('Sphinx')

    ## rst
    #apt('install', 'python-pydot')
    #apt('install', 'rst2pdf')

    ## dicts
    #apt('install', 'ispanish ispell')

    execute(pelican)

@roles('ubuntu')
@task
def pelican():
    # pelican
    #pip_install('pelican')
    #pip_install('markdown')

    # plugins
    apt('install', 'python-bs4')   # required by some plugin
    pip_install('ipython ')
    pip_install('jupyter')

    with cd('~/Documents'):
        if exists('pelican-plugins'):
            run('rm -rf pelican-plugins')

        run('git clone --recursive https://github.com/getpelican/pelican-plugins')

    #run('git submodule add https://github.com/jakevdp/pelican-octopress-theme.git themes/octopress')


@roles('home')
@task
def hpprinter():

    apt('install', 'g++, python-dev')

    #http://sourceforge.net/projects/hplip/files/hplip/3.12.6/hplip-3.12.6.run/download
    #apt('install', 'hplip')



@roles('home')
@task
def resilio():
    filename = '/etc/apt/sources.list.d/resilio-sync.list'
    with warn_only():
        if not exists(filename):
            append(filename,
                   'deb http://linux-packages.resilio.com/resilio-sync/deb resilio-sync non-free',
                   use_sudo=True)
            sudo('wget -qO - https://linux-packages.resilio.com/resilio-sync/key.asc | sudo apt-key add -')
            sudo('apt-get update')
        apt('install', 'resilio-sync')


@roles('ubuntu')
@task
def sublimetext():
    filename = '/etc/apt/sources.list.d/sublime-text.list'
    with warn_only():
        if not exists(filename):
            append(filename,
                   'deb https://download.sublimetext.com/ apt/dev/',
                   use_sudo=True)
            sudo('wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | sudo apt-key add -')
            sudo('apt-get update')
        apt('install', 'sublime-text')

        license = 'sublime-text/License.sublime_license'
        if os.path.exists(license):
            safe_cp('sublime-text/License.sublime_license',
                    '~/.config/sublime-text-3/Local/License.sublime_license')
        else:
            print "You may set your Sublime License in %s for automatic deploying" % license


@roles('ubuntu')
@task
def desktop():
    # chrome
    apt('install', 'libcurl3 libssh2-1 xdg-utils')
    wget_install_deb('https://dl-ssl.google.com/linux/direct/google-chrome-stable_current_i386.deb')

    run('dropbox start -i')

    # graphs
    apt('install', 'a2ps')
    apt('install', 'graphviz')
    apt('install', 'imagemagick')
    apt('install', 'gimp')

    #
    # documentation
    execute(documentation)

    # fonts
    apt('install', 'ttf-mscorefonts-installer')
    #rsync -azvP /usr/share/fonts/truetype/ root@$HOST:/usr/share/fonts/truetype/

    # PIL (resize, etc)
    apt('install', 'python-imaging')

    # flashplayer
    # remove flash-player official version to avoid CPU problems.
    apt_remove('browser-plugin-gnash gnash gnash-common')

    #wget_install_deb $@ http://fpdownload.macromedia.com/get/flashplayer/current/install_flash_player_10_linux.deb flash_player
    #URL=http://fpdownload.macromedia.com/get/flashplayer/pdc/11.2.202.236/install_flash_player_11_linux.i386.tar.gz
    #URL=http://ardownload.adobe.com/pub/adobe/reader/unix/9.x/9.5.1/enu/AdbeRdr9.5.1-1_i486linux_enu.bin

    # printers
    apt('install', 'cups-pdf ghostscript-cups')
    apt('install', 'libsane-extras xsane')

    # desktop
    apt('install', 'gnome-desktop-environment')
    apt('install', 'openoffice.org')


@roles('ubuntu')
@task
def multimedia():
    # music
    # apt('install', 'rhythmbox')
    # vlc
    apt('install', 'vlc')

    # flash
    # apt('install', 'flashplugin-nonfree')


@task
@roles('ubuntu')
def virtualization():
    "Install VirtualBox"
    execute(configure_apt)

    run('wget -q http://download.virtualbox.org/virtualbox/debian/oracle_vbox.asc -O- | sudo apt-key add -')
    run('apt-get update')

    add_source_list('deb http://download.virtualbox.org/virtualbox/debian squeeze contrib')


    # download Extension Pack
    VERSION = '4.1.6'
    FILENAME = 'Oracle_VM_VirtualBox_Extension_Pack-%s.vbox-extpack' % VERSION

    apt('install', 'virtualbox-%s' % ('.'.join(VERSION.split('.')[:2])))

    wget('http://download.virtualbox.org/virtualbox/%s/%s' \
         % (VERSION, FILENAME))

    INSTALLER = ' %s/%s' % (DOWNLOADS, FILENAME)
    run('VBoxManage extpack install %s' % INSTALLER)

    # fix USB problem in debian
    USB_CONFIG = '/etc/udev/rules.d/10-vboxdrv.rules'
    sed(USB_CONFIG, 'GROUP="root"', 'GROUP="vboxusers"')

    run('adduser agp vboxusers')
    run('adduser lola vboxusers')


    reboot()



#---------------------------------------------------------------------
# Ubuntu specific tasks
#---------------------------------------------------------------------
@task
@roles('ubuntu')
def restricted_drivers():
    "Install restricted drivers"
    with warn_only():
        sudo('ubuntu-drivers autoinstall')
        reboot(wait=120)
    #reboot(command='tmux new-session -d "sleep 1; reboot;"')
    print run('hostname')


#---------------------------------------------------------------------
# NVIDIA Tasks
#---------------------------------------------------------------------
@roles('ubuntu')
@task
def nvidia():
    "Helps to install NDIVIA drivers as much as possible ..."
    execute(configure_apt)

    apt('install', 'binutils gcc-4.3 make build-essential')
    apt('install', 'linux-headers-$(uname -r)')

    # set the right GCC for compile the driver in kernel
    GCC = '/usr/bin/gcc'
    VERSION = '4.3'

    make_link = True
    if exists(GCC):
        r = run('ls -l %s' % GCC)
        if r.endswith(VERSION):
            make_link = False

    if make_link:
        run('rm -rf %s' % GCC)
        run('ln -s %s-4.3 %s' % (GCC, GCC))

    # disable Nouveau driver
    FILENAME = '/etc/modprobe.d/nvidia-installer-disable-nouveau.conf'
    run('touch %s' % FILENAME)
    content = """# generated by nvidia-installer
blacklist nouveau
options nouveau modeset=0
"""
    append(FILENAME, content, partial=True, use_sudo=True)

    # download driver
    VERSION = '295.53'
    FILENAME = 'NVIDIA-Linux-x86-%s.run' % VERSION
    wget('http://us.download.nvidia.com/XFree86/Linux-x86/%s/%s' \
         % (VERSION, FILENAME))

    INSTALLER = ' %s/%s' % (DOWNLOADS, FILENAME)
    run('chmod a+x %s' % INSTALLER)

    reboot()

    # stop GDM and
    time.sleep(10)
    run('/etc/init.d/gdm3 stop')
    run('%s --silent --uninstall' % (INSTALLER))
    run('%s --silent --no-nouveau-check --run-nvidia-xconfig' % (INSTALLER))
    reboot()




@task
@roles('ubuntu')
def nividia_brightness():
    put('nvidia/nvidia-brightness.sh', '/usr/local/bin/nvidia-brightness.sh', use_sudo=True)


#---------------------------------------------------------------------
# Macbook Tasks
#---------------------------------------------------------------------
@roles('ubuntu', 'home', )
@task
def fix_efiboot():
    "Assure that the system can recover Mac OS partition"
    regexp = re.compile(r'Boot(\d+)')
    partitions = []
    macpartition = None
    for line in sudo('efibootmgr').splitlines():
        m = regexp.match(line)
        if m:
            key = m.groups()[0]
            if 'Mac OS' in line:
                macpartition = True
                partitions.insert(0, key)
            else:
                partitions.append(key)

    if macpartition:
        print('reordering boot order to set MAC OS or rEFI 1st')
        sudo('efibootmgr -o %s' % ','.join(partitions))
    else:
        print('No MAC OS found')


#---------------------------------------------------------------------
# Group of Tasks
#---------------------------------------------------------------------
@task
@roles('ubuntu')
def all():
    execute(fix_efiboot)

    execute(base)
    execute(restricted_drivers)

    execute(admin)
    execute(install_vivaldi)
    execute(install_chrome)
    #execute(protection)
    #execute(desktop)
    execute(multimedia)
    #execute(virtualization)

    execute(resilio)
    execute(sublimetext)
    execute(install_wingide)

    execute(nividia_brightness)

    #execute(remove_tracking)
    print "-End-"


@task
@roles('ubuntu')
def test():
    execute(base)
    execute(admin)
    execute(install_chrome)
    execute(install_vivaldi)
    #execute(protection)
    #execute(desktop)
    execute(multimedia)
    #execute(virtualization)

    execute(resilio)
    execute(sublimetext)
    execute(install_wingide)

    execute(nividia_brightness)

    #execute(remove_tracking)
    print "-End-"

@task
def uptime():
    run('uptime')
