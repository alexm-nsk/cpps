python3 sisal.py -i $1 | g++ -w -xc++ - -ljsoncpp -o $1_bin; echo $2| ./$1_bin ; rm $1_bin
