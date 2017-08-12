set -e
cd `dirname $0`
if [ ! -e ../external/libusb-1.0.21-windows/ ]; then
	mkdir -p ../external
	pushd ../external
	wget https://github.com/libusb/libusb/releases/download/v1.0.21/libusb-1.0.21.7z
	workdir=`pwd`
	# Unfortunately the binary release uses 7-zip so we need the user to install this
	printf "Please install 7-zip from http://www.7-zip.org/ad extract the file at $workdir, to directory libusb-1.0.21.  Press enter when extracted"
	read
	mv libusb-1.0.21 libusb-1.0.21-windows
	popd
fi
if [ -d /C/Windows/SysWOW64 ]; then
  cp ../external/libusb-1.0.21-windows/MS64/dll/libusb-1.0.dll /C/Windows/System32
  cp ../external/libusb-1.0.21-windows/MS32/dll/libusb-1.0.dll /C/Windows/SysWOW64/
else
  cp ../external/libusb-1.0.21-windows/MS32/dll/libusb-1.0.dll /C/Windows/System32/
fi
git submodule update --init
pushd ../external/pyusb
python setup.py install
