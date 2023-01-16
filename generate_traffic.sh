#!/bin/bash

iperf -s -u &
ips=($1)
len=$( expr ${#ips[@]} - 1 )
id=$2

while :
do
    ruch=$(shuf -i 10-60 -n 1) 
    echo "${2} generate traffic to ${ips[$i]} with ${ruch} Mbits/s" >> results${2}.txt
    i=$(shuf -i 0-${len} -n 1) 
    iperf -c $(echo "${ips[$i]}") -u -t 15 -b $(echo "${ruch}")Mbits >> results${2}.txt
    waiting=$(shuf -i 1-5 -n 1)
    echo "No traffic for ${waiting} seconds" >>  results${2}.txt
    sleep ${waiting}
done