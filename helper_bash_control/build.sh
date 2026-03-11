cd ../gr-AoA_mod
sudo rm -rf build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$(gnuradio-config-info --prefix) ..
make
sudo make install