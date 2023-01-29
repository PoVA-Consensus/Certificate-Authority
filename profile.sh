#!/bin/bash

info=$(sudo dmidecode -t system)
manufacturer=$(grep "" /sys/class/dmi/id/sys_vendor)
product_name=$(grep "" /sys/class/dmi/id/board_name)

mac_address=$(ifconfig | grep -Po 'ether \K\S+')

echo "{\"Manufacturer_name\":\"$manufacturer\",\"Device_name\":\"$product_name\",\"MAC_address\":\"$mac_address\"}" > device_info.json
