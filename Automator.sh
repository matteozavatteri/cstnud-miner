#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo "Usage: $0 <BenchDir>"
	exit
fi

rm -rf mined
mkdir mined
mkdir mined/stats
name=$1

for d in `ls $name`; do
    stats=mined/stats/$d
    mkdir mined/$d
    for f in `ls $name/$d`; do
        log=$name/$d/$f
        network=mined/$d/$f
	echo $log
        python3 cstnud-miner.py -m $log $network
        cat ._stats >> $stats
    done
done

rm -rf ._*
