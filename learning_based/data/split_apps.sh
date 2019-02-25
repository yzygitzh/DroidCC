rm -rf run
mkdir -p run

head -n   64 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4444"}' > run/cluster01_androtest.sh
head -n  128 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4445"}' > run/cluster02_androtest.sh
head -n  192 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4446"}' > run/cluster03_androtest.sh
head -n  256 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4447"}' > run/cluster04_androtest.sh
head -n  320 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4448"}' > run/cluster05_androtest.sh
head -n  384 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4449"}' > run/cluster06_androtest.sh
head -n  448 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4450"}' > run/cluster07_androtest.sh
head -n  512 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4451"}' > run/cluster08_androtest.sh
head -n  576 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4452"}' > run/cluster09_androtest.sh
head -n  640 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4453"}' > run/cluster10_androtest.sh
head -n  704 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4454"}' > run/cluster11_androtest.sh
head -n  768 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4455"}' > run/cluster12_androtest.sh
head -n  832 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4456"}' > run/cluster13_androtest.sh
head -n  896 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4457"}' > run/cluster14_androtest.sh
head -n  960 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4458"}' > run/cluster15_androtest.sh
head -n 1024 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4459"}' > run/cluster16_androtest.sh
head -n 1088 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4460"}' > run/cluster17_androtest.sh
head -n 1152 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4461"}' > run/cluster18_androtest.sh
head -n 1216 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4462"}' > run/cluster19_androtest.sh
head -n 1280 app_list.txt | tail -n 64 | awk '{print "bash seed.sh "$1" 4463"}' > run/cluster20_androtest.sh
