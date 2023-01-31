#!/bin/bash

iperf -s -u &
ips=($1)
len=$( expr ${#ips[@]} - 1 )
id=$2

while :
do
    # Krakow do Gdanska reszta background ruch
    if [ "${2}" == "10.0.0.6" ]
    then 
        echo "${2} generate traffic to 10.0.0.3 with 900 Kbits/s" >> results/results${2}.txt 
        iperf -c 10.0.0.3 -u -t 20 -b 800Kbits >> results/results${2}.txt
        waiting=$(shuf -i 1-2 -n 1)
        echo "No traffic for ${waiting} seconds" >>  results/results${2}.txt
        sleep ${waiting}
    elif [ "${2}" == "10.0.0.3" ]
    then
        echo "No traffic for ${waiting} seconds" >>  results/results${2}.txt
        sleep ${waiting}
    else
        ruch=$(shuf -i 100-300 -n 1) 
        echo "${2} generate traffic to ${ips[$i]} with ${ruch} Kbits/s" >> results/results${2}.txt
        i=$(shuf -i 0-${len} -n 1) 
        iperf -c $(echo "${ips[$i]}") -u -t 20 -b $(echo "${ruch}")Kbits >> results/results${2}.txt
        waiting=$(shuf -i 1-5 -n 1)
        echo "No traffic for ${waiting} seconds" >>  results/results${2}.txt
        sleep ${waiting}
    fi
done