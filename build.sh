#!/bin/bash
# Mugsy build script
# builds a stand-alone executable with cx_freeze and packages it into an rpm.
#
if [[ -z "$1" ]]; then
  echo "You need to specify the next version number. e.g.:  ./build.sh 0.5.8"
  exit 1
fi

# settings
export MUGSY_VER=${1}
packagedir=${HOME}/mugsy-pkg

# do work
cd /home/zzjason/mugsy
echo "Deleting pyc files..."
find . -name "*.pyc" -exec rm -rf {} \;
source bin/activate

echo "Building..."
python setup.py install

echo "Preparing for packaging..."
echo "Destroying old packaging directory ${packagedir}..."
sudo rm -rf ${packagedir}

echo "Creating packaging directory structure..."
sudo mkdir -p ${packagedir}/etc/init.d
sudo mkdir -p ${packagedir}/var/mugsy

echo "Copying build files to package directory..."
sudo cp -r lib/mugsy-${1} ${packagedir}/var/mugsy/lib

echo "Copying misc files to package directory..."
sudo cp config.yml.example ${packagedir}/var/mugsy/
sudo cp init.sh ${packagedir}/var/mugsy/lib/
sudo cp mugsy.init.d ${packagedir}/etc/init.d/mugsy

# set strict owner and perms that the rpm package should take on
sudo chmod 700 ${packagedir} -R
sudo chown root:root ${packagedir} -R

#sudo yumify --no-upload --source ${packagedir} --rpm-name mugsy --ver ${1} --after-install ${packagedir}/lib/init.sh
echo "Packaging into an rpm..."
sudo /usr/bin/fpm --rpm-use-file-permissions --after-install /var/mugsy/lib/init.sh -s dir -t rpm --package ${HOME} --no-auto-depends -n mugsy -v ${1} -C ${packagedir} var/mugsy/lib/ var/mugsy/config.yml.example etc/init.d/mugsy