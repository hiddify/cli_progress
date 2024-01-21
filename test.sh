#!/bin/bash

for ((c = 1; c <= 10; c++)); do
    echo "factor: $c" 
    echo "####$c####title: $c####descr: $c#####"
    sleep 0.1
done

for ((c = 1; c <= 10; c++)); do
    echo "factor: $c" >&2
    echo "####$c####title: $c####descr: $c#####"
    sleep 0.1
done


