# according to https://en.wikipedia.org/wiki/Raspberry_Pi, the soc of raspberrypi 2.1.2/3/3+
# is bcm2837, the difference between them is other hardware. it will reduce our work if we use soc as tag.

if(DEFINED POLLY_RASPBERRYPI_BCM2837_CMAKE)
  return()
else()
  set(POLLY_RASPBERRYPI_BCM2837_CMAKE 1)
endif()

set(ENV{RASPBERRYPI_CROSS_COMPILE_TOOLCHAIN_PATH} "$ENV{RASPBERRYPI_HOME}/arm-rpi-4.9.3-linux-gnueabihf/bin")
set(ENV{RASPBERRYPI_CROSS_COMPILE_TOOLCHAIN_PREFIX} "arm-linux-gnueabihf")
set(ENV{RASPBERRYPI_CROSS_COMPILE_SYSROOT} "$ENV{RASPBERRYPI_HOME}/arm-rpi-4.9.3-linux-gnueabihf/arm-linux-gnueabihf/sysroot")
include("${CMAKE_CURRENT_LIST_DIR}/raspberrypi3-gcc-pic-hid-sections.cmake")
